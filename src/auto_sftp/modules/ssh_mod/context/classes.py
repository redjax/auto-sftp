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

    def sftp_download_all(
        self,
        remote_src: t.Union[str, Path] = None,
        local_dest: t.Union[str, Path] = None,
    ):
        """Download all files from a remote src directory to a local destination."""
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
        local_dest = Path(local_dest).expanduser()

        if not self.ssh_client:
            msg = Exception(f"SSH client is None.")
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

        def _sftp_walk(remotepath):
            path = remotepath
            files = []
            folders = []
            for f in sftp_client.listdir_attr(remotepath):
                if S_ISDIR(f.st_mode):
                    folders.append(f.filename)
                else:
                    files.append(f.filename)
            if files:
                yield path, files
            for folder in folders:
                new_path = os.path.join(remotepath, folder)
                for x in _sftp_walk(new_path):
                    yield x

        path = remote_src
        files = []
        folders = []
        for f in sftp_client.listdir_attr(remote_src):
            if S_ISDIR(f.st_mode):
                folders.append(f.filename)
            else:
                files.append(f.filename)
        if files:
            yield path, files
        for folder in folders:
            new_path = os.path.join(remote_src, folder)
            for x in _sftp_walk(new_path):
                yield x

        for path, files in _sftp_walk("." or "/remotepath/"):
            for file in files:
                # sftp.get(remote, local) line for dowloading.
                sftp_client.get(os.path.join(os.path.join(path, file)), "/local/path/")

    # def sftp_download_all(
    #     self,
    #     remote_src: t.Union[str, Path] = None,
    #     local_dest: t.Union[str, Path] = None,
    # ):
    #     """Download all files from a remote src directory to a local destination."""
    #     assert remote_src, ValueError("Missing a remote source directory")
    #     assert isinstance(remote_src, str) or isinstance(remote_src, Path), TypeError(
    #         f"remote_src should be a string or Path. Got type: ({type(remote_src)})"
    #     )
    #     if isinstance(remote_src, Path):
    #         remote_src: str = f"{remote_src}"

    #     assert local_dest, ValueError("Missing a local destination directory")
    #     assert isinstance(local_dest, str) or isinstance(local_dest, Path), TypeError(
    #         f"local_dest"
    #     )
    #     if isinstance(local_dest, Path):
    #         if "~" in f"{local_dest}":
    #             local_dest: Path = Path(f"{local_dest}").expanduser()
    #     elif isinstance(local_dest, str):
    #         if "~" in local_dest:
    #             local_dest: Path = Path(local_dest).expanduser()
    #         else:
    #             local_dest: Path = Path(local_dest)

    #     if not self.ssh_client:
    #         msg = Exception(f"SSH client is None.")

    #         return

    #     else:
    #         sftp_client: paramiko.SFTPClient = self.get_sftp_client()

    #         try:
    #             # remote_files = sftp_client.listdir(remote_src)
    #             remote_files = self.sftp_list_files(remote_path=remote_src)
    #         except Exception as exc:
    #             msg = Exception(
    #                 f"Unhandled exception getting list of files from remote path '{remote_src}'. Details: {exc}"
    #             )
    #             log.error(msg)

    #             raise exc

    #         if remote_files:
    #             log.debug(
    #                 f"Found [{len(remote_files)}] file(s) in remote path '{remote_src}'"
    #             )
    #             with helpers.simple_spinner(
    #                 text=f"({self.user}@{self.host}) Downloading [{len(remote_files)}] file(s) to '{local_dest}' ...\n"
    #             ):

    #                 loop_count: int = 1
    #                 max_loops = len(remote_files)

    #                 for f in remote_files:
    #                     _local_path = Path(f"{local_dest}/{f}")
    #                     _remote_path = f"{remote_src}/{f}"

    #                     if _local_path.exists():
    #                         log.warning(
    #                             f"File '{f}' already exists at local path: {_local_path}. Skipping download."
    #                         )
    #                         continue

    #                     if not local_dest.exists():
    #                         log.info(
    #                             f"Downloading file from '{_remote_path}' to '{_local_path}"
    #                         )
    #                         try:
    #                             local_dest.mkdir(parents=True, exist_ok=True)
    #                         except PermissionError as perm_exc:
    #                             msg = Exception(
    #                                 f"Permission denied creating path '{local_dest}'. Details: {perm_exc}"
    #                             )
    #                             log.error(msg)

    #                             raise perm_exc
    #                         except Exception as exc:
    #                             msg = Exception(
    #                                 f"Unhandled exception creating directory '{local_dest}'. Details: {exc}"
    #                             )
    #                             log.error(msg)

    #                             raise exc

    #                     log.info(
    #                         f"[{loop_count}/{max_loops}] Downloading file from remote: {f} to local path: {_local_path}"
    #                     )

    #                     try:
    #                         sftp_client.get(
    #                             remotepath=f"{_remote_path}", localpath=_local_path
    #                         )

    #                         loop_count += 1
    #                     except Exception as exc:
    #                         msg = Exception(
    #                             f"Unhandled exception downloading file '{_remote_path}' from remote. Details: {exc}"
    #                         )
    #                         log.error(msg)

    #                         raise exc
