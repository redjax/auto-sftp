from __future__ import annotations

from auto_sftp.main import run_backup

from core import settings, ssh_settings
from core.paths import ENSURE_DIRS
from loguru import logger as log
from red_utils.ext.loguru_utils import init_logger, sinks

if __name__ == "__main__":
    init_logger(sinks=[sinks.LoguruSinkStdErr(level=settings.log_level).as_dict()])

    log.info(
        f""">> Start Backup
Remote Host: {ssh_settings.remote_host}:{ssh_settings.remote_port}
Remote User: {ssh_settings.remote_user}
Remote CWD: {ssh_settings.remote_cwd}
    Extra Path Suffix: {ssh_settings.extra_path_suffix}
"""
    )

    try:
        run_backup(ssh_settings=ssh_settings)
    except Exception as exc:
        msg = Exception(f"Unhandled exception running backup. Details: {exc}")
        log.error(msg)

        raise msg

    log.info("<< End Backup")
