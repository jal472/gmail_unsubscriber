import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def main():
    # Make sure the file is being run from its current working directory
    curr_file_path = os.path.dirname(os.path.abspath(__file__))
    os.chdir(curr_file_path)

    # (1) Authorize and Authenticate into Gmail account

    # (2) Get Inbox

    # (3) For each file in the inbox, click unsubscribe.
    #   (3.1) No need to fill out a form - clicking unsubscribe works.
    #   (3.2) Form needs to be filled out on unsubscribing site - these will likely be unique.


if __name__ == "__main__":
    main()
