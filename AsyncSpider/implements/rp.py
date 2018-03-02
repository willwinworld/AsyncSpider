from ..core import RequestProcessor, Request
from fake_useragent import UserAgent
import asyncio

__all__ = ['TokenBucketRP', 'RandomUserAgentRP']


class TokenBucketRP(RequestProcessor):
    def __init__(self, fetcher):
        super().__init__(fetcher)

        self._qps = self.fetcher.settings['qps']
        self._max_qps = self.fetcher.settings['max_qps']
        self._token_num = self._max_qps

        self._cond = asyncio.Condition(loop=fetcher.loop)

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
        self.fetcher.run_coro(self._add_token())

    async def process(self, request):
        await self.acquire()


class RandomUserAgentRP(RequestProcessor):
    ua = UserAgent()

    async def process(self, request: Request):
        h = request.get('headers', {})
        h['User-Agent'] = self.ua.random
        request['headers'] = h
