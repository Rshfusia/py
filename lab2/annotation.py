import csv
import os

def save_annotation(file_paths: list[str], annotation_path: str) -> None:
    """
    Сохраняет CSV-аннотацию с абсолютными и относительными путями к файлам.

    :param file_paths: список путей к скачанным файлам
    :param annotation_path: путь к выходному CSV-файлу
    """
    parent_dir = os.path.dirname(annotation_path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)

    data: list[list[str]] = [["absolute_path", "relative_path"]]
    for path in file_paths:
        data.append([os.path.abspath(path), os.path.relpath(path)])

    with open(
        annotation_path, mode="w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.writer(file)
        writer.writerows(data)
