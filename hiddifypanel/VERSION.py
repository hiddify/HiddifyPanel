import importlib.metadata
from datetime import datetime

__version__ = importlib.metadata.version(__package__ or __name__)
__release_time__= datetime.strptime('2024-12-15T01:28:01','%Y-%m-%dT%H:%M:%S')
is_released_version = False