#!/usr/bin/env python3
from constellation.core.logging import setup_cli_logging
from constellation.core.datasender import DataSenderArgumentParser
from constellation.core.satellite import SatelliteArgumentParser

from aidatlu_satellite import AidaTLU


def main(args=None):
    """Controlling of a Satellite for the AIDA-2020 TLU"""

    parser = SatelliteArgumentParser()
    args = vars(parser.parse_args(args))

    # set up logging
    setup_cli_logging(args.pop("level"))

    # start satellite with remaining args
    s = AidaTLU(**args)
    s.run_satellite()


if __name__ == "__main__":
    main()
