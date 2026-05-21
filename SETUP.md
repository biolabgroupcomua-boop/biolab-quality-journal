# SETUP — наступні мануальні кроки

Цей файл — інструкції для **тебе або іншого розробника** на наступну сесію.
Усе, що в цьому файлі, ти виконуєш сама в терміналі PowerShell. Claude Code
запустить це по черзі за твоїм запитом.

## Стан зараз (2026-05-21)

Готово:
- ✅ CLAUDE.md (специфікація проєкту, ~600 рядків)
- ✅ pyproject.toml (залежності)
- ✅ .gitignore, README.md
- ✅ app/ скелет (main, config, db)
- ✅ 7 SQLAlchemy моделей (Customer → ProductVariant → Product → Specification → BulkBatch → FinishedBatch → QualityCertificate)
- ✅ Сервіс verdict_calculator (логіка OK/OUT) + 13 тестів

Не готово:
- ⏳ Залежності не встановлені (треба `pip install`)
- ⏳ Alembic не ініціалізовано → нема таблиць у БД
- ⏳ Імпорт з Google Sheet (скрипт ще не написаний)
- ⏳ Шаблон паспорта не експортований у HTML/Jinja
- ⏳ Роутери і UI (HTMX-форми) — нічого нема
- ⏳ git-репо локально не ініціалізовано, GitHub-репо нема

## Крок 1 — встановити Python-залежності

```powershell
# у корені c:\Users\nomer\biolab-quality-journal
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

Перевірка: `python -c "import fastapi, sqlalchemy, weasyprint; print('OK')"`

⚠️ WeasyPrint на Windows потребує GTK3-runtime. Якщо `import weasyprint` падає
з помилкою `cairo`/`pango`, треба завантажити GTK3 з
https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases
і додати в PATH. Це разово.

## Крок 2 — перевірити що тести зеленіють

```powershell
pytest -v
```

Очікую: 13 тестів verdict_calculator проходять. Це підтвердить що моделі і
сервіс імпортуються правильно.

## Крок 3 — ініціалізувати alembic

```powershell
alembic init migrations
```

Тоді відкрити `migrations\env.py` і:
1. Замінити `target_metadata = None` на:
   ```python
   from app.db import Base
   from app.models import *  # noqa: F401, F403 — імпорт реєструє моделі
   target_metadata = Base.metadata
   ```
2. У `alembic.ini` замінити `sqlalchemy.url = ...` на:
   ```ini
   sqlalchemy.url = sqlite:///data/journal.db
   ```

Згенерувати першу міграцію:

```powershell
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```

Перевірка: `data\journal.db` створено, є 7 таблиць.

## Крок 4 — запустити сервер

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Відкрити `http://localhost:8000/health` — має повернути `{"status":"ok"}`.
Відкрити `http://localhost:8000/docs` — Swagger UI (поки пустий, бо ще нема роутерів).

## Крок 5 — git init + GitHub

```powershell
git init
git add CLAUDE.md README.md SETUP.md pyproject.toml .gitignore app tests
git commit -m "Initial commit — CLAUDE.md, models, verdict_calculator"

# створити репо на GitHub через gh CLI
gh repo create biolab-quality-journal --private --source . --remote origin --push
```

## Крок 6 — наступна сесія з Claude Code

Попросити Claude:
1. Експортувати gdoc шаблон паспорта (`1DkJyL0A38qZNpbWdr8PkutwpvlTHKlePXcfU3XLlnQY`) у `app/templates/passport.html.j2`.
2. Написати `app/services/certificate_generator.py` — рендер HTML → PDF через WeasyPrint.
3. Написати `scripts/import_from_sheet.py` — імпорт 9 вкладок Sheet → SQLite з `--dry-run` режимом.
4. Перші роутери: `app/routers/products.py`, `customers.py`, `specifications.py` (CRUD на HTMX).
5. UI: `app/templates/base.html`, `pages/dashboard.html`, форми створення.

## Контрольний чек-ліст готовності до бойового запуску

- [ ] Альфа-тест на одній варці: завести Product, Specification, BulkBatch,
      ProductVariant, FinishedBatch, згенерувати PDF — звірити з існуючим паспортом
- [ ] Імпорт даних із Sheet (всі 9 вкладок)
- [ ] Дзеркало Sheet (cron-задача раз на годину)
- [ ] Бекап БД (Windows Task Scheduler — щодня)
- [ ] Прості логін/пароль (один на команду, в .env)
- [ ] Інструкція для технологів (`docs/workflow.md`)
- [ ] Існуючий Sheet перейменовано на "АРХІВ (read-only)", замки на редагування
