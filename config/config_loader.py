# config/config_loader.py

import yaml
from pathlib import Path


def load_config(path: str = "config/config.yaml") -> dict:
    """
    Load the pipeline configuration from a YAML file.

    Args:
        path: Relative or absolute path to the config YAML file.
              Defaults to 'config/config.yaml'.

    Returns:
        A dictionary containing all configuration values.

    Raises:
        FileNotFoundError: If the config file does not exist at the given path.
        yaml.YAMLError: If the file contains invalid YAML syntax.
    """
    config_path = Path(path)

    if not config_path.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {config_path.resolve()}\n"
            f"Make sure 'config/config.yaml' exists in the project root."
        )

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if config is None:
        raise ValueError(f"Configuration file is empty: {config_path}")

    _validate_config(config)

    return config


def _validate_config(config: dict) -> None:
    """
    Validate that required top-level configuration sections exist.

    Args:
        config: The loaded configuration dictionary.

    Raises:
        KeyError: If a required section is missing from the config.
    """
    required_sections = ["watcher", "sources", "logging"]

    for section in required_sections:
        if section not in config:
            raise KeyError(
                f"Missing required config section: '{section}'. "
                f"Please check your config/config.yaml file."
            )

    # Validate watcher section
    watcher = config["watcher"]
    required_watcher_keys = ["data_dir", "processed_dir", "file_patterns"]
    for key in required_watcher_keys:
        if key not in watcher:
            raise KeyError(
                f"Missing required key in 'watcher' section: '{key}'"
            )

    # Validate logging section
    logging_cfg = config["logging"]
    if "file" not in logging_cfg:
        raise KeyError("Missing required key in 'logging' section: 'file'")


def get_watcher_config(config: dict) -> dict:
    """
    Extract and return only the watcher section of the config.

    Args:
        config: The full configuration dictionary.

    Returns:
        The watcher configuration dictionary.
    """
    return config["watcher"]


def get_csv_config(config: dict) -> dict:
    """
    Extract and return the CSV source configuration.

    Args:
        config: The full configuration dictionary.

    Returns:
        The CSV source configuration dictionary.
    """
    return config["sources"]["csv"]


def get_logging_config(config: dict) -> dict:
    """
    Extract and return the logging configuration.

    Args:
        config: The full configuration dictionary.

    Returns:
        The logging configuration dictionary.
    """
    return config["logging"]


def is_source_enabled(config: dict, source: str) -> bool:
    """
    Check whether a specific data source is enabled in the configuration.

    Args:
        config: The full configuration dictionary.
        source: The source name to check — 'csv', 'database', or 'api'.

    Returns:
        True if the source is enabled, False otherwise.
    """
    return config.get("sources", {}).get(source, {}).get("enabled", False)