from AsyncSpider import *


class TestItem(Item):
    number = Field(default=0)
    title = Field(default='hao123')
    summary = Field(default='')


class PrintSaver(Saver):
    async def save(self, item):
        print(f'PrintSaver: save {item}')


class TestSpider(Spider):
    async def get(self, url, **kwargs):
        return await self.fetch(Request('get', url, **kwargs))

    @actionmethod
    async def start_action(self):
        print('start_action start')
        for n in range(1, 10 + 1):
            yield self.parse(n)
        print('start_action end')

    @actionmethod
    async def parse(self, n):
        print(f'parse {n} start')
        resp = await self.get("https://www.hao123.com/")
        yield TestItem(number=n, summary=resp.text[:50].strip())
        print(f'parse {n} end')


if __name__ == '__main__':
    spd = TestSpider({'Saver': {'class': PrintSaver}})
    spd.start()
    print('spd start')
    spd.join()
    print('spd end')
