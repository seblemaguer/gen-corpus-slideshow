#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUTHOR

    Sébastien Le Maguer <lemagues@tcd.ie>

DESCRIPTION

LICENSE
    This script is in the public domain, free from copyrights or restrictions.
    Created: 25 November 2021
"""
#
from pathlib import Path
import subprocess
import shutil

# Arguments
import argparse

# Messaging/logging
import logging
from logging.config import dictConfig

###############################################################################
# global constants
###############################################################################
LEVEL = [logging.WARNING, logging.INFO, logging.DEBUG]
TMP_DIR = Path("tmp/")
SNIPPET_UTT = "\\begin{frame}\\frametitle{%s}\n\t%s\n\\end{frame}\n"

###############################################################################
# Functions
###############################################################################
def configure_logger(args) -> logging.Logger:
    """Setup the global logging configurations and instanciate a specific logger for the current script

    Parameters
    ----------
    args : dict
        The arguments given to the script

    Returns
    --------
    the logger: logger.Logger
    """
    # create logger and formatter
    logger = logging.getLogger()

    # Verbose level => logging level
    log_level = args.verbosity
    if args.verbosity >= len(LEVEL):
        log_level = len(LEVEL) - 1
        # logging.warning("verbosity level is too high, I'm gonna assume you're taking the highest (%d)" % log_level)

    # Define the default logger configuration
    logging_config = dict(
        version=1,
        disable_existing_logger=True,
        formatters={
            "f": {
                "format": "[%(asctime)s] [%(levelname)s] — [%(name)s — %(funcName)s:%(lineno)d] %(message)s",
                "datefmt": "%d/%b/%Y: %H:%M:%S ",
            }
        },
        handlers={
            "h": {
                "class": "logging.StreamHandler",
                "formatter": "f",
                "level": LEVEL[log_level],
            }
        },
        root={"handlers": ["h"], "level": LEVEL[log_level]},
    )

    # Add file handler if file logging required
    if args.log_file is not None:
        logging_config["handlers"]["f"] = {
            "class": "logging.FileHandler",
            "formatter": "f",
            "level": LEVEL[log_level],
            "filename": args.log_file,
        }
        logging_config["root"]["handlers"] = ["h", "f"]

    # Setup logging configuration
    dictConfig(logging_config)

    # Retrieve and return the logger dedicated to the script
    logger = logging.getLogger(__name__)
    return logger


def define_argument_parser() -> argparse.ArgumentParser:
    """Defines the argument parser

    Returns
    --------
    The argument parser: argparse.ArgumentParser
    """
    parser = argparse.ArgumentParser(description="")

    # Add options
    parser.add_argument("-l", "--log_file", default=None, help="Logger file")
    parser.add_argument(
        "-v",
        "--verbosity",
        action="count",
        default=0,
        help="increase output verbosity",
    )
    parser.add_argument("-t", "--template", default="assets/default.tex", help="The template file")

    # Add arguments
    parser.add_argument("text_dir", help="The directory containing the text files, the basename of the file is used as the ID of the utterance")
    parser.add_argument("output_file")

    # Return parser
    return parser


###############################################################################
#  Envelopping
###############################################################################
if __name__ == "__main__":
    # Initialization
    arg_parser = define_argument_parser()
    args = arg_parser.parse_args()
    logger = configure_logger(args)

    # Load text file
    text_dir = Path(args.text_dir)
    dict_text = dict()
    for cur_file in text_dir.iterdir():
        if cur_file.suffix in set([".txt", ".TXT", ".text", ".TEXT"]):
            with open(cur_file) as f_text:
                dict_text[cur_file.stem] = f_text.read().strip()

    # Generate snippets
    content = [SNIPPET_UTT % (k, dict_text[k]) for k in dict_text]

    # Generate latex
    with open(args.template) as f_template:
        template = f_template.read()
        content = template % ("\n".join(content))

    # Generate temp file
    output_file = Path(args.output_file)
    TMP_DIR.mkdir(exist_ok=True, parents=True)
    with open(Path(TMP_DIR, output_file.stem + ".tex"), "w") as f_tmp_file:
        f_tmp_file.write(content)

    # Compile file (twice for references if there are some...)
    p = subprocess.Popen(["pdflatex", output_file.stem + ".tex"], cwd=TMP_DIR)
    p.wait()
    p = subprocess.Popen(["pdflatex", output_file.stem + ".tex"], cwd=TMP_DIR)
    p.wait()

    # Get the output file and remove temp directory
    shutil.move(Path(TMP_DIR, output_file.name), output_file)
    shutil.rmtree(TMP_DIR)
