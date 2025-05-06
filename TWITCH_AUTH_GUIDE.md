# Руководство по Авторизации и Обновлению Токенов Twitch OAuth2

Это руководство объясняет процесс авторизации вашего бота на Twitch с использованием OAuth2 и последующее обновление токенов доступа. Понимание этого процесса важно для создания стабильных ботов, которые могут взаимодействовать с API Twitch от имени пользователя (в данном случае, вашего бота).

## Общая схема авторизации Twitch OAuth2 (Authorization Code Grant Flow)

Этот метод является наиболее распространенным и безопасным для серверных приложений, таких как ваш Twitch-бот.

### Шаг 1: Регистрация приложения на Twitch Developer Console

1.  **Перейдите на [Twitch Developer Console](https://dev.twitch.tv/console/apps).**
2.  **Войдите в свой аккаунт Twitch.** (Это может быть ваш основной аккаунт, регистрация приложения не привязывает его к боту напрямую).
3.  **Нажмите "Register Your Application".**
4.  **Заполните форму:**
    *   **Name:** Имя вашего приложения/бота (например, "MyCoolBot"). **Важно:** Не используйте слово "twitch" в названии.
    *   **OAuth Redirect URLs:** Укажите `http://localhost:3000`. Это URI, на который Twitch перенаправит пользователя после успешной авторизации. Даже если ваш бот работает на сервере, для первоначального получения токена часто используется `localhost`.
    *   **Category:** Выберите "Chat Bot" или другую подходящую категорию.
5.  **Нажмите "Create".**
6.  **Сохраните Client ID.** Он будет отображен сразу.
7.  **Нажмите "New Secret", чтобы сгенерировать Client Secret.** **ВАЖНО:** Скопируйте и сохраните Client Secret немедленно. Вы не сможете увидеть его снова.

    *   `Client ID`: Публичный идентификатор вашего приложения.
    *   `Client Secret`: Конфиденциальный ключ, используемый для аутентификации вашего приложения. **Никогда не делитесь им и не встраивайте его в клиентский код.**

### Шаг 2: Авторизация пользователя (получение Authorization Code)

1.  **Сформируйте URL авторизации.** Ваш бот должен перенаправить пользователя (в данном случае, владельца бота, который логинится под аккаунтом бота) на этот URL.
    ```
    https://id.twitch.tv/oauth2/authorize
        ?client_id=<ВАШ_CLIENT_ID>
        &redirect_uri=http://localhost:3000
        &response_type=code
        &scope=<СПИСОК_ПРАВ_ЧЕРЕЗ_ПРОБЕЛ_ИЛИ_ЗНАК_ПЛЮС>
        &force_verify=true  // (Опционально) Заставляет пользователя всегда вводить учетные данные
    ```
    *   **`client_id`**: Ваш Client ID.
    *   **`redirect_uri`**: Тот же `http://localhost:3000`, который вы указали при регистрации приложения.
    *   **`response_type=code`**: Указывает, что вы запрашиваете Authorization Code.
    *   **`scope`**: Список запрашиваемых прав (permissions). Например:
        *   `chat:read` - чтение сообщений чата
        *   `chat:edit` - отправка сообщений в чат
        *   `channel:moderate` - модерация канала (таймауты, баны)
        *   `whispers:read` - чтение личных сообщений
        *   `whispers:edit` - отправка личных сообщений
        *   Полный список прав доступен в [документации Twitch](https://dev.twitch.tv/docs/authentication/scopes/). Ваш скрипт `twitch_oauth_setup.py` использует: `chat:read+chat:edit+channel:moderate+moderator:manage:chat_messages+moderator:manage:banned_users+moderator:read:followers+whispers:edit+whispers:read+user:manage:whispers`.

2.  **Пользователь переходит по URL.** Пользователь (вы, войдя под аккаунтом бота) должен открыть этот URL в браузере. Twitch запросит разрешение на предоставление вашему приложению указанных прав.
3.  **Twitch перенаправляет на `redirect_uri` с Authorization Code.** После успешной авторизации Twitch перенаправит браузер на:
    `http://localhost:3000/?code=<АВТОРИЗАЦИОННЫЙ_КОД>&scope=<ПОЛУЧЕННЫЕ_ПРАВА>`
    *   `<АВТОРИЗАЦИОННЫЙ_КОД>`: Это временный код, который вы будете использовать для получения токенов.

### Шаг 3: Обмен Authorization Code на Access Token и Refresh Token

1.  **Ваше приложение (серверная часть или скрипт `twitch_oauth_setup.py`) делает POST-запрос** на эндпоинт токенов Twitch:
    ```
    POST https://id.twitch.tv/oauth2/token
    ```
    **Тело запроса (form-data):**
    ```
    client_id=<ВАШ_CLIENT_ID>
    &client_secret=<ВАШ_CLIENT_SECRET>
    &code=<АВТОРИЗАЦИОННЫЙ_КОД_ИЗ_ШАГА_2>
    &grant_type=authorization_code
    &redirect_uri=http://localhost:3000
    ```

2.  **Twitch отвечает JSON-объектом, содержащим токены:**
    ```json
    {
      "access_token": "НОВЫЙ_ACCESS_TOKEN",
      "refresh_token": "НОВЫЙ_REFRESH_TOKEN",
      "expires_in": 14000, // Время жизни access_token в секундах
      "scope": ["chat:read", "chat:edit"],
      "token_type": "bearer"
    }
    ```
    *   **`access_token`**: Используется для аутентифицированных запросов к API Twitch. Он имеет ограниченный срок действия.
    *   **`refresh_token`**: Используется для получения нового `access_token` без необходимости повторной авторизации пользователя. **Храните его надежно!**
    *   **`expires_in`**: Время жизни `access_token`.

    **Сохраните `access_token` и `refresh_token`** (например, в `.env` файле), они понадобятся вашему боту для работы.

## Валидация и Обновление Токенов

### Валидация Access Token

Перед использованием `access_token` или периодически во время работы бота, полезно проверять его валидность.
Вы можете сделать GET-запрос:
```
GET https://id.twitch.tv/oauth2/validate
```
**Headers:**
```
Authorization: Bearer <ВАШ_ACCESS_TOKEN>
```
Если токен валиден, Twitch вернет `200 OK` и информацию о токене, включая `expires_in` (оставшееся время жизни). Если токен невалиден или истек, будет ошибка (например, `401 Unauthorized`).

### Обновление Access Token с помощью Refresh Token

Когда `access_token` истекает (или близок к истечению), его необходимо обновить, используя `refresh_token`.

1.  **Ваше приложение делает POST-запрос** на эндпоинт токенов Twitch:
    ```
    POST https://id.twitch.tv/oauth2/token
    ```
    **Тело запроса (form-data):**
    ```
    grant_type=refresh_token
    &refresh_token=<ВАШ_REFRESH_TOKEN>
    &client_id=<ВАШ_CLIENT_ID>
    &client_secret=<ВАШ_CLIENT_SECRET>
    ```

2.  **Twitch отвечает новым `access_token` (и, возможно, новым `refresh_token`):**
    ```json
    {
      "access_token": "СВЕЖИЙ_ACCESS_TOKEN",
      "refresh_token": "ОБНОВЛЕННЫЙ_ИЛИ_СТАРЫЙ_REFRESH_TOKEN", // Twitch может вернуть новый refresh_token
      "expires_in": 14000,
      "scope": ["chat:read", "chat:edit"],
      "token_type": "bearer"
    }
    ```
    **Сохраните новый `access_token` и новый `refresh_token` (если он изменился).**

## Как это реализовано в вашем проекте (с `twitchio`)

Ваш проект использует библиотеку `twitchio` и кастомные скрипты для управления этим процессом.

### 1. Первоначальная настройка (`twitch_oauth_setup.py`)

Этот скрипт автоматизирует Шаги 1-3 общего процесса:
*   Запрашивает `Client ID`, `Client Secret`, имя бота и имя канала.
*   Формирует URL авторизации и открывает его в браузере.
*   Просит вас скопировать URL после редиректа (чтобы извлечь `Authorization Code`).
*   Обменивает `Authorization Code` на `access_token` и `refresh_token`.
*   Валидирует полученный `access_token`.
*   Сохраняет все учетные данные, включая токены, в файл `.env`.

### 2. Загрузка учетных данных и проверка токена перед запуском бота (`main.py` и `twitch_auth.py`)

*   **`main.py` -> `load_credentials()`**: Загружает `CLIENT_ID`, `CLIENT_SECRET`, `ACCESS_TOKEN`, `REFRESH_TOKEN` и другие данные из `.env`.
*   **`main.py` -> `validate_token_sync()` (из `twitch_auth.py`)**:
    *   Вызывается перед инициализацией бота.
    *   **`twitch_auth.py` -> `validate_token_sync()`**:
        *   Делает запрос к `https://id.twitch.tv/oauth2/validate` с текущим `ACCESS_TOKEN`.
        *   Если токен валиден и не истекает в ближайший час, возвращает `True`.
        *   Если токен невалиден, истек или скоро истечет, вызывает `refresh_oauth_token_sync()`.
    *   **`twitch_auth.py` -> `refresh_oauth_token_sync()`**:
        *   Делает POST-запрос к `https://id.twitch.tv/oauth2/token` с `grant_type=refresh_token`.
        *   Получает новые `ACCESS_TOKEN` и `REFRESH_TOKEN`.
        *   Обновляет глобальные переменные `ACCESS_TOKEN` и `REFRESH_TOKEN` в модуле `twitch_auth`.
        *   Обновляет значения `ACCESS_TOKEN` и `REFRESH_TOKEN` в файле `.env` с помощью `set_key`.
        *   Возвращает `True` в случае успеха.
*   **`main.py`**: Если `validate_token_sync()` вернул `False`, бот не запускается. Иначе, получает обновленные учетные данные через `get_auth_credentials()` из `twitch_auth.py`.

### 3. Инициализация бота и автоматическое обновление токена (`bot.py`)

*   **`bot.py` -> `CustomBot.__init__()`**:
    *   Сохраняет полученные учетные данные (включая актуальный `access_token` после синхронной проверки/обновления).
    *   Вызывает `super().__init__(token=self._access_token, ...)`, передавая `access_token` в конструктор `twitchio.ext.commands.Bot`. Библиотека `twitchio` будет использовать этот токен для своих внутренних IRC-соединений и API-запросов.
    *   Запускает асинхронную задачу `self.loop.create_task(self.token_check_loop())`.

*   **`bot.py` -> `CustomBot.token_check_loop()`**:
    *   Это бесконечный цикл, который выполняется в фоновом режиме.
    *   Каждые 30 минут (1800 секунд) вызывает `self.validate_token()`.
    *   В случае ошибки ждет 5 минут перед повторной попыткой.

*   **`bot.py` -> `CustomBot.validate_token()` (асинхронный)**:
    *   Аналогичен `validate_token_sync()` из `twitch_auth.py`, но асинхронный.
    *   Делает GET-запрос к `https://id.twitch.tv/oauth2/validate`.
    *   Если токен валиден и `expires_in < 3600` (меньше часа), или если токен невалиден, вызывает `self.refresh_oauth_token()`.
    *   Если токен был успешно обновлен (`self.refresh_oauth_token()` вернул `True`), то обновляет токен в текущем соединении бота: `self._connection.token = self._access_token`. Это важно, чтобы `twitchio` использовал новый токен для последующих операций.

*   **`bot.py` -> `CustomBot.refresh_oauth_token()` (асинхронный)**:
    *   Аналогичен `refresh_oauth_token_sync()`, но асинхронный и использует `requests` (который является блокирующей библиотекой; для полноценного асинхронного приложения здесь лучше бы подошел `aiohttp`).
    *   Делает POST-запрос на обновление токена.
    *   Обновляет `self._access_token` и `self._refresh_token` в экземпляре бота.
    *   Обновляет токены в файле `.env`.
    *   **Важно:** После успешного обновления токена, он также обновляет токен в активном соединении `twitchio`: `self._connection.token = self._access_token`.

### Использование токена в `twitchio`

*   Когда вы инициализируете `commands.Bot(token=ACCESS_TOKEN, ...)`, `twitchio` использует этот токен для подключения к IRC Twitch и для выполнения API-запросов от имени бота (например, отправка сообщений, получение информации о пользователях и т.д.).
*   Метод `send_whisper` в вашем `bot.py` также явно использует `self._access_token` для авторизации запроса к Helix API для отправки личных сообщений.

## Ключевые моменты работы с токенами в вашем коде:

1.  **Два этапа проверки/обновления:**
    *   **Синхронный:** Перед запуском бота (`twitch_auth.py`), чтобы убедиться, что у бота есть валидный токен для старта.
    *   **Асинхронный:** Во время работы бота (`bot.py`), чтобы поддерживать токен в актуальном состоянии без перезапуска.
2.  **Сохранение токенов:** Токены хранятся в файле `.env` и обновляются как скриптом первоначальной настройки, так и самим ботом при обновлении.
3.  **Обновление токена в `twitchio`:** Критически важно после обновления `access_token` присвоить его `self._connection.token`, чтобы `twitchio` начал использовать новый токен.

Этот многоуровневый подход к управлению токенами помогает обеспечить непрерывную работу бота, даже если `access_token` истекает. 