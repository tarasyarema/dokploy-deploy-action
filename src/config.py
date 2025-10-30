"""
Configuration file management for Dokploy CLI.
Handles loading and validating ~/.dokploy/deploy.yaml
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
import yaml


class ConfigError(Exception):
    """Raised when configuration is invalid or missing."""
    pass


class AppConfig:
    """Configuration for a single application."""

    def __init__(self, name: str, data: Dict[str, Any], defaults: Dict[str, Any]):
        self.name = name
        self.id = data.get('id')
        self.app_name = data.get('name')

        # Merge with defaults
        self.wait_for_completion = data.get('wait_for_completion', defaults.get('wait_for_completion', True))
        self.restart = data.get('restart', defaults.get('restart', False))
        self.debug = data.get('debug', defaults.get('debug', False))

        # Validate
        if not self.id:
            raise ConfigError(f"App '{name}' missing required field: 'id'")
        if not self.app_name:
            raise ConfigError(f"App '{name}' missing required field: 'name'")

    def __repr__(self):
        return f"AppConfig(name={self.name}, id={self.id}, app_name={self.app_name})"


class DokployConfig:
    """Main configuration loaded from ~/.dokploy/deploy.yaml"""

    DEFAULT_CONFIG_PATH = Path.home() / '.dokploy' / 'deploy.yaml'

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.dokploy_url: Optional[str] = None
        self.auth_token: Optional[str] = None
        self.defaults: Dict[str, Any] = {}
        self.apps: Dict[str, AppConfig] = {}

        if self.config_path.exists():
            self._load()
        else:
            raise ConfigError(
                f"Config file not found: {self.config_path}\n"
                f"Run 'dokdeploy init' to create it."
            )

    def _load(self):
        """Load and parse YAML config file."""
        try:
            with open(self.config_path, 'r') as f:
                data = yaml.safe_load(f)

            if not data:
                raise ConfigError("Config file is empty")

            # Load Dokploy settings
            dokploy = data.get('dokploy', {})
            self.dokploy_url = dokploy.get('url')
            self.auth_token = dokploy.get('auth_token')

            # Support environment variable expansion
            if self.auth_token and self.auth_token.startswith('$'):
                env_var = self.auth_token[1:]
                self.auth_token = os.getenv(env_var)
                if not self.auth_token:
                    raise ConfigError(f"Environment variable not set: {env_var}")

            if not self.dokploy_url:
                raise ConfigError("Missing required field: dokploy.url")
            if not self.auth_token:
                raise ConfigError("Missing required field: dokploy.auth_token")

            # Load defaults
            self.defaults = data.get('defaults', {})

            # Load apps
            apps_data = data.get('apps', {})
            if not apps_data:
                raise ConfigError("No apps defined in config file")

            for app_name, app_data in apps_data.items():
                self.apps[app_name] = AppConfig(app_name, app_data, self.defaults)

        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML in config file: {e}")
        except FileNotFoundError:
            raise ConfigError(f"Config file not found: {self.config_path}")
        except Exception as e:
            raise ConfigError(f"Failed to load config: {e}")

    def get_app(self, name: str) -> AppConfig:
        """Get app config by name."""
        if name not in self.apps:
            available = ', '.join(self.apps.keys())
            raise ConfigError(
                f"App '{name}' not found in config.\n"
                f"Available apps: {available}"
            )
        return self.apps[name]

    def list_apps(self) -> List[str]:
        """Get list of configured app names."""
        return list(self.apps.keys())

    @classmethod
    def create_template(cls, config_path: Optional[Path] = None):
        """Create template config file."""
        path = config_path or cls.DEFAULT_CONFIG_PATH
        path.parent.mkdir(parents=True, exist_ok=True)

        template = """# Dokploy Deployment Configuration
# Config file for dokdeploy CLI tool

dokploy:
  # Your Dokploy instance URL (no trailing slash)
  url: https://app.dokploy.com

  # API token (get from Dokploy dashboard → Settings → API Tokens)
  # Can be literal value or environment variable reference
  auth_token: $DOKPLOY_AUTH_TOKEN  # or put token directly here

# Default settings applied to all apps (can be overridden per-app)
defaults:
  wait_for_completion: true  # Wait for deployment to finish
  restart: false             # Restart app after deployment
  debug: false               # Enable debug logging

# Your applications
apps:
  # Example app configuration
  my-app:
    id: your-app-id-here           # From Dokploy dashboard
    name: your-app-name-here        # Application name
    # Inherits defaults unless overridden
    # wait_for_completion: true
    # restart: false

  # Add more apps:
  # api:
  #   id: abc123
  #   name: my-api
  #   restart: true
  #
  # worker:
  #   id: def456
  #   name: my-worker
  #   wait_for_completion: false
"""

        with open(path, 'w') as f:
            f.write(template)

        return path

    def validate(self) -> List[str]:
        """Validate configuration and return list of issues."""
        issues = []

        if not self.dokploy_url:
            issues.append("Missing dokploy.url")
        elif not self.dokploy_url.startswith('http'):
            issues.append(f"Invalid dokploy.url: {self.dokploy_url} (must start with http:// or https://)")

        if not self.auth_token:
            issues.append("Missing dokploy.auth_token")

        if not self.apps:
            issues.append("No apps defined")

        for name, app in self.apps.items():
            if not app.id:
                issues.append(f"App '{name}' missing id")
            if not app.app_name:
                issues.append(f"App '{name}' missing name")

        return issues


def load_config(config_path: Optional[Path] = None) -> DokployConfig:
    """Load configuration from file."""
    return DokployConfig(config_path)
