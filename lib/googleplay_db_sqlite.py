import sqlite3
from sqlite3 import Error
import os
from time import strftime

from lib.simple_logger import SimpleLogger
from config import config


class GooglePlayDbSqlite():

    def __init__(self):
        self.log = SimpleLogger(__name__)
        self.conn = None

        try:
            if not os.path.exists(config.SQLITE_PATH):
                os.makedirs(config.SQLITE_PATH)

            self.conn = sqlite3.connect(f'{config.SQLITE_PATH}/google_play_store.db')
            self.conn.enable_load_extension(True)
            self.create_tables()
        except Error as e:
            self.log.error(e)
            raise

    def __del__(self):
        if self.conn:
            self.conn.close()

    def create_tables(self):
        cur = self.conn.cursor()

        self.log.info(f'sqlite3.version {sqlite3.version}')
        self.log.info(f'sqlite3.sqlite_version {sqlite3.sqlite_version}')

        create_google_play_store_rank_table_sql = """
                            CREATE TABLE IF NOT EXISTS google_play_store_rank (
                                collector_date  TEXT NOT NULL,
                                locale          TEXT NOT NULL,
                                top_chart       TEXT NOT NULL,
                                category        TEXT NOT NULL,
                                app_id          TEXT NOT NULL,
                                app_rank        INTEGER NOT NULL,
                                unique (collector_date,locale,top_chart,category,app_rank)
                            );
                        """

        cur.execute(create_google_play_store_rank_table_sql)
        self.conn.commit()

        create_google_play_store_details_table_sql = """
                            CREATE TABLE IF NOT EXISTS google_play_store_details (
                                collector_date      TEXT NOT NULL,
                                locale              TEXT NOT NULL,
                                app_id              TEXT NOT NULL,
                                app_creator         TEXT NOT NULL,
                                app_title           TEXT NOT NULL,
                                app_summary_json    TEXT DEFAULT NULL,
                                app_details_json    TEXT DEFAULT NULL,
                                unique (collector_date,locale,app_id)
                            );
                        """

        cur.execute(create_google_play_store_details_table_sql)
        self.conn.commit()

    # Insert rank data into database
    def insert_app_rankings(self, app_rankings_data):
        cur = self.conn.cursor()
        data = []
        for item in app_rankings_data:
            data.append((
                item['collector_date'],
                item['locale'],
                item['top_chart'],
                item['category'],
                item['app_id'],
                item['app_rank']
            ))

        sql_statement = 'REPLACE INTO google_play_store_rank (collector_date,locale,top_chart,category,app_id,app_rank) VALUES (?, ?, ?, ?, ?, ?)'
        cur.executemany(sql_statement, data)
        self.conn.commit()

    # Insert details data into database
    def insert_app_details(self, app_details_data):
        cur = self.conn.cursor()
        data = []
        for item in app_details_data:
            data.append((
                item['collector_date'],
                item['locale'],
                item['app_id'],
                item['app_creator'],
                item['app_title'],
                item['app_summary_json'],
                item['app_details_json']
            ))

        sql_statement = 'REPLACE INTO google_play_store_details (collector_date,locale,app_id,app_creator,app_title,app_summary_json,app_details_json) VALUES (?, ?, ?, ?, ?, ?, ?)'
        cur.executemany(sql_statement, data)
        self.conn.commit()

    def select_app_no_details(self):
        cur = self.conn.cursor()
        date = strftime("%Y-%m-%d")
        sql_statement = f'SELECT app_id FROM google_play_store_details WHERE locale=\'{config.LOCALE}\' and collector_date=\'{date}\' and app_details_json=\'\''
        self.log.info(f'SQL: {sql_statement}')
        cur.execute(sql_statement)
        rows = cur.fetchall()
        app_ids = []
        for item in rows:
            app_ids.append(item[0])

        return app_ids

    def update_app_details(self, app_details_data):
        cur = self.conn.cursor()
        date = strftime("%Y-%m-%d")
        app_id = app_details_data['app_id']
        sql_statement = f'SELECT app_id FROM google_play_store_details WHERE locale=\'{config.LOCALE}\' and collector_date=\'{date}\' and app_id=\'{app_id}\''
        cur.execute(sql_statement)
        rows = cur.fetchall()

        if len(rows) > 0:
            self.log.info(f'Need to update {app_id}')
            sql_statement = f'UPDATE google_play_store_details SET app_details_json = ? WHERE collector_date = ? AND locale = ? AND app_id = ?'
            cur.execute(sql_statement, (
                app_details_data['app_details_json'],
                app_details_data['collector_date'],
                app_details_data['locale'],
                app_details_data['app_id']
            ))
            self.conn.commit()
        else:
            sql_statement = f'REPLACE INTO google_play_store_details (collector_date,locale,app_id,app_creator,app_title,app_summary_json,app_details_json) VALUES (?, ?, ?, ?, ?, ?, ?)'
            cur.execute(sql_statement, (
                app_details_data['collector_date'],
                app_details_data['locale'],
                app_details_data['app_id'],
                app_details_data['app_creator'],
                app_details_data['app_title'],
                '',
                app_details_data['app_details_json']
            ))
            self.conn.commit()
