from os import (
    path as os_path
)

HERE = os_path.dirname(os_path.abspath( __file__ ))
CACHE_PATH = os_path.join(HERE, '.cache')
CACHE_FILE = os_path.join(CACHE_PATH, 'tools.csv')
VERSIONS_FILE = os_path.join(CACHE_PATH, 'versions.csv')
BADGES_PATH = os_path.join(CACHE_PATH, 'badges')
VERSIONS_PATH = os_path.join(CACHE_PATH, 'versions')
STATIC_PATH = os_path.join(HERE, 'static')
DATA_PATH = os_path.join(HERE, 'data')
CREDS_PATH = os_path.join(HERE, 'creds')
