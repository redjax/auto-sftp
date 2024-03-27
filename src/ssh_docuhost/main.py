from __future__ import annotations

from pathlib import Path
import sys
import typing as t

from core.config import settings, ssh_settings
from core.paths import DATA_DIR, ENSURE_DIRS
from loguru import logger as log
from red_utils.ext.loguru_utils import init_logger, sinks
from red_utils.std import path_utils

if __name__ == "__main__":
    init_logger(sinks=[sinks.LoguruSinkStdErr(level=settings.log_level).as_dict()])

    path_utils.ensure_dirs_exist(ENSURE_DIRS)

    log.info("App start")
    log.debug(f"App settings: {settings}")
    log.debug(f"SSH settings: {ssh_settings}")

    log.debug(
        f"Private key [exists:{ssh_settings.privkey_exists}]: {ssh_settings.privkey}"
    )
    log.debug(
        f"Public key [exists:{ssh_settings.pubkey_exists}]: {ssh_settings.pubkey}"
    )
