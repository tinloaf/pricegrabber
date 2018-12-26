"""Exceptions thrown from pricegrabber."""


class NetworkException(Exception):
    """A network error has happened."""

    def __init__(self, message):
        super().__init__(message)


class ConfigException(Exception):
    """Something is wrong with the (site) configuration."""

    def __init__(self, message):
        super().__init__(message)
