from AsyncSpider._saver import Saver
from AsyncSpider._item import Item, Field
from AsyncSpider._utils import asleep
import time


class TestItem(Item):
    title = Field()
    content = Field()


class PrintSaver(Saver):
    async def save(self, item):
        await asleep(1)
        print(item)


if __name__ == '__main__':
    s = PrintSaver()
    s.start()
    q = s.item_queue
    for x in range(1, 10 + 1):
        i = TestItem(title=x, content=x)
        q.put(i)
        time.sleep(0.2)
    s.stop(join=True)
