import sqlite3
from typing import *
from logging import (
    Logger,
    getLogger
)

class Database:

    def __init__(
        self,
        filename: str,
        logger: Logger = getLogger(__name__)
    ):
        self.__logger = logger
        self.__conn = sqlite3.connect(filename)
        cursor = self.__conn.cursor()

    def logger(self):
        return self.__logger

    def sql_do(self, sql, *params) -> Dict:
        self.logger().debug(sql)
        cursor = self.__conn.cursor()
        cursor.execute(sql, params)
        self.__conn.commit()
        result = cursor.fetchall()
        try:
            return result[0]
        except IndexError as e:
            return None

    def create_table(
        self,
        table: str,
        columns: str,
        overwrite: bool = False
    ):
        if overwrite:
            self.sql_do(f'DROP TABLE IF EXISTS "{table}"')
        self.sql_do(
            f'''
            CREATE TABLE
            IF NOT EXISTS
            "{table}" {columns}
            '''
        )

    def exists(self, table: str, column: str, value: str) -> bool:
        result = self.sql_do(
            f'''
            SELECT *
            FROM "{table}"
            WHERE "{column}" = "{value}";
            '''
        )
        return (
            result is not None
            and result != []
        )


class TVM_Database(Database):

    def __init__(
        self,
        filename: str,
        logger: Logger = getLogger(__name__)
    ):
        super().__init__(filename, logger)

    def create_table__versions(self, platforms: List[str]):
        self.__versions_ref = 'tool'
        for platform in platforms:
            self.create_table(
                table=f'{platform}_versions',
                columns=f'("{self.__versions_ref}" text, version text, UNIQUE(tool))'
            )
 
    def create_table__tools(self, fields: List[str], uniqueID: int = 0):
        # Wrap fields with quotes
        _fields = [f'"{field}"' for field in fields]
        self.create_table(
            table='tools',
            columns=f'({" text, ".join(_fields)}, UNIQUE({_fields[uniqueID]}))'
        )
        self.__tools_ref = fields[0]
 
    def set_infos(self, tool: str, infos: Dict):
        self.logger().debug(tool, infos)
        if self.tool_exists(tool):
            values = ', '.join([f'"{f}" = "{c}"' for f, c in zip(infos.keys(), infos.values())])
            self.sql_do(
                f'''
                UPDATE 'tools'
                SET {values}
                WHERE "{self.__tools_ref}" = '{tool}';
                '''
            )
        else:
            values = ', '.join([f"'{f}'" for f in infos.values()])
            self.sql_do(
                f'''
                INSERT INTO tools
                VALUES({values});
                '''
            )

    def get_version(self, platform: str, tool: str) -> str:
        result = self.sql_do(
            f'''
            SELECT *
            FROM "{platform}_versions"
            WHERE "{self.__versions_ref}" = "{tool}"
            '''
        )
        if result is None:
            return None
        else:
            return result[0]

    def version_exists(self, platform: str, tool: str) -> bool:
        return self.exists(f'{platform}_versions', self.__versions_ref, tool)

    def tool_exists(self, tool: str) -> bool:
        return self.exists('tools', self.__tools_ref, tool)

    def set_version(
        self,
        platform: str,
        tool: str,
        version: str
    ):
        if version == '':
            return
        if self.version_exists(platform, tool):
            self.sql_do(
                f'''
                UPDATE "{platform}_versions"
                SET version = "{version}"
                WHERE "{self.__versions_ref}" = "{tool}";
                '''
            )
        else:
            self.sql_do(
                f'''
                INSERT INTO "{platform}_versions"
                VALUES("{tool}", "{version}");
                '''
            )
