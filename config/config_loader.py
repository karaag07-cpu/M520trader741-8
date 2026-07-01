import re
import yaml
import os
from dotenv import load_dotenv

load_dotenv()

DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'settings.yaml')

_ENV_PATTERN = re.compile(r'\$\{([^}]+)\}')


def _expand_env_vars(obj):
    """Recursively expand ``${VAR}`` placeholders from the environment.

    Secrets live in the environment (or a .env file), never in settings.yaml.
    An unset variable expands to an empty string so downstream truthiness
    checks (e.g. ``if cfg.get('api_key')``) correctly treat it as absent and
    fall back to mock data instead of using a literal ``${VAR}`` string.
    """
    if isinstance(obj, dict):
        return {k: _expand_env_vars(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_expand_env_vars(v) for v in obj]
    if isinstance(obj, str):
        return _ENV_PATTERN.sub(lambda m: os.environ.get(m.group(1), ''), obj)
    return obj


def load_config(config_path=None):
    # Resolution order: explicit arg -> MINUTETRADER_CONFIG env var ->
    # settings.yaml co-located with this module. No machine-specific absolute
    # paths, so the bot runs on any host or CI runner.
    config_path = config_path or os.environ.get('MINUTETRADER_CONFIG', DEFAULT_CONFIG_PATH)
    if not os.path.exists(config_path):
        return {}

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f) or {}

    # Resolve ${VAR} secret placeholders from the environment.
    return _expand_env_vars(config)

def get_exchange_config(config, exchange_name):
    exchanges = config.get('exchanges', {})
    return exchanges.get(exchange_name, {})
