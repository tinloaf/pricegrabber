#!/usr/bin/env python

from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(name='pricegrabber',
      version='0.0.1',
      description='Package to scrape prices from various websites',
      author='Lukas Barth',
      author_email='mail@tinloaf.de',
      long_description=long_description,
      long_description_content_type="text/markdown",
      license='MIT',
      url='https://github.com/tinloaf/pricegrabber',
      packages=find_packages(),
      classifiers=[
          "Programming Language :: Python :: 3",
          "License :: OSI Approved :: MIT License",
          "Operating System :: OS Independent",
          'Development Status :: 3 - Alpha',
          'Intended Audience :: Developers',
          'Topic :: Internet :: WWW/HTTP',
          'Topic :: Software Development :: Libraries'
      ],
      install_requires=[
          'requests>=2.21.0',
          'lxml>=4.2.5'
      ],
      keywords='library prices scraping',

      )
