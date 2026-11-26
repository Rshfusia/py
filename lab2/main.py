import argparse
import requests

from annotation import save_annotation
from iterator import FilePathIterator
from scraper import download_covers

# python main.py --count 2 --output covers --annotation annotation.csv

def parse_args() -> argparse.Namespace:
    """
    Разбирает аргументы командной строки.

    :return: объект с переданными аргументами
    """
    parser = argparse.ArgumentParser(
        description="Скачивание обложек книг по жанрам"
)
    parser.add_argument(
        "--count",
        type=int,
        required=True,
        help="Количество книг одного жанра (минимум 1)",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Папка для сохранения обложек",
    )
    parser.add_argument(
        "--annotation",
        required=True,
        help="Путь к CSV-файлу аннотации",
    )
    return parser.parse_args()

def show_paths(source: str) -> None:
    """
    Выводит пути к файлам с помощью FilePathIterator.

    :param source: путь к папке или CSV-файлу аннотации
    """
    iterator = FilePathIterator(source)
    for path in iterator:
        print(path)

def main() -> None:
    """
    Точка входа программы.
    """
    try:
        args = parse_args()
        saved_files = download_covers(args.count, args.output)
        save_annotation(saved_files, args.annotation)
        show_paths(args.annotation)
    except ValueError as exc:
        print(f"Ошибка значения: {exc}")
    except FileNotFoundError as exc:
        print(f"Ошибка пути: {exc}")
    except requests.RequestException as exc:
        print(f"Ошибка сети: {exc}")
    except OSError as exc:
        print(f"Ошибка работы с файлами: {exc}")

if __name__ == "__main__":
    main()
