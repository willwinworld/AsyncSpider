from threading import Thread
import asyncio


def run_in_loop(main_loop, coro, sub_loop) -> asyncio.Future:
    future = asyncio.run_coroutine_threadsafe(coro, loop=sub_loop)
    return asyncio.futures.wrap_future(future, loop=main_loop)


def cancel_all_tasks(loop):
    tasks = asyncio.Task.all_tasks(loop=loop)
    if tasks:
        for task in tasks:
            task.cancel()
        loop.run_until_complete(asyncio.wait(tasks))


class AioThreadActor:
    def __init__(self):
        self._loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()
        self._thread = Thread(target=self._run,
                              daemon=True,
                              name=self.__class__.__name__)

    def _run(self):
        self.open()
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()
        cancel_all_tasks(loop=self._loop)
        self.close()

    def open(self):
        pass

    def close(self):
        pass

    def start(self):
        self._thread.start()

    def stop(self):
        self._loop.call_soon_threadsafe(self._loop.stop)

    def join(self):
        self._thread.join()

    def run_coro(self, coro, *, loop=None):
        loop = loop or asyncio.get_event_loop()
        return run_in_loop(loop, coro, self._loop)


class AbstractFetcher(AioThreadActor):
    async def fetch(self, *requests):
        raise NotImplementedError


class AbstractSaver(AioThreadActor):
    async def save(self, item):
        raise NotImplementedError
