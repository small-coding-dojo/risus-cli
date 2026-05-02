"""Config file read/write for connection defaults (server, name)."""

import configparser
from pathlib import Path

_SECTION = "risus"


def read_config(base_dir: Path) -> tuple[str | None, str | None]:
    """Read server and name from base_dir/risus.cfg. Returns (None, None) on any absence."""
    cfg_path = base_dir / "risus.cfg"
    if not cfg_path.exists():
        return None, None
    try:
        parser = configparser.ConfigParser()
        parser.read(cfg_path)
        if not parser.has_section(_SECTION):
            return None, None
        server = parser.get(_SECTION, "server", fallback=None)
        name = parser.get(_SECTION, "name", fallback=None)
        return server, name
    except Exception:
        return None, None


def write_config(base_dir: Path, server: str, name: str) -> None:
    """Write server and name to base_dir/risus.cfg. Silently ignores all errors."""
    try:
        cfg_path = base_dir / "risus.cfg"
        parser = configparser.ConfigParser()
        parser[_SECTION] = {"server": server, "name": name}
        with cfg_path.open("w") as f:
            parser.write(f)
    except Exception:
        pass
