from copy import deepcopy
from os import (
    getenv,
    path as os_path
)

from types import MethodType
from requests import (
    get as requests_get,
    JSONDecodeError
)
from json import (
    dump as json_dump,
    load as json_load
)
from typing import *
from brs_utils import download
from logging import (
    Logger,
    getLogger
)
import re

from .Const import *
# from .Database import TVM_Database


# def make_get_platform_version(platform: str):
#     def get_platform_version(self):
#         return self.db().get_version(platform=platform, tool=self.name())
#     return get_platform_version

# def make_set_platform_version(platform: str):
#     def set_platform_version(self, version):
#         self.db().set_version(
#             platform=platform,
#             tool=self.name(),
#             version=version
#         )
#     return set_platform_version


class Tool:

    # __DB = TVM_Database(os_path.join(CACHE_PATH, 'tvm.db'))

    # conn.close()

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
        force: bool=True,
        logger: Logger = getLogger(__name__)
    ):
        self.__logger = logger
        self.__GitHub_TOKEN = github_token
        self.__attributes = deepcopy(values)
        self.__logger.debug(self.dict())
        # for platform in ['github', 'conda', 'galaxy']:
        #     setattr(
        #         self,
        #         f'get_{platform}_version',
        #         MethodType(make_get_platform_version(platform), self)
        #     )
        #     setattr(
        #         self,
        #         f'set_{platform}_version',
        #         MethodType(make_set_platform_version(platform), self)
        #     )
        # Tool.db().create_table__versions(['github', 'conda', 'galaxy'])
        # Tool.db().create_table__tools(list(values.keys()))
        self.__version_file = os_path.join(VERSIONS_PATH, f'{self.name()}.json')
        self.__versions = {}
        self.set_versions(force)
        self.__badges_path = os_path.join(BADGES_PATH)
        self.__badges = {}
        self.set_badges(force)

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
        return f'Tool("{self.__attributes[Tool.__FIELDS[0]]}")'

    def __str__(self):
        return f'{vars(self)}'
    
    def dict(self) -> Dict:
        return self.__attributes

    # def db():
    #     return Tool.__DB

    # def get_infos(self) -> Dict:
    #     return Tool.db().get_infos(self.name())

    # def set_infos(self, infos: Dict) -> Dict:
    #     return Tool.db().set_infos(self.name(), infos)

    def version_file(self) -> str:
        return re.sub(r'\s+', '_', self.__version_file)

    def badge_file(self, platform: str) -> str:
        return os_path.join(self.__badges_path, self.get_badge(platform))

    def get_versions(self) -> Dict:
        return self.__versions
        # return Tool.db().get_version(platform, self.name())

    def get_version(self, platform: str) -> str:
        return self.get_versions().get(platform, None)
        # return Tool.db().get_version(platform, self.name())

    def set_version(self, platform: str, version: str):
        # if not hasattr(self, '__versions'):
        #     self.get_versions = {}
        self.__versions[platform] = version
        self.update_versions_file(platform, version)
        # Tool.db().set_version(platform, self.name(), version)

    def set_badge(self, platform: str):
        self.__badges[platform] = f'{platform}_{self.name()}.svg'

    def get_badge(self, platform: str):
        return self.get_badges().get(platform, '')

    def get_badges(self):
        return self.__badges

    def name(self) -> str:
        return re.sub(r'\s+', '_', self.__attributes[Tool.field(0, self.__logger)])

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
        self.set_badges(True)

    def update_versions_file(self, platform: str, version: str):
        try:
            f = open(self.version_file())
            versions = json_load(f)
            f.close()
        except FileNotFoundError as e:
            versions = {}
        versions[platform] = version
        with open(self.version_file(), 'w') as f:
            json_dump(versions, f)
        # # Create a local endpoint to download from shields.io
        # endpoint = {
        #     'latest_version': self.galaxy_latest_release()
        # }

    def set_versions(self, force: bool):
        self.__logger.debug(self.name())
        self.__logger.debug('='*len(self.name()))
        if force or not os_path.exists(self.version_file()):
            self.__logger.debug(f'Fetching GitHub {self.name()} release ')
            self.fetch_github_latest_release()
            self.__logger.debug(f'Fetching Conda {self.name()} release ')
            self.fetch_conda_latest_release()
            self.__logger.debug(f'Fetching Galaxy {self.name()} release ')
            self.fetch_galaxy_latest_release()
        else:
            self.__logger.debug(f'Loading Galaxy {self.name()} releases ')
            with open(self.version_file()) as f:
                versions = json_load(f)
                for platform, version in versions.items():
                    self.set_version(platform, version)

    def platforms(self):
        return ['github', 'conda', 'galaxy']

    def set_badges(self, force: bool=False):
        self.__logger.debug(self.name())
        self.__logger.debug('='*len(self.name()))
        for platform in self.platforms():
            self.set_badge(platform)
            if force or not os_path.exists(self.badge_file(platform)):
                self.__logger.debug(f'Fetching {platform} {self.name()} badge ')
                getattr(self, f'fetch_{platform}_badge')()
            else:
                self.__logger.debug(f'Badge {platform} for {self.name()} is already there ')

    def fetch_github_latest_release(self) -> str:
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
            version = r.json().get('tag_name', '')
            self.set_version('github', version)
            return version
        except JSONDecodeError as e:
            self.__logger.debug(r)
            return ''

    def fetch_conda_latest_release(self) -> str:
        query_url = f'https://api.anaconda.org/package/{self.conda_channel()}/{self.conda_pkg()}'
        self.__logger.debug(query_url)
        r = requests_get(query_url)
        try:
            self.__logger.debug(r.json())
            version = r.json().get('latest_version', '')
            self.set_version('conda', version)
            return version
        except JSONDecodeError as e:
            self.__logger.debug(r)
            return ''

    def fetch_galaxy_latest_release(self) -> str:
        if is_None(self.galaxy_wrapper()) or is_None(self.galaxy_owner()):
            return ''
        headers = {'content-type': 'application/json'}
        main_url = 'https://toolshed.g2.bx.psu.edu/api'
        # Get the latest release ID
        rel_id = self.__get_galaxy_latest_rel_id(main_url, headers)
        # Get version of the latest release
        return self.__get_galaxy_latest_release(main_url, headers, rel_id)

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
        version = datas[1]['valid_tools'][0]['version']
        self.set_version('galaxy', version)
        return version

    def github_badge(self) -> str:
        badge = self.get_badge('github')
        link = f'https://github.com/{self.github_owner()}/{self.github_repo()}'
        self.__logger.debug(badge)
        return f'<a href="{link}"><img src="badges/{badge}" alt="{self.github_repo()} GitHub latest release"></a>'

    def fetch_github_badge(self):
        badge = self.get_badge('github')
        badge_abs = os_path.join(BADGES_PATH, badge)
        download(
            f'https://img.shields.io/badge/dynamic/json?url=https://api.github.com/repos/{self.github_owner()}/{self.github_repo()}/releases/latest&label=GitHub&query=tag_name&style=plastic',
            badge_abs
        )
        self.__logger.debug(badge)
        self.__logger.debug(badge_abs)

    def conda_badge(self) -> str:
        badge = self.get_badge('conda')
        link = f'https://anaconda.org/{self.conda_channel()}/{self.conda_pkg()}'
        self.__logger.debug(badge)
        return f'<a href="{link}"><img src="badges/{badge}" alt="{self.conda_pkg()} Conda latest release"></a>'

    def fetch_conda_badge(self) -> str:
        badge = self.get_badge('conda')
        badge_abs = os_path.join(BADGES_PATH, badge)
        color = get_color(
            self.get_version('github'),
            self.get_version('conda')
        )
        download(
            f'https://img.shields.io/badge/dynamic/json?url=https://api.anaconda.org/package/{self.conda_channel()}/{self.conda_pkg()}&label=Conda&query=latest_version&color={color}&style=plastic',
            badge_abs
        )
        self.__logger.debug(badge)
        self.__logger.debug(badge_abs)

    def galaxy_badge(self) -> str:
        if is_None(self.galaxy_wrapper()) or is_None(self.galaxy_owner()):
            return ''
        badge = self.get_badge('galaxy')
        link = f'https://toolshed.g2.bx.psu.edu/view/{self.galaxy_owner()}/{self.galaxy_wrapper()}'
        self.__logger.debug(badge)
        return f'<a href="{link}"><img src="badges/{badge}" alt="{self.galaxy_wrapper()} Conda latest release"></a>'

    def fetch_galaxy_badge(self) -> str:
        if is_None(self.galaxy_wrapper()) or is_None(self.galaxy_owner()):
            return ''
        badge = self.get_badge('galaxy')
        badge_abs = os_path.join(BADGES_PATH, badge)
        color = get_color(
            self.get_version('github'),
            self.get_version('conda')
        )
        download(
            f'https://img.shields.io/badge/dynamic/json?url=https://tvm.micalis.inrae.fr/badges/{badge}.json&label=Galaxy&query=latest_version&color={color}&style=plastic',
            badge_abs
        )
        self.__logger.debug(badge)
        self.__logger.debug(badge_abs)

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

def gen_tools(
    tools: List,
    github_token: str='',
    force: bool=True,
    logger: Logger = getLogger(__name__)
) -> Dict:
    _tools = {}

    for i_tool in range(len(tools)):
        _tools[
            re.sub(r'\s+', '_', tools[i_tool][Tool.field(0)].lower())
        ] = Tool(
            values=tools[i_tool],
            github_token=github_token,
            force=force,
            logger=logger
        )
    return _tools
