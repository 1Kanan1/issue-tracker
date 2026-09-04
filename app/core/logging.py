import logging
import sys

from uvicorn.logging import DefaultFormatter


def setup_logging():
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        DefaultFormatter(
            fmt="%(levelprefix)s %(name)s - %(message)s",
            use_colors=True,
        )
    )

    logger = logging.getLogger("app")
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
