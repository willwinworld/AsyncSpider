import AsyncSpider
from AsyncSpider import Item, Field, Spider, Fetcher, Saver
from AsyncSpider.implements import TokenBucketRP
from random import random
import asyncio


class TestItem(Item):
    number = Field(default=0)
    title = Field(default='hao123')
    summary = Field(default='')


class LogIP(AsyncSpider.ItemProcessor):
    async def process(self, item: TestItem):
        await asyncio.sleep(random() * 4)
        self.saver.logger.info(str(item))


class TestSpider(Spider):
    async def get(self, url, **kwargs):
        return await self.fetch('get', url, **kwargs)

    async def start_action(self):
        self.logger.info('start_action start')
        for n in range(1, 15 + 1):
            yield self.parse(n)
        self.logger.info('start_action end')

    async def parse(self, n):
        self.logger.info(f'parse {n} start')
        resp = await self.get("https://www.hao123.com/")
        yield TestItem(number=n, summary=resp.text()[:50].strip())
        self.logger.info(f'parse {n} end')


if __name__ == '__main__':
    spd = TestSpider(concurrency=4)

    spd.set_fetcher(Fetcher())
    spd.fetcher.add_processor(TokenBucketRP(qps=3, max_qps=3))

    spd.set_saver(Saver())
    spd.saver.add_processor(LogIP())

    AsyncSpider.logger.info('Spd start')
    AsyncSpider.run_all(spd)
    # spd.fetcher.start()
    # spd.saver.start()
    # spd.start()
    # spd.join()
    # spd.fetcher.stop()
    # spd.saver.stop()
    AsyncSpider.logger.info('Spd end')
