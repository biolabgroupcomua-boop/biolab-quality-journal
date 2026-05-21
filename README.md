# biolab-quality-journal

Веб-застосунок для ведення журналу варок (bulk напівфабрикатів) і журналу
готової продукції Biolab Group, з автоматичною генерацією паспортів якості
(CoA) на партію.

Замінює Google Sheet `журнал обліку і контролю якості_Bulk_ГП`, у якому
формули регулярно рвуться від ручного редагування кількома користувачами.

**Стек:** Python 3.11+, FastAPI, SQLAlchemy + SQLite, Jinja2 + HTMX, WeasyPrint.

**Повна специфікація:** див. [CLAUDE.md](./CLAUDE.md).

## Швидкий старт (для розробника)

```powershell
# 1. Створити віртуальне середовище
python -m venv .venv
.venv\Scripts\Activate.ps1

# 2. Встановити залежності (включно з dev для тестів)
pip install -e ".[dev]"

# 3. Ініціалізувати міграції (тільки перший раз)
alembic init migrations
# вручну налаштувати alembic/env.py щоб імпортувати models.Base

# 4. Створити першу міграцію зі схеми
alembic revision --autogenerate -m "initial"
alembic upgrade head

# 5. Запустити сервер
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Імпорт існуючих даних з Google Sheet

```powershell
# Покласти service_account.json у credentials/
python scripts/import_from_sheet.py --dry-run
# Перевірити вивід, потім без --dry-run
python scripts/import_from_sheet.py
```

## Структура

Див. [CLAUDE.md](./CLAUDE.md#структура-репозиторію).

## Власник

Olena Nomerovska, Biolab Group · biolabgroup.com.ua@gmail.com
