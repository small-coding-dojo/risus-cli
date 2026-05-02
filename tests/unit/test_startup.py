"""Unit tests for risus.py startup prompt logic."""

import sys
from pathlib import Path
from unittest.mock import patch


import risus
from risus import _prompt_required


# --- _prompt_required unit tests ---

def test_prompt_required_returns_typed_value():
    with patch("builtins.input", return_value="typed"):
        assert _prompt_required("Server address", None) == "typed"


def test_prompt_required_accepts_default_on_empty():
    with patch("builtins.input", return_value=""):
        assert _prompt_required("Server address", "localhost:8765") == "localhost:8765"


def test_prompt_required_shows_default_in_hint():
    with patch("builtins.input", return_value="") as mock_input:
        _prompt_required("Server address", "localhost:8765")
        mock_input.assert_called_with("Server address [localhost:8765]: ")


def test_prompt_required_no_default_no_hint():
    with patch("builtins.input", return_value="host:8765") as mock_input:
        _prompt_required("Server address", None)
        mock_input.assert_called_with("Server address: ")


def test_prompt_required_reprompts_on_empty_no_default():
    responses = iter(["", "", "host:8765"])
    with patch("builtins.input", side_effect=responses) as mock_input:
        result = _prompt_required("Server address", None)
    assert result == "host:8765"
    assert mock_input.call_count == 3


# --- main() integration-level tests ---

def test_no_args_no_config_both_prompts_blank():
    """No CLI args + no config → both prompts shown with no default hint."""
    with patch.object(sys, "argv", ["risus.py"]), \
         patch("client.config.read_config", return_value=(None, None)), \
         patch("client.config.write_config"), \
         patch("builtins.input", side_effect=["host:8765", "Conan", "6"]) as mock_input, \
         patch("risus.connect_or_die"), \
         patch("atexit.register"), \
         patch("risus.clear"), \
         patch("risus.show_state"):
        try:
            risus.main()
        except SystemExit:
            pass
    calls = [c.args[0] for c in mock_input.call_args_list]
    assert any("Server address:" in c and "[" not in c for c in calls)
    assert any("Your name:" in c and "[" not in c for c in calls)


def test_no_args_config_with_both_prompts_show_defaults():
    """No CLI args + config has both values → prompts show defaults in brackets."""
    with patch.object(sys, "argv", ["risus.py"]), \
         patch("client.config.read_config", return_value=("saved:8765", "SavedName")), \
         patch("client.config.write_config"), \
         patch("builtins.input", side_effect=["", "", "6"]) as mock_input, \
         patch("risus.connect_or_die"), \
         patch("atexit.register"), \
         patch("risus.clear"), \
         patch("risus.show_state"):
        try:
            risus.main()
        except SystemExit:
            pass
    calls = [c.args[0] for c in mock_input.call_args_list]
    assert any("[saved:8765]" in c for c in calls)
    assert any("[SavedName]" in c for c in calls)


def test_server_arg_provided_only_name_prompted():
    """Server arg given → only name is prompted."""
    with patch.object(sys, "argv", ["risus.py", "myhost:8765"]), \
         patch("client.config.read_config", return_value=(None, None)), \
         patch("client.config.write_config"), \
         patch("builtins.input", side_effect=["Conan", "6"]) as mock_input, \
         patch("risus.connect_or_die"), \
         patch("atexit.register"), \
         patch("risus.clear"), \
         patch("risus.show_state"):
        try:
            risus.main()
        except SystemExit:
            pass
    calls = [c.args[0] for c in mock_input.call_args_list]
    assert not any("Server address" in c for c in calls)
    assert any("Your name" in c for c in calls)


def test_both_args_provided_no_prompts():
    """Both CLI args given → no prompts shown."""
    with patch.object(sys, "argv", ["risus.py", "myhost:8765", "Conan"]), \
         patch("client.config.read_config", return_value=(None, None)), \
         patch("client.config.write_config"), \
         patch("builtins.input", side_effect=["6"]) as mock_input, \
         patch("risus.connect_or_die"), \
         patch("atexit.register"), \
         patch("risus.clear"), \
         patch("risus.show_state"):
        try:
            risus.main()
        except SystemExit:
            pass
    calls = [c.args[0] for c in mock_input.call_args_list]
    assert not any("Server address" in c for c in calls)
    assert not any("Your name" in c for c in calls)


def test_atexit_registered_after_arg_resolution():
    """atexit.register is called with write_config, base_dir, server, name."""
    with patch.object(sys, "argv", ["risus.py", "myhost:8765", "Conan"]), \
         patch("client.config.read_config", return_value=(None, None)), \
         patch("client.config.write_config"), \
         patch("builtins.input", side_effect=["6"]), \
         patch("risus.connect_or_die"), \
         patch("atexit.register") as mock_atexit, \
         patch("risus.clear"), \
         patch("risus.show_state"):
        try:
            risus.main()
        except SystemExit:
            pass
    mock_atexit.assert_called_once()
    args = mock_atexit.call_args[0]
    assert callable(args[0])
    assert isinstance(args[1], Path)
    assert args[2] == "myhost:8765"
    assert args[3] == "Conan"
