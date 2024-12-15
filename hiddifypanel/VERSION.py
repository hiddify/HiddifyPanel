import importlib.metadata
from datetime import datetime

__version__ = importlib.metadata.version(__package__ or __name__)
__release_time__= datetime.strptime('2024-12-16T01:49:47','%Y-%m-%dT%H:%M:%S')
is_released_version = False