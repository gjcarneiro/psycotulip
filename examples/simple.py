import time
import tulip
import psycopg2
import psycotulip


@tulip.coroutine
def main(pool):
    conn = yield from pool.get()

    with conn.cursor() as cur:
        yield from cur.begin()
        try:
            yield from cur.execute('select pg_sleep(1);')
            yield from cur.commit()
        except:
            yield from cur.rollback()
            raise

    pool.put(conn)


def test(pool):
    t1 = tulip.Task(main(pool))
    t2 = tulip.Task(main(pool))
    t3 = tulip.Task(main(pool))
    t4 = tulip.Task(main(pool))
    yield from tulip.wait([t1, t2, t3, t4])


if __name__ == '__main__':
    t0 = time.monotonic()
    loop = tulip.get_event_loop()

    pool = psycotulip.PostgresConnectionPool(
        maxsize=3, loop=loop, dsn='dbname=postgres')

    try:
        loop.run_until_complete(test(pool))
    except:
        pass

    delay = time.monotonic() - t0
    print ('Running "select pg_sleep(1);" 4 times with 3 connections. '
           'Should take about 2 seconds: %.2fs' % delay)
