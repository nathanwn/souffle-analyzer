import logging
import logging.config
import os
from typing import Dict

from souffle_analyzer.metadata import PROG


def configure_logging(log_file: str, verbose: bool) -> None:
    log_dir = os.path.dirname(log_file)
    if log_dir == "":
        log_dir = "."
    os.makedirs(log_dir, exist_ok=True)
    logging.config.dictConfig(gen_logging_config(log_file, verbose))


def gen_logging_config(log_file_path: str, verbose: bool) -> Dict:
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": f"[{PROG} %(levelname)s] %(message)s",
            },
            "detailed": {
                "format": (
                    "[%(levelname)s|%(module)s|L%(lineno)d] %(asctime)s: %(message)s"
                ),
                # use "%Y-%m-%dT%H:%M:%S%z" for more standard use cases
                "datefmt": "%H:%M:%S",
            },
        },
        "handlers": {
            "stderr": {
                "class": "logging.StreamHandler",
                "level": "WARNING",
                "formatter": "standard",
                "stream": "ext://sys.stderr",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG" if verbose else "INFO",
                "formatter": "detailed",
                "filename": log_file_path,
                "maxBytes": 1024 * 1024,
                "backupCount": 3,
            },
        },
        "loggers": {
            "": {  # Root logger
                "level": "DEBUG",
                "handlers": [
                    "stderr",
                    "file",
                ],
            },
        },
    }


logger = logging.getLogger(name=PROG)
