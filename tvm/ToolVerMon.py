from os import (
    path as os_path
)
from threading import Timer
from logging import (
    Logger,
    getLogger,
    DEBUG
)

from bottle import (
    route,
    run,
    static_file,
    jinja2_template as template,
    error,
    response
)

from .Const import *
from .Args import (
    DEFAULT_port,
    DEFAULT_host,
    DEFAULT_sourcefile,
    DEFAULT_googleapi
)
from .Data import (
    read_from_file,
    read_from_googlesheet,
    save_to_csvfile
)
from ._version import __version__
from .Tool import Tool


def render_tools(tool_names):
    rows = []
    for tool_name in tool_names:
        tool = TOOLS[tool_name]
        badges = [
            f'{tool.github_badge()}',
            f'{tool.conda_badge()}',
            f'{tool.galaxy_badge()}'
        ]
        rows += [(tool.name(), badges)]
    return template(
        os_path.join(STATIC_PATH, 'tvm.tpl'),
        {
            'rows': rows,
            'version': __version__
        }
    )

@route('/<toolname>')
def tool(toolname):
    tool_lst = [t for t in TOOLS.keys() if t.startswith(toolname)]
    return render_tools(tool_lst)

@route('/')
def index():
    return render_tools(TOOLS.keys())

@route('/static/<filename:re:.*\.css>')
def stylesheets(filename):
    return static_file(
        filename,
        root=STATIC_PATH
    )

@route('/badges/<filename:re:.*\.svg>')
def badges(filename):
    return static_file(
        filename,
        root=BADGES_PATH
    )

@route('/force_check')
def force_check():
    for tool in TOOLS.values():
        tool.force_check()
    return index()

def redirect(url: str, status: int=303):
    response.status = status
    response.set_header('Location', url)

def gen_tools(
    tools,
    db,
    github_token: str='',
    logger: Logger = getLogger(__name__)
):
    _tools = {}
    for row in tools:
        _tools[
            row[Tool.field(0)].lower().replace(' ', '_')
        ] = Tool(
            values=row,
            github_token=github_token,
            db=db,
            logger=logger
        )

    return _tools

@route('/force_reload')
def force_reload():
    _reload(force=True)

def _reload(force: bool):

    global TOOLS

    if force is None:
        force = True

    LOGGER.info('Refreshing releases and badges')

    if SOURCE_GOOGLESHEET != '':
        tools = read_from_googlesheet(
            googlesheet=SOURCE_GOOGLESHEET,
            googleapi=GOOGLEAPI,
            logger=LOGGER
        )
    else:
        tools = read_from_file(
            SOURCE_FILE,
            logger=LOGGER
        )

    TOOLS = gen_tools(
        tools=tools,
        github_token=GITHUB_TOKEN,
        db=DB,
        logger=LOGGER
    )

    if SOURCE_GOOGLESHEET != '':
        save_to_csvfile(
            tools=TOOLS,
            filename=os_path.join(DATA_PATH, 'googlesheet.csv'),
            logger=LOGGER
        )

    for tool in TOOLS.values():
        tool.set_badges(force=force)

    LOGGER.info('--> OK')

    redirect(f'http://{HOST}:{PORT}')

@error(404)
def error404(error):
    return "The page does not exist..."


def set_token(github_token: str):
    token = github_token
    if token is None or token == '':
        try:
            with open(os_path.join(CREDS_PATH, '.secrets')) as f:
                secret = f.read()
                token = secret
        except FileNotFoundError as e:
            pass
    return token

def start(
    db,
    host: str=DEFAULT_port,
    port: int=DEFAULT_host,
    github_token: str='',
    source_file: str=DEFAULT_sourcefile,
    source_googlesheet: str='',
    googleapi: str=DEFAULT_googleapi,
    logger: Logger = getLogger(__name__)
):
    global HOST
    HOST = host
    global PORT
    PORT = port
    global LOGGER
    LOGGER = logger
    global GITHUB_TOKEN
    GITHUB_TOKEN = set_token(github_token)
    global SOURCE_FILE
    SOURCE_FILE = source_file
    global GOOGLEAPI
    GOOGLEAPI = googleapi if googleapi != '' else DEFAULT_googleapi
    global SOURCE_GOOGLESHEET
    SOURCE_GOOGLESHEET = source_googlesheet
    global DB
    DB = db
    global TOOLS
    TOOLS = {}

    logger.info('Configuration')
    logger.info('-------------')
    params = locals()
    for param in params:
        if param == 'source_file' and source_googlesheet != '':
            continue
        if param == 'googleapi' and source_googlesheet == '':
            continue
        if globals()[param.upper()] != '':
            logger.info(f'{param}: {globals()[param.upper()]}')
    logger.info('')

    _reload(force=False)
    # Timer(60*10, force_check).start()
    Timer(60*60, _reload, True).start()
    run(
        server='bjoern',
        host=host,
        port=port,
        debug=logger.getEffectiveLevel()<=DEBUG
    )
