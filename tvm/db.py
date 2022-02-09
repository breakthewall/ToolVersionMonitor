from os import (
    path as os_path
)
from csv import DictReader as csv_DictReader
from sqlite3 import (
    connect,
    IntegrityError as sql_IntegrityError,
    Error as sql_Error
)
from logging import (
    Logger,
    getLogger
)
from .tool import Tool

here = os_path.dirname(os_path.abspath( __file__ ))


def get_connection():
    return connect(os_path.join(here, 'tools.db'))


def close_connection(conn):
    if conn:
        conn.close()


def init_db():
    con = get_connection()
    cur = con.cursor()
    # Create table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS Tools(
            name text,
            github_repo text,
            github_owner text,
            conda_pkg text,
            conda_channel text,
            galaxy_wrapper text,
            galaxy_owner text,
            UNIQUE(name)
        )
        '''
    )
    return cur, con


def delete_entries(conn=None):
    if conn is None:
        conn = get_connection()
        close_conn = True
    else:
        close_conn = False
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Tools")
    if close_conn:
        close_connection(conn)


def read_from_file(filename: str, logger: Logger = getLogger(__name__)):
    tools = {}
    with open(filename, mode='r') as f:
        records = csv_DictReader(f)
        for row in records:
            tools[
                row['NAME'].lower().replace(' ', '_')
            ] = Tool(
                **{k.lower(): v for k, v in row.items()},
                logger=logger
            )
    return tools


def reset():
    conn = get_connection()
    delete_entries(conn)

    tools = read_from_file(os_path.join(here, 'static', 'tools.csv'))

    infos = []
    for tool in tools:
        infos += [add_tool(**tool, conn=conn)]

    close_connection(conn)

    return infos


def tool_to_dict(records):
    if not records:
        return {}
    infos = {
        'name': records[0],
        'github': {
            'repo': records[1],
            'owner': records[2],
        },
        'conda': {
            'pkg': records[3],
            'channel': records[4]
        },
        'galaxy': {
            'tool': records[5],
            'owner': records[6]
        }
    }
    infos['github']['latest_release'] = github_latest_release(
        infos['github']['repo'],
        infos['github']['owner']
    )
    infos['conda']['latest_release'] = conda_latest_release(
        infos['conda']['pkg'],
        infos['conda']['channel']
    )
    return infos


def get_tool(name, cursor=None):
    connection = db.get_connection()
    cursor = connection.cursor()
    select_query = """SELECT * from Tools where name = ?"""
    cursor.execute(select_query, (name,))
    records = cursor.fetchall()
    db.close_connection(connection)
    return tool_to_dict(records[0])


def get_tools():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * from Tools")
    records = cursor.fetchall()
    close_connection(connection)
    infos = []
    for row in records:
        infos += [tool_to_dict(row)]
    return infos


#@route('/add/<name>&<github_repo>&<github_owner>&<conda_pkg>&<conda_channel>')
def add_tool(name, github_repo, github_owner, conda_pkg, conda_channel, galaxy_wrapper, galaxy_owner, conn=None):
    if conn is None:
        # Init DB
        cursor, conn = init_db()
        close_conn = True
    else:
        cursor = conn.cursor()
        close_conn = False

    try:
        values = f'("{name}", "{github_repo}", "{github_owner}", "{conda_pkg}", "{conda_channel}", "{galaxy_wrapper}", "{galaxy_owner}")'
        # Insert a row of data
        cursor.execute(f'INSERT INTO Tools VALUES {values}')
        infos = f'New tool {name} inserted in DB with values: {values}'
        # Save (commit) the changes
        conn.commit()
    except sql_IntegrityError as error:
        infos = f'Tool {name} already in DB, nothing has been done'

    if close_conn:
        # We can also close the connection if we are done with it.
        # Just be sure any changes have been committed or they will be lost.
        conn.close()

    return infos


