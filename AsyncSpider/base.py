from .log import logger
from enum import IntEnum
from threading import Thread
from queue import Queue as ThreadsafeQueue
from queue import Empty
from asyncio import AbstractEventLoop
from functools import partial
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import concurrent.futures
import asyncio


class ExecutorState(IntEnum):
    initial = 0
    starting = 1
    running = 2
    stopping = 3
    stopped = 4


class BaseExecutor:
    def __init__(self):
        self._state = ExecutorState.initial

    def _set_state(self, state: str):
        self._state = ExecutorState[state]

    def is_initial(self):
        return self._state == ExecutorState.initial

    def is_starting(self):
        return self._state == ExecutorState.starting

    def is_running(self):
        return self._state == ExecutorState.running

    def is_stopping(self):
        return self._state == ExecutorState.stopping

    def is_stopped(self):
        return self._state == ExecutorState.stopped


class CallbackExecutor(BaseExecutor):
    def __init__(self):
        super().__init__()
        self._callback_queues = dict(
            start=ThreadsafeQueue(),
            stop=ThreadsafeQueue()
        )
        self.logger = logger

    def _call(self, key, func, *args, **kwargs):
        func = partial(func, *args, **kwargs)
        self._callback_queues[key].put(func)

    def _exec_all(self, key):
        queue = self._callback_queues[key]

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
                self.logger.exception('Callback {} failed.'.format(func))

    def call_on_start(self, func, *args, **kwargs):
        self._call('start', func, *args, **kwargs)

    def call_on_stop(self, func, *args, **kwargs):
        self._call('stop', func, *args, **kwargs)

    def _exec_start_callbacks(self):
        self._exec_all('start')

    def _exec_stop_callbacks(self):
        self._exec_all('stop')


class AioExecutor(CallbackExecutor):
    _thread_pool_executor = ThreadPoolExecutor()
    _process_pool_executor = ProcessPoolExecutor()

    def __init__(self):
        super().__init__()
        self._loop: AbstractEventLoop = asyncio.new_event_loop()

    @property
    def loop(self):
        return self._loop

    def _run(self):
        try:
            self._set_state('starting')
            self._exec_start_callbacks()

            self._set_state('running')
            self._loop.run_forever()

            self._set_state('stopping')
            self._exec_stop_callbacks()
        finally:
            self._clean_loop()
            self._loop.close()
            self._set_state('stopped')

    def _clean_loop(self):
        # cancel all tasks
        tasks = asyncio.Task.all_tasks(loop=self._loop)
        if tasks:
            for task in tasks:
                task.cancel()
            self._loop.run_until_complete(asyncio.wait(tasks))

    def _check_before_stop(self):
        assert not self.is_stopping() and not self.is_stopped()

    def call_soon(self, func, *args, **kwargs):
        self._check_before_stop()
        func = partial(func, *args, **kwargs)
        self._loop.call_soon(func)

    def call_soon_threadsafe(self, func, *args, **kwargs):
        self._check_before_stop()
        func = partial(func, *args, **kwargs)
        self._loop.call_soon_threadsafe(func)

    def run_in_thread_pool(self, func, *args, **kwargs) -> asyncio.Future:
        self._check_before_stop()
        func = partial(func, *args, **kwargs)
        return self._loop.run_in_executor(self._thread_pool_executor, func)

    def run_in_process_pool(self, func, *args, **kwargs) -> asyncio.Future:
        self._check_before_stop()
        func = partial(func, *args, **kwargs)
        return self._loop.run_in_executor(self._process_pool_executor, func)

    def run_coro(self, coro) -> asyncio.Task:
        self._check_before_stop()
        return self._loop.create_task(coro)

    def run_coro_threadsafe(self, coro) -> concurrent.futures.Future:
        self._check_before_stop()
        return asyncio.run_coroutine_threadsafe(coro, loop=self._loop)


class AioThreadExecutor(AioExecutor):
    def __init__(self):
        super().__init__()
        self._thread = None
        self.call_on_start(asyncio.set_event_loop, self._loop)

    def start(self):
        assert self.is_initial()
        self._thread = Thread(target=self._run)
        self._thread.start()

    def join(self):
        assert self._thread is not None and self._thread.is_alive()
        self._thread.join()

    def stop(self):
        self._check_before_stop()
        self._loop.call_soon_threadsafe(self._loop.stop)
