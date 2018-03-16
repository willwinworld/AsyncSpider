from ..processor import ItemProcessor

__all__ = ['LogIP']


class LogIP(ItemProcessor):
    async def process(self, item):
        self.saver.logger.info(str(item))
