from __future__ import annotations

from pathlib import Path
import sys
from os import system
import typing as t

from paramiko.channel import ChannelFile, ChannelStderrFile, ChannelStdinFile

from core.config import settings, ssh_settings
from core.paths import DATA_DIR, ENSURE_DIRS

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

    return return_val


def upload_ssh_key(
    privkey_path: t.Union[str, Path] = None,
    remote_user: str = None,
    remote_host: str = None,
):
    assert privkey_path, ValueError("Missing SSH private keyfile path")
    assert isinstance(privkey_path, str) or isinstance(privkey_path, Path), TypeError(
        f"privkey_path must be a string or Path object. Got type: ({type(privkey_path)})"
    )

    assert remote_user, ValueError("Missing remote_user")
    assert isinstance(remote_user, str), TypeError(
        f"remote_user must be a string. Got type: ({type(remote_user)})"
    )

    assert remote_host, ValueError("Missing remote_host")
    assert isinstance(remote_host, str), TypeError(
        f"remote_host must be a string. Got type: ({type(remote_host)})"
    )

    publickey_path: Path = Path(f"{privkey_path}.pub")
    assert Path(f"{publickey_path}").exists(), FileNotFoundError(
        f"Could not find public keyfile at path '{publickey_path}"
    )

    try:
        if _os == "windows":
            _cmd = f"ssh-copy-id -i {privkey_path}.pub {remote_user}@{remote_host}"

            log.warning(
                NotImplementedError(f"Uploading SSH key from Windows not supported")
            )
        else:
            _cmd = f"ssh-copy-id -i {privkey_path}.pub {remote_user}@{remote_host}>/dev/null 2>&1"
            system(_cmd)
    except FileNotFoundError as fnf:
        msg = Exception(f"Could not find public keyfile at path '{privkey_path}.pub'")
        log.error(msg)

        raise fnf
    except Exception as exc:
        msg = Exception(
            f"Unhandled exception uploading SSH public keyfile from path '{privkey_path}.pub' to {remote_user}@{remote_host}. Details: {exc}"
        )
        log.error(msg)

        raise msg


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

    log.info(f"Getting SSHClient")
    ssh_client: paramiko.SSHClient = paramiko.SSHClient()
    ssh_client.load_system_host_keys()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    log.info("Loading private key")
    ## Get SSH key
    try:
        _privkey: paramiko.RSAKey = paramiko.RSAKey.from_private_key_file(
            filename=f"{ssh_settings.privkey}"
        )
    except paramiko.SSHException as ssh_exc:
        msg = Exception(
            f"Unhandled exception loading SSH private key. Details: {ssh_exc}"
        )
        log.error(msg)

        raise ssh_exc
    except Exception as exc:
        msg = Exception(f"Unhandled exception loading SSH private key. Details: {exc}")
        log.error(msg)

        raise msg

    try:
        upload_ssh_key(
            privkey_path=ssh_settings.privkey,
            remote_host=ssh_settings.remote_host,
            remote_user=ssh_settings.remote_user,
        )
    except Exception as exc:
        msg = Exception(f"Unhandledd exception uploading SSH key. Details:  {exc}")
        log.error(msg)

        raise msg

    log.info("Attempting connection")
    try:
        ssh_client.connect(
            hostname=ssh_settings.remote_host,
            username=ssh_settings.remote_user,
            port=ssh_settings.remote_port,
            password=ssh_settings.remote_password,
            key_filename=f"{ssh_settings.privkey}",
            timeout=5000,
        )
        log.success(
            f"Connected to {ssh_settings.remote_user}@{ssh_settings.remote_host}:{ssh_settings.remote_port}"
        )
    except Exception as exc:
        msg = Exception(
            f"Unhandled exception connecting to remote host {ssh_settings.remote_user}@{ssh_settings.remote_host}:{ssh_settings.remote_port}. Details: {exc}"
        )
        log.error(f"({type(exc)}) {msg}")

        raise exc

    log.info("Getting SFTP client")
    try:
        sftp = ssh_client.open_sftp()
        log.success(f"SFTP connected")
    except Exception as exc:
        msg = Exception(f"Unhandled exception getting SFTP client. Details: {exc}")
        log.error(msg)

        raise msg

    # log.info(
    #     f"Copying 'example' file to remote path '/home/jack/example_from_colossus'."
    # )
    # try:
    #     sftp.put(Path("example"), "/home/jack/example_from_colossus")
    # except Exception as exc:
    #     msg = Exception(f"Unhandled exception copying file to remote. Details: {exc}")
    #     log.error(msg)

    #     raise exc

    # log.info(
    #     f"Downloading file '/home/jack/example_from_colossus' to ./example_response"
    # )
    # try:
    #     sftp.get("/home/jack/example_from_colossus", "./example_response")
    #     log.success(
    #         f"Pulled file '/home/jack/example_from_colossus' from remote {ssh_settings.remote_user}@{ssh_settings.remote_host}:{ssh_settings.remote_port} to ./example_response"
    #     )
    # except Exception as exc:
    #     msg = Exception(f"Unhandled exception pulling file from remote. Details: {exc}")
    #     log.error(msg)

    #     raise exc

    try:
        sftp.remove("/home/jack/example_from_colossus")
        log.success(
            f"Removed file/home/jack/example_from_colossus from remote {ssh_settings.remote_host}"
        )
    except FileNotFoundError as fnf:
        msg = Exception(
            f"Could not find file /home/jack/example_from_colossus on remote {ssh_settings.remote_host}"
        )
        log.warning(f"{msg}")

    except Exception as exc:
        msg = Exception(
            f"Unhandled exception removing file /home/jack/example_from_colossus from remote {ssh_settings.remote_host}. Details: {exc}"
        )
        log.error(msg)

        raise exc

    ## Close the SFTP session
    sftp.close()
    ## Close SSH client
    ssh_client.close()
