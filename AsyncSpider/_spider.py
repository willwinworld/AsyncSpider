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

    def __init__(self, fetcher, saver, **settings):
        super().__init__()

        self.max_current_actions = settings.get('max_current_actions', 10)
        assert self.max_current_actions >= 1 and isinstance(self.max_current_actions, int)

        self.fetcher = fetcher
        self.saver = saver

        self._action_queue = AsyncQueue()
        self._action_queue.put_nowait(self.start_action())

        self._driving_action_num = 0
        self._action_finished_event = asyncio.Event(loop=self._loop)

    def start(self):
        self.fetcher.start()
        self.saver.start()
        super().start()

    def stop(self):
        self.fetcher.stop()
        self.saver.stop()
        super().stop()

    def join(self):
        super().join()
        self.fetcher.stop()
        self.saver.stop()
        self.fetcher.join()
        self.saver.join()

    def open(self):
        self._loop.create_task(self._driver_adder())

    async def fetch(self, *requests):
        return await self.fetcher.run_coro(self.fetcher.fetch(*requests), loop=self._loop)

    async def save(self, item, wait_for_result=False):
        future = self.saver.run_coro(self.saver.save(item), loop=self._loop)
        if wait_for_result:
            return await future

    async def add_action(self, action):
        await self._action_queue.put(action)

    async def _drive(self, action, semaphore):
        async def handle_obj(obj):
            if obj is None:
                pass
            elif isinstance(obj, Item):
                await self.save(obj)
            elif isinstance(obj, Action):
                await self.add_action(obj)
            else:
                raise TypeError(f'{action.name} yield an unexpected object {obj}.')

        def exit_drive():
            self._driving_action_num -= 1
            self._action_finished_event.set()

        async with semaphore:
            try:
                async for o in action:
                    await handle_obj(o)
            finally:
                exit_drive()

    async def _driver_adder(self):
        semaphore = asyncio.Semaphore(self.max_current_actions, loop=self._loop)
        while True:
            while not self._action_queue.empty():
                act = self._action_queue.get_nowait()
                self._loop.create_task(self._drive(act, semaphore))
                self._driving_action_num += 1
                self._action_queue.task_done()
            await self._action_finished_event.wait()
            if self._driving_action_num == 0 and self._action_queue.empty():
                break
            self._action_finished_event.clear()
        self._loop.stop()

    @actionmethod
    async def start_action(self):
        yield
