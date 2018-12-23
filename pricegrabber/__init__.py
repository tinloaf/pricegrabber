from .siteconfig import SiteConfigRepo
from .grabber import Grabber
from .exceptions import ConfigException, NetworkException
from .testrunner import TestRunner

import os

_ROOT = os.path.abspath(os.path.dirname(__file__))
_SITE_CONFIG_DIR = os.path.join(_ROOT, 'data')

SiteConfigRepo(data_dir=_SITE_CONFIG_DIR)
