# auto-sftp

Automate SFTP file downloads with [`Paramiko`](https://www.paramiko.org).

## Description

Configure your remote by editing files in [`./config`](./config) and run the app to automate pulling all files in a remote path to a local destination.

## Setup

⚠️ **NOTE**: Your SSH key must already be copied to the remote (i.e. `ssh-copy-id -i ~/.ssh/id_rsa.pub user@remote`). To create a new key, use `ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""`, then copy the `id_rsa.pub` file to your remote.

### Config Files

Before installing anything, do the following in the  [`config/`](./config/) directory:

- In all directories (i.e. including [`config/db`](./config/db) and [`config/ssh`](./config/ssh)):
  - Copy any `settings.toml` files to `settings.local.toml`
  - Copy and `.secrets.example.toml`  files to `.secrets.toml`
- Edit the following:
  - `./config/settings.local.toml`
    
  - `./config/ssh/settings.local.toml`
    - In the `[dev]` and/or `[prod]` sections, edit the `ssh_remote_*` values, inputting SSH connection information for your remote.
    - Optionally, add extra paths with `ssh_extra_path_prefix`.
      - This is useful if your `ssh_remote_cwd` is something like `/mnt/backup`, and you want to target different folders within by quickly changing a single value (i.e. when running in a container).
      - If you set (for example) `ssh_extra_path_suffix = "some_app/data"`, then your new remote path will be `/mnt/backup/some_app/data` when the app runs.
  - `./config/ssh/.secrets.toml`
    - If your SSH key is `~/.ssh/id_rsa`, you do not need to edit anything in this file.
    - If you named your key something else, like `~/.ssh/backup_id_rsa`, edit `ssh_privkey_file = "~/.ssh/backup_id_rsa"` and `ssh_pubkey_file = "~/.ssh/backup_id_rsa.pub"`
  - `./config/db`
    - As of now, this app does not use a database, and no files need to be edited.

### (Optional) Set environment variable

This project uses [`Dynaconf`](https://dynaconf.com) to manage app configuration. Configurations are loaded from the [`config/`](./config) directory.

You can control running this app in `prod` (default) or `dev` mode; the only real difference between the 2 is that `prod`'s log level is `INFO` (meaning debug messages are hidden), and `dev`'s level is `DEBUG`.

To change the environment using an environment variable, do one of the following:

#### Prepend script with env variable

```shell
$ ENV_FOR_DYNACONF=dev pdm run python src/auto_sftp
```

#### Set environment variable

```shell
## Linux
$ export ENV_FOR_DYNACONF=dev
```

```powershell
## Windows
$ $env:ENV_FOR_DYNACONF="dev"
```

### With PDM

- Install the project

```shell
$ pdm install
```

- (Optional) Build project wheel

```shell
$ pdm build
```

- Run the project

```shell
## Run directly with Python
$ pdm run python src/auto_sftp
```

- The project also has start scripts defined in the [`pyproject.toml`](./pyproject.toml) file (under `[tool.pdm.scripts]`)

```shell
## Run with PDM start script
$ pdm run start

## Run in dev mode, with debugging
$ pdm run start-dev
```

### With virtualenv

- Create a virtualenv

```shell
$ virtualenv .venv
```

- Activate the virtualenv

```shell
## Linux
$ . ./.venv/bin/activate

## Windows
$ . .\.venv\Scripts\activate
```

- Install requirements

```shell
## If you just want to run the app
$ pip install -r requirements.txt

## If you are going to develop
$ pip install -r requirements.dev.txt
```

- Run the app (from the git root)

```shell
$ python src/auto_sftp/main.py

## Run the project as a module
$ python src/auto_sftp
```
