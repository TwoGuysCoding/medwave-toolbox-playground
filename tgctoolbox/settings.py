import logging
import os
from typing import List
from typing import Optional

import yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SettingsMeta(type):
    """Metaclass to create a singleton Settings class."""

    _instance = None

    def __call__(cls, *args, **kwargs):
        """Create a new instance of the class if it doesn't exist, otherwise return the existing instance.

        Returns:
            The existing instance of the class.
        """
        if cls._instance is None:
            cls._instance = super().__call__(*args, **kwargs)
        return cls._instance


class Settings(metaclass=SettingsMeta):
    """Class to manage application settings."""

    def __init__(
        self,
        load_predefined: bool = True,
        reload: bool = False,
        load_env: bool = False,
        base_dir: Optional[str] = None,
        config_files: Optional[List[str]] = None,
    ):
        """
        Initialize Settings object. Load settings from YAML files and environment variables.

        Note: The settings are loaded from the following sources:
        1. Predefined YAML files (base.yaml, local.yaml, production.yaml) - this setting is enabled by default and uses the APP_ENVIRONMENT environment variable to choose the YAML files based on convention
        2. Custom YAML files - pass the list of paths to the YAML files to load and set load_predefined to False
        3. Environment variables - set load_env to True to load settings from environment variables, which should be prefixed with 'VAR_' as per convention

        Args:
            load_predefined (bool): Load settings from predefined YAML files. Default is True.
            reload (bool): Whether to reload settings. Default is False.
            load_env (bool): Load settings from environment variables. Default is False.
            base_dir (str): Path to the directory containing the YAML files. Default is 'configuration'.
            config_files (list): List of paths to the YAML files to load. By default, it loads 'base.yaml', 'local.yaml', and 'production.yaml'.
        """
        BASE_DIR = base_dir or "configuration"
        BASE_FILES = [
            os.path.join(BASE_DIR, "base.yaml"),
            os.path.join(BASE_DIR, "local.yaml"),
            os.path.join(BASE_DIR, "production.yaml"),
        ]

        REQUIRED_SETTINGS = ["port", "host"]

        if not hasattr(self, "_initialized") or reload:
            self.port = None
            self.host = None
            self._settings = {}
            config_files = config_files or BASE_FILES
            if load_predefined:
                self._load_from_yaml_predefined(BASE_DIR)
            else:
                self._load_from_yaml(config_files)
            if load_env:
                self._load_from_env()
            self._initialized = True
            self._set_settings(self._settings, REQUIRED_SETTINGS)

    def _set_settings(self, settings, req_settings):
        """Set settings from a dictionary."""
        for setting in req_settings:
            if not self.get(setting):
                raise ValueError(f"Setting '{setting}' is required")
            else:
                setattr(self, setting, self.get(setting))

    def _load_from_yaml_predefined(self, dir_path):
        """Load settings from predefined YAML files.

        Note: This method chooses the YAML files based on the APP_ENVIRONMENT environment variable.
        APP_ENVIRONMENT can be 'local' or 'production'. If not set, 'local' is used by default.

        Args:
            dir_path (str): Path to the directory containing the YAML files.
        """
        base_path = os.path.join(dir_path, "base.yaml")
        local_path = os.path.join(dir_path, "local.yaml")
        prod_path = os.path.join(dir_path, "production.yaml")
        app_env = os.environ.get("APP_ENVIRONMENT", "local")
        if app_env not in ["local", "production"]:
            raise ValueError(
                "Invalid APP_ENVIRONMENT value. Use 'local' or 'production'."
            )
        FILES = [base_path, local_path if app_env == "local" else prod_path]
        self._load_from_yaml(FILES)

    def _load_from_yaml(self, config_files):
        """Load settings from YAML files."""
        loaded_settings = {}
        settings_names = []
        if config_files:
            for file in config_files:
                try:
                    with open(file, "r") as f:
                        settings = yaml.safe_load(f)
                        if settings:
                            loaded_settings.update(settings)
                            settings_names.extend(settings.keys())
                except FileNotFoundError:
                    logger.warning(f"Configuration file not found: {file}")
                    continue
                except yaml.YAMLError:
                    logger.warning(f"Error loading configuration file: {file}")
                    continue
        self._settings.update(loaded_settings)
        logger.info("Following settings were loaded from YAML files:")
        for name in settings_names:
            logger.info(f"  - {name}")

    def _load_from_env(self):
        """Load settings from environment variables."""
        settings_names = []
        for key, value in os.environ.items():
            if key.startswith("VAR_"):
                keys = key.split("_")[1:]  # Remove 'VAR_' prefix
                settings_names.append(keys[-1])
                current_level = self._settings
                for k in keys[:-1]:
                    current_level = current_level.setdefault(k, {})
                current_level[keys[-1]] = value
        logger.info("Following settings were loaded from environment variables:")
        for name in settings_names:
            logger.info(f"  - {name}")

    def get(self, key, default=None):
        """
        Get the value of a setting.

        Args:
            key (str): The key of the setting.
            default: Default value if setting not found.

        Returns:
            The value of the setting if found, otherwise default value.
        """
        value = self._settings
        for k in key.split("."):
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value


# Example usage:
if __name__ == "__main__":
    settings = Settings()
    settings2 = Settings()

    # Accessing settings
    app_port = settings.port
    app_host = settings.host
    print(f"App Port: {app_port}, App Host: {app_host}")
    print(settings is settings2)
