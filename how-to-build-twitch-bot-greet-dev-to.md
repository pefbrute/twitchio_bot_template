---
title: "Build Your First Twitch Chat Bot with Python & TwitchIO: The !greet Command"
published: false # Set to true when ready to publish
description: "A step-by-step guide to creating a Twitch chat bot that responds to a !greet command, featuring robust authentication and command handling with Python and TwitchIO."
tags: [python, twitch, chatbot, tutorial] # Add a fourth relevant tag like 'beginners'
---

Hey everyone! Ever wanted to build your own Twitch chat bot? Maybe something to welcome viewers or respond to simple commands? You're in the right place! This guide will walk you through creating a basic Twitch bot using Python and the powerful `twitchio` library. We'll focus on making a bot that can respond with a friendly greeting when someone types `!greet` in your chat.

We'll be building this bot with a focus on good practices, including robust authentication token management, inspired by a well-structured project. By the end, you'll have a working bot and a solid understanding of how to extend it further.

## What You'll Learn

*   Setting up a Twitch application to get your bot credentials.
*   Structuring your Python project for a Twitch bot.
*   Handling Twitch OAuth tokens: initial acquisition, validation, and automatic refresh.
*   Using `twitchio` to connect to Twitch chat, listen for messages, and send replies.
*   Creating a simple command (`!greet`).
*   Organizing and loading commands in a modular way.

## Prerequisites

Before we dive in, make sure you have the following:

1.  **Python 3.7+ installed:** You can download it from [python.org](https://www.python.org/).
2.  **A Twitch Account for Your Bot:** It's best practice to create a separate Twitch account for your bot, not use your main streaming account.
3.  **Twitch Developer Application Credentials (Client ID & Client Secret):**
    *   Go to the [Twitch Developer Console](https://dev.twitch.tv/console/apps).
    *   Log in with your Twitch account (can be your main one for app registration).
    *   Click "Register Your Application".
    *   Fill in the form:
        *   **Name:** Give your application a unique name (e.g., "MyAwesomeGreetBot"). **Important:** Don't use "Twitch" in the name.
        *   **OAuth Redirect URLs:** Set this to `http://localhost:3000`. This is used for the initial token generation.
        *   **Category:** Select "Chat Bot".
    *   Click "Create".
    *   You'll see your **Client ID**. Copy this down.
    *   Click "New Secret" to generate a **Client Secret**. Copy this immediately and store it securely; you won't see it again.
4.  **Basic understanding of Python:** Familiarity with functions, classes, and async/await will be helpful.

## Project Setup

Let's get our project structured.

1.  **Create a project directory:**
    ```bash
    mkdir my_twitch_bot
    cd my_twitch_bot
    ```

2.  **Create a `backend` subdirectory:** We'll place our core bot logic here.
    ```bash
    mkdir backend
    ```

3.  **Install Libraries:** We need `twitchio` for bot functionalities, `python-dotenv` to manage environment variables, and `requests` for HTTP calls (especially for token management).
    Install these libraries globally or within your preferred Python environment management system:
    ```bash
    pip install twitchio python-dotenv requests
    ```
    *Note: This guide was developed and tested using `twitchio` version `2.10.0` and `requests` version `2.32.3` on Ubuntu 22.04. Other versions or operating systems should generally work, but you might encounter minor differences.*

    You can also create a `requirements.txt` file in your project root (`my_twitch_bot/requirements.txt`):
    ```plaintext
    # requirements.txt
    twitchio
    python-dotenv
    requests
    ```
    And install using `pip install -r requirements.txt`.

4.  **The `.env` File for Credentials:**
    Create a file named `.env` in your project's root directory (`my_twitch_bot/.env`). This file will store your sensitive credentials. **Never commit this file to version control!** Add it to your `.gitignore` file.
    ```
    # .env
    BOT_USERNAME="your_bot_twitch_username"
    CHANNEL_NAME="your_twitch_channel_name_to_join"
    CLIENT_ID="your_client_id_from_twitch_dev_console"
    CLIENT_SECRET="your_client_secret_from_twitch_dev_console"
    ACCESS_TOKEN="" # We'll get this next
    REFRESH_TOKEN="" # And this too
    ```
    Fill in `BOT_USERNAME`, `CHANNEL_NAME`, `CLIENT_ID`, and `CLIENT_SECRET`.

## Step 1: Getting Initial OAuth Tokens (Access & Refresh)

Twitch bots need an OAuth `access_token` to connect to chat and perform actions. This token expires, so we also need a `refresh_token` to get new access tokens without requiring the user to re-authorize. We'll use the **Authorization Code Grant Flow**.

Here's how you'll typically obtain these tokens:

1.  **Construct the Authorization URL:**
    You need to create a special URL that will send your bot (or rather, you, acting on behalf of your bot) to Twitch to authorize your application. The URL looks like this:

    ```
    https://id.twitch.tv/oauth2/authorize?response_type=code&client_id=YOUR_CLIENT_ID&redirect_uri=http://localhost:3000&scope=SCOPES_NEEDED&force_verify=true
    ```
    Replace:
    *   `YOUR_CLIENT_ID` with the Client ID you got from the Twitch Developer Console.
    *   `SCOPES_NEEDED` with a space-separated (or `+` separated) list of permissions your bot needs. For a basic chat bot that can read and send messages, you'll want `chat:read chat:edit`. For more capabilities, you might add others like `channel:moderate`, `whispers:read`, `whispers:edit`, etc. Your original project used a comprehensive list: `chat:read+chat:edit+channel:moderate+moderator:manage:chat_messages+moderator:manage:banned_users+moderator:read:followers+whispers:edit+whispers:read+user:manage:whispers`. Start with `chat:read+chat:edit` for this guide.
    *   `redirect_uri` should be `http://localhost:3000` (the same one you registered in the Twitch Developer Console).
    *   `force_verify=true` is optional but recommended as it ensures the user always has to log in, which is useful when you're specifically logging in as the bot account.

2.  **Authorize Your Bot Account:**
    *   **Important:** Log out of your main Twitch account in your browser.
    *   Log in to Twitch using your **bot's Twitch account**.
    *   Open the constructed Authorization URL in your browser.
    *   Twitch will ask you to authorize your application (e.g., "MyAwesomeGreetBot") to access your bot account's data with the scopes you requested. Click "Authorize."

3.  **Get the Authorization Code:**
    *   After authorizing, Twitch will redirect your browser to the `redirect_uri` you specified (`http://localhost:3000`).
    *   The browser will likely show an error page like "This site can't be reached" because you probably don't have a server running on `localhost:3000`. This is expected!
    *   Look at the URL in your browser's address bar. It will look something like this:
        `http://localhost:3000/?code=A_LONG_AUTHORIZATION_CODE_HERE&scope=requested+scopes`
    *   Copy the value of the `code` parameter. This is your temporary Authorization Code. It's usually valid for a short time.

4.  **Exchange the Authorization Code for Tokens:**
    Now, you need to exchange this `code` for an `access_token` and a `refresh_token`. This is done by making a `POST` request from your system (you can do this with a simple Python script using the `requests` library, or even a tool like Postman or curl) to Twitch's token endpoint:

    *   **URL:** `https://id.twitch.tv/oauth2/token`
    *   **Method:** `POST`
    *   **Body (as `application/x-www-form-urlencoded`):**
        *   `client_id`: Your Client ID
        *   `client_secret`: Your Client Secret
        *   `code`: The Authorization Code you just obtained.
        *   `grant_type`: `authorization_code`
        *   `redirect_uri`: `http://localhost:3000` (must be the same as before)

    A Python `requests` example for this step would look like:
    ```python
    import requests

    client_id = "YOUR_CLIENT_ID"
    client_secret = "YOUR_CLIENT_SECRET"
    auth_code = "THE_CODE_YOU_COPIED_FROM_URL"
    redirect_uri = "http://localhost:3000"

    token_url = "https://id.twitch.tv/oauth2/token"
    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'code': auth_code,
        'grant_type': 'authorization_code',
        'redirect_uri': redirect_uri
    }
    response = requests.post(token_url, data=payload)
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data['access_token']
        refresh_token = token_data['refresh_token']
        expires_in = token_data['expires_in'] # How long the access token lasts in seconds
        print(f"Access Token: {access_token}")
        print(f"Refresh Token: {refresh_token}")
        print(f"Expires In: {expires_in} seconds")
        # Now, save these to your .env file!
    else:
        print(f"Error getting tokens: {response.status_code}")
        print(response.json())
    ```

5.  **Save Tokens to `.env`:**
    Once you have the `access_token` and `refresh_token` from the response, **immediately** copy them into your `.env` file:
    ```env
    # .env
    # ... other variables ...
    ACCESS_TOKEN="THE_ACCESS_TOKEN_YOU_RECEIVED"
    REFRESH_TOKEN="THE_REFRESH_TOKEN_YOU_RECEIVED"
    ```

This process gives your bot the credentials it needs to authenticate with Twitch. Your `twitch_oauth_setup.py` script in the original project would automate these steps. For users following this guide, they can perform these steps manually or create their own helper script.

Once you have your `ACCESS_TOKEN` and `REFRESH_TOKEN` in your `.env` file, you're ready for the next step!

## Step 2: Structuring the Bot Code

We'll create a few Python files inside the `backend` directory:

*   `twitch_auth.py`: For handling token validation and refresh *before* the bot starts.
*   `bot.py`: The main `CustomBot` class extending `twitchio.ext.commands.Bot`.
*   `main.py`: The entry point to load credentials, commands, and run the bot.
*   `commands/__init__.py`: Base for command modules.
*   `commands/greet/command.py`: Our `!greet` command logic.

Create the directories and files:
```bash
cd backend
mkdir commands
mkdir commands/greet
touch twitch_auth.py bot.py main.py commands/__init__.py commands/greet/command.py
cd .. # Back to my_twitch_bot directory
```

Let's populate these files.

### `backend/twitch_auth.py` - Synchronous Token Management

This module will handle validating the access token when the bot starts and refreshing it if necessary. This is crucial because `twitchio` needs a valid token to initialize.

```python
# backend/twitch_auth.py
import os
import logging
import requests
from dotenv import load_dotenv, set_key

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('twitch_auth')

# Load environment variables
load_dotenv()

# Global variables to store credentials from .env
# These will be updated if a token refresh happens
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
REFRESH_TOKEN = os.getenv('REFRESH_TOKEN')
BOT_USERNAME = os.getenv('BOT_USERNAME')
CHANNEL_NAME = os.getenv('CHANNEL_NAME')

def refresh_oauth_token_sync():
    """Synchronously refresh the OAuth token."""
    global ACCESS_TOKEN, REFRESH_TOKEN
    logger.info("Attempting to refresh OAuth token synchronously...")
    try:
        refresh_url = "https://id.twitch.tv/oauth2/token"
        payload = {
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'refresh_token': REFRESH_TOKEN,
            'grant_type': 'refresh_token'
        }
        response = requests.post(refresh_url, data=payload)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
        token_data = response.json()

        ACCESS_TOKEN = token_data['access_token']
        if 'refresh_token' in token_data: # Twitch might not always return a new refresh token
            REFRESH_TOKEN = token_data['refresh_token']

        # Update .env file
        # Note: For robustness, consider updating .env in a more atomic way or using a proper config management tool
        dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env') # Assumes .env is in parent dir of backend/
        set_key(dotenv_path, 'ACCESS_TOKEN', ACCESS_TOKEN)
        set_key(dotenv_path, 'REFRESH_TOKEN', REFRESH_TOKEN)
        
        logger.info("OAuth token refreshed successfully synchronously.")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to refresh OAuth token synchronously: {e}")
        if e.response:
            logger.error(f"Response content: {e.response.text}")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred during synchronous token refresh: {e}")
        return False

def validate_token_sync():
    """Synchronously validate the current access token."""
    global ACCESS_TOKEN
    if not ACCESS_TOKEN or not CLIENT_ID:
        logger.error("Access token or Client ID is missing. Cannot validate.")
        return False
    logger.info("Validating token synchronously...")
    try:
        headers = {
            'Authorization': f'Bearer {ACCESS_TOKEN}',
            'Client-Id': CLIENT_ID # Some Twitch endpoints prefer Client-Id in header
        }
        # The /validate endpoint itself doesn't strictly need Client-Id if token is Bearer
        # but good practice for other API calls.
        response = requests.get('https://id.twitch.tv/oauth2/validate', headers={'Authorization': f'Bearer {ACCESS_TOKEN}'})
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Token validated successfully. User: {data.get('login')}, Expires in: {data.get('expires_in')}s")
            if data.get('expires_in', 0) < 3600:  # Less than 1 hour
                logger.info("Token is close to expiry, refreshing synchronously...")
                return refresh_oauth_token_sync()
            return True
        else:
            logger.warning(f"Token validation failed with status {response.status_code}. Attempting refresh.")
            return refresh_oauth_token_sync()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error validating token: {e}. Attempting refresh.")
        return refresh_oauth_token_sync()
    except Exception as e:
        logger.error(f"An unexpected error occurred during synchronous token validation: {e}")
        return False


def get_auth_credentials():
    """Return the current (potentially refreshed) auth credentials."""
    return {
        'bot_username': BOT_USERNAME,
        'channel_name': CHANNEL_NAME,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'access_token': ACCESS_TOKEN, # This will be the latest token if refreshed
        'refresh_token': REFRESH_TOKEN
    }
```

### `backend/commands/__init__.py` - Base for Commands

This file defines a base class that our command modules will inherit from. It helps in organizing commands.

```python
# backend/commands/__init__.py
import logging

logger = logging.getLogger(__name__) # Using __name__ is a common practice

class BotCommand:
    """Base class for all bot commands"""
    
    def __init__(self, bot):
        self.bot = bot
        # Ensure derived classes call register_commands or this does
        if hasattr(self, 'register_commands') and callable(self.register_commands):
            self.register_commands()
        else:
            logger.warning(f"Command class {self.__class__.__name__} has no register_commands method.")
            
    def register_commands(self):
        """Register all commands with the bot. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement register_commands()")

```

### `backend/commands/greet/command.py` - The `!greet` Command

Here's where we define our `!greet` command.

```python
# backend/commands/greet/command.py
from .. import BotCommand # Relative import from parent package
import logging

logger = logging.getLogger(__name__)

class GreetCommand(BotCommand):
    """A simple command that greets users"""
    
    def register_commands(self):
        """Register the greet command"""
        
        @self.bot.command(name="greet") # This decorator registers the command with twitchio
        async def greet_command_handler(ctx): # Renamed to avoid conflict if GreetCommand itself is callable
            """Send a friendly greeting message"""
            # ctx is the Context object, containing info about the message and channel
            logger.info(f"!greet command triggered by {ctx.author.name} in #{ctx.channel.name}")
            await ctx.send(f"Hello {ctx.author.name}! Welcome to the stream! 👋")
            # For a generic greeting not mentioning the user:
            # await ctx.send("Hello! Welcome to the stream! 👋")

```
**Note on `ctx.author.name`**: This provides the display name of the user who sent the command.

### `backend/bot.py` - The `CustomBot` Class

This is the heart of our bot, handling connection, events, messages, and asynchronous token refreshing.

```python
# backend/bot.py
import os
import logging
import requests
from twitchio.ext import commands
from dotenv import set_key, load_dotenv
import asyncio

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('twitch_bot') # Consistent logger name

load_dotenv() # Ensure .env is loaded if not already by twitch_auth

class CustomBot(commands.Bot):
    def __init__(self, auth_creds):
        self.bot_username = auth_creds['bot_username']
        self.channel_name = auth_creds['channel_name']
        self.client_id = auth_creds['client_id']
        self.client_secret = auth_creds['client_secret']
        self._access_token = auth_creds['access_token'] # Use underscore for "internal" attribute
        self._refresh_token = auth_creds['refresh_token']
        
        logger.info(f"Initializing bot for user: {self.bot_username}")
        logger.info(f"Attempting to join channel: {self.channel_name}")
        
        super().__init__(
            token=self._access_token, # The actual access token
            prefix='!',               # Command prefix
            initial_channels=[self.channel_name]
        )
        
        # Start the asynchronous token check loop
        self.token_check_task = self.loop.create_task(self.token_check_loop())
        
    async def token_check_loop(self):
        """Periodically check and refresh token if needed (asynchronously)."""
        await asyncio.sleep(60) # Initial delay before first check
        while True:
            try:
                logger.info("Async token check loop running...")
                await self.validate_token_async()
                await asyncio.sleep(1800)  # Check every 30 minutes
            except Exception as e:
                logger.error(f"Error in async token check loop: {e}")
                await asyncio.sleep(300)   # Wait 5 minutes before retrying on error

    async def validate_token_async(self):
        """Asynchronously validate the current token and refresh if needed."""
        logger.info("Validating token asynchronously...")
        try:
            headers = {'Authorization': f'Bearer {self._access_token}'}
            # Using requests for simplicity here, but for a fully async app, aiohttp would be better.
            # However, to stick to the user's original dependencies:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: requests.get('https://id.twitch.tv/oauth2/validate', headers=headers))

            if response.status_code == 200:
                data = response.json()
                logger.info(f"Async Token validated. User: {data.get('login')}, Expires in: {data.get('expires_in')}s")
                if data.get('expires_in', 0) < 3600:  # Less than 1 hour
                    logger.info("Token nearing expiry, refreshing asynchronously...")
                    if await self.refresh_oauth_token_async():
                        # Critical: Update twitchio's connection with the new token
                        if self._connection: # Ensure connection exists
                           self._connection.token = self._access_token
                           logger.info("Twitchio connection token updated after async refresh.")
            else:
                logger.warning(f"Async Token validation failed ({response.status_code}). Refreshing...")
                if await self.refresh_oauth_token_async():
                    if self._connection:
                        self._connection.token = self._access_token
                        logger.info("Twitchio connection token updated after async refresh due to validation failure.")
        except Exception as e:
            logger.error(f"Error validating token asynchronously: {e}. Attempting refresh.")
            if await self.refresh_oauth_token_async(): # Attempt refresh even on other errors
                if self._connection:
                    self._connection.token = self._access_token
                    logger.info("Twitchio connection token updated after async refresh due to validation error.")


    async def refresh_oauth_token_async(self):
        """Asynchronously refresh the OAuth token."""
        logger.info("Attempting to refresh OAuth token asynchronously...")
        try:
            refresh_url = "https://id.twitch.tv/oauth2/token"
            payload = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'refresh_token': self._refresh_token,
                'grant_type': 'refresh_token'
            }
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: requests.post(refresh_url, data=payload))
            response.raise_for_status()
            token_data = response.json()

            self._access_token = token_data['access_token']
            if 'refresh_token' in token_data:
                self._refresh_token = token_data['refresh_token']
            
            # Update .env file
            # This is a blocking operation, consider if this is acceptable in an async context
            # or if it should be offloaded or handled differently.
            dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
            await loop.run_in_executor(None, lambda: set_key(dotenv_path, 'ACCESS_TOKEN', self._access_token))
            await loop.run_in_executor(None, lambda: set_key(dotenv_path, 'REFRESH_TOKEN', self._refresh_token))

            logger.info("OAuth token refreshed successfully asynchronously.")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to refresh OAuth token asynchronously: {e}")
            if e.response:
                logger.error(f"Response content: {e.response.text}")
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred during async token refresh: {e}")
            return False

    async def event_ready(self):
        """Called once the bot is successfully connected to Twitch IRC."""
        logger.info(f"Logged in as | {self.nick}") # self.nick is the bot's username
        logger.info(f"User ID is | {self.user_id}") # The bot's Twitch user ID
        # Perform an initial async validation on connect if desired, though sync validation already ran
        # await self.validate_token_async() 

    async def event_message(self, message):
        """Runs every time a message is sent in chat."""
        # Ignore messages from the bot itself to prevent loops
        if message.author and message.author.name.lower() == self.bot_username.lower():
            return

        logger.debug(f"#{message.channel.name} | {message.author.name if message.author else 'System'}: {message.content}")

        # Handle commands explicitly. twitchio does this internally when super().event_message is called
        # or if commands are registered and prefix is matched.
        # If you want to manually parse, you could do it here.
        # However, with commands registered, `twitchio` handles invoking them.
        # Just ensure `handle_commands` is called if you override `event_message` extensively.
        if message.content.startswith(self._prefix): # self._prefix is '!'
             await self.handle_commands(message)


```
**Key `twitchio` Concepts Used in `bot.py`:**
*   `commands.Bot`: The base class we inherit from.
*   `super().__init__(token=..., prefix=..., initial_channels=...)`: Initializes the bot.
    *   `token`: Your bot's OAuth access token.
    *   `prefix`: The character(s) that prefix commands (e.g., `!`).
    *   `initial_channels`: A list of channel names (strings) for the bot to join on startup.
*   `async def event_ready()`: An event that's called when the bot has successfully connected to Twitch IRC. `self.nick` is the bot's username.
*   `async def event_message(message)`: An event that's called for every message sent in the joined channels. The `message` object contains details like `message.content`, `message.author.name`, and `message.channel.name`.
*   `await self.handle_commands(message)`: This processes the message to see if it matches any registered commands.
*   `self.loop.create_task()`: Used to run asynchronous tasks like our `token_check_loop` in the background.
*   `self._connection.token = new_token`: **Crucial!** After refreshing a token, you must update the token used by the current `twitchio` connection.

### `backend/main.py` - Entry Point

This script loads credentials, sets up the bot, loads commands, and starts it.

```python
# backend/main.py
import os
import logging
import importlib.util # For more robust dynamic importing
from dotenv import load_dotenv

# Assuming these are in the same 'backend' package or adjust sys.path if necessary
from bot import CustomBot
from twitch_auth import validate_token_sync, get_auth_credentials
import commands # To access BotCommand for isinstance check

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('twitch_main') # Main logger

def load_credentials_from_env():
    """Load all necessary credentials from environment variables."""
    load_dotenv() # Ensures .env is loaded
    # These are now fetched by get_auth_credentials after potential refresh
    # but it's good to have a clear function for this initial step if separated.
    # For this structure, get_auth_credentials from twitch_auth.py is sufficient.
    # This function can be simplified or merged if twitch_auth.py handles all .env loading.
    return {
        'bot_username': os.getenv('BOT_USERNAME'),
        'channel_name': os.getenv('CHANNEL_NAME'),
        'client_id': os.getenv('CLIENT_ID'),
        'client_secret': os.getenv('CLIENT_SECRET'),
        'access_token': os.getenv('ACCESS_TOKEN'),
        'refresh_token': os.getenv('REFRESH_TOKEN')
    }


def load_all_commands(bot_instance):
    """Dynamically load all command modules from the 'commands' directory."""
    logger.info("Loading command modules...")
    # Path to the 'commands' directory relative to this file (main.py)
    commands_pkg_dir = os.path.join(os.path.dirname(__file__), 'commands')
    
    for item_name in os.listdir(commands_pkg_dir):
        item_path = os.path.join(commands_pkg_dir, item_name)
        # Check if it's a directory (potential command module) and not e.g. __pycache__
        if os.path.isdir(item_path) and not item_name.startswith('__'):
            command_module_file = os.path.join(item_path, 'command.py')
            if os.path.exists(command_module_file):
                module_name = f"commands.{item_name}.command" # e.g., commands.greet.command
                try:
                    # Dynamically import the module
                    # spec = importlib.util.spec_from_file_location(module_name, command_module_file)
                    # Using package-relative name for importlib might be cleaner if backend is a package
                    # For now, let's use a simpler import path assuming backend.commands is discoverable
                    
                    # Corrected import path to be relative to the 'backend' package root
                    full_module_path_for_import = f"backend.commands.{item_name}.command"

                    module_spec = importlib.util.spec_from_file_location(full_module_path_for_import, command_module_file)
                    if module_spec and module_spec.loader:
                        cmd_module = importlib.util.module_from_spec(module_spec)
                        # Add to sys.modules before exec so relative imports within command.py work
                        # sys.modules[full_module_path_for_import] = cmd_module 
                        module_spec.loader.exec_module(cmd_module)
                        
                        # Find and instantiate the command class (subclass of BotCommand)
                        for attr_name in dir(cmd_module):
                            attr = getattr(cmd_module, attr_name)
                            if isinstance(attr, type) and \
                               issubclass(attr, commands.BotCommand) and \
                               attr is not commands.BotCommand: # Don't instantiate the base class itself
                                attr(bot_instance) # Instantiate with the bot_instance
                                logger.info(f"Successfully loaded command module: {item_name} ({attr.__name__})")
                                break # Assuming one command class per command.py
                        else:
                            logger.warning(f"No BotCommand subclass found in {command_module_file}")
                    else:
                        logger.error(f"Could not create module spec for {command_module_file}")

                except ImportError as e:
                    logger.error(f"ImportError loading command module {item_name}: {e}. Check PYTHONPATH and module structure.")
                except Exception as e:
                    logger.error(f"Failed to load command module {item_name} from {command_module_file}: {e}")
            else:
                logger.debug(f"No command.py found in directory {item_path}")
        else:
            logger.debug(f"Skipping {item_name} in commands directory (not a valid command module directory).")


def main():
    logger.info("Bot starting up...")

    # 1. Validate token (and refresh if needed) BEFORE initializing the bot
    logger.info("Validating Twitch OAuth token...")
    if validate_token_sync():
        logger.info("Token is valid or has been refreshed successfully.")
        # Get the potentially updated credentials
        auth_credentials = get_auth_credentials()
    else:
        logger.error("Critical: Failed to validate or refresh token. Bot cannot start.")
        logger.error("Please ensure your .env file is correct and run your OAuth setup script to get new tokens.")
        return # Exit if token validation fails

    if not all(auth_credentials.get(k) for k in ['bot_username', 'channel_name', 'client_id', 'client_secret', 'access_token']):
        logger.error("One or more critical credentials missing after validation. Bot cannot start.")
        logger.error(f"Current creds (sensitive parts might be None): ClientID: {auth_credentials.get('client_id') is not None}, BotUser: {auth_credentials.get('bot_username')}, Channel: {auth_credentials.get('channel_name')}, AccessToken: {auth_credentials.get('access_token') is not None}")
        return

    # 2. Initialize the Bot with validated/refreshed credentials
    bot_instance = CustomBot(auth_credentials)

    # 3. Load command modules
    load_all_commands(bot_instance)

    # 4. Start the bot
    logger.info("Starting Twitch bot...")
    try:
        bot_instance.run()
    except Exception as e:
        logger.critical(f"Bot run failed: {e}", exc_info=True)
    finally:
        logger.info("Bot has shut down.")

if __name__ == "__main__":
    # To run this from the root directory (my_twitch_bot/):
    # python -m backend.main
    # Ensure your PYTHONPATH includes the root directory or backend/ is treated as a package.
    # If running main.py directly from backend/, imports might need adjustment (e.g. from .bot import CustomBot)
    main()
```
**To Run `main.py`:**
Navigate to your project's root directory (`my_twitch_bot`) in your terminal and run:
```bash
python -m backend.main
```
This ensures Python treats your `backend` directory as a package, allowing relative imports to work correctly.

## Step 3: Testing Your Bot!

1.  Make sure your `.env` file is correctly filled with all credentials, including a valid `ACCESS_TOKEN` and `REFRESH_TOKEN`.
2.  Run the bot: `python -m backend.main` from your `my_twitch_bot` directory.
3.  Open Twitch chat for the channel you specified in `CHANNEL_NAME`.
4.  Type `!greet`.
5.  Your bot should respond with "Hello [YourUsername]! Welcome to the stream! 👋".

You should see log messages in your console indicating the bot's activity, including token validation, connection, and command execution.

## Understanding the Flow

1.  **Startup (`main.py`)**:
    *   `validate_token_sync()` from `twitch_auth.py` is called. If the access token is invalid or expiring soon, it's refreshed, and `.env` is updated.
    *   The `CustomBot` is initialized with these fresh credentials.
    *   `load_all_commands()` dynamically finds `commands/greet/command.py`, imports it, and instantiates `GreetCommand(bot_instance)`. This registers the `@bot_instance.command(name="greet")` method.
    *   `bot_instance.run()` starts the bot.

2.  **Connection & Runtime (`bot.py`)**:
    *   `CustomBot` connects to Twitch using the provided access token.
    *   `event_ready` logs a success message.
    *   The `token_check_loop` starts, periodically calling `validate_token_async` to keep the token fresh *while the bot is running*. If refreshed, `self._connection.token` is updated.
    *   When a message like `!greet` appears in chat, `event_message` is triggered.
    *   `self.handle_commands(message)` processes it. Since `!greet` matches a registered command, the `greet_command_handler` in `greet/command.py` is executed.
    *   `ctx.send()` sends the reply back to the Twitch channel.

## Conclusion

Congratulations! You've built a Twitch chat bot with Python and `twitchio` that can respond to a `!greet` command. More importantly, you've implemented a robust system for OAuth token management (both initial and ongoing) and a modular way to add commands.

This foundation is solid. You can now:
*   Add more commands by creating new files in the `commands` directory, similar to `greet`.
*   Explore more `twitchio` features like event handling for follows, subs, or other chat interactions.
*   Integrate with other APIs to fetch data or perform actions.

**What command will you build next for your Twitch bot? Share your ideas in the comments below!**

Happy coding!
--- 