from ..core import Item, Field, Spider

__all__ = ['ImageItem']


class ImageItem(Item):
    url = Field()
    content = Field()

    @classmethod
    async def load(cls, spider: Spider, img_url,**kwargs):
        resp = await spider.fetch('get', img_url,**kwargs)
        return cls(url=resp.url, content=resp.content)
