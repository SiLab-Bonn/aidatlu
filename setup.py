from setuptools import setup
from setuptools import find_packages

import aidatlu

author = 'Christian Bespin'
author_email = 'bespin@physik.uni-bonn.de'

# Requirements
install_requires = ['online_monitor', 'pytest', 'numpy', 'tables', 'logger']

with open('VERSION') as version_file:
    version = version_file.read().strip()

setup(
    name='aidatlu',
    version=version,
    description='Control software for AIDA-2020 TLU',
    url='https://github.com/Silab-Bonn/aidatlu',
    license='',
    long_description='',
    author=author,
    maintainer=author,
    author_email=author_email,
    maintainer_email=author_email,
    install_requires=install_requires,
    python_requires=">=3.8",
    packages=find_packages(),
    include_package_data=True,
    platforms='posix',
)
