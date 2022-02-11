import sqlite3
from typing import Dict
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
        if result is None:
            return None
        self.logger().debug(result)
        return dict(result)

    def create_table(
        self,
        table: str,
        columns: str,
        overwrite: bool = False
    ):
        if overwrite:
            self.sql_do(f'DROP TABLE IF EXISTS {table}')
        self.sql_do(
            f'CREATE TABLE IF NOT EXISTS {table} {columns}'
        )


class TVM_Database(Database):

    def __init__(
        self,
        filename: str,
        logger: Logger = getLogger(__name__)
    ):
        super().__init__(filename, logger)
        for platform in ['github', 'conda', 'galaxy']:
            self.create_table(
                table=f"'{platform}_versions'",
                columns='(tool text, version text, UNIQUE(tool))'
            )
 
    def get_version(self, platform: str, tool: str) -> str:
        result = self.sql_do(
            f"SELECT * FROM '{platform}_versions' WHERE tool='{tool}'"
        )
        return result.get(tool, '')
        # try:
        #     return cursor.fetchall()[0]
        # except IndexError as e:
        #     return None

    def exists(self, table: str, tool: str) -> bool:
        result = self.sql_do(
            f"SELECT * FROM '{table}' WHERE tool = '{tool}';"
        )
        return result != {}

    def set_version(
        self,
        platform: str,
        tool: str,
        version: str
    ):
        if version == '':
            return
        if self.exists(f'{platform}_versions', tool):
            self.sql_do(
                f'''
                UPDATE '{platform}_versions'
                SET version = '{version}'
                WHERE tool = '{tool}';
                '''
            )
        else:
            self.sql_do(
                f'''
                INSERT INTO {platform}_versions
                VALUES('{tool}', '{version}');
                '''
            )
