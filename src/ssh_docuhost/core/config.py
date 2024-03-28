from __future__ import annotations

from pathlib import Path
import typing as t

from .constants import DEFAULT_SSH_DIR, DEFAULT_SSH_PRIVKEY, DEFAULT_SSH_PUBKEY

from dynaconf import Dynaconf
from pydantic import Field, ValidationError, field_validator
from pydantic_settings import BaseSettings

## Uncomment if adding a database config
# import sqlalchemy as sa
# import sqlalchemy.orm as so

DYNACONF_SETTINGS: Dynaconf = Dynaconf(
    environments=True,
    envvar_prefix="DYNACONF",
    settings_files=["settings.toml", ".secrets.toml"],
)

## Uncomment if adding a database config
# valid_db_types: list[str] = ["sqlite", "postgres", "mssql"]

## Uncomment to load database settings from environment
# DYNACONF_DB_SETTINGS: Dynaconf = Dynaconf(
#     environments=True,
#     envvar_prefix="DB",
#     settings_files=["db/settings.toml", "db/.secrets.toml"],
# )

DYNACONF_SSH_SETTINGS: Dynaconf = Dynaconf(
    environments=True,
    envvar_prefix="SSH",
    settings_files=["ssh/settings.toml", "ssh/.secrets.toml"],
)


class AppSettings(BaseSettings):
    env: str = Field(default=DYNACONF_SETTINGS.ENV, env="ENV")
    container_env: bool = Field(
        default=DYNACONF_SETTINGS.CONTAINER_ENV, env="CONTAINER_ENV"
    )
    log_level: str = Field(default=DYNACONF_SETTINGS.LOG_LEVEL, env="LOG_LEVEL")


class SSHSettings(BaseSettings):
    remote_host: str = Field(
        default=DYNACONF_SSH_SETTINGS.SSH_REMOTE_HOST, env="SSH_REMOTE_HOST"
    )
    remote_user: str = Field(default=DYNACONF_SSH_SETTINGS.SSH_REMOTE_USER)
    remote_password: str | None = Field(
        default=DYNACONF_SSH_SETTINGS.SSH_REMOTE_PASSWORD,
        env="SSH_REMOTE_PASSWORD",
        repr=False,
    )
    remote_cwd: str = Field(
        default=DYNACONF_SSH_SETTINGS.SSH_REMOTE_CWD, env="SSH_REMOTE_CWD"
    )
    remote_port: int = Field(
        default=DYNACONF_SSH_SETTINGS.SSH_REMOTE_SSH_PORT, env="SSH_REMOTE_SSH_PORT"
    )

    local_dest: t.Union[str, Path] = Field(
        default=DYNACONF_SSH_SETTINGS.SSH_LOCAL_DEST_PATH, env="SSH_LOCAL_DEST_PATH"
    )

    privkey: t.Union[str, Path] = Field(
        default=DYNACONF_SSH_SETTINGS.SSH_PRIVKEY_FILE, env="SSH_PRIVKEY_FILE"
    )
    pubkey: t.Union[str, Path] = Field(
        default=DYNACONF_SSH_SETTINGS.SSH_PUBKEY_FILE, env="SSH_PUBKEY_FILE"
    )
    extra_path_suffix: str | None = Field(
        default=DYNACONF_SSH_SETTINGS.SSH_EXTRA_PATH_SUFFIX, env="SSH_EXTRA_PATH_SUFFIX"
    )

    @field_validator("privkey")
    def validate_privkey(cls, v) -> Path:
        if isinstance(v, Path):
            if "~" in f"{v}":
                return v.expanduser()
            else:
                return v

        if isinstance(v, str):
            if "~" in v:
                return Path(v).expanduser()
            else:
                return Path(v)

        raise ValidationError

    @field_validator("pubkey")
    def validate_pubkey(cls, v) -> Path:
        if isinstance(v, Path):
            if "~" in f"{v}":
                return v.expanduser()
            else:
                return v

        if isinstance(v, str):
            if "~" in v:
                return Path(v).expanduser()
            else:
                return Path(v)

        raise ValidationError

    @field_validator("local_dest")
    def validate_local_dest(cls, v) -> Path:
        if isinstance(v, Path):
            if "~" in f"{v}":
                return v.expanduser()
            else:
                return v

        if isinstance(v, str):
            if "~" in v:
                return Path(v).expanduser()
            else:
                return Path(v)

        raise ValidationError

    @property
    def privkey_exists(self) -> bool:
        return self.privkey.exists()

    @property
    def pubkey_exists(self) -> bool:
        return self.pubkey.exists()

    @property
    def local_dest_exists(self) -> bool:
        return self.local_dest.exists()


## Uncomment if you're configuring a database for the app
# class DBSettings(BaseSettings):
#     type: str = Field(default=DYNACONF_SETTINGS.DB_TYPE, env="DB_TYPE")
#     drivername: str = Field(
#         default=DYNACONF_DB_SETTINGS.DB_DRIVERNAME, env="DB_DRIVERNAME"
#     )
#     user: str | None = Field(
#         default=DYNACONF_DB_SETTINGS.DB_USERNAME, env="DB_USERNAME"
#     )
#     password: str | None = Field(
#         default=DYNACONF_DB_SETTINGS.DB_PASSWORD, env="DB_PASSWORD", repr=False
#     )
#     host: str | None = Field(default=DYNACONF_DB_SETTINGS.DB_HOST, env="DB_HOST")
#     port: Union[str, int, None] = Field(
#         default=DYNACONF_DB_SETTINGS.DB_PORT, env="DB_PORT"
#     )
#     database: str = Field(default=DYNACONF_DB_SETTINGS.DB_DATABASE, env="DB_DATABASE")
#     echo: bool = Field(default=DYNACONF_DB_SETTINGS.DB_ECHO, env="DB_ECHO")

#     @field_validator("port")
#     def validate_db_port(cls, v) -> int:
#         if v is None or v == "":
#             return None
#         elif isinstance(v, int):
#             return v
#         elif isinstance(v, str):
#             return int(v)
#         else:
#             raise ValidationError

#     def get_db_uri(self) -> sa.URL:
#         try:
#             _uri: sa.URL = sa.URL.create(
#                 drivername=self.drivername,
#                 username=self.user,
#                 password=self.password,
#                 host=self.host,
#                 port=self.port,
#                 database=self.database,
#             )

#             return _uri

#         except Exception as exc:
#             msg = Exception(
#                 f"Unhandled exception getting SQLAlchemy database URL. Details: {exc}"
#             )
#             raise msg

#     def get_engine(self) -> sa.Engine:
#         assert self.get_db_uri() is not None, ValueError("db_uri is not None")
#         assert isinstance(self.get_db_uri(), sa.URL), TypeError(
#             f"db_uri must be of type sqlalchemy.URL. Got type: ({type(self.db_uri)})"
#         )

#         try:
#             engine: sa.Engine = sa.create_engine(
#                 url=self.get_db_uri().render_as_string(hide_password=False),
#                 echo=self.echo,
#             )

#             return engine
#         except Exception as exc:
#             msg = Exception(
#                 f"Unhandled exception getting database engine. Details: {exc}"
#             )

#             raise msg

#     def get_session_pool(self) -> so.sessionmaker[so.Session]:
#         engine: sa.Engine = self.get_engine()
#         assert engine is not None, ValueError("engine cannot be None")
#         assert isinstance(engine, sa.Engine), TypeError(
#             f"engine must be of type sqlalchemy.Engine. Got type: ({type(engine)})"
#         )

#         session_pool: so.sessionmaker[so.Session] = so.sessionmaker(bind=engine)

#         return session_pool


settings: AppSettings = AppSettings()
## Uncomment if you're configuring a database for the app
# db_settings: DBSettings = DBSettings()
ssh_settings: SSHSettings = SSHSettings()
