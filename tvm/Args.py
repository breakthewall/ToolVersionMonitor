from os import path as os_path
from argparse import ArgumentParser
from typing import Callable
from brs_utils import add_logger_args
from ._version import __version__
from .Const import *

DEFAULT_port = 80
DEFAULT_host = 'localhost'
DEFAULT_sourcefile = os_path.join(DATA_PATH, 'tools.csv')
DEFAULT_googleapi = os_path.join(CREDS_PATH, 'googleapi.json')

def build_args_parser(
    prog: str,
    description: str = '',
    epilog: str = '',
    m_add_args: Callable = None,
) -> ArgumentParser:

    parser = ArgumentParser(
        prog = prog,
        description = description,
        epilog = epilog
    )

    # Build Parser with rptools common arguments
    parser = _add_arguments(parser)

    # Add module specific arguments
    if m_add_args is not None:
        parser = m_add_args(parser)

    return parser

def _add_arguments(parser: ArgumentParser) -> ArgumentParser:

    # Add arguments related to the logger
    parser = add_logger_args(parser)

    # optional arguments
    parser.add_argument(
        '--host',
        type=str,
        default=DEFAULT_host
    )
    parser.add_argument(
        '--port',
        type=int,
        default=DEFAULT_port
    )
    parser.add_argument(
        '--source_file',
        type=str,
        default=DEFAULT_sourcefile
    )
    parser.add_argument(
        '--source_googlesheet',
        type=str,
        default=''
    )
    parser.add_argument(
        '--googleapi',
        type=str,
        default=''
    )
    parser.add_argument(
        '--github_token',
        type=str,
        default=''
    )
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s {}'.format(__version__),
        help='show the version number and exit'
    )

    return parser
