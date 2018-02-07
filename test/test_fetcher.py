from AsyncSpider import Fetcher, Request
import requests
import time


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
    f = Fetcher()
    f.start()
    for i in range(num):
        f.requests_queue.put((i + 1, [Request('get', url)]))

    for _ in range(num):
        aid, responses = f.responses_queue.get()
        resp = responses[0]
        print(f"index: {aid}\tstatus: {resp.status}\ttext: {resp.content.decode('utf8')[:50].strip()}")

    f.stop(join=True)


def fetcher_test2(url, num):
    f = Fetcher()
    f.start()
    f.requests_queue.put((233, [Request('get', url) for _ in range(num)]))

    aid, responses = f.responses_queue.get()
    for i, resp in enumerate(responses):
        print(f"index: {i+1}\tstatus: {resp.status}\ttext: {resp.content.decode('utf8')[:50].strip()}")

    f.stop(join=True)


if __name__ == '__main__':
    target = "https://www.hao123.com/"
    n = 100

    # for func in (requests_test, fetcher_test, fetcher_test2):
    # for func in (fetcher_test, fetcher_test2):
    print('test start')

    for func in (fetcher_test2,):
        t, r = count_time(func, target, n)
        print(f'{func.__name__}: {t}s')

    print('test end')