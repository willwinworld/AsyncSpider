from ..processor import RequestProcessor
from ..reqrep import Request
from fake_useragent import UserAgent
import asyncio

__all__ = ['TokenBucketRP', 'RandomUserAgentRP']


class TokenBucketRP(RequestProcessor):
    def __init__(self, qps, max_qps):
        super().__init__()

        self._qps = qps
        self._max_qps = max_qps
        self._token_num = max_qps

        self._cond = None

    async def _add_token(self):
        while True:
            await asyncio.sleep(1)
            t = self._token_num + self._qps
            if t > self._max_qps:
                self._token_num = self._max_qps
            else:
                self._token_num = t
            async with self._cond:
                self._cond.notify_all()

    async def acquire(self):
        async with self._cond:
            await self._cond.wait_for(lambda: self._token_num >= 1)
            self._token_num -= 1

    def on_start(self):
        self._cond = asyncio.Condition(loop=self.fetcher.loop)
        self.fetcher.run_coro(self._add_token())

    async def process(self, request):
        await self.acquire()


class RandomUserAgentRP(RequestProcessor):
    ua = UserAgent()

    async def process(self, request: Request):
        request.setdefault('headers', {})
        request['headers']['User-Agent'] = self.ua.random
