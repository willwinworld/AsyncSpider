from AsyncSpider import Field
from random import random
import time
import AsyncSpider
import asyncio


class TestItem(AsyncSpider.Item):
    title = Field()
    content = Field()


class LogIP(AsyncSpider.ItemProcessor):
    async def process(self, item: TestItem):
        await asyncio.sleep(random() * 4)
        self.saver.logger.info(str(item))


if __name__ == '__main__':
    sav = AsyncSpider.Saver()

    sav.add_processor(LogIP())
    sav.start()
    for x in 'abcdefg':
        for j in '123':
            i = TestItem(title=x, content=j)
            sav.run_coro(sav.save(i))
        time.sleep(0.2)
    sav.stop()
    sav.join()
