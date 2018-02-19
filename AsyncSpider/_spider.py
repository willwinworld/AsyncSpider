from ._base import AbstractSpider, Action, isactionmethod, actionmethod
from ._item import Item
from asyncio import Queue as AsyncQueue
import asyncio

__all__ = ['SpiderMeta', 'Spider']


class SpiderMeta(type):
    def __new__(mcs, name, bases, namespace: dict):
        spider_class = type.__new__(mcs, name, bases, namespace)
        actions: dict = getattr(spider_class, 'actions')
        actions.update({k: v for k, v in namespace.items() if isactionmethod(v)})
        return spider_class


class Spider(AbstractSpider, metaclass=SpiderMeta):
    actions = {}

    def __init__(self, fetcher, saver, settings):
        super().__init__()

        self.settings = settings
        self.max_current_actions = settings.spider.get('max_current_actions')

        self.fetcher = fetcher
        self.saver = saver

        self._driver_semaphore = asyncio.Semaphore(self.max_current_actions, loop=self._loop)
        self._driving_action_num = 0
        self._action_queue = AsyncQueue(loop=self._loop)
        self._action_queue.put_nowait(self.start_action())

    def start_sub(self):
        self.fetcher.start()
        self.saver.start()

    def stop_sub(self):
        self.fetcher.stop()
        self.saver.stop()

    def join_sub(self):
        self.fetcher.join()
        self.saver.join()

    def open(self):
        self._next()

    async def fetch(self, method, url, **kwargs):
        return await self.fetcher.run_coro(self.fetcher.fetch(method, url, **kwargs), loop=self._loop)

    async def save(self, item, wait_for_result=False):
        future = self.saver.run_coro(self.saver.save(item), loop=self._loop)
        if wait_for_result:
            return await future

    async def add_action(self, action):
        await self._action_queue.put(action)

    async def _drive(self, action):
        async with self._driver_semaphore:
            try:
                async for obj in action:
                    if obj is None:
                        pass
                    elif isinstance(obj, Item):
                        await self.save(obj)
                    elif isinstance(obj, Action):
                        await self.add_action(obj)
                    else:
                        raise TypeError('{} yield an unexpected object {}.'.format(action.name, obj))
            finally:
                self._driving_action_num -= 1
                self._next()

    def _next(self):
        if self._action_queue.empty():
            if self._driving_action_num == 0:
                self._loop.stop()
        else:
            while not self._action_queue.empty():
                act = self._action_queue.get_nowait()
                self._loop.create_task(self._drive(act))
                self._driving_action_num += 1
                self._action_queue.task_done()

    @actionmethod
    async def start_action(self):
        yield
