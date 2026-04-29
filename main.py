import json
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import urllib.request
import urllib.parse
import ssl

API_URL = "https://api.github.com/search/users?q="
FAV_FILE = "favorites.json"


def load_favorites():
    try:
        with open(FAV_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []


def save_favorites(favorites):
    with open(FAV_FILE, "w", encoding="utf-8") as f:
        json.dump(favorites, f, ensure_ascii=False, indent=2)


def search_github_users(query):
    ctx = ssl.create_default_context()
    params = urllib.parse.quote(query)
    url = API_URL + params
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "GitHub-User-Finder"}
    )
    with urllib.request.urlopen(req, context=ctx) as response:
        data = response.read().decode("utf-8")
    return json.loads(data)


class GitHubUserFinder(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("GitHub User Finder")
        self.geometry("700x400")

        self.favorites = load_favorites()
        self.search_results = []

        self.create_widgets()

    def create_widgets(self):
        top_frame = ttk.Frame(self)
        top_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(top_frame, text="GitHub username or query:").pack(side=tk.LEFT)

        self.search_entry = ttk.Entry(top_frame)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        search_button = ttk.Button(top_frame, text="Search", command=self.on_search)
        search_button.pack(side=tk.LEFT)

        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        results_frame = ttk.Labelframe(paned, text="Search results")
        self.results_listbox = tk.Listbox(results_frame)
        self.results_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        add_button = ttk.Button(
            results_frame,
            text="Add to favorites",
            command=self.on_add_favorite
        )
        add_button.pack(pady=5)

        paned.add(results_frame, weight=1)

        fav_frame = ttk.Labelframe(paned, text="Favorites")
        self.fav_listbox = tk.Listbox(fav_frame)
        self.fav_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        remove_button = ttk.Button(
            fav_frame,
            text="Remove selected",
            command=self.on_remove_favorite
        )
        remove_button.pack(pady=5)

        paned.add(fav_frame, weight=1)

        self.status_label = ttk.Label(self, text="Ready")
        self.status_label.pack(fill=tk.X, padx=10, pady=(0, 5))

        self.update_favorites_listbox()

    def on_search(self):
        query = self.search_entry.get().strip()
        if not query:
            messagebox.showerror("Error", "Search field must not be empty")
            return

        self.status_label.config(text="Searching...")
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
                self.status_label.config(text="No users found")
            else:
                self.status_label.config(text=f"Found {len(items)} user(s)")
        except Exception as exc:
            messagebox.showerror("Error", f"Failed to search users: {exc}")
            self.status_label.config(text="Error during search")

    def on_add_favorite(self):
        selection = self.results_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Select a user in search results")
            return
        index = selection[0]
        user = self.search_results[index]
        login = user.get("login")
        html_url = user.get("html_url")

        if any(f["login"] == login for f in self.favorites):
            messagebox.showinfo("Info", "User is already in favorites")
            return

        self.favorites.append({"login": login, "html_url": html_url})
        save_favorites(self.favorites)
        self.update_favorites_listbox()
        self.status_label.config(text=f"Added {login} to favorites")

    def on_remove_favorite(self):
        selection = self.fav_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Select a user in favorites")
            return
        index = selection[0]
        user = self.favorites.pop(index)
        save_favorites(self.favorites)
        self.update_favorites_listbox()
        self.status_label.config(text=f"Removed {user['login']} from favorites")

    def update_favorites_listbox(self):
        self.fav_listbox.delete(0, tk.END)
        for fav in self.favorites:
            self.fav_listbox.insert(tk.END, f"{fav['login']} | {fav['html_url']}")


if __name__ == "__main__":
    app = GitHubUserFinder()
    app.mainloop()