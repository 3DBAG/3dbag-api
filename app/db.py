"""Database helper functions

Copyright 2022 3DGI <info@3dgi.nl>
"""

import logging
import os
import sqlite3
import psycopg2 as pg
from psycopg2.extensions import connection


def get_connection() -> connection:
    '''
        This function connects to the database server
        based on environment variables.
    '''
    try:
        logging.info("Connecting to Godzilla DB")
        conn = pg.connect(user=os.environ["POSTGRES_USER"],
                          host=os.environ["POSTGRES_HOST"],
                          port=os.environ["POSTGRES_PORT"],
                          database=os.environ["POSTGRES_DB"],
                          password=os.environ["POSTGRES_PWD"])
        conn.set_session(isolation_level="READ COMMITTED")
    except pg.OperationalError as e:
        logging.error(f"DB connection failed! {e}")
        raise e
    
    return conn


class Db(object):
    """A database connection class.

    :raise: :class:`psycopg2.OperationalError`
    """

    def __init__(self, dbfile=None):
        if dbfile is None:
            self.conn = get_connection()
        else:
            self.dbfile = dbfile
            try:
                self.conn = sqlite3.connect(dbfile, check_same_thread=False)
                logging.info(f"Opened connection to {self.dbfile}")
            except sqlite3.OperationalError:
                logging.exception(
                    f"Unable to connect to the database {dbfile}")
                raise

    def send_query(self, query):
        """Send a query to the DB when no results need to return (e.g. CREATE).
        """
        with self.conn:
            cur = self.conn.cursor()
            cur.execute(query)

    def get_query(self, query):
        """DB query where the results need to return (e.g. SELECT)."""
        with self.conn:
            cur = self.conn.cursor()
            cur.execute(query)
            return cur.fetchall()
