from loguru import logger as log
import typing as t
from pathlib import Path

from core.paths import DATA_DIR
from core import SSHSettings, ssh_settings, AppSettings, settings

from modules import sort as _sort


def sort_local_backups(local_backups_dir: t.Union[str, Path] = None):
    _sort.sort_into_date_dirs(src_dir=local_backups_dir)
    raise NotImplementedError("Sorting local backed up files is not fully implemented")
