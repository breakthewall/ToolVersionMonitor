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
from .Const import *


def init_db():
    conn = sqlite3.connect(os_path.join(HERE, 'versions.db'))
    cursor = conn.cursor()
    # Create table
    cursor.execute(
        '''CREATE TABLE IF NOT EXISTS versions
                (tool text, platform text, version text, UNIQUE(tool))'''
    )
    conn.commit()
    return conn, cursor

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

    conn, cursor = init_db()

    start(
        host=args.host,
        port=args.port,
        github_token=args.github_token,
        source_file=args.source_file,
        source_googlesheet=args.source_googlesheet,
        googleapi=args.googleapi,
        db=conn,
        logger=logger
    )

    conn.close()


if __name__ == '__main__':
    _cli()
