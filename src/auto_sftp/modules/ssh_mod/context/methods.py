from __future__ import annotations

from contextlib import contextmanager
from os import system
from pathlib import Path
import sys
import typing as t

from core import SSHSettings, ssh_settings
from core.helpers import get_host_os
from loguru import logger as log
import paramiko

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
    if not ssh_client:
        assert ssh_settings, ValueError(
            "No ssh_client was passed, and ssh_settings is None. If you are not passing an initialized paramiko.SSHClient, you must pass an SSHSettings object."
        )
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
