"""Config file read/write for connection defaults (server, name)."""

import configparser
from pathlib import Path

_SECTION = "risus"


def read_config(base_dir: Path) -> tuple[str | None, str | None, str | None]:
    """Read server, name, token from base_dir/risus.cfg. Returns (None, None, None) on any absence."""
    cfg_path = base_dir / "risus.cfg"
    if not cfg_path.exists():
        return None, None, None
    try:
        parser = configparser.ConfigParser()
        parser.read(cfg_path)
        if not parser.has_section(_SECTION):
            return None, None, None
        server = parser.get(_SECTION, "server", fallback=None)
        name = parser.get(_SECTION, "name", fallback=None)
        token = parser.get(_SECTION, "token", fallback=None)
        return server, name, token
    except Exception:
        return None, None, None


def write_config(base_dir: Path, server: str, name: str, token: str | None = None) -> None:
    """Write server, name, and optional token to base_dir/risus.cfg. Silently ignores all errors."""
    try:
        cfg_path = base_dir / "risus.cfg"
        parser = configparser.ConfigParser()
        data: dict[str, str] = {"server": server, "name": name}
        if token is not None:
            data["token"] = token
        parser[_SECTION] = data
        with cfg_path.open("w") as f:
            parser.write(f)
    except Exception:
        pass
