from .base import AioThreadExecutor
from .item import Item
from .fetsav import FetcherRefMixin, SaverRefMixin
from .reqrep import Response
from .data import FrozenDict
from asyncio import Queue as AsyncQueue
from asyncio import wrap_future
from collections import AsyncGenerator
from threading import Lock

__all__ = ['Spider']


class Spider(AioThreadExecutor, FetcherRefMixin, SaverRefMixin):
    def __init__(self, concurrency=10, stop_when_empty=True, **settings):
        AioThreadExecutor.__init__(self)
        FetcherRefMixin.__init__(self)
        SaverRefMixin.__init__(self)

        self.runtime_data = dict(fetch_count=0, item_count=0)
        self.mutex = Lock()

        assert concurrency >= 1
        self.settings = FrozenDict(concurrency=concurrency, stop_when_empty=stop_when_empty, **settings)

        self._action_queue = AsyncQueue(loop=self.loop)
        self._working_num = 0

        self.call_on_start(self._check_fetcher)
        self.call_on_start(self._check_saver)
        self.call_on_start(self._action_queue.put_nowait, self.start_action())
        for _ in range(concurrency):
            self.call_on_start(self.run_coro, self._worker())

    async def add_action(self, action):
        assert isinstance(action, AsyncGenerator)
        await self._action_queue.put(action)

    async def fetch(self, method, url, **kwargs) -> Response:
        fut = self.fetcher.run_coro_threadsafe(self.fetcher.fetch(method, url, **kwargs))
        fut = wrap_future(fut, loop=self._loop)
        resp = await fut
        with self.mutex:
            self.runtime_data['fetch_count'] += 1
        return resp

    async def save(self, item, wait=False):
        fut = self.saver.run_coro_threadsafe(self.saver.save(item))
        if wait:
            fut = wrap_future(fut, loop=self._loop)
            await fut
        with self.mutex:
            self.runtime_data['item_count'] += 1

    async def _worker(self):
        while True:
            act = await self._action_queue.get()

            self._working_num += 1
            try:
                await self._drive(act)
            except Exception:
                self.logger.exception('Action {} failed.'.format(act))
            finally:
                self._working_num -= 1
                self._action_queue.task_done()
                if self.settings['stop_when_empty'] and self._action_queue.empty() and self._working_num == 0:
                    self._loop.stop()

    async def _drive(self, action):
        async for obj in action:
            if obj is None:
                pass
            elif isinstance(obj, AsyncGenerator):
                await self.add_action(obj)
            elif isinstance(obj, Item):
                await self.save(obj, wait=False)
            else:
                self.logger.warning('{} yield an unexpected object: {}'.format(action, obj))

    async def start_action(self):
        yield
