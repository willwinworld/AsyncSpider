from .base import AioThreadExecutor, SuperProcessorMixin, ControllerShortcutMixin
from .reqrep import Request, Response
import asyncio
import aiohttp

__all__ = ['Fetcher', 'Saver']


def active_all(sp):
    for p in sp.processors:
        sp.call_on_start(p.on_start)
        sp.call_on_stop(p.on_stop)


class Fetcher(AioThreadExecutor, SuperProcessorMixin, ControllerShortcutMixin):
    def add_processor(self, request_processor):
        assert self.is_initial
        SuperProcessorMixin.add_processor(self, request_processor)

    def remove_processor(self, request_processor):
        assert self.is_initial
        SuperProcessorMixin.remove_processor(self, request_processor)

    def __init__(self, controller):
        ControllerShortcutMixin.__init__(self, controller)
        SuperProcessorMixin.__init__(self)
        AioThreadExecutor.__init__(self)
        self._session: aiohttp.ClientSession = None

        def set_session():
            self._session = aiohttp.ClientSession(loop=self._loop)

        def close_session():
            self._loop.run_until_complete(self._session.close())

        self.call_on_start(set_session)
        self.call_on_stop(close_session)
        self.call_on_start(active_all, self)

    async def fetch(self, method, url, **kwargs):
        req = Request(method, url, **kwargs)
        for p in self._processors:
            await p.process(req)
        async with self._session.request(method, url, **kwargs) as resp:
            return await Response.from_client_response(resp)


class Saver(AioThreadExecutor, SuperProcessorMixin, ControllerShortcutMixin):
    def add_processor(self, item_processor):
        assert self.is_initial
        SuperProcessorMixin.add_processor(self, item_processor)

    def remove_processor(self, item_processor):
        assert self.is_initial
        SuperProcessorMixin.remove_processor(self, item_processor)

    def _clean_loop(self):
        tasks = asyncio.Task.all_tasks(loop=self._loop)
        if tasks:
            self._loop.run_until_complete(asyncio.wait(tasks))

    def __init__(self, controller):
        ControllerShortcutMixin.__init__(self, controller)
        SuperProcessorMixin.__init__(self)
        AioThreadExecutor.__init__(self)
        self.call_on_start(active_all, self)

    async def save(self, item):
        for p in self._processors:
            await p.process(item)
