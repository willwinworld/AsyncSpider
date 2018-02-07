from threading import Thread, Lock
import asyncio

__all__ = ['AioThreadActor']


class ThreadActor:
    def __init__(self):
        self._thread = Thread(name=self.__class__.__name__,
                              target=lambda: (self.open(), self._run(), self.close()),
                              daemon=True)
        self._thread_lock = Lock()

    def start(self):
        self._thread.start()

    def stop(self, join: bool = True):
        raise NotImplementedError

    def join(self):
        self._thread.join()

    def _run(self):
        pass

    def open(self):
        pass

    def close(self):
        pass


class AioThreadActor(ThreadActor):
    def __init__(self):
        super().__init__()
        self._loop = asyncio.new_event_loop()
        self._stop_event = asyncio.Event(loop=self._loop)

    def _run(self):
        self._loop.run_until_complete(self._loop.create_task(self._main()))

    def stop(self, join: bool = True):
        with self._thread_lock:
            self._stop_event.set()
        if join:
            self.join()

    def cancel_all_tasks(self):
        cur_task = asyncio.Task.current_task(loop=self._loop)
        tasks = asyncio.Task.all_tasks(loop=self._loop)
        tasks.remove(cur_task)
        for task in tasks:
            task.cancel()

    async def wait_until_stopped(self):
        await self._stop_event.wait()

    async def _main(self):
        await self.wait_until_stopped()
        self.cancel_all_tasks()
