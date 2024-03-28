import typing as t
from pathlib import Path

from core.config import SSHSettings, AppSettings
from core.paths import ENSURE_DIRS

from dynaconf import Dynaconf
from red_utils.std import path_utils

DYNACONF_SETTINGS: Dynaconf = Dynaconf(
    environments=True,
    envvar_prefix="DYNACONF",
    settings_files=["settings.toml", ".secrets.toml"],
)

DYNACONF_SSH_SETTINGS: Dynaconf = Dynaconf(
    environments=True,
    envvar_prefix="SSH",
    settings_files=["ssh/settings.toml", "ssh/.secrets.toml"],
)

## Uncomment if adding a database config
# valid_db_types: list[str] = ["sqlite", "postgres", "mssql"]

## Uncomment to load database settings from environment
# DYNACONF_DB_SETTINGS: Dynaconf = Dynaconf(
#     environments=True,
#     envvar_prefix="DB",
#     settings_files=["db/settings.toml", "db/.secrets.toml"],
# )


def ensure_dirs(paths: list[Path] = ENSURE_DIRS) -> None:
    try:
        path_utils.ensure_dirs_exist(ensure_dirs=paths)
    except Exception as exc:
        msg = Exception(f"Unhandled exception creating paths. Details: {exc}")
        raise msg


settings: AppSettings = AppSettings(
    env=DYNACONF_SETTINGS.ENV,
    container_env=DYNACONF_SETTINGS.CONTAINER_ENV,
    log_level=DYNACONF_SETTINGS.LOG_LEVEL,
)
ssh_settings: SSHSettings = SSHSettings(
    remote_host=DYNACONF_SSH_SETTINGS.SSH_REMOTE_HOST,
    remote_port=DYNACONF_SSH_SETTINGS.SSH_REMOTE_PORT,
    remote_user=DYNACONF_SSH_SETTINGS.SSH_REMOTE_USER,
    remote_password=DYNACONF_SSH_SETTINGS.SSH_REMOTE_PASSWORD,
    remote_cwd=DYNACONF_SSH_SETTINGS.SSH_REMOTE_CWD,
    local_dest=DYNACONF_SSH_SETTINGS.SSH_LOCAL_DEST_PATH,
    extra_path_suffix=DYNACONF_SSH_SETTINGS.SSH_EXTRA_PATH_SUFFIX,
    privkey=DYNACONF_SSH_SETTINGS.SSH_PRIVKEY_FILE,
    pubkey=DYNACONF_SSH_SETTINGS.SSH_PUBKEY_FILE,
)
