"""Configuration management for Telegram Signal Extractor"""
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
from dotenv import load_dotenv


class ConfigManager:
    """Manages application configuration from files and environment variables"""

    def __init__(self, config_path: Optional[str] = None, env_path: Optional[str] = None):
        """
        Initialize configuration manager

        Args:
            config_path: Path to config.yaml file
            env_path: Path to .env file
        """
        # Get project root
        self.project_root = Path(__file__).parent.parent.parent

        # Set config paths
        self.config_path = config_path or self.project_root / "config" / "config.yaml"
        self.env_path = env_path or self.project_root / ".env"

        # Load environment variables first (highest priority)
        load_dotenv(self.env_path)

        # Load configuration
        self.config = self._load_config()

        # Validate required fields
        self._validate_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file with environment variable overrides"""
        # Load YAML file
        if not Path(self.config_path).exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # Override with environment variables
        config = self._apply_env_overrides(config)

        return config

    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides to config"""
        # Telegram credentials from environment
        if 'telegram' not in config:
            config['telegram'] = {}

        if os.getenv('TELEGRAM_API_ID'):
            config['telegram']['api_id'] = int(os.getenv('TELEGRAM_API_ID'))

        if os.getenv('TELEGRAM_API_HASH'):
            config['telegram']['api_hash'] = os.getenv('TELEGRAM_API_HASH')

        if os.getenv('TELEGRAM_PHONE'):
            config['telegram']['phone'] = os.getenv('TELEGRAM_PHONE')

        if os.getenv('SESSION_NAME'):
            config['telegram']['session_name'] = os.getenv('SESSION_NAME')

        # Output paths from environment
        if os.getenv('CSV_OUTPUT_PATH'):
            if 'output' not in config:
                config['output'] = {}
            if 'csv' not in config['output']:
                config['output']['csv'] = {}
            config['output']['csv']['file_path'] = os.getenv('CSV_OUTPUT_PATH')

        if os.getenv('ERROR_LOG_PATH'):
            if 'output' not in config:
                config['output'] = {}
            if 'error_log' not in config['output']:
                config['output']['error_log'] = {}
            config['output']['error_log']['file_path'] = os.getenv('ERROR_LOG_PATH')

        # Extraction settings from environment
        if os.getenv('MIN_CONFIDENCE'):
            if 'extraction' not in config:
                config['extraction'] = {}
            config['extraction']['min_confidence'] = float(os.getenv('MIN_CONFIDENCE'))

        # Logging from environment
        if os.getenv('LOG_LEVEL'):
            if 'logging' not in config:
                config['logging'] = {}
            config['logging']['level'] = os.getenv('LOG_LEVEL')

        return config

    def _validate_config(self):
        """Validate that required configuration fields are present"""
        # Required Telegram fields
        required_telegram_fields = ['api_id', 'api_hash']
        if 'telegram' not in self.config:
            raise ValueError("Missing 'telegram' section in configuration")

        for field in required_telegram_fields:
            if field not in self.config['telegram']:
                raise ValueError(f"Missing required Telegram field: {field}")

        # Validate API ID is an integer
        try:
            int(self.config['telegram']['api_id'])
        except (ValueError, TypeError):
            raise ValueError("telegram.api_id must be a valid integer")

        # Validate channels exist
        channels = self.config.get('telegram', {}).get('channels', [])
        if not channels:
            raise ValueError("No channels configured. Add at least one channel to monitor.")

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation

        Args:
            key_path: Path to config value (e.g., "telegram.api_id")
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key_path.split('.')
        value = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def get_telegram_config(self) -> Dict[str, Any]:
        """Get Telegram configuration"""
        return self.config.get('telegram', {})

    def get_channels(self) -> List[Dict[str, Any]]:
        """Get list of channels to monitor"""
        return self.config.get('telegram', {}).get('channels', [])

    def get_enabled_channels(self) -> List[Dict[str, Any]]:
        """Get list of enabled channels"""
        return [ch for ch in self.get_channels() if ch.get('enabled', True)]

    def get_extraction_config(self) -> Dict[str, Any]:
        """Get extraction configuration"""
        return self.config.get('extraction', {})

    def get_output_config(self) -> Dict[str, Any]:
        """Get output configuration"""
        return self.config.get('output', {})

    def get_csv_path(self) -> Path:
        """Get CSV output file path"""
        csv_path = self.get('output.csv.file_path', 'output/signals.csv')
        path = Path(csv_path)

        # Make absolute if relative
        if not path.is_absolute():
            path = self.project_root / path

        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        return path

    def get_error_log_path(self) -> Path:
        """Get error log file path"""
        log_path = self.get('output.error_log.file_path', 'logs/extraction_errors.jsonl')
        path = Path(log_path)

        # Make absolute if relative
        if not path.is_absolute():
            path = self.project_root / path

        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        return path

    def get_session_path(self) -> Path:
        """Get Telegram session file path"""
        session_name = self.get('telegram.session_name', 'telegram_session')
        session_path = self.project_root / "sessions" / f"{session_name}.session"

        # Ensure sessions directory exists
        session_path.parent.mkdir(parents=True, exist_ok=True)

        return session_path

    def get_min_confidence(self) -> float:
        """Get minimum confidence threshold"""
        return self.get('extraction.min_confidence', 0.75)

    def get_symbol_mapping(self) -> Dict[str, str]:
        """Get symbol normalization mapping"""
        return self.get('extraction.symbol_mapping', {})

    def reload(self):
        """Reload configuration from file"""
        self.config = self._load_config()
        self._validate_config()
