from ._base import AioThreadActor
from ._utils import Storage, asleep, ThreadSafeQueue
import asyncio
import aiohttp

__all__ = ['Request', 'Response', 'Fetcher']


class Request(Storage):
    def __init__(self, method, url, **kwargs):
        super().__init__(method=method, url=url, **kwargs)


class Response(Storage):
    def __init__(self, status, content, **kwargs):
        super().__init__(status=status, content=content, **kwargs)

    def text(self, encoding='utf8') -> str:
        return self.content.decode(encoding)


class TokenBucket:
    def __init__(self, qps: int, size: int, *, loop=None):
        assert 1 <= qps <= size
        self.qps = qps
        self.size = size
        self.token_num = 0
        self._loop = loop or asyncio.get_event_loop()
        self._task = None
        self._condition = asyncio.Condition(loop=self._loop)

    def start(self):
        self.token_num = self.size
        self._task = self._loop.create_task(self._run())

    async def _run(self):
        while True:
            await asleep(1)
            self.token_num += self.qps
            if self.token_num > self.size:
                self.token_num = self.size
            async with self._condition:
                self._condition.notify_all()

    def stop(self):
        self._task.cancel()
        self._task = None

    async def acquire(self):
        while True:
            if self.token_num >= 1:
                self.token_num -= 1
                break
            else:
                async with self._condition:
                    await self._condition.wait()


class Fetcher(AioThreadActor):
    qps = 100
    max_qps = 200

    def __init__(self, requests_queue=None, responses_queue=None):
        super().__init__()
        self.requests_queue = requests_queue or ThreadSafeQueue()
        self.responses_queue = responses_queue or ThreadSafeQueue()
        self.token_bucket = None
        self.session = None

    def open(self):
        self.token_bucket = TokenBucket(self.qps, self.max_qps, loop=self._loop)
        self.session = aiohttp.ClientSession(loop=self._loop)

    def close(self):
        self.token_bucket = None
        self.session.close()
        self.session = None

    async def _main(self):
        self.token_bucket.start()
        self._loop.create_task(self._req_adder())
        await self.wait_until_stopped()
        self.cancel_all_tasks()

    async def _req_adder(self):
        while True:
            if self.requests_queue.empty():
                await asleep(1)
            else:
                aid, requests = self.requests_queue.get_nowait()
                self._loop.create_task(self._handle_requests(aid, requests))
                self.requests_queue.task_done()

    async def process_request(self, request) -> Request:
        return request

    async def request(self, **kwargs):
        await self.token_bucket.acquire()
        async with self.session.request(**kwargs) as resp:
            return await self.process_response(resp)

    async def process_response(self, response) -> Response:
        # todo : extract more info
        return Response(response.status,
                        await response.read())

    async def _handle_request(self, request, index, responses):
        req = await self.process_request(request)
        resp = await self.request(**req)
        responses[index] = resp

    async def _handle_requests(self, aid, requests):
        responses = [None] * len(requests)
        tasks = [self._loop.create_task(self._handle_request(req, i, responses)) for i, req in enumerate(requests)]
        await asyncio.wait(tasks)
        self.responses_queue.put_nowait((aid, responses))
