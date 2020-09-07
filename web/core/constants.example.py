import core.enumerators as enums
import logging

PORT: int = 6920 # Doesn't need an explanation
SECRET_KEY: str = b"youshallnotpass" # any random bytes string that represents the Flask secret key

# These options specify an external .py, .json, .yml or .toml file used for extra configuration.
# Anything specified there is only for use within plugins, core functionality settings belong here.
CONFIG_PATH:	str  = "config.yml" # A relative path to the config path (use an import path if it's a .py file)
CONFIG_FORMAT:  int  = enums.ConfigFormatterEnum.YAML # Use enumerators.py for reference.
CONFIG_ENABLED: bool = True # Setting to False means no external file is loaded.

# Changing this will adjust the functionality of the built-in logging.
# This MUST be a system compatible with the builtin logging library (use a custom instance if you want to use your own).
LOGGING_LEVEL:		     int			   = enums.LoggingLevelEnum.INFO # The logging level that determines what logs are shown.
LOGGING_FORMAT:		     str			   = "%(asctime)s.%(msecs)03d %(levelname)-8.8s  [%(name)s]: %(message)s" # The format of sent messages
LOGGING_DATE_FORMAT:	 str			   = "%d-%m-%Y %H:%M:%S" # A string denoting the format of the printed timestamp.
LOGGING_FORMATTER:	     logging.Formatter = logging.Formatter # If you want to use a custom logging.Formatter implementation, specify a reference to the class here.
LOGGING_NAME:			 str			   = "captain:web" # This is the name of the core's logger, this is mostly just a vanity thing.
LOGGING_FILES:		     list			   = ["web.log"] # A list of relative paths to files where logs are saved.
LOGGING_CONSOLE_HANDLER: bool			   = True # Whether an extra handler should be added to print to stdout, most people will want this set to True.