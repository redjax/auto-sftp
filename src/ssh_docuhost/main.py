from __future__ import annotations

from pathlib import Path
import sys
from os import system
import typing as t

from paramiko.channel import ChannelFile, ChannelStderrFile, ChannelStdinFile

from core.helpers import get_host_os
from core.config import settings, ssh_settings
from core.paths import DATA_DIR, ENSURE_DIRS
from modules import ssh_mod

from loguru import logger as log
from red_utils.ext.loguru_utils import init_logger, sinks
from red_utils.std import path_utils

import paramiko


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

    with ssh_mod.SSHManager(
        host=ssh_settings.remote_host,
        port=ssh_settings.remote_port,
        user=ssh_settings.remote_user,
        password=ssh_settings.remote_password,
        ssh_keyfile=ssh_settings.privkey,
        timeout=5000,
    ) as ssh_manager:
        try:
            sftp: paramiko.SFTPClient = ssh_manager.get_sftp_client()
        except Exception as exc:
            msg = Exception(f"Unhandled exception getting SSH client. Details: {exc}")
            log.error(msg)

            raise exc

        files: list[str] = ssh_manager.sftp_list_files(
            remote_path=f"{ssh_settings.remote_cwd}/docker/paperless-ngx"
        )
        log.debug(f"Files ({len(files)}): {files}")

        ssh_manager.sftp_download_all(
            remote_src=f"{ssh_settings.remote_cwd}/docker/paperless-ngx",
            local_dest=ssh_settings.local_dest,
        )

        # ssh_mod.sftp_download_all(
        #     sftp_client=sftp,
        #     remote_src=f"{ssh_settings.remote_cwd}/docker/paperless-ngx",
        #     local_dest=ssh_settings.local_dest,
        # )
