from setuptools import find_packages, setup

author = "Christian Bespin, Rasmus Partzsch"
author_email = "bespin@physik.uni-bonn.de, rasmus.partzsch@uni-bonn.de"

# Requirements
install_requires = [
    "pytest",
    "numpy",
    "tables",
    "coloredlogs",
    "pyzmq",
    "online_monitor",
    "tqdm",
]

with open("VERSION") as version_file:
    version = version_file.read().strip()

setup(
    name="aidatlu",
    version=version,
    description="Control software for AIDA-2020 TLU",
    url="https://github.com/Silab-Bonn/aidatlu",
    license="License AGPL-3.0 license",
    long_description="Repository for controlling the AIDA-2020 Trigger Logic Unit (TLU) with Python using uHAL bindings from IPbus.",
    author=author,
    maintainer=author,
    author_email=author_email,
    maintainer_email=author_email,
    install_requires=install_requires,
    python_requires=">=3.8",
    packages=find_packages(),
    include_package_data=True,
    platforms="posix",
)
