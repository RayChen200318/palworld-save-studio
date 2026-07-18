from palworld_save_studio.config import APP_DATA_PATH
from palworld_save_studio.utils.logger import Logger, ColorConsoleFormatter

LOGGER = Logger(log_directory=APP_DATA_PATH / "logs")

from palworld_save_studio.utils.util import *
from palworld_save_studio.utils.data_provider import DataProvider
