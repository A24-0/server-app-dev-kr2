## Контрольная работа №2 (FastAPI)

Реализованы задания **3.1**, **3.2**, **5.1**, **5.2**, **5.3**, **5.4**, **5.5**.

### Структура

- `main.py`: FastAPI-приложение и маршруты
- `models.py`: Pydantic-модели и вспомогательные зависимости (заголовки, логин)
- `requirements.txt`: зависимости
- `.gitignore`: игнорирование служебных файлов (`.venv`, `__pycache__` и т.д.)

### Запуск

#### 1) Установка зависимостей

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### 2) Старт сервера

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

База URL: `http://127.0.0.1:8000`

### Тесты (curl)

#### Задание 3.1 — POST `/create_user`

```bash
curl -sS -X POST "http://127.0.0.1:8000/create_user" \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice","email":"alice@example.com","age":30,"is_subscribed":true}'
```

#### Задание 3.2 — GET `/product/{product_id}`

```bash
curl -sS "http://127.0.0.1:8000/product/123"
```

#### Задание 3.2 — GET `/products/search`

```bash
curl -sS "http://127.0.0.1:8000/products/search?keyword=phone&category=Electronics&limit=5"
```

#### Задание 5.1 — логин + GET `/user` (cookie без подписи)

Логин устанавливает cookie `session_token_v51`.

```bash
curl -sS -i -c cookies.txt -X POST "http://127.0.0.1:8000/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"user123","password":"password123"}'
```

```bash
curl -sS -b cookies.txt "http://127.0.0.1:8000/user"
```

Невалидная сессия:

```bash
curl -sS "http://127.0.0.1:8000/user"
```

#### Задания 5.2 + 5.3 — логин + GET `/profile` (подписанная cookie + продление)

Логин устанавливает cookie `session_token` в формате:

`<user_id>.<timestamp>.<signature>`

```bash
curl -sS -i -c cookies.txt -X POST "http://127.0.0.1:8000/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"user123","password":"password123"}'
```

Проверка профиля (валидная сессия):

```bash
curl -sS -i -b cookies.txt "http://127.0.0.1:8000/profile"
```

Проверка сценариев продления:

- **через 2 минуты** (cookie не обновляется)
- **через 4 минуты** (cookie обновляется и продлевается на 5 минут)
- **через 6 минут** (401 и `{"message":"Session expired"}`)

Для отслеживания обновления cookie смотрите заголовки `Set-Cookie` в ответе:

```bash
curl -sS -i -b cookies.txt "http://127.0.0.1:8000/profile" | sed -n '1,25p'
```

Проверка подделки cookie (должно быть 401 и `{"message":"Invalid session"}`):

1) Получите cookie в `cookies.txt`.
2) Вручную измените значение `session_token` (например, поменяйте 1 символ).
3) Выполните:

```bash
curl -sS -i -b cookies.txt "http://127.0.0.1:8000/profile"
```

#### Задания 5.4 + 5.5 — GET `/headers` и GET `/info` (CommonHeaders)

Корректный запрос:

```bash
curl -sS "http://127.0.0.1:8000/headers" \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)" \
  -H "Accept-Language: en-US,en;q=0.9,es;q=0.8"
```

```bash
curl -sS -i "http://127.0.0.1:8000/info" \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)" \
  -H "Accept-Language: en-US,en;q=0.9,es;q=0.8"
```

Проверка отсутствующих заголовков (должно быть 400):

```bash
curl -sS -i "http://127.0.0.1:8000/headers"
```

Проверка неверного формата `Accept-Language` (должно быть 400):

```bash
curl -sS -i "http://127.0.0.1:8000/headers" \
  -H "User-Agent: test" \
  -H "Accept-Language: ???"
```

