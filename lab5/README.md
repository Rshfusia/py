# Лабораторная работа №5: Асинхронное программирование (`asyncio`)

- `src/lab5/domain.py` — чистая бизнес-логика и модели данных (Core/Domain)
- `src/lab5/storage.py` — асинхронное хранилище SQLite через `asyncio.to_thread` (Storage)
- `src/lab5/app.py` — пайплайн (`asyncio.TaskGroup`, `asyncio.Semaphore`, `CancelledError`) и CLI
- `tests/test_lab5.py` — асинхронные тесты (`pytest` + `pytest-asyncio`)

## Установка и проверка (Windows PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

pytest
mypy src
ruff check .
```

## Запуск

```powershell
$env:PYTHONPATH="src"
python -m lab5.app
```
