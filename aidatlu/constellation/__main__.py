#!/usr/bin/env python3
"""
SPDX-FileCopyrightText: 2024 DESY and the Constellation authors
SPDX-License-Identifier: CC-BY-4.0

This is the entry point for the example satellite.
"""


from constellation.core.logging import setup_cli_logging
from constellation.core.satellite import SatelliteArgumentParser

from .aidatlu_satellite import AidaTLU


def main(args=None):
    """Satellite controlling a Satellite for the AIDA-2020 TLU"""

    parser = SatelliteArgumentParser(description=main.__doc__)
    args = vars(parser.parse_args(args))

    # set up logging
    setup_cli_logging(args.pop("log_level"))

    # start server with remaining args
    s = AidaTLU(**args)
    s.run_satellite()


main()
