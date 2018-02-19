from ._settings import default_settings
from ._spider import Spider
from contextlib import contextmanager

__all__ = ['run']


@contextmanager
def run(spider_class, fetcher_class, saver_class, settings=None):
    settings = settings or default_settings

    fetcher = fetcher_class(settings)
    saver = saver_class(settings)
    spider: Spider = spider_class(fetcher, saver, settings)

    spider.start_sub()
    spider.start()

    yield spider

    spider.stop()
    spider.stop_sub()

# for example:

# with run(spd_cls, fc, sc, settings) as spd:
#     spd.join()
