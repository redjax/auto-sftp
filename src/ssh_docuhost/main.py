from __future__ import annotations

from pathlib import Path
import sys
from os import system
import typing as t

from paramiko.channel import ChannelFile, ChannelStderrFile, ChannelStdinFile

from core.config import settings, ssh_settings
from core.paths import DATA_DIR, ENSURE_DIRS
from modules import ssh_mod

from loguru import logger as log
from red_utils.ext.loguru_utils import init_logger, sinks
from red_utils.std import path_utils

import paramiko


def get_host_os() -> str:
    VALID_PLATFORMS: list[str] = ["linux", "win32", "darwin"]
    return_map: dict[str, str] = {"linux": "linux", "win32": "windows", "darwin": "mac"}

    _platform = sys.platform

    assert _platform in VALID_PLATFORMS, ValueError(
        f"Unknown platform: {_platform}. Expected one of {VALID_PLATFORMS}"
    )

    return_val = return_map[_platform]
    assert return_val, ValueError("return_val should not be None")


#     return return_val


# def upload_ssh_key(
#     privkey_path: t.Union[str, Path] = None,
#     remote_user: str = None,
#     remote_host: str = None,
# ):
#     assert privkey_path, ValueError("Missing SSH private keyfile path")
#     assert isinstance(privkey_path, str) or isinstance(privkey_path, Path), TypeError(
#         f"privkey_path must be a string or Path object. Got type: ({type(privkey_path)})"
#     )

#     assert remote_user, ValueError("Missing remote_user")
#     assert isinstance(remote_user, str), TypeError(
#         f"remote_user must be a string. Got type: ({type(remote_user)})"
#     )

#     assert remote_host, ValueError("Missing remote_host")
#     assert isinstance(remote_host, str), TypeError(
#         f"remote_host must be a string. Got type: ({type(remote_host)})"
#     )

#     publickey_path: Path = Path(f"{privkey_path}.pub")
#     assert Path(f"{publickey_path}").exists(), FileNotFoundError(
#         f"Could not find public keyfile at path '{publickey_path}"
#     )

#     try:
#         if _os == "windows":
#             _cmd = f"ssh-copy-id -i {privkey_path}.pub {remote_user}@{remote_host}"

#             log.warning(
#                 NotImplementedError(f"Uploading SSH key from Windows not supported")
#             )
#         else:
#             _cmd = f"ssh-copy-id -i {privkey_path}.pub {remote_user}@{remote_host}>/dev/null 2>&1"
#             system(_cmd)
#     except FileNotFoundError as fnf:
#         msg = Exception(f"Could not find public keyfile at path '{privkey_path}.pub'")
#         log.error(msg)

#         raise fnf
#     except Exception as exc:
#         msg = Exception(
#             f"Unhandled exception uploading SSH public keyfile from path '{privkey_path}.pub' to {remote_user}@{remote_host}. Details: {exc}"
#         )
#         log.error(msg)

#         raise msg


if __name__ == "__main__":
    init_logger(sinks=[sinks.LoguruSinkStdErr(level=settings.log_level).as_dict()])

    path_utils.ensure_dirs_exist(ENSURE_DIRS)

    _os = ssh_mod.get_host_os()
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

    ## Using ssh_client
    # with ssh_mod.get_ssh_client(ssh_settings=ssh_settings) as ssh_client:
    #     try:
    #         ssh_mod.sftp_download_all(
    #             ssh_client=ssh_client,
    #             remote_src=f"{ssh_settings.remote_cwd}/docker/paperless-ngx",
    #             local_dest=ssh_settings.local_dest,
    #         )
    #     except Exception as exc:
    #         msg = Exception(f"Unhandled exception downloading files. Details: {exc}")
    #         log.error(msg)

    #         raise exc

    # with ssh_mod.get_sftp_client(ssh_settings=ssh_settings) as sftp:
    # try:
    #     sftp.remove("/home/jack/example_from_colossus")
    #     log.success(
    #         f"Removed file/home/jack/example_from_colossus from remote {ssh_settings.remote_host}"
    #     )
    # except FileNotFoundError as fnf:
    #     msg = Exception(
    #         f"Could not find file /home/jack/example_from_colossus on remote {ssh_settings.remote_host}"
    #     )
    #     log.warning(f"{msg}")

    # except Exception as exc:
    #     msg = Exception(
    #         f"Unhandled exception removing file /home/jack/example_from_colossus from remote {ssh_settings.remote_host}. Details: {exc}"
    #     )
    #     log.error(msg)

    #     raise exc

    ## With sftp_client
    # with ssh_mod.get_sftp_client(ssh_settings=ssh_settings) as sftp:

    #     try:
    #         ssh_mod.sftp_download_all(
    #             sftp_client=sftp,
    #             remote_src=f"{ssh_settings.remote_cwd}/docker/paperless-ngx",
    #             local_dest=ssh_settings.local_dest,
    #         )
    #     except Exception as exc:
    #         msg = Exception(f"Unhandled exception downloading files. Details: {exc}")
    #         log.error(msg)

    #         raise exc
