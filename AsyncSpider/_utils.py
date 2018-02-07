import queue
import asyncio

__all__ = ['ThreadSafeQueue', 'AsyncQueue', 'asleep', 'Storage']

ThreadSafeQueue = queue.Queue
AsyncQueue = asyncio.Queue

asleep = asyncio.sleep


class Storage(dict):
    def __init__(self, **kwargs):
        dict.__init__(self, **kwargs)

    def __getattr__(self, key):
        return self[key]

    def __setattr__(self, key, value):
        self[key] = value

    def copy(self):
        return self.__class__(**self)
