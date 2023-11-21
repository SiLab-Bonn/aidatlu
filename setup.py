from setuptools import setup
from setuptools import find_packages

import aidatlu

author = 'Christian Bespin'
author_email = 'bespin@physik.uni-bonn.de'

# Requirements
install_requires = ['']


setup(
    name='aidatlu',
    version='0.1.0',
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
