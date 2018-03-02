from .base import AioThreadExecutor, ControllerShortcutMixin
from .item import Item
from .fetsav import Fetcher, Saver
from .reqrep import Response
from asyncio import Queue as AsyncQueue
from asyncio import wrap_future
from collections import AsyncGenerator

__all__ = ['Spider']


class Spider(AioThreadExecutor, ControllerShortcutMixin):
    def __init__(self, controller):
        ControllerShortcutMixin.__init__(self, controller)
        AioThreadExecutor.__init__(self)

        self.concurrency = self.settings['concurrency']
        assert self.concurrency >= 1

        self.stop_when_empty = self.settings.get('stop_when_empty', True)

        self._action_queue = AsyncQueue(loop=self._loop)
        self._working_num = 0

        self.call_on_start(self._action_queue.put_nowait, self.start_action())
        for _ in range(self.concurrency):
            self.call_on_start(self.run_coro, self._worker())

    @property
    def fetcher(self) -> Fetcher:
        return self._controller.fetcher

    @property
    def saver(self) -> Saver:
        return self._controller.saver

    async def add_action(self, action):
        assert isinstance(action, AsyncGenerator)
        await self._action_queue.put(action)

    async def fetch(self, method, url, **kwargs) -> Response:
        fut = self.fetcher.run_coro_threadsafe(self.fetcher.fetch(method, url, **kwargs))
        fut = wrap_future(fut, loop=self._loop)
        return await fut

    async def save(self, item, wait=False):
        fut = self.saver.run_coro_threadsafe(self.saver.save(item))
        if wait:
            fut = wrap_future(fut, loop=self._loop)
            await fut

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
                if self.stop_when_empty and self._working_num == 0 and self._action_queue.empty():
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
