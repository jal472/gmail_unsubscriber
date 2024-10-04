import os.path
import argparse

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# readonly scope only necessary for reading message bodies
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
API_NAME = "gmail"
API_VERSION = "v1"
USER_EMAIL_ENDPOINT = "https://www.googleapis.com/oauth2/v2/userinfo?access_token="


def gmail_authenticate() -> Credentials:
    if os.path.exists("credentials.json") is False:
        print("File Not Found Error: \"credentials.json\" is missing. Please be sure to pull your credentials.json file from your Google Cloud account. See details here on how to generate this: https://developers.google.com/gmail/api/quickstart/python#authorize_credentials_for_a_desktop_application")
        exit()
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
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return creds


def get_emails(creds: Credentials, filter: str = None) -> list:
    # Call the Gmail API
    service = build("gmail", "v1", credentials=creds)
    results = ""
    if filter is not None:
        results = service.users().messages().list(userId="me", q=filter).execute()
    else:
        results = service.users().messages().list(userId="me").execute()

    return results["messages"]


def get_email_contents(creds: Credentials, email_id: str):
    service = build("gmail", "v1", credentials=creds)
    results = service.users().messages().get(userId="me", id=email_id).execute()
    print(results["payload"]["parts"])


def unsubscribe_scrape(creds: Credentials, email_ids: list):
    # For each file in the inbox, click unsubscribe.
    get_email_contents(creds=creds, email_id=email_ids[0]["id"])
    # for email in email_ids:
    #     get_email_contents(creds=creds, email_id=email["id"])
    # No need to fill out a form - clicking unsubscribe works.
    # Form needs to be filled out on unsubscribing site - these will likely be unique.


def main(args: dict):
    # Make sure the file is being run from its current working directory
    curr_file_path = os.path.dirname(os.path.abspath(__file__))
    os.chdir(curr_file_path)

    # (1) Authorize and Authenticate into Gmail account
    creds = gmail_authenticate()
    if creds is None:
        print("Credentials are not valid. Adjust your authentication code and rerun.")
        exit()
    # (2) Filter email messages based on the user query provided
    email_ids = get_emails(creds=creds, filter=args["filter"])
    # (3) Scrape the email contents and unsubscribe to the marketing email
    unsubscribe_scrape(creds=creds, email_ids=email_ids)


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
