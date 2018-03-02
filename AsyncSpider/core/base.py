from . import log
from .data import FrozenDict
from threading import Thread
from queue import Queue as ThreadSafeQueue
from queue import Empty
from asyncio import AbstractEventLoop
from functools import partial
from logging import Logger
import concurrent.futures
import asyncio
import weakref

__all__ = ['CallbackMixin',
           'AioExecutor', 'AioThreadExecutor',
           'SuperProcessorMixin',
           'ControllerShortcutMixin']


class CallbackMixin:
    def __init__(self):
        self._on_start_callback_queue = ThreadSafeQueue()
        self._on_stop_callback_queue = ThreadSafeQueue()

    @staticmethod
    def _call(queue, func, *args, **kwargs):
        func = partial(func, *args, **kwargs)
        queue.put(func)

    def call_on_start(self, func, *args, **kwargs):
        self._call(self._on_start_callback_queue, func, *args, **kwargs)

    def call_on_stop(self, func, *args, **kwargs):
        self._call(self._on_stop_callback_queue, func, *args, **kwargs)

    def _exec_all(self, queue):
        def gen_fn():
            while True:
                try:
                    fn = queue.get_nowait()
                except Empty:
                    break
                else:
                    yield fn

        for func in gen_fn():
            try:
                func()
            except Exception:
                logger = getattr(self, 'logger') or log.logger
                logger.exception('Callback {} failed.'.format(func))

    def _exec_start_callbacks(self):
        self._exec_all(self._on_start_callback_queue)

    def _exec_stop_callbacks(self):
        self._exec_all(self._on_stop_callback_queue)


class AioExecutor(CallbackMixin):
    def __init__(self):
        CallbackMixin.__init__(self)
        self._loop = asyncio.new_event_loop()
        self._is_initial = True
        self._is_running = False
        self._is_stopped = False

    @property
    def loop(self) -> AbstractEventLoop:
        return self._loop

    @property
    def is_initial(self):
        return self._is_initial

    @property
    def is_running(self):
        return self._is_running

    @property
    def is_stopped(self):
        return self._is_stopped

    @property
    def is_closed(self):
        return self._loop.is_closed()

    def _run(self):
        try:
            self._exec_start_callbacks()

            self._is_initial, self._is_running = False, True
            self._loop.run_forever()
            self._clean_loop()
            self._is_running, self._is_stopped = False, True

            self._exec_stop_callbacks()
        finally:
            self._loop.close()

    def _clean_loop(self):
        tasks = asyncio.Task.all_tasks(loop=self._loop)
        for task in tasks:
            task.cancel()
        if tasks:
            self._loop.run_until_complete(asyncio.wait(tasks))

    def run(self):
        self._run()

    def call_soon(self, func, *args, **kwargs):
        assert not self.is_stopped
        func = partial(func, *args, **kwargs)
        self._loop.call_soon(func)

    def call_soon_threadsafe(self, func, *args, **kwargs):
        assert not self.is_stopped
        func = partial(func, *args, **kwargs)
        self._loop.call_soon_threadsafe(func)

    def run_coro(self, coro) -> asyncio.Task:
        assert not self.is_stopped
        return self._loop.create_task(coro)

    def run_coro_threadsafe(self, coro) -> concurrent.futures.Future:
        assert not self.is_stopped
        return asyncio.run_coroutine_threadsafe(coro, loop=self._loop)


class AioThreadExecutor(AioExecutor):
    def run(self):
        self.start()
        self.join()

    @property
    def is_running(self):
        return not self._is_stopped and self._thread.is_alive()

    @property
    def is_closed(self):
        return not self._thread.is_alive() and not self._is_initial

    def __init__(self):
        AioExecutor.__init__(self)
        self._thread = Thread(target=self._run)
        self.call_on_start(asyncio.set_event_loop, self._loop)

    def start(self):
        assert not self._thread.is_alive()
        self._thread.start()

    def join(self):
        assert self._thread.is_alive()
        self._thread.join()

    def stop(self):
        assert self.is_running
        self.call_soon_threadsafe(self._loop.stop)


class SuperProcessorMixin:
    def __init__(self):
        self._processors = []

    def add_processor(self, processor):
        if processor in self._processors:
            raise ValueError('{} is already in {}.processors'.format(processor, self))
        self._processors.append(processor)

    def remove_processor(self, processor):
        try:
            self._processors.remove(processor)
        except ValueError as exc:
            exc.args = ('{} is not in {}.processors'.format(processor, self),)
            raise

    @property
    def processors(self):
        return tuple(self._processors)


class ControllerShortcutMixin:
    def __init__(self, controller):
        self._controller = weakref.proxy(controller)

    @property
    def settings(self) -> FrozenDict:
        return self._controller.settings

    @property
    def logger(self) -> Logger:
        return self._controller.logger

    @property
    def runtime_data(self) -> dict:
        return self._controller.runtime_data
