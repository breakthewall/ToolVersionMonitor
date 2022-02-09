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

from .db import read_from_file
from .const import *
from .Args import (
    DEFAULT_port,
    DEFAULT_host
)

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
        rows=rows
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

@route('/force_reload')
def force_reload():
    global TOOLS
    TOOLS = read_from_file(os_path.join(DATA_PATH, 'tools.csv'))
    redirect(f'http://{HOST}:{PORT}')

@error(404)
def error404(error):
    return "The page does not exist..."

def start(
    host: str=DEFAULT_port,
    port: int=DEFAULT_host,
    logger: Logger = getLogger(__name__)
):
    global HOST
    HOST = host
    global PORT
    PORT = port

    force_reload()
    # Timer(60*10, force_check).start()
    Timer(60*60, force_reload).start()
    run(
        server='bjoern',
        host=host,
        port=port,
        debug=logger.getEffectiveLevel()<=DEBUG
    )
