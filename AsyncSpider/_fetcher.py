from ._base import AbstractFetcher
from ._utils import Storage
import asyncio
import aiohttp


class Request(Storage):
    __slots__ = ('method', 'url', 'params', 'data', 'encoding', 'headers', 'proxy', 'proxy_headers', 'allow_redirects',
                 'max_redirects',)

    def __init__(self, method, url, **kwargs):
        super().__init__()
        self.update(method=method, url=url, **kwargs)


class Response(Storage):
    __slots__ = ('status', 'content', 'encoding',
                 'headers', 'cookies',
                 'host', 'history')

    def __init__(self, status, content, encoding, headers, cookies, host, history):
        super().__init__()
        self.update(status=status, content=content, encoding=encoding,
                    headers=headers, cookies=cookies,
                    host=host, history=history)

    @property
    def text(self):
        return self.content.decode(self.encoding)

    @classmethod
    async def from_ClientResponse(cls, resp: aiohttp.ClientResponse):
        return cls(status=resp.status,
                   content=await resp.read(),
                   encoding=resp._get_encoding(),
                   headers=resp.headers,
                   cookies=resp.cookies,
                   host=resp.host,
                   history=resp.history)


class TokenBucket:
    def __init__(self, qps: int, size: int, *, loop=None):
        assert 1 <= qps <= size
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
            self._token_num += self.qps
            if self._token_num > self.size:
                self._token_num = self.size
            async with self._condition:
                self._condition.notify_all()

    async def acquire(self):
        while True:
            if self._token_num >= 1:
                self._token_num -= 1
                break
            else:
                async with self._condition:
                    await self._condition.wait()


class Fetcher(AbstractFetcher):
    def __init__(self, settings: dict):
        super().__init__()
        self.session: aiohttp.ClientSession = None
        self._token_bucket: TokenBucket = None

        self.qps = settings.get('qps', 100)
        self.max_qps = settings.get('max_qps', 200)

    def open(self):
        self.session = aiohttp.ClientSession(loop=self._loop)
        self._token_bucket = TokenBucket(qps=self.qps, size=self.max_qps, loop=self._loop)
        self._token_bucket.start()

    def close(self):
        self.session.close()
        self.session = None
        self._token_bucket.stop()
        self._token_bucket = None

    async def fetch(self, *requests) -> [Response, ]:
        try:
            requests[0]
        except IndexError:
            raise RuntimeError('fetch(*requests) got no requests')
        responses = await self._handle_requests(requests)
        try:
            responses[1]
        except IndexError:
            return responses[0]
        else:
            return responses

    async def _handle_requests(self, requests) -> [Response, ]:
        requests = [await self.process_request(req) for req in requests]
        responses = [None] * len(requests)

        async def _request(index, request):
            responses[index] = await self._request(request)

        await asyncio.wait([_request(i, req) for i, req in enumerate(requests)])
        return responses

    async def process_request(self, request: Request) -> Request:
        return request

    async def _request(self, request: Request) -> Response:
        await self._token_bucket.acquire()
        kwargs = request.as_dict()
        async with self.session.request(**kwargs) as resp:
            return await Response.from_ClientResponse(resp)
