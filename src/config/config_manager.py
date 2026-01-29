"""Configuration management for Telegram Signal Extractor"""
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
from dotenv import load_dotenv


class ConfigManager:
    """Manages application configuration from files and environment variables"""

    @staticmethod
    def _get_base_path() -> Path:
        """
        Get the base path for config files
        Works for both development and PyInstaller bundle
        """
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            # Use the directory containing the executable
            return Path(sys.executable).parent
        else:
            # Running in development
            return Path(__file__).parent.parent.parent

    def __init__(self, config_path: Optional[str] = None, env_path: Optional[str] = None, validate: bool = True):
        """
        Initialize configuration manager

        Args:
            config_path: Path to config.yaml file
            env_path: Path to .env file
            validate: Whether to validate config (set False for GUI to handle gracefully)
        """
        # Get project root (handle both development and PyInstaller bundle)
        self.project_root = self._get_base_path()

        # Set config paths
        self.config_path = config_path or self.project_root / "config" / "config.yaml"
        self.env_path = env_path or self.project_root / "config" / ".env"

        # Load environment variables first (highest priority)
        load_dotenv(self.env_path)

        # Load configuration
        self.config = self._load_config()

        # Validate required fields (optional for GUI)
        if validate:
            self._validate_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file with environment variable overrides"""
        # Load YAML file or create default config
        if not Path(self.config_path).exists():
            # Create default configuration
            config = self._get_default_config()

            # Try to save default config for future use
            try:
                self.config_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            except Exception:
                # If we can't write, just use the default in memory
                pass
        else:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

        # Override with environment variables
        config = self._apply_env_overrides(config)

        return config

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'telegram': {
                'api_id': '',  # Will be set via environment variables
                'api_hash': '',  # Will be set via environment variables
                'phone': '',  # Will be set via environment variables
                'session_name': 'telegram_signal_session',
                'channels': [
                    {
                        'username': 'nickalphatrader',
                        'enabled': True,
                        'description': 'Nick Alpha Trader signals'
                    },
                    {
                        'username': 'GaryGoldLegacy',
                        'enabled': True,
                        'description': 'Gary Gold Legacy signals'
                    }
                ]
            },
            'extraction': {
                'min_confidence': 0.75,
                'confidence_weights': {
                    'symbol': 0.25,
                    'direction': 0.25,
                    'entry': 0.20,
                    'stop_loss': 0.15,
                    'take_profit': 0.15
                },
                'symbol_mapping': {
                    'GOLD': 'XAUUSD',
                    'Gold': 'XAUUSD',
                    'XAU/USD': 'XAUUSD',
                    'XAUUSD': 'XAUUSD',
                    'EUR/USD': 'EURUSD',
                    'EURUSD': 'EURUSD',
                    'GBP/USD': 'GBPUSD',
                    'GBPUSD': 'GBPUSD',
                    'BTC/USD': 'BTCUSD',
                    'BTCUSD': 'BTCUSD'
                }
            },
            'output': {
                'csv': {
                    'file_path': '%APPDATA%\\MetaQuotes\\Terminal\\Common\\Files\\TelegramSignals\\signals.csv',
                    'encoding': 'utf-8',
                    'append_mode': True,
                    'fields': [
                        'message_id',
                        'channel_username',
                        'timestamp',
                        'symbol',
                        'direction',
                        'entry_price',
                        'entry_price_min',
                        'entry_price_max',
                        'stop_loss',
                        'take_profit_1',
                        'take_profit_2',
                        'take_profit_3',
                        'take_profit_4',
                        'confidence_score',
                        'raw_message',
                        'extracted_at'
                    ]
                },
                'error_log': {
                    'file_path': 'logs/extraction_errors.jsonl',
                    'max_bytes': 10485760,
                    'backup_count': 5
                }
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'console': {
                    'enabled': True,
                    'level': 'INFO'
                },
                'file': {
                    'enabled': True,
                    'level': 'DEBUG',
                    'file_path': 'logs/app.log',
                    'max_bytes': 10485760,
                    'backup_count': 5
                }
            },
            'server': {
                'enabled': True,
                'host': '0.0.0.0',
                'port': 4726,
                'max_signal_age_hours': 24
            }
        }

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

    def is_valid(self) -> tuple[bool, str]:
        """
        Check if configuration is valid without raising exceptions

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            self._validate_config()
            return True, ""
        except ValueError as e:
            return False, str(e)

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
        """Get extraction configuration with channel confidence from channels list"""
        extraction_config = self.config.get('extraction', {}).copy()

        # Build channel_confidence dict from channels list
        channel_confidence = {}
        for channel in self.get_channels():
            username = channel.get('username')
            confidence = channel.get('confidence', 1.0)
            if username:
                channel_confidence[username] = confidence

        extraction_config['channel_confidence'] = channel_confidence
        return extraction_config

    def get_output_config(self) -> Dict[str, Any]:
        """Get output configuration"""
        return self.config.get('output', {})

    def get_csv_path(self) -> Path:
        """Get CSV output file path"""
        csv_path = self.get('output.csv.file_path', 'output/signals.csv')

        # Expand environment variables (e.g., %TEMP% on Windows)
        csv_path = os.path.expandvars(csv_path)
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

        # Expand environment variables (e.g., %TEMP% on Windows)
        log_path = os.path.expandvars(log_path)
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

    def add_channel(self, username: str, description: str = None, confidence: float = 1.0):
        """
        Add a new channel to the configuration

        Args:
            username: Channel username (without @)
            description: Optional description for the channel
            confidence: Channel confidence multiplier (0.0-1.0)
        """
        if username.startswith('@'):
            username = username[1:]

        # Check if channel already exists
        channels = self.get_channels()
        for channel in channels:
            if channel.get('username', '').lower() == username.lower():
                # Channel already exists, just enable it
                channel['enabled'] = True
                channel['confidence'] = confidence
                self._save_config()
                return

        # Add new channel
        new_channel = {
            'username': username,
            'enabled': True,
            'confidence': confidence,
            'description': description or f'{username} signals'
        }

        if 'telegram' not in self.config:
            self.config['telegram'] = {}
        if 'channels' not in self.config['telegram']:
            self.config['telegram']['channels'] = []

        self.config['telegram']['channels'].append(new_channel)
        self._save_config()

    def update_channel(self, username: str, description: str = None, confidence: float = None, enabled: bool = None):
        """
        Update an existing channel's configuration

        Args:
            username: Channel username (without @)
            description: New description (optional)
            confidence: New confidence multiplier (optional)
            enabled: New enabled state (optional)
        """
        if username.startswith('@'):
            username = username[1:]

        channels = self.get_channels()
        for channel in channels:
            if channel.get('username', '').lower() == username.lower():
                if description is not None:
                    channel['description'] = description
                if confidence is not None:
                    channel['confidence'] = confidence
                if enabled is not None:
                    channel['enabled'] = enabled
                self._save_config()
                return True
        return False

    def _save_config(self):
        """Save configuration to YAML file"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)
        except Exception as e:
            # Log the error but don't raise - config is still valid in memory
            import logging
            logging.getLogger(__name__).error(f"Failed to save config: {e}")

    def reload(self):
        """Reload configuration from file"""
        self.config = self._load_config()
        self._validate_config()
