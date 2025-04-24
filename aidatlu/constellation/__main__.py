#!/usr/bin/env python3
from constellation.core.logging import setup_cli_logging
from constellation.core.satellite import SatelliteArgumentParser

from .aidatlu_satellite import AidaTLU


def main(args=None):
    """Controlling of a Satellite for the AIDA-2020 TLU"""

    parser = SatelliteArgumentParser(description=main.__doc__)
    args = vars(parser.parse_args(args))

    # set up logging
    setup_cli_logging(args.pop("log_level"))

    # start server with remaining args
    s = AidaTLU(**args)
    s.run_satellite()


main()
