from __future__ import print_function
import os
import re
import time
import sys
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from itertools import zip_longest

# Shared function to get credentials
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
def resourcePath(relativePath):
    #Get absolute path to resource, works for dev and for PyInstaller
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        basePath = sys._MEIPASS
    except Exception:
        basePath = os.path.abspath(".")

    return os.path.join(basePath, relativePath)

def get_credentials() -> Credentials:
    creds = None
    token_path = resourcePath('credentials/token.json')
    client_secret_path = resourcePath('credentials/credentials.json')

    # Check if token file exists and load credentials
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    # If no valid credentials are available, get new ones
    if not creds or not creds.valid:
        # If the credentials exist but are expired, try refreshing
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Failed to refresh token: {e}")
                # Delete the expired token and obtain a new one
                os.remove(token_path)
                return get_credentials()  # Retry with a fresh flow
        else:
            # No valid credentials or cannot refresh, initiate new authorization flow
            flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, SCOPES)
            creds = flow.run_local_server(port=0)
            # Save the new token for future use
            with open(token_path, 'w') as token:
                token.write(creds.to_json())

    return creds
def initialize_sheets_service():
    creds = get_credentials()
    service = build('sheets', 'v4', credentials=creds)
    return service

def find_first_empty_row(service, spreadsheet_id, sheetstring='Sheet1'):
    try:
        result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=sheetstring).execute()
        values = result.get('values', [])
        return len(values) + 1 if values else 1
    except HttpError as e:
        print(f"Error finding empty row: {e}")
        return None

def append_column_as_values(service, spreadsheet_id, sheetstring, start_row, column_letter, data):
    if start_row:
        values = [[item] if not isinstance(item, list) else [' '.join(item)] for item in data]
        range_to_append = f'{sheetstring}!{column_letter}{start_row}'

        request = {
            'valueInputOption': 'USER_ENTERED',
            'data': [{'range': range_to_append, 'values': values}]
        }
        response = service.spreadsheets().values().batchUpdate(spreadsheetId=spreadsheet_id, body=request).execute()
        print(f'Column {column_letter} data appended successfully.')
    else:
        print('No empty row found in the specified sheet.')

def append_2d_table_as_values(service, spreadsheet_id, sheetstring, start_row, data_2d):
    if start_row and data_2d:
        max_columns = max(len(row) for row in data_2d)
        data_2d_padded = [row + [''] * (max_columns - len(row)) for row in data_2d]
        range_to_append = f'{sheetstring}!A{start_row}:{chr(ord("A") + max_columns - 1)}{start_row + len(data_2d) - 1}'

        request = {
            'valueInputOption': 'USER_ENTERED',
            'data': [{'range': range_to_append, 'values': data_2d_padded}]
        }

        retries = 3
        max_retries = 6  # Max number of retries before giving up
        backoff_factor = 2  # Exponential backoff factor

        while retries < max_retries:
            try:
                response = service.spreadsheets().values().batchUpdate(spreadsheetId=spreadsheet_id, body=request).execute()
                print('2D table data appended successfully.')
                return  # Exit the function after successful upload
            except HttpError as error:
                if error.resp.status == 429:  # Rate limit exceeded
                    retries += 1
                    wait_time = backoff_factor ** retries  # Exponential backoff
                    print(f'Rate limit exceeded. Retrying in {wait_time} seconds...')
                    time.sleep(wait_time)
                else:
                    # If it's another error, re-raise it
                    raise error

        print('Max retries reached. Could not append data due to API rate limit.')
    else:
        print('No data or empty row found in the specified sheet.')

def main():
    service = initialize_sheets_service()
    spreadsheet_id = '1HbF_0IPMC_fZmMwPHXvmyhIlY5JFu1S2lp7Y3AwdDyU'
    first_empty_row = find_first_empty_row(service, spreadsheet_id, 'Sheet1')

    append_2d_table_as_values(service, spreadsheet_id, 'Sheet1', first_empty_row,[['Big Fish', 'Egoist', 'Super Surge']])
    #append_column_as_values(service, spreadsheet_id, 'Sheet1', first_empty_row, 'A', ['Big Fish', 'Egoist', 'Super Surge'])


if __name__ == '__main__':
    main()
