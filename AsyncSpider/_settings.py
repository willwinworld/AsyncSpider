from ._fetcher import Fetcher
from ._saver import Saver

__all__ = ['default_settings']

default_settings = {
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
