"""Telegram client wrapper using Telethon"""
import asyncio
import logging
from typing import Callable, List, Optional
from pathlib import Path

from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError
from telethon.tl.types import User


logger = logging.getLogger(__name__)


class TelegramListener:
    """Wrapper around Telegram client for monitoring channels"""

    def __init__(self, api_id: int, api_hash: str, session_path: Path):
        """
        Initialize Telegram listener

        Args:
            api_id: Telegram API ID
            api_hash: Telegram API Hash
            session_path: Path to session file
        """
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_path = session_path

        # Create client
        self.client = TelegramClient(
            str(session_path),
            self.api_id,
            self.api_hash
        )

        self.connected = False
        self.channels: List[str] = []
        self._message_handlers: List[Callable] = []

    async def authenticate(self, phone: Optional[str] = None, code_callback=None, password_callback=None):
        """
        Authenticate with Telegram

        Args:
            phone: Phone number (with country code, e.g., +1234567890)
            code_callback: Optional async function that returns the verification code (for GUI)
            password_callback: Optional async function that returns the 2FA password (for GUI)

        Raises:
            ValueError: If phone number is required but not provided
            SessionPasswordNeededError: If 2FA is enabled (not yet supported)
        """
        if not await self.client.is_user_authorized():
            logger.info("Not authorized, starting authentication...")

            if phone is None:
                raise ValueError("Phone number required for first-time authentication")

            # Send code request
            logger.info(f"Sending code request to {phone}")
            await self.client.send_code_request(phone)

            # Get code from user
            if code_callback:
                code = await code_callback()
            else:
                # Fallback to console input (only works in console mode)
                try:
                    code = input("Enter the code you received: ")
                except (EOFError, OSError):
                    raise RuntimeError("Cannot read verification code - no console available")

            try:
                # Sign in with code
                await self.client.sign_in(phone, code)
                logger.info("Successfully authenticated!")

            except SessionPasswordNeededError:
                # 2FA is enabled
                if password_callback:
                    password = await password_callback()
                    await self.client.sign_in(password=password)
                    logger.info("Successfully authenticated with 2FA!")
                else:
                    logger.error("2FA is enabled but no password callback provided")
                    raise

        else:
            logger.info("Already authorized, using existing session")

        # Get current user info
        me: User = await self.client.get_me()
        logger.info(f"Logged in as: {me.first_name} ({me.phone})")

    async def connect(self, phone: Optional[str] = None, code_callback=None, password_callback=None):
        """
        Connect to Telegram

        Args:
            phone: Phone number for authentication if needed
            code_callback: Optional async function that returns verification code
            password_callback: Optional async function that returns 2FA password

        Raises:
            ConnectionError: If connection fails
        """
        try:
            logger.info("Connecting to Telegram...")
            await self.client.connect()

            # Authenticate if needed
            await self.authenticate(phone, code_callback, password_callback)

            self.connected = True
            logger.info("Successfully connected to Telegram")

        except Exception as e:
            logger.error(f"Failed to connect to Telegram: {e}")
            self.connected = False
            raise ConnectionError(f"Telegram connection failed: {e}")

    async def disconnect(self):
        """Disconnect from Telegram"""
        if self.connected:
            logger.info("Disconnecting from Telegram...")
            await self.client.disconnect()
            self.connected = False
            logger.info("Disconnected from Telegram")

    def add_channel(self, channel_username: str):
        """
        Add a channel to monitor

        Args:
            channel_username: Channel username (without @)
        """
        # Remove @ if present
        if channel_username.startswith('@'):
            channel_username = channel_username[1:]

        if channel_username not in self.channels:
            self.channels.append(channel_username)
            logger.info(f"Added channel to monitor: @{channel_username}")

    def remove_channel(self, channel_username: str):
        """
        Remove a channel from monitoring

        Args:
            channel_username: Channel username (without @)
        """
        if channel_username.startswith('@'):
            channel_username = channel_username[1:]

        if channel_username in self.channels:
            self.channels.remove(channel_username)
            logger.info(f"Removed channel from monitoring: @{channel_username}")

    def on_new_message(self, handler: Callable):
        """
        Register a handler for new messages

        Args:
            handler: Async function to call when new message arrives
                     Should accept (message, channel) parameters
        """
        self._message_handlers.append(handler)
        logger.info(f"Registered message handler: {handler.__name__}")

    async def start_monitoring(self):
        """Start monitoring channels for new messages"""
        if not self.connected:
            raise RuntimeError("Not connected to Telegram. Call connect() first.")

        if not self.channels:
            raise ValueError("No channels to monitor. Add channels with add_channel()")

        logger.info(f"Starting to monitor {len(self.channels)} channel(s): {', '.join(self.channels)}")

        # Register event handler
        @self.client.on(events.NewMessage(chats=self.channels))
        async def handle_new_message(event):
            try:
                message = event.message
                chat = await event.get_chat()

                channel_username = getattr(chat, 'username', 'unknown')
                logger.debug(f"New message from @{channel_username}: {message.id}")

                # Call all registered handlers
                for handler in self._message_handlers:
                    try:
                        await handler(message, chat)
                    except Exception as e:
                        logger.error(f"Error in message handler {handler.__name__}: {e}", exc_info=True)

            except Exception as e:
                logger.error(f"Error processing new message: {e}", exc_info=True)

        logger.info("Message monitoring started. Press Ctrl+C to stop.")

    async def run_until_disconnected(self):
        """Run the client until disconnected"""
        await self.client.run_until_disconnected()

    async def get_channel_info(self, channel_username: str) -> dict:
        """
        Get information about a channel

        Args:
            channel_username: Channel username

        Returns:
            Dictionary with channel information
        """
        if channel_username.startswith('@'):
            channel_username = channel_username[1:]

        try:
            entity = await self.client.get_entity(channel_username)
            return {
                'id': entity.id,
                'title': getattr(entity, 'title', ''),
                'username': getattr(entity, 'username', ''),
                'participants_count': getattr(entity, 'participants_count', None)
            }
        except Exception as e:
            logger.error(f"Failed to get info for @{channel_username}: {e}")
            return {}

    async def test_channel_access(self, channel_username: str) -> bool:
        """
        Test if we can access a channel

        Args:
            channel_username: Channel username

        Returns:
            True if channel is accessible, False otherwise
        """
        try:
            info = await self.get_channel_info(channel_username)
            if info:
                logger.info(f"Successfully accessed channel: @{channel_username}")
                return True
            return False
        except Exception as e:
            logger.error(f"Cannot access channel @{channel_username}: {e}")
            return False
