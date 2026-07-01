import yaml
import os
from dotenv import load_dotenv

load_dotenv()

DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'settings.yaml')


def load_config(config_path=None):
    # Resolution order: explicit arg -> MINUTETRADER_CONFIG env var ->
    # settings.yaml co-located with this module. No machine-specific absolute
    # paths, so the bot runs on any host or CI runner.
    config_path = config_path or os.environ.get('MINUTETRADER_CONFIG', DEFAULT_CONFIG_PATH)
    if not os.path.exists(config_path):
        return {}
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Environment variable overrides (optional but recommended for secrets)
    # This is a simple implementation, can be more robust
    return config

def get_exchange_config(config, exchange_name):
    exchanges = config.get('exchanges', {})
    return exchanges.get(exchange_name, {})
