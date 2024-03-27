import typing as t
from pathlib import Path
from contextlib import contextmanager
from os import system
import sys

from core.config import ssh_settings, SSHSettings

from loguru import logger as log
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

    _os: str = get_host_os()

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


@contextmanager
def get_ssh_client(
    ssh_settings: SSHSettings = ssh_settings,
) -> t.Generator[paramiko.SSHClient, t.Any, None]:
    """Context manager for building & yielding a Paramiko SSHClient."""
    assert ssh_settings, ValueError("Missing SSH settings.")
    assert isinstance(ssh_settings, SSHSettings), TypeError(
        f"ssh_settings should be an initialized SSHSettings object. Got type: ({type(ssh_settings)})"
    )

    log.info(f"Getting SSHClient")
    try:
        ssh_client: paramiko.SSHClient = paramiko.SSHClient()
        ssh_client.load_system_host_keys()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    except Exception as exc:
        msg = Exception(f"Unhandled exception building SSHClient. Details: {exc}")
        log.error(msg)

        raise exc

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

        yield ssh_client
    except Exception as exc:
        msg = Exception(
            f"Unhandled exception connecting to remote host {ssh_settings.remote_user}@{ssh_settings.remote_host}:{ssh_settings.remote_port}. Details: {exc}"
        )
        log.error(f"({type(exc)}) {msg}")

        raise exc
    finally:
        ssh_client.close()


@contextmanager
def get_sftp_client(
    ssh_settings: SSHSettings | None = None,
    ssh_client: paramiko.SSHClient | None = None,
) -> t.Generator[paramiko.SFTPClient, t.Any, None]:
    assert ssh_settings or ssh_client, ValueError(
        "Must pass an SSHSettings object, or an initialized Paramiko SSHClient."
    )

    if ssh_settings:
        assert isinstance(ssh_settings, SSHSettings), TypeError(
            f"ssh_settings must be of type SSHSettings. Got type: ({type(ssh_settings)})"
        )

        try:
            with get_ssh_client(ssh_settings=ssh_settings) as ssh_client:
                try:
                    _sftp: paramiko.SFTPClient = ssh_client.open_sftp()

                    yield _sftp

                except Exception as exc:
                    msg = Exception(
                        f"Unhandled exception getting SFTP client from SSH client. Details: {exc}"
                    )
                    log.error(msg)

                    raise exc

                finally:
                    _sftp.close()

        except Exception as exc:
            msg = Exception(f"Unhandled exception getting SSH client. Details: {exc}")
            log.error(msg)

            raise exc
        finally:
            ssh_client.close()

    else:

        assert ssh_client, ValueError("Missing ssh_client")
        assert isinstance(ssh_client, paramiko.SSHClient), TypeError(
            f"ssh_client must be a paramiko.SSHClient. Got type: ({type(ssh_client)})"
        )

        log.info("Extracting SFTP client from SSH client")
        try:
            sftp_client: paramiko.SFTPClient = ssh_client.open_sftp()

            yield sftp_client

        except Exception as exc:
            msg = Exception(f"Unhandled exception getting SFTP client. Details: {exc}")
            log.error(msg)

            raise exc
        finally:
            sftp_client.close()
