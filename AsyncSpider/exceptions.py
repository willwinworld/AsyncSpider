from concurrent.futures import TimeoutError

__all__ = ['BaseSpiderException',

           'FetcherException',
           'RequestFailError', 'DropRequest', 'TimeoutError',

           'SaverException',
           'ItemFailError', 'DropItem',

           'SpiderException',
           'ActionFailError'
           ]


class BaseSpiderException(Exception):
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
