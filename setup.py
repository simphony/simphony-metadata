import os

from setuptools import setup, find_packages

MAJOR = 0
MINOR = 1
MICRO = 0

IS_RELEASED = False

VERSION = '%d.%d.%d' % (MAJOR, MINOR, MICRO)

if not IS_RELEASED:
    VERSION += '.dev0'


def write_version_py(filename=None):
    if filename is None:
        filename = os.path.join(
            os.path.dirname(__file__), 'simphony_metadata', 'version.py')
    ver = """\
version = '%s'
"""
    fh = open(filename, 'wb')
    try:
        fh.write(ver % VERSION)
    finally:
        fh.close()

write_version_py()

# main setup configuration class
setup(
    name='simphony_metadata',
    version=VERSION,
    author='SimPhoNy, EU FP7 Project (Nr. 604005) www.simphony-project.eu',
    description='SimPhoNy Metadata',
    install_requires=["click >= 3.3", "pyyaml >= 3.11", "numpy>=1.4.1"],
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            ('simphony-meta-generate = '
             'simphony_metadata.scripts.generate:cli')]},
    )
