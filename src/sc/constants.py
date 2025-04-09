import os
from pathlib import Path

SC_CONFIG_DIR = Path.home() / ".sc_config"
SC_USER_CONFIG = Path(os.getenv("SC_USER_CONFIG", SC_CONFIG_DIR / "config.yaml"))
SC_ADMIN_CONFIG = Path("/etc/sc/config.yaml")
