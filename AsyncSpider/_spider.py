from ._base import AioThreadActor
from ._fetcher import Fetcher
from ._saver import Saver
from ._item import Item
from ._settings import default_settings
from functools import wraps
from collections import AsyncGenerator
from asyncio import Queue as AsyncQueue
import asyncio


class Action(AsyncGenerator):
    def __init__(self, gen: AsyncGenerator, name):
        self._gen = gen
        self.name = name

    async def __anext__(self):
        return await self.asend(None)

    async def asend(self, value):
        return await self._gen.asend(value)

    async def athrow(self, typ, val=None, tb=None):
        return await self._gen.athrow(typ, val, tb)

    async def aclose(self):
        return await self._gen.aclose()


def isactionmethod(func):
    return getattr(func, '__isactionmethod__', False)


def actionmethod(func):
    func.__isactionmethod__ = True

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        return Action(func(self, *args, **kwargs), func.__name__)

    return wrapper


class SpiderMeta(type):
    def __new__(mcs, name, bases, namespace: dict):
        spider_class = type.__new__(mcs, name, bases, namespace)
        actions: dict = getattr(spider_class, 'actions')
        actions.update({k: v for k, v in namespace.items() if isactionmethod(v)})
        return spider_class


class Spider(AioThreadActor, metaclass=SpiderMeta):
    actions = {}

    def __init__(self, settings: dict = None):
        super().__init__()
        settings = settings or default_settings

        spider_settings = settings.get('Spider', {})
        self.max_current_actions = spider_settings.get('max_current_actions') or 10
        assert self.max_current_actions >= 1 and isinstance(self.max_current_actions, int)

        fetcher_settings = settings.get('Fetcher', {})
        fetcher_class = fetcher_settings.get('class', Fetcher)
        self.fetcher = fetcher_class(fetcher_settings)

        saver_settings = settings.get('Saver', {})
        saver_class = saver_settings.get('class', Saver)
        self.saver = saver_class(saver_settings)

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
        self._loop.create_task(self.driver_adder())

    async def fetch(self, *requests):
        return await self.fetcher.run_coro(self.fetcher.fetch(*requests), loop=self._loop)

    async def save(self, item, wait_for_result=False):
        future = self.saver.run_coro(self.saver.save(item), loop=self._loop)
        if wait_for_result:
            return await future

    async def add_action(self, action: AsyncGenerator):
        await self._action_queue.put(action)

    async def drive(self, action: Action):
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

        try:
            async for o in action:
                await handle_obj(o)
        finally:
            exit_drive()

    async def driver_adder(self):
        while True:
            while not self._action_queue.empty():
                act = self._action_queue.get_nowait()
                self._loop.create_task(self.drive(act))
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
