import yaml
import os
from dotenv import load_dotenv

load_dotenv()

def load_config(config_path='/home/team/shared/trading_bot/config/settings.yaml'):
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
