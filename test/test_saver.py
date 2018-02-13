from AsyncSpider import Saver, Item, Field
import asyncio
import time
from random import random


class TestItem(Item):
    title = Field()
    content = Field()


class PrintSaver(Saver):
    async def save(self, item):
        await asyncio.sleep(random())
        print(item)


if __name__ == '__main__':
    s = PrintSaver({})
    s.start()
    for x in 'abcdefg':
        for j in '123':
            i = TestItem(title=x, content=j)
            s.run_coro(s.save(i))
        time.sleep(0.2)
    s.stop()
    s.join()
