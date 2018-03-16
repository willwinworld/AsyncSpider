from .base import AioThreadExecutor
from .reqrep import Request, Response
import asyncio
import aiohttp

__all__ = ['Fetcher', 'Saver', 'FetcherRefMixin', 'SaverRefMixin']


class SuperProcessor(AioThreadExecutor):
    def __init__(self):
        super().__init__()
        self._processors = []
        self.call_on_start(self._register_all)

    def _register_all(self):
        for p in self._processors:
            self.call_on_start(p.on_start)
            self.call_on_stop(p.on_stop)

    def add_processor(self, processor):
        assert self.is_initial()
        if processor in self._processors:
            raise ValueError('{} already has the processor {}'.format(self, processor))
        self._processors.append(processor)

    def remove_processor(self, processor):
        assert self.is_initial()
        try:
            self._processors.remove(processor)
        except ValueError as exc:
            exc.args = ('{} does not have the processor {}'.format(self, processor),)
            raise

    @property
    def processors(self):
        return tuple(self._processors)


class Fetcher(SuperProcessor):
    def add_processor(self, request_processor):
        super().add_processor(request_processor)
        request_processor.set_fetcher(self)

    def remove_processor(self, request_processor):
        super().remove_processor(request_processor)
        request_processor.set_fetcher(None)

    def __init__(self):
        super().__init__()
        self._session: aiohttp.ClientSession = None

        def set_session():
            self._session = aiohttp.ClientSession(loop=self._loop)

        def close_session():
            self.loop.run_until_complete(self._session.close())

        self.call_on_start(set_session)
        self.call_on_stop(close_session)

    async def fetch(self, method, url, **kwargs):
        req = Request(method, url, **kwargs)
        for p in self._processors:
            await p.process(req)
        async with self._session.request(method, url, **kwargs) as resp:
            return await Response.from_client_response(resp)


class Saver(SuperProcessor):
    def add_processor(self, item_processor):
        super().add_processor(item_processor)
        item_processor.set_saver(self)

    def remove_processor(self, item_processor):
        super().remove_processor(item_processor)
        item_processor.set_saver(None)

    def _clean_loop(self):
        tasks = asyncio.Task.all_tasks(loop=self._loop)
        if tasks:
            self._loop.run_until_complete(asyncio.wait(tasks))

    async def save(self, item):
        for p in self._processors:
            await p.process(item)


class FetcherRefMixin:
    def __init__(self):
        self._fetcher = None

    def set_fetcher(self, fetcher):
        self._fetcher = fetcher

    @property
    def fetcher(self) -> Fetcher:
        return self._fetcher

    def _check_fetcher(self):
        assert isinstance(self._fetcher, Fetcher)


class SaverRefMixin:
    def __init__(self):
        self._saver = None

    def set_saver(self, saver):
        self._saver = saver

    @property
    def saver(self) -> Saver:
        return self._saver

    def _check_saver(self):
        assert isinstance(self._saver, Saver)
