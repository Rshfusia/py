# Лабораторная работа №4: Сетевое взаимодействие (Клиент-сервер / Sockets)

- `src/lab4/protocol.py` — протокол `[4 байта длины Big-Endian][JSON UTF-8]` и `FrameDecoder`
- `src/lab4/server.py` — неблокирующий TCP-сервер на `selectors.DefaultSelector`
- `src/lab4/client.py` — TCP-клиент `TcpClient` с таймаутом
- `tests/test_lab4.py` — тесты (`pytest`)

## Установка и проверка (Windows PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

pytest
mypy src
ruff check .
```

## Запуск сервера и клиента

```powershell
# Терминал 1 — сервер
$env:PYTHONPATH="src"
python -m lab4.server --port 9000

# Терминал 2 — клиент
$env:PYTHONPATH="src"
python -m lab4.client --port 9000 --action ping
```
