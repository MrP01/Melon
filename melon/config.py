"""This submodule only does one thing: loading configuration from the right place."""
import pathlib

try:
    import tomllib
except ImportError:  # pragma: no cover
    import tomli as tomllib  # pragma: no cover

CONFIG_FOLDER = pathlib.Path.home() / ".config" / "melon"
CONFIG_FOLDER.mkdir(exist_ok=True)
CONFIG_PATH = CONFIG_FOLDER / "config.toml"

CONFIG = {"client": {"url": "http://localhost:8000/dav/user/calendars/", "username": None, "password": None}}


def load_config():
    """Loads, or re-loads, the configuration file."""
    global CONFIG
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "rb") as f:
            CONFIG = tomllib.load(f)


load_config()
