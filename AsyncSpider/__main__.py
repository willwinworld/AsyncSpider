import os

cwd = os.getcwd()


def create_py_file(path, name, text):
    path = os.path.join(path, name + '.py')
    with open(path, 'w', encoding='utf8') as f:
        f.write(text.strip())


fetcher_py = '''
from AsyncSpider import Fetcher, Request


class MyFetcher(Fetcher):
    async def process_request(self, request: Request):
        return request
'''

item_py = '''
from AsyncSpider import Item, Field


class MyItem(Item):
    content = Field()
'''

saver_py = '''
from AsyncSpider import Saver
from .item import MyItem

class MySaver(Saver):
    def open(self):
        pass

    def close(self):
        pass

    async def save(self, item: MyItem):
        pass
'''
spider_py = '''
from AsyncSpider import Spider, actionmethod


class MySpider(Spider):
    @actionmethod
    async def start_action(self):
        yield self.do_sth()

    @actionmethod
    async def do_sth(self):
        yield
'''
settings_py = '''
my_settings = {
    'Spider': {
        'max_current_actions': 10
    },
    'Fetcher': {
        'qps': 100,
        'max_qps': 200,
    },
    'Saver': {
        'run_until_complete': True
    }
}
'''
init_py = '''
from .fetcher import MyFetcher
from .saver import MySaver
from .spider import MySpider
from .settings import my_settings
'''

main_py = '''
from AsyncSpider import run
from MySpider import MyFetcher, MySaver, MySpider, my_settings

run(fetcher_class=MyFetcher,
    saver_class=MySaver,
    spider_class=MySpider,
    settings=my_settings)
'''

n_t = (('fetcher', fetcher_py),
       ('saver', saver_py),
       ('item', item_py),
       ('spider', spider_py),
       ('settings', settings_py),
       ('__init__', init_py),
       ('__main__', main_py))
package_path = os.path.join(cwd, 'MySpider')

if __name__ == '__main__':
    print('Create AsyncSpider Project: MySpider at {}'.format(package_path))
    os.mkdir(package_path)
    for n, t in n_t:
        create_py_file(package_path, n, t)
    print('To run this project,please execute "python -m MySpider"')
