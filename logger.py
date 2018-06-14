TRACE = 'trace'
DEBUG = 'debug'
INFO = 'info'
WARN = 'warn'
ERROR = 'error'
FATAL = 'fatal'

LEVELS = {TRACE: 0,
          DEBUG: 1,
          INFO: 2,
          WARN: 3,
          ERROR: 4,
          FATAL: 5}

LEVEL = DEBUG


def log(msg, level):
    if LEVELS[level] >= LEVELS[LEVEL]:
        print(msg)


def debug(msg):
    log(msg, DEBUG)


def trace(msg):
    log(msg, TRACE)


def info(msg):
    log(msg, INFO)


def warn(msg):
    log(msg, WARN)


def error(msg):
    log(msg, ERROR)


def fatal(msg):
    log(msg, FATAL)
