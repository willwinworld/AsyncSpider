from ..core import ItemProcessor

__all__ = ['LogIP', 'CountItemIP']


class LogIP(ItemProcessor):
    async def process(self, item):
        self.saver.logger.info(str(item))


class CountItemIP(ItemProcessor):
    async def process(self, item):
        c = self.saver.runtime_data.setdefault('item_count', 0)
        c += 1
        self.saver.runtime_data['item_count'] = c
