import typing as t
from pathlib import Path

from core import settings, ssh_settings
from core import helpers

from loguru import logger as log
from red_utils.std import path_utils
import pendulum


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
