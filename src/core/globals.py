# TODO: This module will be deprecated.
#   It is rather crude and does not take advantage of Python's own logging module.
import enum
from functools import reduce
from operator import add

class LogLevel(enum.Enum):
    """!The severity of a logged message.
        The log level used by error loggers. A system-wide log level controls what messages are logged.
    """
    NON = 0
    ERR = 11
    WRN = 10
    INF = 12
    DBG = 13
    TRC = 14

    def __lt__(self, other):
        # A higher value means more detailed logs
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented

    def __eq__(self, other):
        # A higher value means more detailed logs
        if self.__class__ is other.__class__:
            return self.value == other.value
        return NotImplemented
    
    def __le__(self, other):
        # A higher value means more detailed logs
        if self.__class__ is other.__class__:
            return self.value >= other.value
        return NotImplemented

# All messages at or below this log level are reported.
LOG_LEVEL = LogLevel.DBG

def report(level: LogLevel, *str):
    """!Log a message
        Report the log message if the specified log level is below the global log level. Otherwise, do nothing.
    """
    COL = ""
    COL_DEFAULT = "\033[0m"
    global LOG_LEVEL
    # TODO Problems here need to be addressed.
    #   No need for an adapter, if the Python logger is flexible enough.
    #   Consider
    match level:
        case LogLevel.ERR:
            COL = "\033[31mERR: "
        case LogLevel.WRN:
            COL = "\033[33mWRN: "
        case LogLevel.INF: # Teh normal log level
            COL = "\033[34mINF: "
        case LogLevel.DBG:
            COL = "\033[36mDBG: "
        case LogLevel.TRC:
            COL = "\033[0mTRC: "
        # Comment out the TRC level. The reporting mechanism is being migrated
        #   to the Python logger. If I do not comment this line out, then
        #   output gets overwhelmed by trivial logs.
        # case LogLevel.TRC:
        #     COL = "\033[0mTRC: "
        case _:
            COL = "\033[0m[cannot interpret log level:] "
    if (level >= LogLevel.DBG):
        print(f"{COL}{reduce(add, str, "")}")