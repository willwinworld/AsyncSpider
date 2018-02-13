from ._fetcher import Fetcher
from ._saver import Saver

default_settings = {
    'Spider': {
        'max_current_actions': 10
    },
    'Fetcher': {
        'class': Fetcher,
        'qps': 100,
        'max_qps': 200,
    },
    'Saver': {
        'class': Saver,
        'run_until_complete': True
    }
}
