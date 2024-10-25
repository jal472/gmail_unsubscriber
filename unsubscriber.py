import os.path
import argparse
import base64
from bs4 import BeautifulSoup
import requests
import time

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError
from google.auth.exceptions import RefreshError

# Global Vars
# readonly scope only necessary for reading message bodies
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
API_NAME = "gmail"
API_VERSION = "v1"
USER_EMAIL_ENDPOINT = "https://www.googleapis.com/oauth2/v2/userinfo?access_token="
GMAIL_CREDENTIALS = None
UNSUBSCRIBE_LINK_COUNT = 0
UNSUBSCRIBE_LINK_STR_LIST = ['unsubscribe', 'preferences']
GMAIL_SERVICE = None


def gmail_user_auth() -> Credentials:
    '''
    Let user login to grant access to their account.
    '''
    flow = InstalledAppFlow.from_client_secrets_file(
        "credentials.json", SCOPES
    )
    creds = flow.run_local_server(port=0)
    return creds


def gmail_authenticate():
    '''
    Authenticate the user with Google API. Returns a Google API Credentials object.
    '''
    if os.path.exists("credentials.json") is False:
        print("File Not Found Error: \"credentials.json\" is missing. Please be sure to pull your credentials.json file from your Google Cloud account. See details here on how to generate this: https://developers.google.com/gmail/api/quickstart/python#authorize_credentials_for_a_desktop_application")
        exit()
    global GMAIL_CREDENTIALS
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    # If token.json is present, user has already granted access prior.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except RefreshError as e:
                print("Google Auth RefreshError: ", e)
                print("Getting new credentials...")
                creds = gmail_user_auth()
            except Exception as e:
                print("General Exception Caught: ", e)
                print("Getting new credentials...")
                creds = gmail_user_auth()
        else:
            creds = gmail_user_auth()
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    GMAIL_CREDENTIALS = creds


def gmail_message_search(service: Resource, filter: str = None, pageToken: str = None) -> dict:
    '''
    Make gmail api call to get emails
    '''
    options = {
        'userId': 'me',  # Use 'me' for the authenticated user
        'q': filter,  # Example query to get unread messages
        'pageToken': pageToken,  # Replace with a valid token if needed
        'maxResults': 49,  # Maximum number of results to return - set this to 49 to stay within the 250 quota limit per second
    }
    # update options excluding None values
    options = {k: v for k, v in options.items() if v is not None}
    results = service.users().messages().list(**options).execute()
    return results


def get_unsubscribe_link(email_id: str) -> str:
    '''
    Given an email id, get the contents in html and use beautiful soup to quickly find the unsubscribe link.
    '''
    unsubscribe_link = ""
    service = build("gmail", "v1", credentials=GMAIL_CREDENTIALS)
    results = ""
    # Call the Gmail API to get the email contents
    try:
        results = service.users().messages().get(
            userId="me",
            id=email_id,
            format="full"
        ).execute()
    except Exception as e:
        print("Error when using gmail api to get email contents: ", e)
        return ""

    # Extract the HTML content from the email payload
    try:
        message_parts = results["payload"]["parts"]
        for part in message_parts:
            decoded_html = base64.urlsafe_b64decode(
                part["body"]["data"].encode('UTF8'))

            # use beautiful soup to ingest the html content and sort based on <a> - anchor tags (FIND UNSUBSCRIBE LINK)
            soup = BeautifulSoup(markup=decoded_html, features="html.parser")

            links = soup.find_all("a")
            unsubscribe_found = False
            for link in links:
                if link.contents:
                    lower_link_contents = str(link.contents[0]).lower()

                    # using list comprehension
                    # checking if link contents contains possible unsubscribe strings
                    res = any(ele in lower_link_contents for ele in UNSUBSCRIBE_LINK_STR_LIST)  # nopep8
                    if res:
                        # prefer unsubscribe
                        if "unsubscribe" in lower_link_contents:
                            unsubscribe_found = True
                            unsubscribe_link = link.get("href")
                        elif not unsubscribe_found:
                            unsubscribe_link = link.get("href")
    except Exception as e:
        # print("Error when accessing email contents: ", e)
        pass

    return unsubscribe_link


def request_unsubscribe_link(link: str):
    '''
    Given and unsubscribe link, use the requests package to make an http request to the url.
    '''
    global UNSUBSCRIBE_LINK_COUNT
    try:
        response = requests.get(link)
        if response.status_code == 200:
            UNSUBSCRIBE_LINK_COUNT += 1
        # TODO: Integrate Google's Gemini LLM to tell us how to fill out forms on the next page
    except Exception as e:
        # For now, suppress the error message. TODO: Add this to a log file.
        # print("Request Failed for link: ", link)
        # print("General Exception Caught: ", e)
        pass


def unsubscribe_scrape(email_ids: list):
    '''
    Given a list of emails, scrape the email for the unsubscribe link and access it to unsubscribe the user.
    '''
    # For each file in the inbox, click unsubscribe.
    count = 0
    for email in email_ids:
        unsubscribe_link = get_unsubscribe_link(email_id=email["id"])
        if unsubscribe_link != "":
            count += 1
            # Make http request to access the link to unsubscribe - currently assumes just accessing the link will unsubscribe the user.
            request_unsubscribe_link(link=unsubscribe_link)
            #   No need to fill out a form - clicking unsubscribe works.
            #   Form needs to be filled out on unsubscribing site - these will likely be unique.

    print(f"Attempted to unsubscribe from: {count}")


def main(args: dict):
    '''
    Main function to unsubscribe a gmail user from marketing emails.
    '''
    # Make sure the file is being run from its current working directory
    curr_file_path = os.path.dirname(os.path.abspath(__file__))
    os.chdir(curr_file_path)

    # (1) Authorize and Authenticate into Gmail account
    print("Authenticating access to Gmail account...")
    gmail_authenticate()
    if GMAIL_CREDENTIALS is None:
        print("Credentials are not valid. Adjust your authentication code and rerun.")
        exit()

    # Call the Gmail API
    service = build("gmail", "v1", credentials=GMAIL_CREDENTIALS)
    results = ""
    page_count = 1
    email_count = 0
    while True:
        # (2) Filter email messages based on the user query provided
        email_ids = []
        print(f"Getting email messages on page {page_count}")
        if "nextPageToken" in results:
            # use next page token to continue appending email ids
            results = gmail_message_search(
                service=service, filter=args["filter"], pageToken=results["nextPageToken"])
            email_ids = results["messages"]
        elif results == "":
            # perform first search
            results = gmail_message_search(
                service=service, filter=args["filter"])
            email_ids = results["messages"]
        else:
            # otherwise break
            break
        email_count += len(email_ids)

        print(f"Current GMail quota units used: {(len(email_ids)+1)*5}")

        # (3) Scrape the email contents and unsubscribe to the marketing email
        print("Unsubscribing from marketing emails...")
        unsubscribe_scrape(email_ids=email_ids)

        # We want to sleep for 1 second between the many calls to the gmail api being made.
        # This will prevent us from hitting request limit (250 quota units per user per second)
        print("entering sleep to prevent quota limit...")
        time.sleep(1)
        print()

        page_count += 1

    # Report to user the amount of emails attempted to unsubscribe from
    print(f"Total unsubscribe attempts: {UNSUBSCRIBE_LINK_COUNT} out of {email_count}.")  # nopep8


# my filter:  "unsubscribe -{usps, linkedin, amazon web services, geico}"
if __name__ == "__main__":
    # parse args
    parser = argparse.ArgumentParser(
        prog="gmail-unsubscriber",
        description="Unsubscribes you from marketing emails in your gmail account.",
    )
    parser.add_argument(
        "-f", "--filter",
        default=None,
        type=str,
        help="String in Gmail's advanced search syntax. See https://support.google.com/mail/answer/7190 for details. WARNING: This app currently does not validate the input search string. Be careful to test your search in gmail itself first to make sure it is the desired filter.",
        dest="filter"
    )
    args = vars(parser.parse_args())
    # If the user does not input a filter, make sure they want to proceed. If they do not provide a filter, the app will unsubscribe on all emails and that may not be the desired result.
    if args["filter"] is None:
        resp = input(
            "You have not specified a filter. Do you wish to continue? (y=yes OR n=no): "
        ).lower()
        if resp != "y" and resp != "yes":
            print("Rerun the program with the \"-f --filter\" option. Use the \"-h --help\" option to see details on filter formatting.")
            exit()
    # run the main function
    main(args)
