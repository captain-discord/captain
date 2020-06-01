# =====================
# Import PATH libraries
# =====================
# -----------------
# Builtin libraries
# -----------------
import datetime, inspect, sys, typing, os

class blueprint:
    """This class serves as a structure for all other blueprints, containing information ideal for debugging.
    
    However, this class is entirely open for others to use, all they have to do is inherit from it and they're good to go!
    
    [Note]: Don't bother trying to create and instance of this class, you won't find anything special."""

    def __repr__(self) -> str:
        """Instead of defining a repr for every single blueprint, it's easier to do it automagically from the 
           blueprint...well...blueprint!"""

        return f"<{self.class_name} {' '.join(f'{property_name}:{property.__class__.__name__}={property}' for property_name, property in self.class_properties().items())}>"

    def __iter__(self) -> iter:
        """This overload simply takes the class_properties and yields from it."""

        yield from self.class_properties().items()

    @property
    def class_name(self) -> str:
        """Returns the deriving class' name."""

        return self.__class__.__name__

    def class_properties(self) -> dict:
        """Returns the property names of the deriving class.
        
        This has to be a function, otherwise we'd end up with recursion errors."""

        attributes = []

        for property in inspect.getmembers(object=self,
                                           predicate=lambda prop: not inspect.isroutine(object=prop)):
            if not property[0].startswith("_"):
                attributes.append((property[0], str(property[1]) if not isinstance(property[1], 
                                                                                   (str, int, float, dict, tuple, list, set)) \
                                                                 else property[1]))

        return {name: value for name, value in attributes}

class log(blueprint):
    """An instance of this class represents a single log made using Custos."""

    __slots__ = ("project", "format_string", "log_level", "log_id", "timestamp", "origin", "content")

    def __init__(self,
                 **log_info: dict):
        self.project: str = log_info.pop("project", "custos")

        self.log_level: str = log_info.pop("log_level")
        self.log_id: int = log_info.pop("log_id")

        self.timestamp: datetime.datetime = log_info.pop("timestamp")
        self.format: str = log_info.pop("format_string")

        self.origin: str = log_info.pop("origin")
        self.content: str = log_info.pop("content")

    def __str__(self) -> str:
        """Returns the uncoloured text format for the log."""

        return self.format.format(id=self.log_id,
                                  level=self.log_level,
                                  project=self.project,
                                  ts=self.timestamp,
                                  origin=self.origin,
                                  content=self.content)

    def __int__(self) -> int:
        """Returns the ID of the log if it was provided.
        
        If a log_id wasn't provided, then None is returned."""

        return self.log_id

    def __iter__(self) -> iter:
        """Returns an iterable whenever this object is looped through."""

        yield from dict(log_level=self.log_level,
                        timestamp=self.timestamp,
                        origin=self.origin,
                        content=self.content)

class timestamp(blueprint):
    """This class represents the datetime values used in log formats.
    
    This is effectively the same as using .strftime, except it's shorter but doesn't contain all possible datetime values."""

    __slots__ = "object"

    def __init__(self,
                 object: datetime.datetime):
        self.ts = object

    @property
    def year(self) -> str:
        """Returns the year."""

        return self.ts.strftime(format="%Y")

    @property
    def month(self) -> str:
        """Returns the zero padded month of the year."""

        return self.ts.strftime(format="%m")

    @property
    def day(self) -> str:
        """Returns the zero padded day of the month."""

        return self.ts.strftime(format="%d")

    @property
    def hour(self) -> str:
        """Returns the zero padded hour of the day."""

        return self.ts.strftime(format="%H")

    @property
    def hour_12(self) -> str:
        """Returns the zero padded 12 hour clock hour of the day."""

        return self.ts.strftime(format="%I")

    @property
    def minute(self) -> str:
        """Returns the zero padded minute of the hour."""

        return self.ts.strftime(format="%M")

    @property
    def second(self) -> int:
        """Returns the zero padded second of the minute."""

        return self.ts.strftime(format="%S")

    @property
    def microsecond(self) -> int:
        """Returns the decimal microsecond of the second."""

        return str(round(number=int(self.ts.strftime(format="%f")) / 1000)).rjust(3, '0')

    @property
    def am_pm(self) -> str:
        """Returns AM or PM depending on the time of day."""

        return self.ts.strftime(format="%p")

class version(blueprint):
    """This class is used to represent the version information of the package.
    
    This is nothing special, but if this module is used in larger packages, knowing the version of Custos may prove useful."""

    __slots__ = ("major", "minor", "patch", "release")

    def __init__(self,
                 **versions):
        self.major: int = versions.pop("major", 1)
        self.minor: int = versions.pop("minor", 0)
        self.patch: int = versions.pop("patch", 0)
        self.release: str = versions.pop("release", "stable")

        self.hash = f"{self.major}.{self.minor}.{self.patch}-{self.release}"

    @classmethod
    def from_str(cls,
                 fmt: str) -> blueprint:
        """Constructs a version class from a given string.
        
        This string must use the following format:
            major.minor.patch.release
            
        If the format is invalid, None is returned, and a console log is made just in case."""

        fmt.split(".")

        try:
            major, minor, patch = map(int, fmt[:3])
        
        except ValueError:
            return None

        return cls(major=major,
                   minor=minor,
                   patch=patch,
                   release=fmt[-1])

    def __str__(self) -> str:
        """Returns the version hash in the format 'v<major>.<minor>.<patch>'."""

        return "v{0.major}.{0.minor}.{0.patch}".format(self)

    def __int__(self) -> int:
        """Returns the version as a number in the format '<major><minor><patch>'."""

        return int("{0.major}{0.minor}{0.patch}".format(self))

    def __iter__(self) -> dict:
        """Returns a dictionary form of the version configuration when iterated through."""

        yield from dict(major=self.major,
                        minor=self.minor,
                        patch=self.patch,
                        release=self.release,
                        hash=self.hash,
                        number=str(self)).items()