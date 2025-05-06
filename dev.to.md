---
title: "Create Your First Twitch Chat Bot with Python & TwitchIO: The !greet Command"
published: false # Set to true when you're ready to publish
description: "A beginner-friendly guide to building a simple Twitch chat bot using Python and the twitchio library that responds to a !greet command."
tags: ['python', 'twitch', 'chatbot', 'beginners', 'tutorial']
# cover_image: "URL_to_your_cover_image.png" # Optional: Add a cover image URL
---

Hey everyone! 👋

Ever wanted to make your Twitch stream a bit more interactive? Or maybe you're just curious about how Twitch bots work? You're in the right place! In this guide, we'll walk through creating a very simple Twitch chat bot using Python and a fantastic library called `twitchio`. By the end, you'll have a bot that can join your chat and respond with a friendly greeting when someone types `!greet`.

Let's dive in!

## What You'll Need (Prerequisites)

Before we start coding, make sure you have the following:

1.  **Python Installed:** This guide assumes you have Python 3.7 or newer. If not, head over to [python.org](https://www.python.org/downloads/) to download and install it.
2.  **A Twitch Account for Your Bot:** It's best practice to create a separate Twitch account for your bot (e.g., `YourStreamNameBot`).
3.  **Twitch Developer Application Credentials:**
    *   Go to the [Twitch Developer Console](https://dev.twitch.tv/console/apps).
    *   Log in with your **main** Twitch account (the one that owns the channel, or just any Twitch account to register an app).
    *   Click "Register Your Application".
        *   **Name:** Give your application a unique name (e.g., "MyGreetBotApp"). Avoid using the word "Twitch".
        *   **OAuth Redirect URLs:** Set this to `http://localhost:3000`. We won't use it directly for this simple bot's token, but it's a required field.
        *   **Category:** Choose "Chat Bot".
    *   Click "Create".
    *   You'll see your **Client ID**. Copy this somewhere safe.
    *   Click "New Secret" to generate a **Client Secret**. Copy this immediately and store it securely. You won't see it again!
4.  **Twitch OAuth Access Token:** This is what allows your bot to connect to Twitch chat and act on behalf of the bot account.
    *   **Scopes:** For our greet bot, we need the `chat:read` (to read messages) and `chat:edit` (to send messages) scopes.
    *   **Generating a Token:** For beginners, the easiest way to get a token for a simple bot is using a trusted online generator. A popular one is [TwitchTokenGenerator.com](https://twitchtokengenerator.com/).
        *   When using a generator, ensure you're granting permissions for your **BOT'S Twitch account**, not your personal one.
        *   Select the required scopes: `chat:read` and `chat:edit`.
        *   Generate the token and copy the **Access Token** (it will look like a long string of random characters). **Keep this secret and safe!**
5.  **The `twitchio` Library:** Open your terminal or command prompt and install `twitchio`:
    ```bash
    pip install twitchio
    ```

Phew! That's the setup done. Now for the fun part!

## Step 1: The Basic Bot Structure

Let's create a Python file, say `greet_bot.py`, and start with the basic structure.

```python
# greet_bot.py
from twitchio.ext import commands

# Configuration - Replace with your actual details!
TWITCH_ACCESS_TOKEN = 'YOUR_TWITCH_ACCESS_TOKEN'  # Starts with 'oauth:' if from some generators, or just the token string
BOT_NICKNAME = 'YOUR_BOT_TWITCH_USERNAME'         # Your bot's Twitch username
TARGET_CHANNEL = 'YOUR_TWITCH_CHANNEL_NAME'       # The channel you want the bot to join (e.g., your main Twitch username)

class Bot(commands.Bot):

    def __init__(self):
        # Initialize bot with access token, prefix, and initial channel to join
        super().__init__(token=TWITCH_ACCESS_TOKEN, 
                         prefix='!',  # Commands will start with '!'
                         initial_channels=[TARGET_CHANNEL])

    async def event_ready(self):
        # Called once the bot is successfully connected to Twitch IRC
        print(f"Logged in as | {self.nick}")
        print(f"User ID is | {self.user_id}")
        print(f"Successfully joined channel: {TARGET_CHANNEL}")

if __name__ == "__main__":
    bot = Bot()
    bot.run()
    # bot.run() is blocking and will run until the program is closed.
```

**Let's break this down:**

*   `from twitchio.ext import commands`: We import the necessary `commands` module from `twitchio`.
*   **Configuration Variables:**
    *   `TWITCH_ACCESS_TOKEN`: The OAuth token you generated. **Important:** Some token generators might give you a token that already includes `oauth:` at the beginning. If `twitchio` gives an authentication error, try with and without this prefix.
    *   `BOT_NICKNAME`: The Twitch username of your bot account.
    *   `TARGET_CHANNEL`: The Twitch channel name (lowercase) where the bot should operate.
*   `class Bot(commands.Bot):`: We define our bot class, inheriting from `twitchio.ext.commands.Bot`. This gives us all the base bot functionality.
*   `__init__(self)`: The constructor for our bot.
    *   `super().__init__(...)`: We call the parent class's constructor.
        *   `token=TWITCH_ACCESS_TOKEN`: This is your bot's "password" to connect to Twitch.
        *   `prefix='!'`: This tells `twitchio` that messages starting with `!` should be treated as potential commands. You can change this to `?`, `$`, etc.
        *   `initial_channels=[TARGET_CHANNEL]`: A list of channel names (strings) the bot should join when it starts.
*   `async def event_ready(self):`: This is a special `twitchio` event.
    *   It's an `async` function because `twitchio` is an asynchronous library, meaning it can do multiple things (like listen for messages and respond) efficiently without getting stuck.
    *   This event is triggered once the bot has successfully connected to Twitch and is ready to operate.
    *   We print some useful info to the console to confirm it's working.
*   `if __name__ == "__main__":`: This standard Python construct ensures the code inside only runs when the script is executed directly (not when imported as a module).
    *   `bot = Bot()`: We create an instance of our `Bot`.
    *   `bot.run()`: This starts the bot, connects to Twitch, and keeps it running to listen for messages and commands.

## Step 2: Creating the `!greet` Command

Now, let's add the command that will make our bot say hello.

Modify your `greet_bot.py` like this:

```python
# greet_bot.py
from twitchio.ext import commands
from twitchio import Context # Import Context for type hinting

# Configuration - Replace with your actual details!
TWITCH_ACCESS_TOKEN = 'YOUR_TWITCH_ACCESS_TOKEN'
BOT_NICKNAME = 'YOUR_BOT_TWITCH_USERNAME'
TARGET_CHANNEL = 'YOUR_TWITCH_CHANNEL_NAME'

class Bot(commands.Bot):

    def __init__(self):
        super().__init__(token=TWITCH_ACCESS_TOKEN, 
                         prefix='!', 
                         initial_channels=[TARGET_CHANNEL])

    async def event_ready(self):
        print(f"Logged in as | {self.nick}")
        print(f"User ID is | {self.user_id}")
        print(f"Successfully joined channel: {TARGET_CHANNEL}")

    # This is our new command!
    @commands.command(name="greet")
    async def greet_command(self, ctx: Context):
        # ctx (Context) contains information about the command invocation
        # For example, ctx.author.name is the name of the user who sent the command
        # ctx.channel.name is the channel where the command was sent
        
        # Send a message back to the channel where the command was issued
        await ctx.send(f"Hello {ctx.author.name}! Welcome to the stream! 👋")
        print(f"Sent a greeting to {ctx.author.name} in {ctx.channel.name}")


if __name__ == "__main__":
    bot = Bot()
    bot.run()
```

**What's new?**

*   `from twitchio import Context`: We import `Context` for type hinting, which is good practice.
*   `@commands.command(name="greet")`: This is a decorator. It tells `twitchio` that the following async function, `greet_command`, is a chat command.
    *   `name="greet"`: This sets the name of the command. So, users will type `!greet` to trigger it. If you omit `name="greet"`, the command name would be the function name (`greet_command` in this case, so `!greet_command`).
*   `async def greet_command(self, ctx: Context):`: This is the function that handles the command.
    *   It must be an `async` function.
    *   It takes `self` (as it's a method of a class) and `ctx` as arguments.
    *   `ctx` stands for "Context". It's an object provided by `twitchio` that contains a wealth of information about how the command was invoked:
        *   `ctx.author`: An object representing the user who sent the command (e.g., `ctx.author.name` is their username).
        *   `ctx.channel`: An object representing the channel where the command was sent.
        *   `ctx.message`: The raw message object.
    *   `await ctx.send(f"Hello {ctx.author.name}! Welcome to the stream! 👋")`: This is how the bot sends a message back to the same channel where the `!greet` command was used. We use an f-string to personalize the greeting with the user's name.

## Step 3: Running Your Bot

1.  **Save `greet_bot.py`** with your actual credentials filled in.
2.  **Open your terminal or command prompt.**
3.  **Navigate to the directory** where you saved the file.
4.  **Run the bot:**
    ```bash
    python greet_bot.py
    ```
5.  If everything is correct, you should see output in your terminal like:
    ```
    Logged in as | YOUR_BOT_TWITCH_USERNAME
    User ID is | 123456789 
    Successfully joined channel: YOUR_TWITCH_CHANNEL_NAME
    ```
6.  **Go to your Twitch channel's chat** (the one you set as `TARGET_CHANNEL`).
7.  **Type `!greet`** and hit Enter.

Your bot should respond with: "Hello `YourUsername`! Welcome to the stream! 👋"

(Optional: This is a great place for a GIF showing the bot in action!)

## Understanding Key `twitchio` Concepts

*   **`commands.Bot`**: The main class you'll use to build your bot. It handles connecting to Twitch, processing messages, and managing commands.
*   **`token`**: The OAuth token is crucial for authentication. It proves to Twitch that your bot has permission to connect and act.
*   **`prefix`**: A character (or string) that signals the start of a command (e.g., `!`, `?`, `mybot_`).
*   **`initial_channels`**: A list of channels the bot will automatically join upon startup.
*   **Events (`async def event_...`)**: `twitchio` uses events to notify your bot about things happening, like connecting (`event_ready`), receiving a message (`event_message`), a user joining, etc. You can define functions to handle these events.
*   **Commands (`@commands.command()`)**: A decorator that turns a regular Python async function into a chat command that users can trigger.
*   **`Context` (`ctx`)**: Passed to every command function, `Context` holds all relevant information about the command's invocation—who sent it, where, the message content, and methods to respond (like `ctx.send()`).
*   **`async` and `await`**: `twitchio` is built on Python's `asyncio` library. This allows your bot to handle many things (like listening to chat, responding to commands, and potentially other tasks) concurrently without getting bogged down. Any I/O operation (like sending a message or waiting for one) should generally be `await`ed.

## What's Next?

Congratulations! You've built your first Twitch bot! This is just the tip of the iceberg. From here, you could:

*   Add more simple commands.
*   Make the bot respond to keywords in chat (using the `event_message` event).
*   Store user data or scores.
*   Integrate with other APIs.

The `twitchio` [documentation](https://twitchio.dev/en/stable/) is an excellent resource for exploring more advanced features.

---

I hope this guide helped you get started with Twitch bot development! What other simple commands are you thinking of adding to your bot? Share your ideas in the comments below! Happy coding!