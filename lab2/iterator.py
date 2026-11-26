import csv
import os

class FilePathIterator:
    """Итератор по путям к файлам из папки или CSV-аннотации."""

    def __init__(self, source: str) -> None:
        """
        Инициализирует итератор.

        :param source: путь к папке с файлами или к CSV-файлу аннотации
        """
        self.paths: list[str] = self._load_paths(source)
        self.counter: int = 0

    def _load_paths(self, source: str) -> list[str]:
        """
        Загружает список путей из указанного источника.

        :param source: путь к папке или CSV-файлу
        :return: список путей к файлам
        """
        paths: list[str] = []

        if os.path.isdir(source):
            for name in sorted(os.listdir(source)):
                full_path = os.path.join(source, name)
                if os.path.isfile(full_path):
                    paths.append(full_path)
        elif os.path.isfile(source):
            with open(
                source, mode="r", newline="", encoding="utf-8"
            ) as file:
                reader = csv.reader(file)
                next(reader, None)
                for row in reader:
                    if row:
                        paths.append(row[0])
        else:
            raise FileNotFoundError(f"Путь не найден: {source}")

        return paths

    def __iter__(self) -> "FilePathIterator":
        """
        Возвращает объект итератора.

        :return: экземпляр FilePathIterator
        """
        return self

    def __next__(self) -> str:
        """
        Возвращает следующий путь к файлу.

        :return: путь к файлу
        """
        if self.counter < len(self.paths):
            path = self.paths[self.counter]
            self.counter += 1
            return path
        raise StopIteration
