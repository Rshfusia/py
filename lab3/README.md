# Лабораторная работа №3: Параллелизм, процессы и IPC

- `src/lab3/worker.py` — чистые функции вычислений
- `src/lab3/ipc.py` — обмен через `SharedMemory` + `Event` (с `close()`/`unlink()` в `finally`) и пул процессов через `Queue`
- `src/lab3/main.py` — запуск примера
- `tests/test_lab3.py` — тесты (`pytest`)

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
python -m lab3.main
```
