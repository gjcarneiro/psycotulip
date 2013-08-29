"""Psycopg Connections Pool."""
import tulip
import tulip.queues
import psycotulip
import psycopg2.extensions


class DatabaseConnectionPool(object):

    def __init__(self, maxsize=10, *, loop=None):
        if not isinstance(maxsize, int):
            raise TypeError('Expected integer, got %r' % (maxsize,))
        self._maxsize = maxsize
        self._pool = tulip.queues.Queue(loop=loop)
        self._size = 0

    @tulip.coroutine
    def get(self):
        pool = self._pool
        if self._size >= self._maxsize or pool.qsize():
            return (yield from pool.get())
        else:
            self._size += 1
            try:
                new_item = yield from self.connect()
            except:
                self._size -= 1
                raise
            return new_item

    def put(self, conn):
        if conn.closed:
            raise psycopg2.extensions.OperationalError(
                "Connection is closed: %r" % (conn,))

        self._pool.put_nowait(item)

    def closeall(self):
        pool = self._pool

        while 1:
            try:
                conn = pool.get_nowait()
                conn.close()
            except tulip.queues.Empty:
                break

    def connect(self):
        raise NotImplementedError


class PostgresConnectionPool(DatabaseConnectionPool):

    def __init__(self, *args, **kwargs):
        loop = kwargs.get('loop')
        maxsize = kwargs.pop('maxsize', None)
        self._connect = kwargs.pop('connect', psycotulip.connect)
        self._args = args
        self._kwargs = kwargs
        super().__init__(maxsize, loop=loop)

    @tulip.coroutine
    def connect(self):
        return (yield from self._connect(*self._args, **self._kwargs))
