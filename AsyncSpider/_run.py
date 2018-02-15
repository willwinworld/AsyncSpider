from ._settings import default_settings

__all__ = ['run']


def run(spider_class, fetcher_class, saver_class, settings=None, join=True):
    settings = settings or default_settings

    fetcher = fetcher_class(**settings.get('Fetcher', {}))
    saver = saver_class(**settings.get('Saver', {}))
    spider = spider_class(fetcher, saver, **settings.get('Spider', {}))

    spider.start()
    if join:
        spider.join()
