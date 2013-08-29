__all__ = ['connect', 'PostgresConnectionPool']
import tulip
import functools
import psycopg2
import psycopg2.extensions

from .pool import PostgresConnectionPool


@tulip.coroutine
def wait(conn, loop):
    waiter = tulip.Future(loop=loop)

    _wait(loop, waiter, False, conn)
    try:
        yield from waiter
    finally:
        fd = conn.fileno()
        loop.remove_reader(fd)
        loop.remove_writer(fd)


def _wait(loop, fut, registered, conn):
    try:
        state = conn.poll()
    except Exception as exc:
        fut.set_exception(exc)
        return

    if state == psycopg2.extensions.POLL_OK:
        if not fut.done():
            fut.set_result(True)
    elif not registered:
        fd = conn.fileno()
        loop.add_reader(fd, _wait, loop, fut, True, conn)
        loop.add_writer(fd, _wait, loop, fut, True, conn)


@tulip.coroutine
def connect(dsn=None, *, loop=None):
    if loop is None:
        loop = tulip.get_event_loop()

    conn = psycopg2.connect(
        dsn=dsn,
        cursor_factory=functools.partial(Cursor, loop=loop), async=1)
    yield from wait(conn, loop)
    return conn


class Cursor(psycopg2.extensions.cursor):

    def __init__(self, *args, **kw):
        self._loop = kw.pop('loop')

        super().__init__(*args, **kw)

    def begin(self):
        yield from self.execute('BEGIN')

    def commit(self):
        yield from self.execute('COMMIT')

    def rollback(self):
        yield from self.execute('ROLLBACK')

    def wait(self):
        yield from wait(self.connection, self._loop)        

    def execute(self, *args, **kw):
        super().execute(*args, **kw)

        yield from wait(self.connection, self._loop)
