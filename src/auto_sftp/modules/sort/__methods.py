import typing as t
from pathlib import Path
import re
from loguru import logger as log

from core import settings, ssh_settings

from red_utils.std import path_utils

import pendulum


def extract_dt_from_filename(
    filename: t.Union[str, Path] = None,
    ts_pattern: str = r"(\d{4}-\d{2}-\d{2}_\d{2}-\d{2})",
    # ts_format: str = "YYYY-MM-DD HH:mm",
    ts_format: str = "YYYY-MM-DD_HH-mm",
):
    filename: str = f"{filename}"
    # log.debug(f"Filename: {filename}")

    # Search for the pattern in the filename
    match = re.search(ts_pattern, filename)
    # log.debug(f"Found match: {match}")

    if match:
        # Extract the timestamp as a string
        timestamp_str = match.group(1)
        # log.debug(f"Extracted timestamp string: {timestamp_str}")

        # Convert the timestamp string to a Pendulum DateTime object
        # Replace '_' with ' ' and '-' with ':' for correct format
        # timestamp_str = timestamp_str.replace("_", " ").replace("-", ":", 2)
        # log.debug(f"Formatted timestamp string: {timestamp_str}")

        datetime_obj = pendulum.from_format(timestamp_str, ts_format)
        # log.debug(f"Pendulum DateTime object: {datetime_obj}")

        return datetime_obj
    else:
        raise ValueError(f"No valid timestamp found in filename: '{filename}'")


def _pre_sort_files(files: list[Path] = None):
    filename_dt_pairs: list[dict[str, t.Union[str, pendulum.DateTime]]] = []

    for _file in files:
        filename_dt = extract_dt_from_filename(filename=_file)
        dest_path = _append_local_dest(dt=filename_dt, src_filename=_file.name)

        _pair = {
            "filename": _file.name,
            "src_path": _file.parent,
            "dest_path": dest_path,
            "dt": filename_dt,
        }
        filename_dt_pairs.append(_pair)

    return filename_dt_pairs


def _append_local_dest(dt: pendulum.DateTime = None, src_filename: str = None):
    dir_path = Path(
        f"{ssh_settings.local_dest}/{dt.year}/{dt.month}/{dt.day}/{src_filename}"
    )

    return dir_path


def sort_into_date_dirs(
    src_dir: t.Union[str, Path] = None, filetype_filters: list[str] | None = [".tar.gz"]
):
    """Sort files in a path into subdirectories based on year, month, day.

    Files must contain a formatted timestamp somewhere in the filename, ideally at the beginning.
    i.e. `YYYY-MM-DD_HH-ss-ss_filename.tar.gz`
    """
    assert src_dir, ValueError("Missing a src_dir to scan")
    assert isinstance(src_dir, Path) or isinstance(src_dir, str), TypeError(
        f"src_dir must be a str or Path. Got type: ({type(src_dir)})"
    )
    src_dir: Path = Path(f"{src_dir}")
    if "~" in f"{src_dir}":
        src_dir = src_dir.expanduser()

    if not src_dir.exists():
        raise FileNotFoundError(f"Could not find src_dir '{src_dir}'.")

    files_list = []

    if filetype_filters:
        for _ext in filetype_filters:
            _files: list[Path] = path_utils.crawl_dir(
                target=src_dir, filetype_filter=_ext, return_type="files"
            )

            try:
                files_list = files_list + _files
            except Exception as exc:
                msg = Exception(
                    f"Unhandled exception merging list of crawled files into existing files list. Details: {exc}"
                )
                log.warning(msg)

                continue

    file_sort_meta = _pre_sort_files(files=files_list)
    log.debug(f"Example file sort meta: {file_sort_meta[0]}")

    # log.info(f"Sorting files in path '{src_dir}' into year/month/day directories.")
    # _pre_sort_files()
