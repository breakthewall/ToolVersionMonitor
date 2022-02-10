from copy import deepcopy
from os import (
    getenv,
    path as os_path
)

from requests import (
    get as requests_get,
    JSONDecodeError
)
from json import dump as json_dump
from typing import Dict
from brs_utils import download
from logging import (
    Logger,
    getLogger
)

from .Const import *


class Tool:

    __FIELDS = [
        'TOOL NAME',
        'GITHUB REPO', 'GITHUB OWNER',
        'CONDA PACKAGE', 'CONDA CHANNEL',
        'GALAXY WRAPPER', 'GALAXY OWNER'
    ]

    def __init__(
        self,
        values: Dict,
        github_token: str='',
        logger: Logger = getLogger(__name__)
    ):
        self.__logger = logger
        self.__GitHub_TOKEN = github_token
        self.__attributes = deepcopy(values)
        self.force_check()

    @staticmethod
    def fields(logger: Logger = getLogger(__name__)) -> str:
        return Tool.__FIELDS

    @staticmethod
    def field(i: int, logger: Logger = getLogger(__name__)) -> str:
        try:
            return Tool.__FIELDS[i]
        except IndexError as e:
            logger.warning(f'Index {i} is out of range of {Tool.fields()}')
            return ''

    def __repr__(self):
        return f'Tool("{self.__name}")'

    def __str__(self):
        return f'{vars(self)}'
    
    def dict(self) -> Dict:
        return self.__attributes

    def name(self) -> str:
        return self.__attributes[Tool.field(0, self.__logger)]

    def github_repo(self) -> str:
        return self.__attributes[Tool.field(1, self.__logger)]

    def github_owner(self) -> str:
        return self.__attributes[Tool.field(2, self.__logger)]

    def conda_package(self) -> str:
        return self.__attributes[Tool.field(3, self.__logger)]

    def conda_pkg(self) -> str:
        return self.conda_package()

    def conda_channel(self) -> str:
        return self.__attributes[Tool.field(4, self.__logger)]

    def galaxy_wrapper(self) -> str:
        return self.__attributes[Tool.field(5, self.__logger)]

    def galaxy_owner(self) -> str:
        return self.__attributes[Tool.field(6, self.__logger)]

    def force_check(self):
        self.__logger.debug(self.name())
        self.__logger.debug('='*len(self.name()))
        self.__logger.debug(f'Loading GitHub {self.name()} release ')
        self.__github_latest_release = self.github_latest_release(True)
        self.__logger.debug(f'Loading GitHub {self.name()} badge ')
        self.set_or_fetch_github_badge(True)
        self.__logger.debug(f'Loading Conda {self.name()} release ')
        self.__conda_latest_release = self.conda_latest_release(True)
        self.__logger.debug(f'Loading Conda {self.name()} badge ')
        self.set_or_fetch_conda_badge(True)
        self.__logger.debug(f'Loading Galaxy {self.name()} release ')
        self.__galaxy_latest_release = self.galaxy_latest_release(True)
        self.__logger.debug(f'Loading Galaxy {self.name()} badge ')
        self.set_or_fetch_galaxy_badge(True)

    def github_latest_release(self, force=False) -> str:
        if force:
            if self.__GitHub_TOKEN != '':
                token = getenv('GITHUB_TOKEN', self.__GitHub_TOKEN)
                headers = {'Authorization': f'token {token}'}
                self.__logger.debug(token)
                self.__logger.debug(headers)
            else:
                headers = {}
            query_url = f"https://api.github.com/repos/{self.github_owner()}/{self.github_repo()}/releases/latest"
            self.__logger.debug(query_url)
            r = requests_get(query_url, headers=headers)
            try:
                self.__logger.debug(r.json())
                return r.json().get('tag_name', '')
            except JSONDecodeError as e:
                self.__logger.debug(r)
                return ''
        else:
            return self.__github_latest_release

    def conda_latest_release(self, force=False) -> str:
        if force:
            query_url = f'https://api.anaconda.org/package/{self.conda_channel()}/{self.conda_pkg()}'
            self.__logger.debug(query_url)
            r = requests_get(query_url)
            try:
                self.__logger.debug(r.json())
                return r.json().get('latest_version', '')
            except JSONDecodeError as e:
                self.__logger.debug(r)
                return ''
        else:
            return self.__conda_latest_release

    def galaxy_latest_release(self, force=False) -> str:
        if is_None(self.galaxy_wrapper()) or is_None(self.galaxy_owner()):
            return ''
        if force:
            headers = {'content-type': 'application/json'}
            main_url = 'https://toolshed.g2.bx.psu.edu/api'
            # Get the latest release ID
            rel_id = self.__get_galaxy_latest_rel_id(main_url, headers)
            # Get version of the latest release
            return self.__get_galaxy_latest_release(main_url, headers, rel_id)
        else:
            return self.__galaxy_latest_release

    def __get_galaxy_latest_rel_id(
        self,
        main_url: str,
        headers: str
    ) -> str:
        r = requests_get(
            main_url + '/repositories/get_ordered_installable_revisions',
            params={"name": self.galaxy_wrapper(), "owner": self.galaxy_owner()},
            headers=headers
        )
        try:
            changeset_rev = r.json()
            self.__logger.debug(r.json())
            return changeset_rev[-1]
        except JSONDecodeError as e:
            return ''

    def __get_galaxy_latest_release(
        self,
        main_url: str,
        headers: str,
        rel_id: str
    ) -> str:
        r = requests_get(
            main_url + '/repositories/get_repository_revision_install_info',
            params={"name": self.galaxy_wrapper(), "owner": self.galaxy_owner(), "changeset_revision": rel_id},
            headers=headers
        )
        datas = r.json()
        self.__logger.debug(r.json())
        return datas[1]['valid_tools'][0]['version']

    def github_badge(self) -> str:
        badge = self.set_or_fetch_github_badge()
        link = f'https://github.com/{self.github_owner()}/{self.github_repo()}'
        self.__logger.debug(badge)
        return f'<a href="{link}"><img src="badges/{badge}" alt="{self.github_repo()} GitHub latest release"></a>'

    def set_or_fetch_github_badge(self, force=False):
        badge = f'GitHub_{self.github_owner()}_{self.github_repo()}.svg'
        badge_abs = os_path.join(BADGES_PATH, badge)
        if force or not os_path.exists(badge_abs):
            download(
                f'https://img.shields.io/badge/dynamic/json?url=https://api.github.com/repos/{self.github_owner()}/{self.github_repo()}/releases/latest&label=GitHub&query=tag_name&style=plastic',
                badge_abs
            )
        self.__logger.debug(badge)
        self.__logger.debug(badge_abs)
        return badge

    def conda_badge(self) -> str:
        badge = self.set_or_fetch_conda_badge()
        link = f'https://anaconda.org/{self.conda_channel()}/{self.conda_pkg()}'
        self.__logger.debug(badge)
        return f'<a href="{link}"><img src="badges/{badge}" alt="{self.conda_pkg()} Conda latest release"></a>'

    def set_or_fetch_conda_badge(self, force=False) -> str:
        badge = f'Conda_{self.conda_channel()}_{self.conda_pkg()}.svg'
        badge_abs = os_path.join(BADGES_PATH, badge)
        if force or not os_path.exists(badge_abs):
            color = get_color(
                self.github_latest_release(),
                self.conda_latest_release()
            )
            download(
                f'https://img.shields.io/badge/dynamic/json?url=https://api.anaconda.org/package/{self.conda_channel()}/{self.conda_pkg()}&label=Conda&query=latest_version&color={color}&style=plastic',
                badge_abs
            )
        self.__logger.debug(badge)
        self.__logger.debug(badge_abs)
        return badge

    def galaxy_badge(self) -> str:
        if is_None(self.galaxy_wrapper()) or is_None(self.galaxy_owner()):
            return ''
        badge = self.set_or_fetch_galaxy_badge()
        link = f'https://toolshed.g2.bx.psu.edu/view/{self.galaxy_owner()}/{self.galaxy_wrapper()}'
        self.__logger.debug(badge)
        return f'<a href="{link}"><img src="badges/{badge}" alt="{self.galaxy_wrapper()} Conda latest release"></a>'

    def set_or_fetch_galaxy_badge(self, force=False) -> str:
        if is_None(self.galaxy_wrapper()) or is_None(self.galaxy_owner()):
            return ''
        badge = f'Galaxy_{self.galaxy_owner()}_{self.galaxy_wrapper()}.svg'
        badge_abs = os_path.join(BADGES_PATH, badge)
        if force or not os_path.exists(badge_abs):
            color = get_color(
                self.github_latest_release(),
                self.galaxy_latest_release()
            )
            # Create a local endpoint to download from shields.io
            endpoint = {
                'latest_version': self.galaxy_latest_release()
            }
            with open(f'{badge_abs}.json', 'w') as f:
                json_dump(endpoint, f)
            download(
                f'https://img.shields.io/badge/dynamic/json?url=https://tvm.micalis.inrae.fr/badges/{badge}.json&label=Galaxy&query=latest_version&color={color}&style=plastic',
                badge_abs
            )
        self.__logger.debug(badge)
        self.__logger.debug(badge_abs)
        return badge


def get_color(v1: str, v2: str) -> str:
    try:
        # Remove 'v' prefix before version number
        if v1[0] in ['v', 'V']:
            v1 = v1[1:]
        if v2[0] in ['v', 'V']:
            v2 = v2[1:]
        return 'brightgreen' if v1 == v2 else 'red'
    except IndexError as e:
        return 'grey'

def is_None(value: str) -> bool:
    return value is None or value == 'None' or value == ''
