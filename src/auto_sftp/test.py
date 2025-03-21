from __future__ import annotations

from auto_sftp.main import run_backup

from core import settings, ssh_settings
from core.paths import ENSURE_DIRS
from packages import cleanup

from loguru import logger as log
from red_utils.ext.loguru_utils import init_logger, sinks

from packages import sort_local


def main(cleanup_threshold: int = 14):
    try:
        run_backup(ssh_settings=ssh_settings)
    except Exception as exc:
        msg = Exception(f"Unhandled exception running backup. Details: {exc}")
        log.error(msg)

        raise msg

    log.info("<< End Backup")

    log.info(">> Start Cleanup")
    try:
        cleanup.local.run_local_cleanup(threshold=cleanup_threshold)
    except Exception as exc:
        msg = Exception(f"Unhandled exception running local cleanup. Details: {exc}")
        log.error(msg)

        raise exc


if __name__ == "__main__":
    init_logger(
        sinks=[
            sinks.LoguruSinkStdErr(level=settings.log_level).as_dict(),
            sinks.LoguruSinkAppFile(sink=f"{settings.logs_dir}/app.log").as_dict(),
            sinks.LoguruSinkErrFile(sink=f"{settings.logs_dir}/error.log").as_dict(),
        ]
    )

    #     log.info(f">> Start Backup")
    #     log.info(
    #         f"""Remote Host Details:
    # Remote Host: {ssh_settings.remote_host}:{ssh_settings.remote_port}
    # Remote User: {ssh_settings.remote_user}
    # Remote CWD: {ssh_settings.remote_cwd}
    #     Extra Path Suffix: {ssh_settings.extra_path_suffix}
    # """
    #     )

    #     main(cleanup_threshold=ssh_settings.local_backup_limit)

    try:
        sort_local.sort_local_backups(local_backups_dir=ssh_settings.local_dest)
    except NotImplementedError as notimpl:
        msg = Exception(f"[NotImplemented] {notimpl}")
        log.warning(msg)
