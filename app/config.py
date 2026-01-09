# Import libraries
import os
import yaml

# Load config.yaml for multiple use
config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
with open(config_path) as f:
    full_config = yaml.safe_load(f)
config = full_config[full_config.get("current_env")]
