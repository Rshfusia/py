# Посчитайте количество анкет мужчин в списке. 
# Выведите их количество на экран и сохраните анкеты в новый файл.

import argparse
import re
from typing import TextIO


def forms(file: str) -> list[str]:
    """Считывает файл и возвращает список анкет."""
    data = []
    try:
        with open(file, "r", encoding="utf-8") as f:
            data = f.read().split("\n\n")
    except FileNotFoundError:
        print("Файл не открылся!")
    return data

def check(form: str) -> bool:
    """Проверяет, является ли пол в анкете мужским."""
    flag = False
    if re.search(r"Пол:\s*(?:мужской|м)\b", form, re.IGNORECASE):
        flag = True
    return flag

def save(out: TextIO, res: str) -> None:
    """Записывает подходящую анкету в файл."""
    out.write(res + "\n\n")

def main() -> None:
    """Основная логика подсчета и сохранения анкет."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", "-i", default="data.txt")
    parser.add_argument("--output", "-o", default="res.txt")
    args = parser.parse_args()
    count = 0
    try:
        with open(args.output, "w", encoding="utf-8") as out:
            for form in forms(args.input):
                if check(form):
                    count += 1
                    save(out, form)
    except OSError:
        print("Ошибка при сохранении файла!")
    print(count)


if __name__ == "__main__":
    main()