from ._utils import asleep, ThreadSafeQueue, AsyncQueue
from ._base import AioThreadActor
from ._item import Item
from ._fetcher import Request
from collections.abc import AsyncGenerator
from functools import wraps
import asyncio

__all__ = ['actionmethod', 'Spider']


class Action(AsyncGenerator):
    def __init__(self, gen: AsyncGenerator, action_id):
        super().__init__()
        self._gen = gen
        self.action_id = action_id

    async def __anext__(self):
        return await self._gen.asend(None)

    async def asend(self, value):
        return await self._gen.asend(value)

    async def athrow(self, typ, val=None, tb=None):
        return await self._gen.athrow(typ, val, tb)

    async def close(self):
        await self._gen.aclose()


def actionmethod(func):
    @wraps(func)
    def wrapper(spider, *args, **kwargs):
        gen = func(spider, *args, **kwargs)
        return Action(gen, hash(gen))

    return wrapper


class Spider(AioThreadActor):
    max_concurrent_action_num = 100

    def __init__(self, requests_queue=None, responses_queue=None, item_queue=None):
        super().__init__()

        self.requests_queue = requests_queue or ThreadSafeQueue()
        self.responses_queue = responses_queue or ThreadSafeQueue()
        self.item_queue = item_queue or ThreadSafeQueue()

        self._action_queue = AsyncQueue()

        self._aid2work_cond = {}
        self._aid2responses = {}

    def open(self):
        self._action_queue.put_nowait(self.start_action())

    def close(self):
        self._aid2responses.clear()
        self._aid2work_cond.clear()

    async def _main(self):
        self._loop.create_task(self._work_adder())
        self._loop.create_task(self._responses_putter())
        await self.wait_until_stopped()
        self.cancel_all_tasks()

    async def _work_adder(self):
        work_semaphore = asyncio.Semaphore(self.max_concurrent_action_num, loop=self._loop)
        adder_cond = asyncio.Condition(loop=self._loop)
        working_num = 0

        async def wait_for_responses(requests, aid, work_cond):
            # send requests
            self.requests_queue.put_nowait((aid, requests))
            async with work_cond:
                # wait for responses
                await work_cond.wait()
                resp = self._aid2responses[aid]
                del self._aid2responses[aid]
                return resp

        async def work(action):
            nonlocal working_num
            async with work_semaphore:
                # register this work
                work_cond = asyncio.Condition(loop=self._loop)
                self._aid2work_cond[action.action_id] = work_cond

                # drive the action
                # resp is not Response(s),but a obj to be sent into the action
                resp = None
                while True:
                    try:
                        obj = await action.asend(resp)
                    except StopAsyncIteration:
                        # unregister this work
                        del self._aid2work_cond[action.action_id]
                        working_num -= 1
                        async with adder_cond:
                            adder_cond.notify()
                        break
                    else:
                        if isinstance(obj, Action):
                            await self._action_queue.put(obj)
                            resp = None
                        elif isinstance(obj, Item):
                            self.item_queue.put_nowait(obj)
                            resp = None
                        elif isinstance(obj, Request):
                            resp = (await wait_for_responses([obj], action.action_id, work_cond))[0]
                        elif isinstance(obj, list):
                            resp = await wait_for_responses([obj], action.action_id, work_cond)

        def add_work():
            nonlocal working_num
            act = self._action_queue.get_nowait()
            self._loop.create_task(work(act))
            working_num += 1
            self._action_queue.task_done()

        add_work()

        while True:
            async with adder_cond:
                await adder_cond.wait()
                # when a work finished
                if self._action_queue.empty():
                    if working_num == 0:
                        # there is no action to drive and no action going
                        self._stop_event.set()
                        break
                else:
                    while not self._action_queue.empty():
                        add_work()

    async def _responses_putter(self):
        while True:
            if self.responses_queue.empty():
                await asleep(1)
            else:
                aid, responses = self.responses_queue.get_nowait()
                self._aid2responses[aid] = responses
                self.responses_queue.task_done()
                work_cond = self._aid2work_cond[aid]
                async with work_cond:
                    work_cond.notify()

    @actionmethod
    async def start_action(self):
        yield
