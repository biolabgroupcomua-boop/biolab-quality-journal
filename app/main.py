from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings

app = FastAPI(
    title="Biolab Quality Journal",
    description="Журнал варок і генерація паспортів якості",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    """Health check для перевірки що сервер живий."""
    return {"status": "ok"}


@app.get("/")
def root() -> RedirectResponse:
    """Поки реальний UI не готовий — корінь редіректить на статичний прототип."""
    return RedirectResponse(url="/prototype/index.html")


# Прототип віддається як static files щоб команда могла подивитися макети
# доки бекенд не реалізовано. Після переходу на Jinja-шаблони — приберемо.
prototype_dir = settings.project_root / "prototype"
if prototype_dir.exists():
    app.mount(
        "/prototype",
        StaticFiles(directory=prototype_dir, html=True),
        name="prototype",
    )
