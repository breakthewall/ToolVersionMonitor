from os import (
    path as os_path
)
from logging import (
    Logger,
    getLogger,
    DEBUG
)
from csv import DictReader as csv_DictReader
from typing import Dict
import re
from gspread import authorize as gspread_authorize
from oauth2client.service_account import ServiceAccountCredentials

from .Tool import Tool


def read_from_file(
    filename: str,
    github_token: str='',
    logger: Logger = getLogger(__name__)
) -> Dict:
    tools = {}
    with open(filename, mode='r') as f:
        records = csv_DictReader(f)
        for row in records:
            tools[
                row['NAME'].lower().replace(' ', '_')
            ] = Tool(
                {k.lower(): v for k, v in row.items()},
                github_token=github_token,
                logger=logger
            )
    return tools

def read_from_googlesheet(
    googlesheet: str,
    googleapi: str,
    github_token: str='',
    logger: Logger = getLogger(__name__)
) -> Dict:
    # define the scope
    scope = [
        'https://www.googleapis.com/auth/spreadsheets.readonly',
        'https://www.googleapis.com/auth/drive'
    ]

    # add credentials to the account
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        googleapi,
        scope
    )

    # authorize the clientsheet 
    client = gspread_authorize(creds)

    # get the instance of the Spreadsheet
    sheet = client.open(googlesheet)

    # get the first sheet of the Spreadsheet
    sheet_instance = sheet.get_worksheet(0)

    # get all the records of the data
    records_data = sheet_instance.get_all_records()

    tools = {}
    for row in records_data[1:]:
        tools[
            row['TOOL NAME'].lower().replace(' ', '_')
        ] = Tool(
            values={
                re.sub(r'\s+', '_', k.lower()): v
                for k, v in row.items()
            },
            github_token=github_token,
            logger=logger
        )

    return tools

