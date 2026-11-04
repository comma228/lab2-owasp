# Лабораторная работа 2 — OWASP Top 10: уязвимости, эксплуатация, патч

Учебное веб-приложение **MiniNotes** на Flask (простой сервис заметок с
логином), содержащее две намеренные уязвимости из OWASP Top 10:

| № | Уязвимость | Категория OWASP Top 10 (2021) | Файл / место |
|---|---|---|---|
| 1 | SQL Injection | A03:2021 – Injection | `app.py`, маршрут `/login` |
| 2 | Stored XSS | A03:2021 – Injection (Cross-Site Scripting) | `app.py`, маршрут `/notes` |

## Состав репозитория

```
lab2/
├── app.py            # Часть 1: уязвимое приложение
├── app_patched.py     # Часть 3: пропатченная версия (для справки/проверки)
├── patch.diff          # Часть 3: патч в формате unified diff
├── exploit_sqli.py     # Часть 2: эксплойт SQL Injection
├── exploit_xss.py       # Часть 2: эксплойт Stored XSS
├── requirements.txt
└── README.md
```

## Часть 1 — Уязвимое приложение

Установка и запуск:

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Приложение поднимется на `http://127.0.0.1:5000`, автоматически создаст
SQLite-базу `mininotes.db` и тестовых пользователей:

- `admin` / `S3cr3tAdminPass!`
- `alice` / `alice123`

**Уязвимость 1 (SQL Injection).** В `/login` SQL-запрос собирается
конкатенацией строк из полей формы без параметризации:

```python
query = "SELECT username FROM users WHERE username='" + username + "' AND password='" + password + "'"
```

**Уязвимость 2 (Stored XSS).** В `/notes` текст заметки сохраняется без
фильтрации и выводится в шаблон через `{{ n[1]|safe }}`, то есть
автоэкранирование Jinja2 отключено.

## Часть 2 — Эксплуатация

Приложение должно быть запущено (`python app.py`) в отдельном терминале.

**SQL Injection — обход аутентификации:**

```bash
python exploit_sqli.py
```

Скрипт отправляет на `/login` `username = admin' -- `, что превращает
запрос в `... WHERE username='admin' --' AND password='...'`. Часть
после `--` становится комментарием SQL, проверка пароля отбрасывается,
и скрипт логинится как `admin`, не зная пароля.

**Stored XSS — внедрение скрипта:**

```bash
python exploit_xss.py
```

Скрипт логинится обычным пользователем `alice`, сохраняет заметку с
`<script>document.title = "XSS-EXPLOIT-WORKED";</script>` и показывает,
что сервер возвращает этот payload в HTML без экранирования — то есть в
обычном браузере скрипт реально выполнится у любого, кто откроет
`/notes` (например, может похитить `document.cookie`).

## Часть 3 — Патч

Исправления показаны в `patch.diff` (применяется к `app.py`) и в
готовом виде лежат в `app_patched.py`.

Применить патч:

```bash
patch app.py < patch.diff
# или просто используйте app_patched.py вместо app.py
```

**Патч 1 (SQLi → параметризованный запрос):**

```python
query = "SELECT username FROM users WHERE username=? AND password=?"
cur = db.execute(query, (username, password))
```
Пользовательский ввод передаётся как параметр драйверу БД, а не
встраивается в текст запроса — спецсимволы (`'`, `--`, `;`) больше не
меняют структуру SQL.

**Патч 2 (XSS → автоэкранирование):**

```jinja
<li><b>{{ n[0] }}:</b> {{ n[1] }}</li>
```
Фильтр `|safe` убран — Jinja2 автоматически экранирует HTML/JS
спецсимволы в тексте заметки, и браузер отображает `<script>` как
обычный текст, а не выполняет его.

Проверка: запустите `python app_patched.py` и повторите
`exploit_sqli.py` / `exploit_xss.py` (поменяв порт/URL при
необходимости, если патченная версия запущена отдельно) — оба скрипта
сообщат, что эксплойт не сработал.

## Публикация

```bash
git init
git add .
git commit -m "Lab 2: OWASP Top 10 — SQLi + XSS, exploits, patch"
git remote add origin <ссылка на ваш репозиторий GitHub/GitLab>
git push -u origin main
```

## Дисклеймер

Приложение и эксплойты предназначены исключительно для локального
учебного стенда. Не разворачивать в публичной сети и не применять к
системам, на тестирование которых нет явного разрешения.
