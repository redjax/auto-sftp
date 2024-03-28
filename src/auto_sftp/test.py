from pathlib import Path

from core import SSHSettings, settings, ssh_settings
from loguru import logger as log
from modules import ssh_mod
from packages import cleanup
from red_utils.ext.loguru_utils import init_logger, sinks


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
    assert files, ValueError("Missing list of files")
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
                "ext": extract_file_ext(f),
                "parent": f.parent,
                # "created_at": ...,
                # "modified_at": ...,
                # "size": ...
            }
            log.debug(f"File dict: {f_dict}")
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


if __name__ == "__main__":
    init_logger(sinks=[sinks.LoguruSinkStdErr(level=settings.log_level).as_dict()])

    log.info("Running cleanup")
    files = cleanup.local.list_files(
        path=f"{ssh_settings.local_dest}{ssh_settings.extra_path_suffix}"
    )

    f_dicts = get_file_dicts(files)
    for f in f_dicts:
        log.debug(f"File: {f}")
