from ._base import AioThreadActor
from ._utils import asleep, ThreadSafeQueue
import asyncio

__all__ = ['Saver']


class Saver(AioThreadActor):
    def __init__(self, item_queue=None):
        super().__init__()
        self.item_queue = item_queue or ThreadSafeQueue()
        self._empty_event = asyncio.Event(loop=self._loop)

    async def _main(self):
        self._loop.create_task(self._save_adder())
        await self.wait_until_stopped()
        await self.wait_until_empty()
        # ensure that all items are saved
        main_task = asyncio.Task.current_task(loop=self._loop)
        tasks = asyncio.Task.all_tasks(loop=self._loop)
        tasks.remove(main_task)
        if tasks:
            await asyncio.wait(tasks)

    async def _save_adder(self):
        while True:
            # get item continuously when item_queue is not empty
            # wait for 1 second when item_queue is empty
            if self.item_queue.empty():
                self._empty_event.set()
                if self._stop_event.is_set():
                    break
                await asleep(1)
            else:
                self._empty_event.clear()
                item = self.item_queue.get_nowait()
                self._loop.create_task(self.save(item))
                self.item_queue.task_done()

    async def wait_until_empty(self):
        await self._empty_event.wait()

    async def save(self, item):
        # save item
        pass
