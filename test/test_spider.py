from AsyncSpider import *


class TestItem(Item):
    number = Field(default=0)
    title = Field(default='hao123')
    summary = Field(default='')


class PrintSaver(Saver):
    async def save(self, item):
        print(f'PrintSaver: save {item}')


class TestSpider(Spider):
    @actionmethod
    async def start_action(self):
        print('start_action start')
        for n in range(1, 10 + 1):
            g = self.parse(n)
            print(g)
            yield g
        print('start_action end')

    @actionmethod
    async def parse(self, n):
        print(f'parse {n} start')
        resp = yield Request('get', "https://www.hao123.com/")
        i = TestItem(number=n, summary=resp.text()[:50].strip())
        yield i
        print(f'parse {n} end')


if __name__ == '__main__':
    req_q = ThreadSafeQueue()
    resp_q = ThreadSafeQueue()
    i_q = ThreadSafeQueue()

    spd = TestSpider(requests_queue=req_q, responses_queue=resp_q, item_queue=i_q)
    fetcher = Fetcher(requests_queue=req_q, responses_queue=resp_q)
    saver = PrintSaver(item_queue=i_q)

    saver.start()
    fetcher.start()
    spd.start()

    print('spd start')
    spd.join()
    print('spd end')

    fetcher.stop()
    saver.stop()
