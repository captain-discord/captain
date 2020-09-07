import core.constants as constants
import logging

from sys import stdout

logger = logging.getLogger(constants.LOGGING_NAME)
logger.setLevel(constants.LOGGING_LEVEL)

formatter = constants.LOGGING_FORMATTER(
	fmt=constants.LOGGING_FORMAT,
	datefmt=constants.LOGGING_DATE_FORMAT
)

for file in constants.LOGGING_FILES:
	handler = logging.FileHandler(file)
	handler.setFormatter(formatter)

logger.addHandler(handler)

if constants.LOGGING_CONSOLE_HANDLER:
	console = logging.StreamHandler(stdout)
	console.setFormatter(formatter)

	logger.addHandler(console)