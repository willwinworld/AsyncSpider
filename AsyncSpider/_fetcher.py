from ._base import AbstractFetcher, Storage
from ._settings import Settings
import asyncio
import aiohttp
import chardet

__all__ = ['Request', 'Response', 'TokenBucket', 'Fetcher']


class Request(Storage):
    __slots__ = ('method', 'url', 'params', 'data', 'encoding',
                 'headers', 'proxy', 'proxy_headers',
                 'allow_redirects', 'max_redirects',)

    def __init__(self, method, url, **kwargs):
        super().__init__()
        self.update(method=method, url=url, **kwargs)


class Response(Storage):
    __slots__ = ('status', 'content', '_encoding',
                 'headers', 'cookies',
                 'host', 'history')

    def __init__(self, status, content, headers, cookies, host, history):
        super().__init__()
        self.update(status=status, content=content, _encoding=None,
                    headers=headers, cookies=cookies,
                    host=host, history=history)

    def get_encoding(self):
        if self._encoding:
            return self._encoding

        # copied from aiohttp
        ctype = self.headers.get(aiohttp.hdrs.CONTENT_TYPE, '').lower()
        mtype, stype, _, params = aiohttp.helpers.parse_mimetype(ctype)

        encoding = params.get('charset')
        if not encoding:
            if mtype == 'application' and stype == 'json':
                # RFC 7159 states that the default encoding is UTF-8.
                encoding = 'utf-8'
            else:
                encoding = chardet.detect(self.content)['encoding']
        if not encoding:
            encoding = 'utf-8'

        self.update(_encoding=encoding)
        return encoding

    def text(self, encoding=None, errors='strict'):
        encoding = encoding or self.get_encoding()
        return self.content.decode(encoding, errors=errors)

    @classmethod
    async def fromClientResponse(cls, resp: aiohttp.ClientResponse):
        return cls(status=resp.status,
                   content=await resp.read(),
                   headers=resp.headers,
                   cookies=resp.cookies,
                   host=resp.host,
                   history=resp.history)


class TokenBucket:
    def __init__(self, qps, size, *, loop=None):
        self.qps = qps
        self.size = size
        self._token_num = 0
        self._loop = loop or asyncio.get_event_loop()
        self._task = None
        self._condition = asyncio.Condition(loop=self._loop)

    def start(self):
        self._token_num = self.size
        self._task = self._loop.create_task(self._run())

    def stop(self):
        self._task.cancel()
        self._task = None
        self._token_num = 0

    async def _run(self):
        while True:
            await asyncio.sleep(1)
            tn = self._token_num + self.qps
            self._token_num = self.size if tn > self.size else tn
            async with self._condition:
                self._condition.notify_all()

    async def take(self):
        async with self._condition:
            await self._condition.wait_for(lambda: self._token_num >= 1)
            self._token_num -= 1


class Fetcher(AbstractFetcher):
    def __init__(self, settings: Settings):
        super().__init__()
        self.session: aiohttp.ClientSession = None
        self._token_bucket: TokenBucket = None

        self.settings = settings
        self.qps = settings.fetcher.get('qps')
        self.max_qps = settings.fetcher.get('max_qps')
        assert 0 < self.qps <= self.max_qps

    def open(self):
        self.session = aiohttp.ClientSession(loop=self._loop)
        self._token_bucket = TokenBucket(qps=self.qps, size=self.max_qps, loop=self._loop)
        self._token_bucket.start()

    def close(self):
        self.session.close()
        self.session = None
        self._token_bucket.stop()
        self._token_bucket = None

    async def fetch(self, method, url, **kwargs) -> Response:
        req = Request(method, url, **kwargs)
        req = await self.process_request(req)
        await self._token_bucket.take()
        return await self._request(req)

    async def process_request(self, request: Request) -> Request:
        return request

    async def _request(self, request: Request) -> Response:
        kwargs = request.as_dict()
        async with self.session.request(**kwargs) as resp:
            return await Response.fromClientResponse(resp)
