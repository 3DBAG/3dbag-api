import logging
import sqlite3


class Db(object):
    """A database connection class.

    :raise: :class:`psycopg2.OperationalError`
    """

    def __init__(self, conn=None, dbfile=None):
        if conn is None:
            self.dbfile = dbfile
            try:
                self.conn = sqlite3.connect(dbfile, check_same_thread=False)
                logging.info(f"Opened connection to {self.dbfile}")
            except sqlite3.OperationalError:
                logging.exception(f"Unable to connect to the database {dbfile}")
                raise
        else:
            self.conn = conn

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
