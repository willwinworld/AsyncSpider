from ._base import AbstractSaver
from ._item import Item
import asyncio

__all__ = ['Saver']


class Saver(AbstractSaver):
    def __init__(self, **settings):
        super().__init__()
        self.run_until_complete = settings.get('run_until_complete', True)

    def _run(self):
        self.open()
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()
        tasks = asyncio.Task.all_tasks(loop=self._loop)
        if tasks:
            if self.run_until_complete:
                self._loop.run_until_complete(self._loop.create_task(asyncio.wait(tasks, loop=self._loop)))
            else:
                for task in tasks:
                    task.cancel()
                self._loop.run_forever()
        self.close()

    async def save(self, item: Item):
        pass
