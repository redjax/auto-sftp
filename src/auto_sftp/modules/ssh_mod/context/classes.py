from __future__ import annotations

from contextlib import AbstractContextManager
from pathlib import Path
import typing as t
import os
from stat import S_ISDIR

from core import helpers
from loguru import logger as log
import paramiko


class SSHManager(AbstractContextManager):
    def __init__(
        self,
        host: str,
        user: str,
        port: int = 22,
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

        log.debug("Getting SFTP client")
        try:
            sftp_client = self.ssh_client.open_sftp()
            log.debug(f"SFTP session opened.")
            return sftp_client

        except Exception as exc:
            msg = Exception(
                f"Unhandled exception getting SFTP client from SSH client. Details: {exc}"
            )
            log.error(msg)

            raise exc

    def sftp_list_files(self, remote_path: str = None) -> list[str]:
        assert remote_path, ValueError("Missing a path on the remote to search")
        assert isinstance(remote_path, str), TypeError(
            f"remote_path must be a string. Got type: ({type(remote_path)})"
        )

        log.info(f"Listing files in '{remote_path}' on {self.host}")
        try:
            with helpers.simple_spinner(
                text=f"({self.user}@{self.host}) Listing files in '{remote_path}'...\n"
            ):
                try:
                    sftp: paramiko.SFTPClient = self.get_sftp_client()
                except Exception as exc:
                    msg = Exception(
                        f"Unhandled exception getting SFTP client while listing files. Details: {exc}"
                    )
                    log.error(msg)

                    raise exc

                try:
                    _files: list[str] = sftp.listdir(path=remote_path)

                    return _files
                except Exception as exc:
                    msg = Exception(
                        f"Unhandled exception listing files in remote path '{remote_path}'. Details: {exc}"
                    )
                    log.error(msg)

                    raise exc
        except Exception as exc:
            msg = Exception(
                f"({type(exc)}) Unhandled exception listing files in remote path '{remote_path}'. Details: {exc}"
            )
            log.error(msg)

            raise exc

    def _sftp_walk(self, sftp_client: paramiko.SFTPClient, remotepath: str):
        files_to_download = []

        def recursive_walk(remotepath):
            for item in sftp_client.listdir_attr(remotepath):

                # log.info(f"Processing item: {item.filename}")

                remote_item = f"{remotepath}/{item.filename}"
                if S_ISDIR(item.st_mode):
                    # log.info(f"Item is a directory: {item.filename}")
                    recursive_walk(remote_item)

                else:
                    # log.info(f"Item is a file: {item.filename}")
                    files_to_download.append(remote_item)

        # log.info(f"Crawling remote path: {remotepath}")
        recursive_walk(remotepath)

        return files_to_download

    def sftp_download_all(
        self,
        remote_src: t.Union[str, Path] = None,
        local_dest: t.Union[str, Path] = None,
    ):
        assert remote_src, ValueError("Missing a remote source directory")
        assert isinstance(remote_src, str) or isinstance(remote_src, Path), TypeError(
            f"remote_src should be a string or Path. Got type: ({type(remote_src)})"
        )
        if isinstance(remote_src, Path):
            remote_src = str(remote_src)

        assert local_dest, ValueError("Missing a local destination directory")
        assert isinstance(local_dest, str) or isinstance(local_dest, Path), TypeError(
            f"local_dest should be a string or Path."
        )
        if "~" in f"{local_dest}":
            local_dest = Path(local_dest).expanduser()
        else:
            local_dest: Path = Path(f"{local_dest}")

        if not self.ssh_client:
            msg = Exception(f"SSH client is None.")
            log.error(msg)
            return

        else:
            try:
                sftp_client: paramiko.SFTPClient = self.get_sftp_client()
            except Exception as exc:
                msg = Exception(
                    f"Unhandled exception getting SFTPClient. Details: {exc}"
                )
                log.error(msg)
                raise exc

        try:
            with helpers.cli.spinners.simple_spinner(
                text=f"Getting list of files from remote {self.host}:{remote_src} ..."
            ):
                files_to_download = self._sftp_walk(
                    sftp_client=sftp_client, remotepath=remote_src
                )

            for remote_item in files_to_download:
                local_item = local_dest / Path(os.path.basename(remote_item))

                if not local_item.exists():
                    with helpers.cli.spinners.simple_spinner(
                        text=f"Downloading file '{remote_item}' to '{local_item}' ..."
                    ):
                        sftp_client.get(remote_item, local_item)

        except Exception as exc:
            msg = Exception(
                f"Unhandled exception recursively downloading remote path '{remote_src}' to local destination '{local_dest}'. Details: {exc}"
            )
            log.error(msg)
            raise exc
