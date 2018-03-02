from AsyncSpider import Field
import AsyncSpider
import time
from random import random


class TestItem(AsyncSpider.Item):
    title = Field()
    content = Field()


class LogProcessor(AsyncSpider.ItemProcessor):
    async def process(self, item: TestItem):
        await AsyncSpider.sleep(random() * 4)
        self.saver.logger.info(str(item))


if __name__ == '__main__':
    ctrl = AsyncSpider.Controller('test')
    print(ctrl.logger)
    sav = ctrl.saver
    sav.add_processor(LogProcessor(sav))
    sav.start()
    for x in 'abcdefg':
        for j in '123':
            i = TestItem(title=x, content=j)
            sav.run_coro(sav.save(i))
        time.sleep(0.2)
    sav.stop()
    sav.join()
