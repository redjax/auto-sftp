from __future__ import annotations

from pathlib import Path
import typing as t

from core import SSHSettings, ssh_settings
from loguru import logger as log
from modules import ssh_mod

from .helpers import _str


def run_sftp_backup(
    ssh_settings: SSHSettings = None,
    remote_dir: str = None,
    local_backup_path: t.Union[str, Path] = None,
):
    assert ssh_settings, ValueError(
        "Missing SSHSettings object to configure SSH client."
    )
    assert isinstance(ssh_settings, SSHSettings), TypeError(
        f"ssh_settings must be of type SSHSettings. Got type: ({type(ssh_settings)})"
    )

    assert remote_dir, ValueError("Missing remote directory to scan")
    assert isinstance(remote_dir, str), TypeError(
        f"remote_dir should be a string. Got type: ({type(remote_dir)})"
    )

    assert local_backup_path, ValueError("Missing local backup destination path")
    assert isinstance(local_backup_path, str) or isinstance(
        local_backup_path, Path
    ), TypeError(
        f"local_backup_path should be a string or Path. Got type: ({type(local_backup_path)})"
    )
    if isinstance(local_backup_path, Path):
        if "~" in f"{local_backup_path}":
            local_backup_path: Path = local_backup_path.expanduser()
    if isinstance(local_backup_path, str):
        if "~" in local_backup_path:
            local_backup_path: Path = Path(local_backup_path).expanduser()
        else:
            local_backup_path: Path = Path(local_backup_path)

    y_m_str = _str.get_year_month_str()
    remote_dir: str = f"{remote_dir}/{y_m_str}"

    try:
        with ssh_mod.SSHManager(
            host=ssh_settings.remote_host,
            port=ssh_settings.remote_port,
            user=ssh_settings.remote_user,
            password=ssh_settings.remote_password,
            ssh_keyfile=ssh_settings.privkey,
            timeout=5000,
        ) as ssh_manager:

            try:
                files: list[str] = ssh_manager.sftp_list_files(remote_path=remote_dir)
                if not files:
                    log.warning(f"No files found in remote path '{remote_dir}'")
                    return
            except Exception as exc:
                msg = Exception(
                    f"Unhandled exception getting files from remote. Details: {exc}"
                )
                log.error(msg)

                raise exc

            try:
                ssh_manager.sftp_download_all(
                    remote_src=remote_dir,
                    local_dest=local_backup_path,
                )
                # log.success(
                #     f"Downloaded [{len(files)}] file(s) to path '{local_backup_path}'."
                # )

            except Exception as exc:
                msg = Exception(
                    f"Unhandled exception downloading [{len(files)}] file(s) from remote path '{remote_dir}'. Details: {exc}"
                )
                log.error(msg)

                raise exc

    except Exception as exc:
        msg = Exception(f"Unhandled exception getting SSHManager. Details: {exc}")
        log.error(msg)

        raise exc
