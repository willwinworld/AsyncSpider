from AsyncSpider import Fetcher
from AsyncSpider.exceptions import TimeoutError
from asyncio import wrap_future
import time
import asyncio


def count_time(func, *args, **kwargs):
    t0 = time.time()
    result = func(*args, **kwargs)
    t1 = time.time()
    return round(t1 - t0, 4), result


def fetcher_test(url, num):
    loop = asyncio.get_event_loop()

    async def func(i):
        f.logger.info(f"count: {i:<5}\trequesting")
        try:
            resp = await wrap_future(f.run_coro_threadsafe(f.fetch('get', url, timeout=30)), loop=loop)
        except TimeoutError:
            f.logger.error(f"count: {i:<5}\ttimeout")
        except Exception as exc:
            f.logger.error(f"count: {i:<5}\t{exc!r}")
        else:
            f.logger.info(f"count: {i:<5}\tstatus: {resp.status:<5}\ttext: {resp.text()[:50].strip()}")

    f.start()
    try:
        loop.run_until_complete(asyncio.wait([func(i) for i in range(num)]))
    finally:
        f.stop()
        f.join()


if __name__ == '__main__':
    target = "https://www.hao123.com/"
    n = 500
    f = Fetcher()

    f.logger.info('test start')

    t, r = count_time(fetcher_test, target, n)

    f.logger.info(f'test:{n} requests in {t}s')
    f.logger.info('test end')
