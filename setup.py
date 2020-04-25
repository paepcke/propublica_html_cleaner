import multiprocessing
from setuptools import setup, find_packages
import os
import glob

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name = "propublica_html_cleaner",
    version = "0.1",
    packages = find_packages(),

    # Dependencies on other packages:
    setup_requires   = [],
    install_requires = ['beautifulsoup4>=4.9.0',
                        ],

    #dependency_links = ['https://github.com/DmitryUlyanov/Multicore-TSNE/tarball/master#egg=package-1.0']
    # Unit tests; they are initiated via 'python setup.py test'
    test_suite       = 'nose.collector',
    #test_suite       = 'tests',
    tests_require    =['nose'],

    # metadata for upload to PyPI
    author = "Andreas Paepcke",
    author_email = "paepcke@cs.stanford.edu",
    description = "Removing html tags from Propublica online ad .csv export",
    long_description_content_type = "text/markdown",
    long_description = long_description,
    license = "BSD",
    keywords = "propublic",
    url = "https://github.com/paepcke/propublica_html_cleaner",   # project home page, if any
)
