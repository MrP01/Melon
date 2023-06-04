import pathlib

import tomllib

CONFIG_FOLDER = pathlib.Path("~").expanduser().resolve() / ".config" / "melon"

with open(CONFIG_FOLDER / "config.toml", "rb") as f:
    CONFIG = tomllib.load(f)
