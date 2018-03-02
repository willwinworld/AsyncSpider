from .fetsav import Fetcher, Saver
from .reqrep import Request
from .item import Item
import weakref

__all__ = ['RequestProcessor', 'ItemProcessor']


class BaseProcessor:
    def on_start(self):
        pass

    def on_stop(self):
        pass

    async def process(self, value):
        pass


class RequestProcessor(BaseProcessor):
    def __init__(self, fetcher):
        BaseProcessor.__init__(self)
        self._fetcher = weakref.proxy(fetcher)

    @property
    def fetcher(self) -> Fetcher:
        return self._fetcher

    async def process(self, request: Request):
        pass


class ItemProcessor(BaseProcessor):
    def __init__(self, saver):
        BaseProcessor.__init__(self)
        self._saver = weakref.proxy(saver)

    @property
    def saver(self) -> Saver:
        return self._saver

    async def process(self, item: Item):
        pass
