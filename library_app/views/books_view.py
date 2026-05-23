import os
import tkinter as tk
from PIL import Image, ImageTk
import ttkbootstrap as ttkb


def _get_books_word(count: int) -> str:
    """Возвращает правильное склонение слова 'книга'"""
    if count % 10 == 1 and count % 100 != 11:
        return "книга"
    elif 2 <= count % 10 <= 4 and not (12 <= count % 100 <= 14):
        return "книги"
    else:
        return "книг"

class BooksView:
    def __init__(self, parent, controller, notebook):
        self.controller = controller
        self.notebook = notebook
        self.images = {}
        self.view_sort_col = ""
        self.view_sort_reverse = False
        self.style = ttkb.Style()
        self.setup_ui(parent)

    def _safe_call(self, func, *args, **kwargs):
        if self.controller and func:
            return func(*args, **kwargs)

    def setup_ui(self, frame):
        filter_frame = ttkb.Labelframe(frame, text="Фильтры", bootstyle="primary")
        filter_frame.pack(fill="x", padx=10, pady=2)
        filter_frame.columnconfigure(6, weight=1)

        self.theme_btn = ttkb.Button(filter_frame, text="🌙 Темная тема", bootstyle="secondary",
                                    command=lambda: self.controller.toggle_theme())
        self.theme_btn.grid(row=0, column=0, padx=8, pady=8, sticky="w")

        self.category_label = ttkb.Label(
            filter_frame,
            text="Текущая категория: Базовая",
            font=("Segoe UI", 12, "bold"),
            bootstyle="info",
            anchor="center"
        )
        # --- РЯД 0: Заголовок и тема ---
        # Размещаем label по центру, растянув на 7 колонок
        self.category_label.grid(
            row=0, column=0, columnspan=7, sticky="ew", padx=5, pady=(4, 0)
        )

        # Кнопку темы прижимаем к правому краю (8-я колонка)
        self.theme_btn.grid(row=0, column=7, padx=8, pady=4, sticky="e")

        # --- РЯД 1: Поиск и Теги (был ряд 0) ---
        ttkb.Label(filter_frame, text="Поиск:").grid(
            row=1, column=2, padx=8, pady=4, sticky="w"
        )
        self.search_var = tk.StringVar()
        ttkb.Entry(filter_frame, textvariable=self.search_var, width=35).grid(
            row=1, column=3, padx=5, pady=4, sticky="w"
        )
        self.search_var.trace_add(
            "write", lambda *args: self.controller.apply_filters()
        )

        ttkb.Label(filter_frame, text="Теги:").grid(
            row=1, column=4, padx=8, pady=4, sticky="w"
        )
        self.tag_button = ttkb.Button(
            filter_frame,
            text="Выбрать теги ▼",
            bootstyle="info",
            command=self._open_tag_selector,
        )
        self.tag_button.grid(row=1, column=5, padx=5, pady=4, sticky="w")

        # --- РЯД 2: Издательство, Год и Сброс (был ряд 1) ---
        ttkb.Label(filter_frame, text="Издательство:").grid(
            row=2, column=2, padx=8, pady=4, sticky="w"
        )
        self.publisher_var = tk.StringVar()
        self.publisher_combo = ttkb.Combobox(
            filter_frame, textvariable=self.publisher_var, state="readonly", width=25
        )
        self.publisher_combo.grid(row=2, column=3, padx=5, pady=4, sticky="w")
        self.publisher_combo.bind(
            "<<ComboboxSelected>>",
            lambda e: self._safe_call(self.controller.apply_filters),
        )

        ttkb.Label(filter_frame, text="Год:").grid(
            row=2, column=4, padx=8, pady=4, sticky="w"
        )
        self.year_var = tk.StringVar()
        self.year_combo = ttkb.Combobox(
            filter_frame, textvariable=self.year_var, state="readonly", width=12
        )
        self.year_combo.grid(row=2, column=5, padx=5, pady=4, sticky="w")
        self.year_combo.bind(
            "<<ComboboxSelected>>",
            lambda e: self._safe_call(self.controller.apply_filters),
        )

        ttkb.Button(
            filter_frame,
            text="Сбросить",
            bootstyle="secondary",
            command=lambda: self._safe_call(self.reset_filters),
        ).grid(row=2, column=6, padx=5, pady=4, sticky="sw")

        # --- Счетчик найденных книг (Колонка 7, Ряд 2) ---
        self.counter_label = ttkb.Label(
            filter_frame,
            text="Всего показано: 0 книг",
            font=("Segoe UI", 9, "italic"),
            foreground="gray",
        )
        # sticky="e" прижмет текст к правому краю 7-й колонки
        self.counter_label.grid(row=2, column=7, sticky="e", padx=10, pady=4)

        columns = ("title", "author", "publisher", "year", "tags")
        self.tree = ttkb.Treeview(
            frame, columns=columns, show="tree headings", height=18, bootstyle="primary"
        )
        self.tree.heading("#0", text="Обложка")
        self.tree.heading(
            "title", text="Название книги", command=lambda: self._on_view_sort("title")
        )
        self.tree.heading(
            "author", text="Автор", command=lambda: self._on_view_sort("author")
        )
        self.tree.heading(
            "publisher",
            text="Издательство",
            command=lambda: self._on_view_sort("publisher"),
        )
        self.tree.heading(
            "year", text="Год", command=lambda: self._on_view_sort("year")
        )
        self.tree.heading("tags", text="Теги")

        self.tree.column("#0", width=130, stretch=False, anchor="center")
        self.tree.column("title", width=500, anchor="w")
        self.tree.column("author", width=130, anchor="w")
        self.tree.column("publisher", width=80, anchor="w")
        self.tree.column("year", width=60, anchor="center")
        self.tree.column("tags", width=250, anchor="w")

        self._apply_treeview_styles()

        vsb = ttkb.Scrollbar(
            frame, orient="vertical", command=self.tree.yview, bootstyle="primary"
        )
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=8)
        vsb.pack(side="right", fill="y")

        self.tree.bind(
            "<Double-1>", lambda e: self._safe_call(self.controller.on_double_click, e)
        )
        self.tree.bind(
            "<Return>", lambda e: self._safe_call(self.controller.on_double_click, e)
        )

    def refresh_table(self, filtered_books, get_img_path_func, str_tags):
        # --- ОБНОВЛЯЕМ СЧЕТЧИК ---
        count = len(filtered_books)
        word = _get_books_word(count)
        self.counter_label.configure(text=f"Всего показано: {count} {word}")
        # ---------------------------
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.images.clear()
        for i, book in enumerate(filtered_books):
            tags_str = ", ".join(
                [str_tags[idx] for idx in book.tags if idx < len(str_tags)]
            )
            year_str = str(book.year) if book.year is not None else ""
            values = (book.title, book.author, book.publisher, year_str, tags_str)

            photo = None
            cover_path = get_img_path_func(book.cover)
            if cover_path and os.path.exists(cover_path):
                try:
                    img = Image.open(cover_path).convert("RGB")
                    img.thumbnail((100, 140), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    self.images[i] = photo
                except Exception as e:
                    pass

            values = (
                book.title,
                book.author,
                book.publisher,
                year_str,
                tags_str,
            )
            item_id = self.tree.insert(
                "",
                "end",
                values=values,
                tags=("even_row" if i % 2 == 0 else "odd_row", str(id(book))),
            )
            if photo:
                self.tree.item(item_id, image=photo)

    def update_comboboxes(self, publishers, years):
        self.publisher_combo["values"] = [""] + publishers
        self.year_combo["values"] = [""] + years

    def update_category_label(self, current_category):
        text = f"Текущая категория: {current_category.title if current_category else 'Базовая'}"
        self.category_label.configure(text=text)

    def reset_filters(self):
        self.search_var.set("")
        self.publisher_var.set("")
        self.year_var.set("")
        self.controller.selected_tags = set()
        self.tag_button.configure(text="Выбрать теги ▼")
        self.controller.apply_filters()

    def _open_tag_selector(self):
        self._safe_call(self.controller.show_tag_selector)

    def handle_tag_selection(self, selected_indices, close_func):
        self.controller.selected_tags = set(selected_indices)
        text = (
            f"Выбрано: {len(selected_indices)} ▼"
            if selected_indices
            else "Выбрать теги ▼"
        )
        self.tag_button.configure(text=text)

        # Сначала закрываем окно выбора тегов (это отвяжет прокрутку)
        close_func()

        # Затем обновляем таблицу
        self.controller.apply_filters()

    def _on_view_sort(self, col):
        if self.view_sort_col == col:
            self.view_sort_reverse = not self.view_sort_reverse
        else:
            self.view_sort_col, self.view_sort_reverse = col, False

        headers = {
            "title": "Название книги",
            "author": "Автор",
            "publisher": "Издательство",
            "year": "Год",
        }
        for c, txt in headers.items():
            arrow = (
                (" ▼" if self.view_sort_reverse else " ▲")
                if c == self.view_sort_col
                else ""
            )
            self.tree.heading(c, text=txt + arrow)
        self._safe_call(self.controller.apply_filters)

    def get_selected_book_id(self):
        sel = self.tree.selection()
        if not sel:
            return None
        item_tags = self.tree.item(sel[0], "tags")
        return int(item_tags[1]) if item_tags else None

    def _apply_treeview_styles(self):
        """Применяет кастомные стили таблицы с учетом текущей темы"""
        # Безопасная проверка: если контроллер еще не подключен (старт приложения)
        try:
            is_dark = self.controller.state.current_theme == "darkly"
        except AttributeError:
            is_dark = False
        bg_even = "#2b2b2b" if is_dark else "#F5F5F5"
        bg_odd = "#353535" if is_dark else "#D8D8D8"

        self.style.configure("Treeview", rowheight=144, font=("Segoe UI", 10, "bold"))
        self.style.configure("primary.Treeview", rowheight=144)
        self.style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

        if hasattr(self, 'tree'):
            self.tree.tag_configure("even_row", background=bg_even)
            self.tree.tag_configure("odd_row", background=bg_odd)
