import typing as t
from pathlib import Path

from core import settings, ssh_settings
from core import helpers

from loguru import logger as log
from red_utils.std import path_utils
import pendulum

from .classes import File


def list_files(path: t.Union[str, Path] = None):
    assert path, ValueError("Missing a path to scan")
    assert isinstance(path, str) or isinstance(path, Path), TypeError(
        f"path must be a Path object. Got type: ({type(path)})"
    )
    if isinstance(path, Path):
        if "~" in f"{path}":
            path: Path = path.expanduser()
    if isinstance(path, str):
        if "~" in path:
            path: Path = Path(path).expanduser()
        else:
            path: Path = Path(path)

    assert path.exists(), FileNotFoundError(f"Could not find path: '{path}'.")

    log.info(f"Getting list of files in path '{path}'")
    try:
        files: list[Path] = path_utils.scan_dir(target=path, as_pathlib=True)
        if files:
            log.debug(f"Found [{len(files)}] file(s) in path '{path}')")

        return files

    except Exception as exc:
        msg = Exception(
            f"Unhandled exception getting list of files from path '{path}'. Details: {exc}"
        )
        log.error(msg)

        raise exc


def extract_file_ext(path: Path = None) -> str:
    """Extract full file extension from a Path.

    Description:
        Given a file with multiple file extensions, i.e. `file.tar.gz`, this function
        will join all suffixes (`.tar`, `.gz`) into a single string. A `Path.suffix`
        on its own only returns the last suffix (i.e. `.gz`).

    Params:
        path (Path): A `pathlib.Path` object to a file. Path is checked with `.is_file()`, skipping
            directories passed by mistake.
    """
    assert path, ValueError("Missing a file path")
    assert isinstance(path, Path), TypeError(
        f"path must be a pathlib.Path object. Got type: ({type(path)})"
    )
    if not path.is_file():
        log.warning(ValueError(f"path should be a file, but {path} is a directory."))

        return ""

    ## Extract all suffixes from file path
    suffixes: list[str] = path.suffixes

    if len(suffixes) > 1:
        ## Join suffixes, i.e. [".tar", ".gz"] -> ".tar.gz"
        return "".join(suffixes)

    elif len(suffixes) == 1:
        ## Return [".suffix"] -> ".suffix"
        return suffixes[0]

    else:
        ## No suffix(es) detected, return empty string
        return ""


def get_file_dicts(files: list[Path] = None) -> list[dict]:
    assert files, ValueError("No files found during scan, skipping conversion to dicts")
    assert isinstance(files, list), TypeError(
        f"files must be a list of Path objects. Got type: ({type(files)})"
    )

    _dicts: list[Path] = []
    dirs: list[Path] = []
    seen_dirs: list[Path] = []

    for f in files:
        if f.is_dir():
            if not f in seen_dirs:
                log.warning(f"Path '{f}' is a dir and will be scanned at the end.")
                dirs.append(f)
                seen_dirs.append(f)

                continue

        else:
            f_dict: dict = {
                "name": f.name,
                "path": f,
                "ext": extract_file_ext(f),
                "parent": f.parent,
                "created_at": pendulum.from_timestamp(f.stat().st_ctime),
                "modified_at": pendulum.from_timestamp(f.stat().st_mtime),
                "size_in_bytes": f.stat().st_size,
            }

            # log.debug(f"File dict: {f_dict}")
            if f not in _dicts:
                _dicts.append(f_dict)
            else:
                continue

    if dirs:
        raise NotImplementedError(
            "Recursively scanning direcetories not yet supported."
        )
        log.info(f"Scanning [{len(dirs)}] dir(s)")
        for d in dirs:
            _files = ...

    return _dicts


def delete_oldest(files: list[File] = None, threshold: int = 3):
    assert files, ValueError("Missing list of files")
    assert isinstance(files, list), TypeError(
        f"files must be a list of File objects. Got type: ({type(files)})"
    )

    sorted_files: list[File] = sorted(files, key=lambda x: x.path.stat().st_ctime)
    delete_count: list[File] = max(0, len(sorted_files) - threshold)
    _deleted: list[File] = []

    if not len(files) > threshold:
        log.warning(
            f"Number of files [{len(files)}] is less than the threshold of [{threshold}]. Skipping deletions."
        )
        return

    for f in range(delete_count):

        delete_file: File = sorted_files[f]

        try:
            log.info(f"Deleting file '{delete_file.path}'.")
            delete_file.path.unlink()
            log.success(f"File deleted")

            _deleted.append(f)
        except Exception as exc:
            msg = Exception(
                f"Unhandled exception deleting file '{delete_file}'. Details: {exc}"
            )
            log.error(msg)
            continue

            # raise exc

    return _deleted


def run_local_cleanup(
    local_dest: t.Union[str, Path] = Path(
        f"{ssh_settings.local_dest}{ssh_settings.extra_path_suffix}"
    ),
    threshold: int = 10,
) -> list[File]:
    assert local_dest, ValueError(f"local_dest cannot be None")
    assert isinstance(local_dest, str) or isinstance(local_dest, Path), TypeError(
        f"local_dest must be a str or Path. Got type: ({type(local_dest)})"
    )
    if isinstance(local_dest, str):
        if "~" in local_dest:
            local_dest: Path = Path(local_dest).expanduser()
        else:
            local_dest: Path = Path(local_dest)
    if isinstance(local_dest, Path):
        if "~" in f"{local_dest}":
            local_dest: Path = Path(local_dest).expanduser()

    assert threshold and isinstance(threshold, int) and threshold > 0, ValueError(
        f"threshold must be a non-zero, positive integer. Got type: ({type(threshold)})"
    )

    log.info("Running cleanup")

    try:
        scanned_files: list[Path] = list_files(path=local_dest)
    except Exception as exc:
        msg = Exception(
            f"Unhandled exception getting list of files in path '{local_dest}'. Details: {exc}"
        )
        log.error(msg)

        raise msg

    _files: list[File] = []

    try:
        f_dicts = get_file_dicts(scanned_files)
        _continue: bool = True
    except AssertionError as err:
        log.warning(f"No files found in path '{local_dest}'")
        _continue = False

    if _continue:
        for f in f_dicts:
            # log.debug(f"File dict: {f}")

            try:
                _file = File.model_validate(f)
                # log.debug(f"File: {_file}")
                # log.debug(f"Test: {_file.model_dump_json()}")

                _files.append(_file)
            except Exception as exc:
                msg = Exception(
                    f"Unhandled exception creating File object. Details: {exc}"
                )
                log.error(msg)

                continue

    # log.info(f"Deleting oldest backups. Threshold: {threshold}")
    try:
        _deleted: list[File] = delete_oldest(files=_files, threshold=threshold)
    except Exception as exc:
        msg = Exception(f"Unhandled exception deleting oldest file(s). Details: {exc}")
        log.error(msg)

        raise exc

    return _deleted
