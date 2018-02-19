from ._base import Storage

__all__ = ['Settings', 'default_settings']


class Settings(Storage):
    __slots__ = ('basic', 'spider', 'fetcher', 'saver')

    def __init__(self, basic: dict, spider: dict, fetcher: dict, saver: dict):
        super().__init__()
        self.update(basic=basic, spider=spider, fetcher=fetcher, saver=saver)

    @classmethod
    def from_dict(cls, d):
        return cls(**d)


default_settings = Settings.from_dict({
    'basic': {

    },
    'spider': {
        'max_current_actions': 10
    },
    'fetcher': {
        'qps': 100,
        'max_qps': 200,
    },
    'saver': {
        'run_until_complete': True
    }
})
