"""Module to scrape prices off various websites."""

import os

from .siteconfig import SiteConfigRepo
from .grabber import Grabber
from .exceptions import ConfigException, NetworkException
from .testrunner import TestRunner

_ROOT = os.path.abspath(os.path.dirname(__file__))
_SITE_CONFIG_DIR = os.path.join(_ROOT, 'data')

SiteConfigRepo(data_dir=_SITE_CONFIG_DIR)
