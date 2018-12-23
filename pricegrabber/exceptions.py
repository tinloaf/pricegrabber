class NetworkException(Exception):
    def __init__(self, message):
        super().__init__(message)


class ConfigException(Exception):
    def __init__(self, message):
        super().__init__(message)
