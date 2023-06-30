"""This submodule only does one thing: loading configuration from the right place."""
import pathlib

try:
    import tomllib
except ImportError:
    import tomli as tomllib

CONFIG_FOLDER = pathlib.Path.home() / ".config" / "melon"
CONFIG_FOLDER.mkdir(exist_ok=True)

CONFIG = {"client": {"url": "http://localhost:8000/dav/user/calendars/", "username": None, "password": None}}
if (CONFIG_FOLDER / "config.toml").exists():
    with open(CONFIG_FOLDER / "config.toml", "rb") as f:
        CONFIG = tomllib.load(f)
