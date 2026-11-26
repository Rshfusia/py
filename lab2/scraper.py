import os
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://books.toscrape.com/"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )
}

def sanitize_name(name: str) -> str:
    """
    Очищает строку от символов, недопустимых в имени файла.

    :param name: исходное название
    :return: безопасная строка для имени файла
    """
    return "".join(c if c.isalnum() else "_" for c in name).strip("_")

def fetch_soup(session: requests.Session, url: str) -> BeautifulSoup:
    """
    Загружает HTML-страницу и возвращает объект BeautifulSoup.

    :param session: HTTP-сессия requests
    :param url: адрес страницы
    :return: разобранное HTML-дерево страницы
    """
    response = session.get(url, timeout=15)
    response.raise_for_status()
    return BeautifulSoup(response.content, "html.parser")

def get_genres(session: requests.Session) -> list[tuple[str, str]]:
    """
    Получает список жанров и ссылок на них с главной страницы сайта.

    :param session: HTTP-сессия requests
    :return: список кортежей (название жанра, URL страницы жанра)
    """
    soup = fetch_soup(session, BASE_URL)
    links = soup.select("div.side_categories ul.nav-list > li > ul > li > a")
    genres: list[tuple[str, str]] = []

    for link in links:
        href = link.get("href")
        if isinstance(href, str):
            name = link.get_text(strip=True)
            genres.append((name, urljoin(BASE_URL, href)))

    return genres

def save_image(
    session: requests.Session, img_url: str, file_path: str
) -> None:
    """
    Скачивает изображение по URL и сохраняет его в файл.

    :param session: HTTP-сессия requests
    :param img_url: URL изображения
    :param file_path: путь для сохранения файла
    """
    response = session.get(img_url, timeout=15)
    response.raise_for_status()
    with open(file_path, "wb") as file:
        file.write(response.content)

def download_genre_covers(
    session: requests.Session,
    genre_name: str,
    genre_url: str,
    count_per_genre: int,
    output_dir: str,
) -> list[str]:
    """
    Скачивает заданное количество обложек книг одного жанра.

    :param session: HTTP-сессия requests
    :param genre_name: название жанра
    :param genre_url: URL первой страницы жанра
    :param count_per_genre: максимальное количество книг для скачивания
    :param output_dir: папка для сохранения обложек
    :return: список путей к скачанным файлам
    """
    safe_genre = sanitize_name(genre_name)
    current_url: str | None = genre_url
    saved_files: list[str] = []

    while current_url and len(saved_files) < count_per_genre:
        page_soup = fetch_soup(session, current_url)
        books = page_soup.select("article.product_pod")

        for book in books:
            if len(saved_files) >= count_per_genre:
                break

            img = book.find("img")
            src = img.get("src") if img else None
            if not isinstance(src, str):
                continue

            img_url = urljoin(current_url, src)
            ext = os.path.splitext(img_url)[1] or ".jpg"
            filename = f"{safe_genre}_{len(saved_files) + 1}{ext}"
            file_path = os.path.join(output_dir, filename)

            save_image(session, img_url, file_path)
            saved_files.append(file_path)

        next_link = page_soup.select_one("li.next a")
        next_href = next_link.get("href") if next_link else None
        current_url = (
            urljoin(current_url, next_href)
            if isinstance(next_href, str)
            else None
        )

    return saved_files

def download_covers(count_per_genre: int, output_dir: str) -> list[str]:
    """
    Скачивает обложки книг каждого жанра, представленного на сайте.

    :param count_per_genre: количество книг одного жанра (минимум 1)
    :param output_dir: папка для сохранения обложек
    :return: список путей к скачанным обложкам
    """
    if count_per_genre < 1:
        raise ValueError(
            "Количество книг одного жанра должно быть не меньше 1"
        )

    os.makedirs(output_dir, exist_ok=True)
    saved_files: list[str] = []

    with requests.Session() as session:
        session.headers.update(HEADERS)
        genres = get_genres(session)
        for genre_name, genre_url in genres:
            genre_files = download_genre_covers(
                session, genre_name, genre_url, count_per_genre, output_dir
            )
            saved_files.extend(genre_files)

    return saved_files
