"""Unit tests for client.config read/write functions."""

import configparser


from client.config import read_config, write_config


def test_read_absent_file(tmp_path):
    assert read_config(tmp_path) == (None, None, None)


def test_read_both_keys(tmp_path):
    cfg = tmp_path / "risus.cfg"
    cfg.write_text("[risus]\nserver = host:8765\nname = Conan\n")
    assert read_config(tmp_path) == ("host:8765", "Conan", None)


def test_read_missing_server_key(tmp_path):
    cfg = tmp_path / "risus.cfg"
    cfg.write_text("[risus]\nname = Conan\n")
    server, name, token = read_config(tmp_path)
    assert server is None
    assert name == "Conan"
    assert token is None


def test_read_missing_name_key(tmp_path):
    cfg = tmp_path / "risus.cfg"
    cfg.write_text("[risus]\nserver = host:8765\n")
    server, name, token = read_config(tmp_path)
    assert server == "host:8765"
    assert name is None
    assert token is None


def test_read_missing_section(tmp_path):
    cfg = tmp_path / "risus.cfg"
    cfg.write_text("[other]\nserver = host:8765\n")
    assert read_config(tmp_path) == (None, None, None)


def test_write_creates_file(tmp_path):
    write_config(tmp_path, "host:8765", "Conan")
    cfg = tmp_path / "risus.cfg"
    assert cfg.exists()
    parser = configparser.ConfigParser()
    parser.read(cfg)
    assert parser.get("risus", "server") == "host:8765"
    assert parser.get("risus", "name") == "Conan"


def test_write_overwrites_existing(tmp_path):
    cfg = tmp_path / "risus.cfg"
    cfg.write_text("[risus]\nserver = old:9999\nname = OldName\n")
    write_config(tmp_path, "new:8765", "NewName")
    parser = configparser.ConfigParser()
    parser.read(cfg)
    assert parser.get("risus", "server") == "new:8765"
    assert parser.get("risus", "name") == "NewName"


def test_write_readonly_path_does_not_raise(tmp_path):
    readonly_dir = tmp_path / "readonly"
    readonly_dir.mkdir()
    readonly_dir.chmod(0o444)
    try:
        write_config(readonly_dir, "host:8765", "Conan")
    finally:
        readonly_dir.chmod(0o755)


# --- T013: Token read/write cases ---

def test_write_config_persists_token(tmp_path):
    write_config(tmp_path, "host:8765", "Conan", "my-secret-token-here")
    cfg = tmp_path / "risus.cfg"
    import configparser
    parser = configparser.ConfigParser()
    parser.read(cfg)
    assert parser.get("risus", "token") == "my-secret-token-here"


def test_read_config_returns_stored_token(tmp_path):
    cfg = tmp_path / "risus.cfg"
    cfg.write_text("[risus]\nserver = host:8765\nname = Conan\ntoken = my-secret-token\n")
    server, name, token = read_config(tmp_path)
    assert token == "my-secret-token"


def test_read_config_returns_none_when_token_absent(tmp_path):
    cfg = tmp_path / "risus.cfg"
    cfg.write_text("[risus]\nserver = host:8765\nname = Conan\n")
    server, name, token = read_config(tmp_path)
    assert token is None


def test_write_config_without_token_omits_key(tmp_path):
    write_config(tmp_path, "host:8765", "Conan")
    server, name, token = read_config(tmp_path)
    assert token is None
