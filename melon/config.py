"""This submodule only does one thing: loading configuration from the right place."""
import pathlib

try:
    import tomllib
except ImportError:
    import tomli as tomllib

CONFIG_FOLDER = pathlib.Path("~").expanduser().resolve() / ".config" / "melon"

with open(CONFIG_FOLDER / "config.toml", "rb") as f:
    CONFIG = tomllib.load(f)
