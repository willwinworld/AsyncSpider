import concurrent.futures

__all__ = ['BaseSpiderException',
           'TimeoutError',

           'FetcherException',
           'RequestFailError', 'DropRequest',

           'SaverException',
           'ItemFailError', 'DropItem',

           'SpiderException',
           'ActionFailError'
           ]


class BaseSpiderException(Exception):
    pass


class TimeoutError(concurrent.futures.TimeoutError, BaseSpiderException):
    pass


class FetcherException(BaseSpiderException):
    pass


class RequestFailError(FetcherException):
    pass


class DropRequest(RequestFailError):
    pass


class SaverException(BaseSpiderException):
    pass


class ItemFailError(SaverException):
    pass


class DropItem(ItemFailError):
    pass


class SpiderException(BaseSpiderException):
    pass


class ActionFailError(SpiderException):
    pass
