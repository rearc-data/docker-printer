import logging
import sys
from logging.config import dictConfig

log = logging.getLogger(__name__)


def main():
    dictConfig(
        dict(
            version=1,
            formatters=dict(
                brief=dict(
                    format=logging.BASIC_FORMAT,
                ),
                bare=dict(
                    format="%(message)s",
                ),
            ),
            handlers=dict(
                console={
                    "class": "logging.StreamHandler",
                    "formatter": "brief",
                    "level": logging.DEBUG,
                    "stream": sys.stdout,
                },
                console_bare={
                    "class": "logging.StreamHandler",
                    "formatter": "bare",
                    "level": logging.DEBUG,
                    "stream": sys.stderr,
                },
            ),
            loggers=dict(
                rearc_cli=dict(
                    level=logging.DEBUG,
                    propagate=False,
                    handlers=["console_bare"],
                ),
                rearc_data_utils=dict(
                    level=logging.DEBUG,
                    propagate=True,
                ),
                jobs=dict(
                    level=logging.DEBUG,
                    propagate=True,
                ),
                common=dict(
                    level=logging.DEBUG,
                    propagate=True,
                ),
                __main__=dict(
                    level=logging.DEBUG,
                    propagate=True,
                ),
            ),
            root=dict(handlers=["console"]),
        )
    )

    from docker_printer.cli import app

    app()


if __name__ == "__main__":
    main()
