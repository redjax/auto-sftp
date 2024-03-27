import typing as t
from pathlib import Path
from contextlib import AbstractContextManager

import paramiko

from loguru import logger as log


class SSHManager(AbstractContextManager):
    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str | None = None,
        ssh_keyfile: t.Union[str, Path] | None = None,
        timeout: int = 5000,
    ):
        self.host: str = host
        self.port: int = port
        self.user: str = user
        self.password: str | None = password
        self.timeout: int = timeout

        if ssh_keyfile:
            if isinstance(ssh_keyfile, str):
                if "~" in ssh_keyfile:
                    ssh_keyfile: str = f"{Path(ssh_keyfile).expanduser()}"
            elif isinstance(ssh_keyfile, Path):
                if "~" in f"{ssh_keyfile}":
                    ssh_keyfile: str = f"{Path(ssh_keyfile).expanduser()}"
                else:
                    ssh_keyfile: str = f"{ssh_keyfile}"

            self.ssh_keyfile: str = ssh_keyfile
        else:
            self.ssh_keyfile = ssh_keyfile

        ## Initialize a parameter for a paramiko.SSHClient
        self.ssh_client = None

    def __enter__(self) -> t.Self:
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.load_system_host_keys()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            self.ssh_client.connect(
                hostname=self.host,
                port=self.port,
                username=self.user,
                password=self.password,
                key_filename=self.ssh_keyfile,
                timeout=self.timeout,
            )

            return self
        except Exception as exc:
            msg = Exception(
                f"Unhandled exception yielding a paramiko.SSHClient. Details: {exc}"
            )
            log.error(msg)

            self.ssh_client.close()

            raise exc

    def __exit__(self, exc_type, exc_value, traceback):
        if self.ssh_client:
            self.ssh_client.close()
            self.ssh_client = None

        if exc_type is not None:
            msg = f"({exc_type}) Unhandled exception during SSH session: {exc_value}"
            log.error(msg)

            if traceback:
                log.error(f"Traceback:\n{traceback}")

            raise exc_value

        return

    def get_sftp_client(self) -> paramiko.SFTPClient:
        if self.ssh_client is None:
            raise ValueError("SSH client has not been initialized")

        log.info("Getting SFTP client")
        try:
            sftp_client = self.ssh_client.open_sftp()
            log.success(f"SFTP session opened.")
            return sftp_client

        except Exception as exc:
            msg = Exception(
                f"Unhandled exception getting SFTP client from SSH client. Details: {exc}"
            )
            log.error(msg)

            raise exc
