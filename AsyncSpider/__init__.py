from .fetsav import Fetcher, Saver
from .item import Item, Field
from .log import logger
from .processor import RequestProcessor, ItemProcessor
from .reqrep import Request, Response
from .spider import Spider

__author__ = 'Nugine'
__version__ = '0.5.0'


def start(components):
    components = set(components)
    for c in components:
        c.start()


def stop(components):
    components = set(components)
    for c in components:
        c.stop()


def wait(components):
    import time
    components = set(components)
    while True:
        for c in components:
            if not c.is_stopped():
                break
        else:
            break
        time.sleep(0.5)


def run_all(*spiders):
    start(spd.fetcher for spd in spiders)
    start(spd.saver for spd in spiders)
    start(spiders)
    wait(spiders)
    stop(spd.fetcher for spd in spiders)
    stop(spd.saver for spd in spiders)
    wait(spd.fetcher for spd in spiders)
    wait(spd.saver for spd in spiders)
