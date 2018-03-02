from AsyncSpider import Controller
from AsyncSpider.exceptions import TimeoutError
from asyncio import wrap_future
import time
import asyncio
import logging


def count_time(func, *args, **kwargs):
    t0 = time.time()
    r = func(*args, **kwargs)
    t1 = time.time()
    return round(t1 - t0, 4), r


def fetcher_test(ctrl: Controller, url, num):
    f = ctrl.fetcher
    loop = asyncio.get_event_loop()
    f.start()

    async def func(i):
        logger.info(f"count: {i:<5}\trequesting")
        try:
            resp = await wrap_future(f.run_coro_threadsafe(f.fetch('get', url, timeout=20)), loop=loop)
        except TimeoutError:
            logger.error(f"count: {i:<5}\ttimeout")
        except Exception as exc:
            logger.error(f"count: {i:<5}\t{exc!r}")
        else:
            logger.info(f"count: {i:<5}\tstatus: {resp.status:<5}\ttext: {resp.text()[:50].strip()}")

    try:
        loop.run_until_complete(asyncio.wait([func(i) for i in range(num)]))
    finally:
        f.stop()
        f.join()
        pass


if __name__ == '__main__':
    ctrl = Controller('test')
    logger = ctrl.logger
    logger.setLevel(logging.INFO)
    target = "https://www.hao123.com/"
    n = 10
    logger.info('test start')

    t, r = count_time(fetcher_test, ctrl, target, n)

    logger.info(f'test:{n} requests in {t}s')
    logger.info('test end')
