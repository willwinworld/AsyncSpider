from AsyncSpider import Fetcher, Request
import requests
import time
import asyncio


def count_time(func, *args, **kwargs):
    t0 = time.time()
    r = func(*args, **kwargs)
    t1 = time.time()
    return t1 - t0, r


def requests_test(url, num):
    s = requests.session()
    for i in range(1, num + 1):
        resp = s.get(url)
        print(f"index: {i}\tstatus: {resp.status_code}\ttext: {resp.text[:50].strip()}")


def fetcher_test(url, num):
    f = Fetcher(dict(qps=20, max_qps=20))
    loop = asyncio.get_event_loop()
    f.start()

    async def func(i, future):
        resp = await future
        print(f"index: {i}\tstatus: {resp.status}\ttext: {resp.text[:50].strip()}")

    loop.run_until_complete(asyncio.wait([func(i, f.run_coro(f.fetch(Request('get', url)))) for i in range(num)]))

    f.stop()
    f.join()


def fetcher_test2(url, num):
    f = Fetcher(dict(qps=50, max_qps=50))
    loop = asyncio.get_event_loop()
    f.start()
    responses = loop.run_until_complete(f.run_coro(
        f.fetch(*[Request('get', url) for _ in range(num)])))
    for i, resp in enumerate(responses):
        print(f"index: {i}\tstatus: {resp.status}\ttext: {resp.text[:50].strip()}")
    f.stop()
    f.join()


if __name__ == '__main__':
    target = "https://www.hao123.com/"
    n = 100
    print('test start')
    # for func in (requests_test, fetcher_test, fetcher_test2):
    # for func in (fetcher_test, fetcher_test2):
    for func in (fetcher_test,):
        t, r = count_time(func, target, n)
        print(f'{func.__name__}: {t}s')

    print('test end')
