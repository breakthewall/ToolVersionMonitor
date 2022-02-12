from os import (
    path as os_path
)
from logging import (
    Logger,
    getLogger,
    DEBUG
)
from csv import (
    reader as csv_reader,
    DictReader as csv_DictReader,
    DictWriter as csv_DictWriter
)
from typing import (
    Dict,
    List
)
from gspread import authorize as gspread_authorize
from oauth2client.service_account import ServiceAccountCredentials

from .Const import CACHE_FILE, VERSIONS_FILE
from .Tool import Tool
from .Args import DEFAULT_sourcefile


def read_from_file(
    filename: str,
    logger: Logger = getLogger(__name__)
) -> Dict:
    data = []
    with open(filename) as csvfile:
        reader = csv_reader(csvfile)
        headers = next(reader)

        for row in reader:
            row_data = {key: value for key, value in zip(headers, row)}
            data.append(row_data)
    return data

def read_from_googlesheet(
    googlesheet: str,
    googleapi: str,
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

    return records_data[1:]


def save_to_cache(
    tools: Dict[str, Tool],
    logger: Logger = getLogger(__name__)
):
    logger.debug(tools)
    tool_lst = [tool.dict() for tool in tools.values()]
    tool_cat = tool_lst[0].keys()
    version_cat = ['name'] + list(list(tools.values())[0].get_versions().keys())
    version_lst = [
        {
            'name': tool.name(),
            **tool.get_versions()
        } for tool in tools.values()
    ]
    # version_cat = ['name'] + list(list(version_lst[0].values())[0].keys())
    # print(tool_cat)
    # print(tool_lst)
    # print(version_cat)
    # print(version_lst)
    # Write tool references
    with open(CACHE_FILE, 'w') as csvfile:
        writer = csv_DictWriter(csvfile, fieldnames=tool_cat)
        writer.writeheader()
        writer.writerows(tool_lst)
    # # Write tool versions
    # with open(VERSIONS_FILE, 'w') as csvfile:
    #     writer = csv_DictWriter(csvfile, fieldnames=version_cat)
    #     writer.writeheader()
    #     writer.writerows(version_lst)
