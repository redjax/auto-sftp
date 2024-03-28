from __future__ import annotations

from pathlib import Path

DEFAULT_SSH_DIR: Path = Path("~/.ssh").expanduser()
DEFAULT_SSH_PRIVKEY: Path = Path(f"{DEFAULT_SSH_DIR}/id_rsa")
DEFAULT_SSH_PUBKEY: Path = Path(f"{DEFAULT_SSH_DIR}/id_rsa.pub")
