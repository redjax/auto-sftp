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

    def sftp_list_files(self, remote_path: str = None) -> list[str]:
        assert remote_path, ValueError("Missing a path on the remote to search")
        assert isinstance(remote_path, str), TypeError(
            f"remote_path must be a string. Got type: ({type(remote_path)})"
        )

        log.info(f"Listing files in '{remote_path}' on the remote machine.")
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
            remote_src: str = f"{remote_src}"

        assert local_dest, ValueError("Missing a local destination directory")
        assert isinstance(local_dest, str) or isinstance(local_dest, Path), TypeError(
            f"local_dest"
        )
        if isinstance(local_dest, Path):
            if "~" in f"{local_dest}":
                local_dest: Path = Path(f"{local_dest}").expanduser()
        elif isinstance(local_dest, str):
            if "~" in local_dest:
                local_dest: Path = Path(local_dest).expanduser()
            else:
                local_dest: Path = Path(local_dest)

        if not self.ssh_client:
            msg = Exception(f"SSH client is None.")

            return
        else:
            sftp_client: paramiko.SFTPClient = self.get_sftp_client()
            remote_files = sftp_client.listdir(remote_src)
            if remote_files:
                log.debug(
                    f"Found [{len(remote_files)}] file(s) in remote path '{remote_src}'"
                )

                for f in remote_files:
                    _local_path = Path(f"{local_dest}/{f}")
                    _remote_path = f"{remote_src}/{f}"

                    if _local_path.exists():
                        log.warning(
                            f"File '{f}' already exists at local path: {_local_path}. Skipping download."
                        )
                        continue

                    if not local_dest.exists():
                        try:
                            local_dest.mkdir(parents=True, exist_ok=True)
                        except PermissionError as perm_exc:
                            msg = Exception(
                                f"Permission denied creating path '{local_dest}'. Details: {perm_exc}"
                            )
                            log.error(msg)

                            raise perm_exc
                        except Exception as exc:
                            msg = Exception(
                                f"Unhandled exception creating directory '{local_dest}'. Details: {exc}"
                            )
                            log.error(msg)

                            raise exc

                    log.info(
                        f"Downloading file from remote: {f} to local path: {_local_path}"
                    )

                    try:
                        sftp_client.get(
                            remotepath=f"{remote_src}/{f}", localpath=_local_path
                        )
                    except Exception as exc:
                        msg = Exception(
                            f"Unhandled exception downloading file '{f}' from remote. Details: {exc}"
                        )
                        log.error(msg)

                        raise exc
