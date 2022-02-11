from os import (
    path as os_path
)
from logging import (
    Logger,
    getLogger
)
from typing import Dict
from colored import fg, bg, attr
import sqlite3
from brs_utils import (
    create_logger
)
from .Args import (
    build_args_parser
)
from .ToolVerMon import start
from .Database import TVM_Database
from .Const import *


def _cli():
    parser = build_args_parser(
        prog = 'tvm',
        description = 'Tool Version Monitor compare releases'
    )
    args   = parser.parse_args()

    if args.log.lower() in ['silent', 'quiet'] or args.silent:
        args.log = 'CRITICAL'

    # Create logger
    logger = create_logger(parser.prog, args.log)

    logger.debug('args: ' + str(args))

    db = TVM_Database(
        os_path.join(HERE, 'tvm.db'),
        logger
    )

    start(
        host=args.host,
        port=args.port,
        github_token=args.github_token,
        source_file=args.source_file,
        source_googlesheet=args.source_googlesheet,
        googleapi=args.googleapi,
        db=db,
        logger=logger
    )

    conn.close()


if __name__ == '__main__':
    _cli()
