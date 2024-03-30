from __future__ import annotations

from os import system
from pathlib import Path
import sys
import typing as t

from core import SSHSettings, settings, ssh_settings
from core.helpers import get_host_os
from core.paths import DATA_DIR, ENSURE_DIRS
from loguru import logger as log
from modules import ssh_mod
from packages import sftp_backup
from paramiko.channel import ChannelFile, ChannelStderrFile, ChannelStdinFile
from red_utils.ext.loguru_utils import init_logger, sinks
from red_utils.std import path_utils

from packages import cleanup
import pendulum


def run_backup(ssh_settings: t.Union[SSHSettings, dict] = None):
    assert ssh_settings, ValueError("Missing ssh_settings")
    assert isinstance(ssh_settings, SSHSettings) or isinstance(
        ssh_settings, dict
    ), TypeError(
        f"ssh_settings must be a dict or initialized SSHSettings object. Got type: ({type(ssh_settings)})"
    )
    if isinstance(ssh_settings, dict):
        try:
            ssh_settings: SSHSettings = SSHSettings.model_validate(ssh_settings)
        except Exception as exc:
            msg = Exception(
                f"Unhandled exception initializing SSHSettings object from input dict. Details: {exc}"
            )
            log.error(msg)

            raise exc

    try:
        _remote_dir = Path(f"{ssh_settings.remote_cwd}{ssh_settings.extra_path_suffix}")
        _local_backup_path = Path(
            f"{ssh_settings.local_dest}{ssh_settings.extra_path_suffix}"
        )
        log.debug(f"_remote_dir: {_remote_dir}")
        log.debug(f"_local_backup_path: {_local_backup_path}")

        log.info("Starting SFTP backup")
        try:
            sftp_backup.run_sftp_backup(
                ssh_settings=ssh_settings,
                remote_dir=f"{_remote_dir}".replace("\\", "/"),
                local_backup_path=f"{_local_backup_path}".replace("\\", "/"),
            )
            log.success(f"Transferred backups to '{_local_backup_path}'")
        except Exception as exc:
            msg = Exception(f"Unhandled exception running sftp backup. Details: {exc}")
            log.error(msg)

            raise
    except Exception as exc:
        msg = Exception(f"Unhandled exception running SFTP backup. Details: {exc}")
        log.error(msg)

        raise exc


def main(ssh_settings: SSHSettings = ssh_settings, cleanup_threshold: int = 10):
    try:
        run_backup(ssh_settings=ssh_settings)
    except Exception as exc:
        msg = Exception(f"Unhandled exception running backup. Details: {exc}")
        log.error(msg)

        raise exc

    try:
        cleanup.local.run_local_cleanup(threshold=cleanup_threshold)
    except Exception as exc:
        msg = Exception(f"Unhandled exception running local cleanup. Details: {exc}")
        log.error(msg)

        raise exc


if __name__ == "__main__":
    init_logger(sinks=[sinks.LoguruSinkStdErr(level=settings.log_level).as_dict()])

    path_utils.ensure_dirs_exist(ENSURE_DIRS)

    _os = get_host_os()
    log.debug(f"Detected host OS as: {_os}")

    log.info("App start")
    log.debug(f"App settings: {settings}")
    log.debug(f"SSH settings: {ssh_settings}")

    log.debug(
        f"Private key [exists:{ssh_settings.privkey_exists}]: {ssh_settings.privkey}"
    )
    log.debug(
        f"Public key [exists:{ssh_settings.pubkey_exists}]: {ssh_settings.pubkey}"
    )
    log.debug(
        f"Local destination [exists:{ssh_settings.local_dest_exists}]: {ssh_settings.local_dest}"
    )

    main(cleanup_threshold=ssh_settings.local_backup_limit)
