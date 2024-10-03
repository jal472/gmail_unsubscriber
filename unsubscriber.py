import os.path
import argparse

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# readonly scope only necessary for reading message bodies
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def gmail_authenticate():
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


def main(args: dict):
    # Make sure the file is being run from its current working directory
    curr_file_path = os.path.dirname(os.path.abspath(__file__))
    os.chdir(curr_file_path)

    # (1) Authorize and Authenticate into Gmail account
    gmail_authenticate()
    # (2) Filter email messages based on the user query provided

    # (3) For each file in the inbox, click unsubscribe.
    #   (3.1) No need to fill out a form - clicking unsubscribe works.
    #   (3.2) Form needs to be filled out on unsubscribing site - these will likely be unique.


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
