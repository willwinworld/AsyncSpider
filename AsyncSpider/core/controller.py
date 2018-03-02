from .base import CallbackMixin
from .data import FrozenDict
from .spider import Spider
from .fetsav import Fetcher, Saver
from .processor import RequestProcessor, ItemProcessor
from .log import logger
from queue import Queue as ThreadSafeQueue
from logging import Logger
import time

__all__ = ['Controller']


class Controller(CallbackMixin):
    def __init__(self, name: str, settings: dict = None):
        CallbackMixin.__init__(self)
        assert name != 'AsyncSpider'
        self._name = name
        self._logger = logger.getChild(self._name)

        if settings is not None:
            settings = FrozenDict(settings)
        self._settings = settings

        self._fetcher = Fetcher(self)
        self._saver = Saver(self)
        self._spiders = set()

        self._runtime_callback_queue = ThreadSafeQueue()

        self.runtime_data = {}
        st, ed = _set_rt(self)
        self.call_on_start(st)
        self.call_on_stop(ed)

    def call(self, func, *args, **kwargs):
        self._call(self._runtime_callback_queue, func, *args, **kwargs)

    def _exec_runtime_callbacks(self):
        self._exec_all(self._runtime_callback_queue)

    def set_settings(self, settings):
        if isinstance(settings, FrozenDict):
            self._settings = settings
        else:
            self._settings = FrozenDict(settings)

    def construct(self, *classes):
        for cls in classes:
            if issubclass(cls, RequestProcessor):
                self._fetcher.add_processor(cls(self._fetcher))
            elif issubclass(cls, ItemProcessor):
                self._saver.add_processor(cls(self._saver))
            elif issubclass(cls, Spider):
                self._spiders.add(cls(self))
            else:
                self.logger.warning('construct got an unexpected class: {}'.format(cls))

    def _wait_for(self, predicate):
        while True:
            time.sleep(0.1)
            self._exec_runtime_callbacks()
            if predicate():
                break

    def are_all_spiders_closed(self):
        for spd in self._spiders:
            if not spd.is_closed:
                return False
        else:
            return True

    def run_all(self):
        self._exec_start_callbacks()
        self.fetcher.start()
        self.saver.start()
        for spd in self._spiders:
            spd.start()

        self._wait_for(self.are_all_spiders_closed)
        self.fetcher.stop()
        self.saver.stop()

        self._wait_for(lambda: self.fetcher.is_closed and self.saver.is_closed)
        self._exec_stop_callbacks()

    def stop_all(self):
        def gen_ate():
            yield self._fetcher
            yield self._saver
            yield from self._spiders

        for ate in gen_ate():
            if not ate.is_stopped:
                ate.stop()

    def wait_all(self):
        self._wait_for(self.are_all_spiders_closed)
        self._wait_for(lambda: self.fetcher.is_closed and self.saver.is_closed)
        self._exec_stop_callbacks()

    @property
    def name(self) -> str:
        return self._name

    @property
    def logger(self) -> Logger:
        return self._logger

    @property
    def settings(self) -> FrozenDict:
        return self._settings

    @property
    def fetcher(self) -> Fetcher:
        return self._fetcher

    @property
    def saver(self) -> Saver:
        return self._saver

    @property
    def spiders(self) -> tuple:
        return tuple(self._spiders)


def _set_rt(ctrl):
    t0 = 0
    t1 = 0

    def st():
        nonlocal t0
        t0 = time.time()

    def ed():
        nonlocal t1
        t1 = time.time()
        ctrl.runtime_data['runtime'] = round(t1 - t0, 6)

    return st, ed
