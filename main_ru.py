"""Приложение "GitHub User Finder".

Поиск пользователей GitHub через официальный REST API,
отображение результатов в GUI (Tkinter) и сохранение
избранных пользователей в JSON-файл.

Автор: УКАЖИТЕ СВОИ ФИО
"""

import json
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import urllib.request
import urllib.parse
import ssl

# Базовый URL для поиска пользователей GitHub
API_URL = "https://api.github.com/search/users?q="
# Имя файла, в котором храним избранных пользователей
FAV_FILE = "favorites.json"


def load_favorites():
    """Загрузить список избранных пользователей из JSON-файла.

    Если файл отсутствует или повреждён, возвращается пустой список.
    """
    try:
        with open(FAV_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []


def save_favorites(favorites):
    """Сохранить список избранных пользователей в JSON-файл."""
    with open(FAV_FILE, "w", encoding="utf-8") as f:
        json.dump(favorites, f, ensure_ascii=False, indent=2)


def search_github_users(query: str) -> dict:
    """Выполнить запрос к GitHub Search API и вернуть словарь с результатами.

    :param query: строка поиска (имя пользователя или часть имени)
    :return: словарь с JSON-ответом от GitHub
    """
    ctx = ssl.create_default_context()
    params = urllib.parse.quote(query)
    url = API_URL + params

    # GitHub требует указать заголовок User-Agent
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "GitHub-User-Finder"},
    )

    with urllib.request.urlopen(req, context=ctx) as response:
        data = response.read().decode("utf-8")

    return json.loads(data)


class GitHubUserFinder(tk.Tk):
    """Главное окно приложения GitHub User Finder."""

    def __init__(self) -> None:
        super().__init__()
        self.title("GitHub User Finder")
        self.geometry("750x420")

        # В памяти храним список избранных и результаты поиска
        self.favorites = load_favorites()
        self.search_results = []

        self.create_widgets()

    def create_widgets(self) -> None:
        """Создать и разместить все элементы интерфейса."""
        # Верхняя панель: строка ввода + кнопка поиска
        top_frame = ttk.Frame(self)
        top_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(top_frame, text="Имя пользователя GitHub или строка поиска:").pack(
            side=tk.LEFT
        )

        self.search_entry = ttk.Entry(top_frame)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        search_button = ttk.Button(
            top_frame,
            text="Поиск",
            command=self.on_search,
        )
        search_button.pack(side=tk.LEFT)

        # Две панели: слева результаты, справа избранное
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Левая панель — результаты поиска
        results_frame = ttk.Labelframe(paned, text="Результаты поиска")
        self.results_listbox = tk.Listbox(results_frame)
        self.results_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        add_button = ttk.Button(
            results_frame,
            text="Добавить в избранное",
            command=self.on_add_favorite,
        )
        add_button.pack(pady=5)

        paned.add(results_frame, weight=1)

        # Правая панель — список избранных пользователей
        fav_frame = ttk.Labelframe(paned, text="Избранные пользователи")
        self.fav_listbox = tk.Listbox(fav_frame)
        self.fav_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        remove_button = ttk.Button(
            fav_frame,
            text="Удалить выбранного",
            command=self.on_remove_favorite,
        )
        remove_button.pack(pady=5)

        paned.add(fav_frame, weight=1)

        # Строка состояния внизу окна
        self.status_label = ttk.Label(self, text="Готово")
        self.status_label.pack(fill=tk.X, padx=10, pady=(0, 5))

        # Заполнить список избранных при старте
        self.update_favorites_listbox()

    def on_search(self) -> None:
        """Обработчик нажатия кнопки "Поиск"."""
        query = self.search_entry.get().strip()

        # Валидация: поле не должно быть пустым
        if not query:
            messagebox.showerror("Ошибка", "Поле поиска не должно быть пустым")
            return

        self.status_label.config(text="Выполняется поиск...")
        self.update_idletasks()

        try:
            data = search_github_users(query)
            items = data.get("items", [])

            self.search_results = items
            self.results_listbox.delete(0, tk.END)

            for user in items:
                login = user.get("login", "")
                url = user.get("html_url", "")
                self.results_listbox.insert(tk.END, f"{login} | {url}")

            if not items:
                self.status_label.config(text="Пользователи не найдены")
            else:
                self.status_label.config(
                    text=f"Найдено пользователей: {len(items)}"
                )
        except Exception as exc:  # pylint: disable=broad-except
            messagebox.showerror("Ошибка", f"Не удалось выполнить поиск: {exc}")
            self.status_label.config(text="Ошибка при поиске")

    def on_add_favorite(self) -> None:
        """Добавить выбранного пользователя из результатов в избранное."""
        selection = self.results_listbox.curselection()
        if not selection:
            messagebox.showwarning(
                "Предупреждение",
                "Сначала выберите пользователя в списке результатов",
            )
            return

        index = selection[0]
        user = self.search_results[index]
        login = user.get("login")
        html_url = user.get("html_url")

        # Не добавляем дубликаты
        if any(f["login"] == login for f in self.favorites):
            messagebox.showinfo(
                "Информация",
                "Этот пользователь уже есть в списке избранных",
            )
            return

        self.favorites.append({"login": login, "html_url": html_url})
        save_favorites(self.favorites)
        self.update_favorites_listbox()
        self.status_label.config(text=f"Пользователь {login} добавлен в избранное")

    def on_remove_favorite(self) -> None:
        """Удалить выбранного пользователя из избранного."""
        selection = self.fav_listbox.curselection()
        if not selection:
            messagebox.showwarning(
                "Предупреждение",
                "Сначала выберите пользователя в списке избранных",
            )
            return

        index = selection[0]
        user = self.favorites.pop(index)
        save_favorites(self.favorites)
        self.update_favorites_listbox()
        self.status_label.config(
            text=f"Пользователь {user['login']} удалён из избранного"
        )

    def update_favorites_listbox(self) -> None:
        """Обновить содержимое списка избранных пользователей."""
        self.fav_listbox.delete(0, tk.END)
        for fav in self.favorites:
            self.fav_listbox.insert(tk.END, f"{fav['login']} | {fav['html_url']}")


if __name__ == "__main__":
    app = GitHubUserFinder()
    app.mainloop()
