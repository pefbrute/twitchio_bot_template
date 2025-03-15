# Chat Monitor Module Documentation

## Overview
The Chat Monitor module is responsible for monitoring Twitch chat messages and automatically responding to common questions about the current anime, game, difficulty level, and voice acting. It uses both regex patterns and NLP (Natural Language Processing) to detect questions.

## Components

### ChatMonitorCommand Class
Main class that handles chat monitoring and command registration.

#### Key Features:
- Message monitoring and response generation
- NLP-based question detection using spaCy
- Regex pattern fallback for question detection
- Caching of processed messages
- Permission management for commands

### ResponsesManager Class
Manages persistent storage and retrieval of current stream information.

#### Managed Information:
- Current anime name
- Current game name
- Current difficulty level
- Current voice acting studio/person

## Commands

### Moderator Commands
All commands require moderator privileges or specific user permissions.

| Command | Description | Example |
|---------|-------------|---------|
| !указатьаниме | Set current anime | `!указатьаниме Моб Психо 100` |
| !указатьигру | Set current game | `!указатьигру The Last of Us` |
| !указатьсложность | Set difficulty level | `!указатьсложность реализм` |
| !указатьозвучку | Set voice acting info | `!указатьозвучку Анилибрия` |
| !показатьназвания | Show all current settings | `!показатьназвания` |

## Question Detection

### NLP-based Detection
The module uses spaCy with Russian language model (`ru_core_news_sm`) to detect questions about voice acting. It analyzes:
- Question words
- Voice-related keywords
- Context indicators
- Time context (past/present/future)

### Regex Patterns
Fallback patterns are used when:
- spaCy is not available
- Question is about anime/game/difficulty
- Voice question detection via NLP fails

### Keywords and Patterns

#### Voice Acting Keywords:
```python
voice_keywords = [
    "озвучка", "озвучивание", "войс", "голос", "дабберы",
    "дублировать", "перевод", "переводчик", "студия",
    "озвучивать", "озвучить", "дублировать", "переводить",
    "озвучкер", "войсер", "даббер"
]
```

#### Question Words:
```python
question_words = {
    "что", "как", "какой", "где", "когда", "почему", "зачем",
    "кто", "куда", "откуда", "чо", "че", "шо", "какая", "какое"
}
```

## Response Templates

Default response templates for different types of questions:

```python
response_templates = {
    "anime": "ну, чел, ты чо в глаза долбишься, {name}",
    "game": "как обычно, в любимый {name}",
    "difficulty": "{name}, как всегда",
    "anime_voice": "озвучка от {name}, самая лучшая"
}
```

## Data Storage

### File Structure
- Responses are stored in `responses.json`
- Default values are provided if file is missing

### Data Format
```json
{
    "anime": "моб психо 100",
    "game": "зе ласт оф ас часть первая",
    "difficulty": "реализм",
    "anime_voice": "Анилибрия"
}
```

## Permissions

### Allowed Users
Commands can be used by:
- Channel broadcaster
- Channel moderators
- VIP users
- Specific users listed in `ALLOWED_USER_IDS`

## Error Handling

The module includes comprehensive error handling:
- Logging of all errors and debug information
- Graceful fallback when NLP model fails to load
- Message deduplication
- Invalid regex pattern handling

## Performance Considerations

### Caching
- LRU cache for voice question detection
- Processed message IDs are cached (cleared after 1000 messages)

### Resource Usage
- Uses lightweight spaCy model (`ru_core_news_sm`)
- Fallback to regex patterns when NLP is unavailable
- Efficient message processing with early exits

## Logging

The module uses Python's logging system with DEBUG level for detailed information:
- Message processing steps
- NLP analysis results
- Pattern matching results
- Command execution
- Error conditions

## Future Improvements

Potential areas for enhancement:
1. Additional language support
2. More sophisticated question detection
3. Customizable response templates
4. Extended statistics tracking
5. Dynamic pattern updates
6. Enhanced permission system
```