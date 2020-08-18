class ConfigFormatterEnum:
	NULL   = -1
	JSON   = 0
	YAML   = 1
	TOML   = 2
	NATIVE = 3


class LoggingLevelEnum:
	UNKNOWN  = 0
	DEFAULT  = 0
	NOTSET   = 0

	DEBUG	= 10
	VERBOSE  = 10

	INFO	 = 20
	NORMAL   = 20

	WARN	 = 30
	WARNING  = 30

	ERROR	= 40
	FAULT	= 40

	CRITICAL = 50
	FATAL	= 50