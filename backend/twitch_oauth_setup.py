#!/usr/bin/env python3
import os
import sys
import webbrowser
import requests
import json
import time
from urllib.parse import urlparse, parse_qs

print("Скрипт настройки токенов Twitch OAuth для бота-модератора")
print("=========================================================")

# Функция для получения ввода пользователя
def get_input(prompt):
    return input(f"{prompt}: ").strip()

# Проверка наличия .env файла и чтение данных из него, если он существует
env_data = {}
if os.path.exists('.env'):
    print("Найден существующий файл .env. Чтение данных из него...")
    with open('.env', 'r') as file:
        for line in file:
            if '=' in line:
                key, value = line.strip().split('=', 1)
                env_data[key] = value
    print("Данные из .env файла загружены.")

# Получение необходимых данных от пользователя или из .env
client_id = env_data.get('CLIENT_ID') or get_input("Введите ваш Client ID")
client_secret = env_data.get('CLIENT_SECRET') or get_input("Введите ваш Client Secret")
bot_username = env_data.get('BOT_USERNAME') or get_input("Введите имя аккаунта бота (НЕ ваш основной аккаунт)")
channel_name = env_data.get('CHANNEL_NAME') or get_input("Введите имя канала, который будет модерировать бот")

# Сохраняем во временный .env
temp_env_data = {
    'BOT_USERNAME': bot_username,
    'CHANNEL_NAME': channel_name,
    'CLIENT_ID': client_id,
    'CLIENT_SECRET': client_secret,
}

# Генерация URL авторизации
scopes = 'chat:read+chat:edit+channel:moderate+moderator:manage:chat_messages+moderator:manage:banned_users+moderator:read:followers+whispers:edit+whispers:read+user:manage:whispers'
auth_url = f"https://id.twitch.tv/oauth2/authorize?response_type=code&client_id={client_id}&redirect_uri=http://localhost:3000&scope={scopes}&force_verify=true"

print("\n============ ВАЖНО ============")
print("1. Перед продолжением ВЫЙДИТЕ из своего основного аккаунта Twitch")
print("2. Войдите в аккаунт БОТА ({}), который будет модератором".format(bot_username))
print("3. Убедитесь, что вы назначили бота модератором вашего канала")
print("   Для этого напишите в чате вашего канала: /mod {}".format(bot_username))
print("============================\n")

input("После выполнения этих шагов нажмите Enter для продолжения...")

# Открываем URL авторизации в браузере
print(f"\nОткрывается URL для авторизации. Войдите в аккаунт БОТА ({bot_username}) и разрешите доступ.")
print(f"URL авторизации: {auth_url}")
webbrowser.open(auth_url)

# Ожидаем ввода кода авторизации
print("\nПосле авторизации вы будете перенаправлены на localhost с ошибкой 'This site can't be reached'.")
print("Скопируйте весь URL из адресной строки браузера (он содержит код авторизации).")

redirect_url = get_input("Вставьте полный URL, на который вы были перенаправлены")

# Извлечение кода авторизации из URL
parsed_url = urlparse(redirect_url)
query_params = parse_qs(parsed_url.query)
auth_code = query_params.get('code', [None])[0]

if not auth_code:
    print("Ошибка: Не удалось извлечь код авторизации из URL.")
    sys.exit(1)

print(f"Код авторизации получен: {auth_code}")

# Обмен кода авторизации на токены
print("\nОбмен кода авторизации на токены доступа...")

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
    
    # Проверяем, что в ответе есть необходимые токены
    if 'access_token' not in token_data or 'refresh_token' not in token_data:
        print("Ошибка: Не удалось получить токены доступа. Ответ сервера:")
        print(json.dumps(token_data, indent=2))
        sys.exit(1)
    
    access_token = token_data['access_token']
    refresh_token = token_data['refresh_token']
    scopes = token_data.get('scope', [])
    
    print("Токены успешно получены!")
    print(f"Access Token: {access_token[:10]}...{access_token[-5:]} (срок действия: {token_data['expires_in']} секунд)")
    print(f"Refresh Token: {refresh_token[:10]}...{refresh_token[-5:]}")
    print(f"Полученные разрешения (scopes): {', '.join(scopes)}")
    
    # Проверяем, что получены все необходимые разрешения
    required_scopes = ['chat:read', 'chat:edit', 'channel:moderate']
    missing_scopes = [scope for scope in required_scopes if scope not in scopes]
    
    if missing_scopes:
        print("\nВНИМАНИЕ: Не получены все необходимые разрешения!")
        print(f"Отсутствуют разрешения: {', '.join(missing_scopes)}")
        print("Бот может работать некорректно без этих разрешений.")
    
    # Сохраняем токены в .env файл
    temp_env_data['ACCESS_TOKEN'] = access_token
    temp_env_data['REFRESH_TOKEN'] = refresh_token
    
    # Проверяем валидность токена
    print("\nПроверка валидности полученного токена...")
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    validate_response = requests.get('https://id.twitch.tv/oauth2/validate', headers=headers)
    
    if validate_response.status_code == 200:
        validate_data = validate_response.json()
        print(f"Токен действителен! Авторизован как: {validate_data.get('login')}")
        print(f"User ID: {validate_data.get('user_id')}")
        
        # Проверяем, что токен принадлежит боту, а не основному аккаунту
        if validate_data.get('login') != bot_username.lower():
            print(f"\nВНИМАНИЕ! Токен получен для аккаунта {validate_data.get('login')}, а не для бота {bot_username}!")
            print("Это означает, что вы авторизовались под неправильным аккаунтом.")
            print("Рекомендуется очистить куки браузера и повторить процесс, войдя под аккаунтом бота.")
            proceed = input("Хотите продолжить несмотря на это? (да/нет): ").lower()
            if proceed != 'да':
                print("Операция прервана пользователем.")
                sys.exit(1)
    else:
        print("Ошибка при валидации токена:")
        print(validate_response.text)
    
    # Сохраняем все данные в .env файл
    print("\nСохранение данных в файл .env...")
    with open('.env', 'w') as env_file:
        for key, value in temp_env_data.items():
            env_file.write(f"{key}={value}\n")
        
        # Если есть OPENAI_API_KEY в оригинальном .env, сохраняем его тоже
        if 'OPENAI_API_KEY' in env_data:
            env_file.write(f"OPENAI_API_KEY={env_data['OPENAI_API_KEY']}\n")
        else:
            openai_key = get_input("Введите ваш ключ OpenAI API (или оставьте пустым, если его нет)")
            if openai_key:
                env_file.write(f"OPENAI_API_KEY={openai_key}\n")
    
    print("\nНастройка успешно завершена! Файл .env создан/обновлен.")
    print("Теперь необходимо исправить код бота для правильного удаления сообщений.")
    
    # Инструкции по редактированию кода
    print("\nРЕКОМЕНДУЕМЫЕ ИЗМЕНЕНИЯ В КОДЕ БОТА:")
    print("Замените соответствующую часть метода event_message в main.py на:")
    print("""
    if is_spoiler:
        logger.info(f"Spoiler detected in message from {message.author.name}: {message.content}")
        logger.info(f"Message ID: {message.id}")
        
        try:
            # Правильный способ удаления сообщений в twitchio
            logger.info(f"Attempting to delete message with ID: {message.id}")
            await message.channel.send(f"/delete {message.id}")
            logger.info(f"Successfully sent delete command for message from {message.author.name}")
            
            # Уведомляем о причине удаления
            await message.channel.send(f"@{message.author.name}, ваше сообщение было удалено, так как оно содержит спойлер.")
            logger.info(f"Notified user about spoiler message from {message.author.name}")
        except Exception as e:
            logger.error(f"Failed to delete message: {str(e)}")
            # Отправляем предупреждение, если не можем удалить
            await message.channel.send(f"@{message.author.name}, ваше сообщение содержит спойлер! Пожалуйста, не раскрывайте спойлеры в чате.")
            logger.info(f"Warned user about spoiler message from {message.author.name}")
    """)
    
except requests.exceptions.RequestException as e:
    print(f"Ошибка при запросе токенов: {e}")
    sys.exit(1) 