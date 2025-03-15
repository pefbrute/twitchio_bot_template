#!/usr/bin/env python3
import os
import sys
import webbrowser
import requests
import json
import time
from urllib.parse import urlparse, parse_qs

print("Twitch OAuth Token Setup Script for Moderator Bot")
print("=========================================================")

# Function to get user input
def get_input(prompt):
    return input(f"{prompt}: ").strip()

# Check for .env file and read data from it if it exists
env_data = {}
if os.path.exists('.env'):
    print("Found existing .env file. Reading data from it...")
    with open('.env', 'r') as file:
        for line in file:
            if '=' in line:
                key, value = line.strip().split('=', 1)
                env_data[key] = value
    print("Data from .env file loaded.")

# Get required data from user or from .env
client_id = env_data.get('CLIENT_ID') or get_input("Enter your Client ID")
client_secret = env_data.get('CLIENT_SECRET') or get_input("Enter your Client Secret")
bot_username = env_data.get('BOT_USERNAME') or get_input("Enter bot account name (NOT your main account)")
channel_name = env_data.get('CHANNEL_NAME') or get_input("Enter the channel name that the bot will moderate")

# Save to temporary .env
temp_env_data = {
    'BOT_USERNAME': bot_username,
    'CHANNEL_NAME': channel_name,
    'CLIENT_ID': client_id,
    'CLIENT_SECRET': client_secret,
}

# Generate authorization URL
scopes = 'chat:read+chat:edit+channel:moderate+moderator:manage:chat_messages+moderator:manage:banned_users+moderator:read:followers+whispers:edit+whispers:read+user:manage:whispers'
auth_url = f"https://id.twitch.tv/oauth2/authorize?response_type=code&client_id={client_id}&redirect_uri=http://localhost:3000&scope={scopes}&force_verify=true"

print("\n============ IMPORTANT ============")
print("1. Before continuing, LOG OUT of your main Twitch account")
print("2. Log in to the BOT account ({}) that will be the moderator".format(bot_username))
print("3. Make sure you've made the bot a moderator of your channel")
print("   To do this, type in your channel chat: /mod {}".format(bot_username))
print("============================\n")

input("After completing these steps, press Enter to continue...")

# Opening authorization URL in browser
print(f"\nOpening authorization URL. Log in to the BOT account ({bot_username}) and allow access.")
print(f"Authorization URL: {auth_url}")
webbrowser.open(auth_url)

# Wait for authorization code input
print("\nAfter authorization, you will be redirected to localhost with a 'This site can't be reached' error.")
print("Copy the entire URL from your browser's address bar (it contains the authorization code).")

redirect_url = get_input("Paste the full URL you were redirected to")

# Extract authorization code from URL
parsed_url = urlparse(redirect_url)
query_params = parse_qs(parsed_url.query)
auth_code = query_params.get('code', [None])[0]

if not auth_code:
    print("Error: Could not extract authorization code from URL.")
    sys.exit(1)

print(f"Authorization code obtained: {auth_code}")

# Exchange authorization code for tokens
print("\nExchanging authorization code for access tokens...")

token_url = "https://id.twitch.tv/oauth2/token"
payload = {
    'client_id': client_id,
    'client_secret': client_secret,
    'code': auth_code,
    'grant_type': 'authorization_code',
    'redirect_uri': 'http://localhost:3000'
}

try:
    response = requests.post(token_url, data=payload)
    response.raise_for_status()
    token_data = response.json()
    
    # Check if the response contains the required tokens
    if 'access_token' not in token_data or 'refresh_token' not in token_data:
        print("Error: Failed to get access tokens. Server response:")
        print(json.dumps(token_data, indent=2))
        sys.exit(1)
    
    access_token = token_data['access_token']
    refresh_token = token_data['refresh_token']
    scopes = token_data.get('scope', [])
    
    print("Tokens successfully obtained!")
    print(f"Access Token: {access_token[:10]}...{access_token[-5:]} (expires in: {token_data['expires_in']} seconds)")
    print(f"Refresh Token: {refresh_token[:10]}...{refresh_token[-5:]}")
    print(f"Obtained permissions (scopes): {', '.join(scopes)}")
    
    # Check if all required permissions are obtained
    required_scopes = ['chat:read', 'chat:edit', 'channel:moderate']
    missing_scopes = [scope for scope in required_scopes if scope not in scopes]
    
    if missing_scopes:
        print("\nWARNING: Not all required permissions were obtained!")
        print(f"Missing permissions: {', '.join(missing_scopes)}")
        print("The bot may not work correctly without these permissions.")
    
    # Save tokens to .env file
    temp_env_data['ACCESS_TOKEN'] = access_token
    temp_env_data['REFRESH_TOKEN'] = refresh_token
    
    # Validate token
    print("\nValidating obtained token...")
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    validate_response = requests.get('https://id.twitch.tv/oauth2/validate', headers=headers)
    
    if validate_response.status_code == 200:
        validate_data = validate_response.json()
        print(f"Token is valid! Authorized as: {validate_data.get('login')}")
        print(f"User ID: {validate_data.get('user_id')}")
        
        # Check if the token belongs to the bot, not the main account
        if validate_data.get('login') != bot_username.lower():
            print(f"\nWARNING! Token obtained for account {validate_data.get('login')}, not for bot {bot_username}!")
            print("This means you authorized with the wrong account.")
            print("It's recommended to clear your browser cookies and repeat the process, logging in with the bot account.")
            proceed = input("Do you want to continue anyway? (yes/no): ").lower()
            if proceed != 'yes':
                print("Operation cancelled by user.")
                sys.exit(1)
    else:
        print("Error validating token:")
        print(validate_response.text)
    
    # Save all data to .env file
    print("\nSaving data to .env file...")
    with open('.env', 'w') as env_file:
        for key, value in temp_env_data.items():
            env_file.write(f"{key}={value}\n")
        
        # If there's an OPENAI_API_KEY in the original .env, save it too
        if 'OPENAI_API_KEY' in env_data:
            env_file.write(f"OPENAI_API_KEY={env_data['OPENAI_API_KEY']}\n")
        else:
            openai_key = get_input("Enter your OpenAI API key (or leave empty if you don't have one)")
            if openai_key:
                env_file.write(f"OPENAI_API_KEY={openai_key}\n")
    
    print("\nSetup completed successfully! .env file created/updated.")
    print("Now you need to modify the bot code for proper message deletion.")
    
    # Instructions for code modification
    print("\nRECOMMENDED CHANGES IN BOT CODE:")
    print("Replace the corresponding part of the event_message method in main.py with:")
    print("""
    if is_spoiler:
        logger.info(f"Spoiler detected in message from {message.author.name}: {message.content}")
        logger.info(f"Message ID: {message.id}")
        
        try:
            # Correct way to delete messages in twitchio
            logger.info(f"Attempting to delete message with ID: {message.id}")
            await message.channel.send(f"/delete {message.id}")
            logger.info(f"Successfully sent delete command for message from {message.author.name}")
            
            # Notify about deletion reason
            await message.channel.send(f"@{message.author.name}, your message was deleted because it contains a spoiler.")
            logger.info(f"Notified user about spoiler message from {message.author.name}")
        except Exception as e:
            logger.error(f"Failed to delete message: {str(e)}")
            # Send warning if we can't delete
            await message.channel.send(f"@{message.author.name}, your message contains a spoiler! Please don't reveal spoilers in chat.")
            logger.info(f"Warned user about spoiler message from {message.author.name}")
    """)
    
except requests.exceptions.RequestException as e:
    print(f"Error requesting tokens: {e}")
    sys.exit(1) 