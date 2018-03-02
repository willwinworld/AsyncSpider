import AsyncSpider
from AsyncSpider import Item, Field, ItemProcessor, Spider
from random import random
import logging


class TestItem(Item):
    number = Field(default=0)
    title = Field(default='hao123')
    summary = Field(default='')


class LogProcessor(ItemProcessor):
    async def process(self, item: TestItem):
        await AsyncSpider.sleep(random() * 4)
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
    ctrl = AsyncSpider.Controller('test')
    ctrl.set_settings({
        'concurrency': 4
    })
    ctrl.construct(LogProcessor, TestSpider)

    # ctrl.logger.setLevel(logging.WARNING)

    ctrl.logger.info('Spd start')
    ctrl.run_all()
    ctrl.logger.info('Spd end')
