from typing import Dict

import yaml


_ENV_MAPPING = {
    'BOT_TOKEN': 'bot_token',
    'USER_ID': 'user_id',
}


def _load_config_file(file: str):
    with open(file) as f:
        content = f.read()
        return yaml.load(content, Loader=yaml.CLoader)


def load_config(config_path: str, environment: Dict[str, str]):
    config = _load_config_file(config_path)

    for env_key, conf_key in _ENV_MAPPING.items():
        if env_key in environment and environment[env_key]:
            config[conf_key] = environment[env_key]

    return config
