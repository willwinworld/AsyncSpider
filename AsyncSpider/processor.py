from .fetsav import FetcherRefMixin, SaverRefMixin
from .reqrep import Request
from .item import Item

__all__ = ['RequestProcessor', 'ItemProcessor']


class BaseProcessor:
    def on_start(self):
        pass

    def on_stop(self):
        pass

    async def process(self, value):
        pass


class RequestProcessor(BaseProcessor, FetcherRefMixin):
    def __init__(self):
        BaseProcessor.__init__(self)
        FetcherRefMixin.__init__(self)

    async def process(self, request: Request):
        pass


class ItemProcessor(BaseProcessor, SaverRefMixin):
    def __init__(self):
        BaseProcessor.__init__(self)
        SaverRefMixin.__init__(self)

    async def process(self, item: Item):
        pass
