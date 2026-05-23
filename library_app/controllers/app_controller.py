import os
from tkinter import messagebox
from ..models.book import Book
from ..models.category import Category
from ..services import storage, cover_service
from ..services.book_service import BookService
from ..services.filter_service import FilterService
from ..state.app_state import AppState
from ..views.dialogs.book_form import show_book_form

BASE_CAT_TITLE = "Базовая (default)"

class AppController:
    def __init__(self, view):
        self.view = view

        # Внедрение зависимостей (Dependency Injection)
        self.state = AppState(
            base_category_data=Category(title=BASE_CAT_TITLE, is_base=True)
        )
        self.book_service = BookService()
        self.filter_service = FilterService

        self.editing_category_index = None

        # Инициализация
        self._load_categories()
        self._load_books()

    # ====================== ПРОКСИ ДЛЯ STATE ======================
    # Чтобы не переписывать весь View, делаем свойства-прокси
    @property
    def books(self): return self.state.books
    @property
    def filtered_books(self): return self.state.filtered_books
    @property
    def current_category(self): return self.state.current_category
    @property
    def is_modified(self): return self.state.is_modified
    @property
    def selected_tags(self): return self.state.selected_tags

    @is_modified.setter
    def is_modified(self, value): self.state.is_modified = value
    @selected_tags.setter
    def selected_tags(self, value): self.state.selected_tags = value
    @current_category.setter
    def current_category(self, value): self.state.current_category = value

    # ====================== КАТЕГОРИИ ======================
    def _load_categories(self):
        loaded_cats = storage.load_json("category.json", model=Category)
        self.state.categories = []
        if loaded_cats == []:
            return
        for cat in loaded_cats:
            if not hasattr(cat, "is_base"): cat.is_base = False
            if cat.is_base:
                self.state.base_category_data = cat
            else:
                self.state.categories.append(cat)

    def _save_categories(self):
        full_data = [self.state.base_category_data] + self.state.categories
        return storage.save_json("category.json", full_data)

    def get_str_tags(self):
        cat = self.state.current_category or self.state.base_category_data
        return cat.str_tags

    def _save_current_str_tags(self, str_tags):
        if self.state.current_category:
            self.state.current_category.str_tags = str_tags
        else:
            self.state.base_category_data.str_tags = str_tags
        self._save_categories()

    def get_current_paths(self):
        cat = self.state.current_category or self.state.base_category_data
        return {"books": cat.file_json, "img": cat.img, "pdf": cat.pdf}

    def get_img_path(self, filename):
        if not filename: return None
        return os.path.join(self.get_current_paths()["img"], filename)

    def get_pdf_path(self, filename):
        if not filename: return None
        return os.path.abspath(os.path.join(self.get_current_paths()["pdf"], filename))

    def switch_category(self, category_title):
        current_title = self.state.current_category.title if self.state.current_category else None
        if current_title == category_title:
            self._load_books()
            self._refresh_all_ui()
            self.view.switch_to_tab("books")
            return

        if not self.check_unsaved_changes(): return

        category = next((c for c in self.state.categories if c.title == category_title), None)
        if not category: return messagebox.showerror("Ошибка", "Категория не найдена")
        if not storage.validate_and_create_dirs([category.img, category.pdf]): return

        self.state.current_category = category
        self._load_books()
        self._refresh_all_ui()
        self.view.switch_to_tab("books")

    def reset_to_base_paths(self):
        if not self.check_unsaved_changes(): return
        self.state.current_category = None
        self._load_books()
        self._refresh_all_ui()

    def use_selected_category(self):
        sel_id = self.view.categories_view.get_selected_id()
        if sel_id is None:
            self.view.switch_to_tab("books")
            return
        if sel_id == "base": self.reset_to_base_paths()
        elif sel_id < len(self.state.categories): self.switch_category(self.state.categories[sel_id].title)

    def start_add_category(self):
        self.editing_category_index = None
        self.view.categories_view.show_category_form(Category(title=""), None, self.save_category_form, self.cancel_category_form, "")

    def edit_selected_category(self):
        sel_id = self.view.categories_view.get_selected_id()
        if sel_id is None:
            # Ничего не выделено -> открываем на редактирование ТЕКУЩУЮ активную категорию
            if self.state.current_category:
                # Находим индекс текущей категории в списке
                try:
                    idx = self.state.categories.index(self.state.current_category)
                    self.editing_category_index = idx
                    cat = self.state.current_category
                    self.view.categories_view.show_category_form(
                        cat, idx, self.save_category_form, self.cancel_category_form, "\n".join(cat.str_tags)
                    )
                except ValueError:
                    pass # На всякий случай, если состояние сбилось
            else:
                # Если текущая категория None, значит используется базовая
                self.edit_base_category()
            return
        if sel_id == "base": self.edit_base_category()
        else:
            if sel_id >= len(self.state.categories): return
            self.editing_category_index = sel_id
            cat = self.state.categories[sel_id]
            self.view.categories_view.show_category_form(cat, sel_id, self.save_category_form, self.cancel_category_form, "\n".join(cat.str_tags))

    def edit_base_category(self):
        self.editing_category_index = "base"
        self.view.categories_view.show_category_form(self.state.base_category_data, "base", self.save_category_form, self.cancel_category_form, "\n".join(self.state.base_category_data.str_tags))

    def delete_selected_category(self):
        sel_id = self.view.categories_view.get_selected_id()
        if not sel_id: return
        if sel_id == "base": return messagebox.showinfo("Информация", "Базовую категорию нельзя удалить.")

        cat_title = self.state.categories[sel_id].title
        is_active = self.state.current_category and self.state.current_category.title == cat_title
        msg = f"⚠️ Категория «{cat_title}» сейчас активна!\nУдалить и сбросить?" if is_active else f"Удалить категорию «{cat_title}»?"

        if not messagebox.askyesno("Подтверждение", msg): return
        if is_active: self.reset_to_base_paths()

        del self.state.categories[sel_id]
        if self._save_categories():
            self._refresh_all_ui()
            messagebox.showinfo("Удалено", f"Категория «{cat_title}» удалена")

    def save_category_form(self):
        vars = self.view.categories_view.cat_form_vars
        title, file_json = vars["title"].get().strip(), vars["file_json"].get().strip()
        img, pdf = vars["img"].get().strip() or "img", vars["pdf"].get().strip() or "pdf"
        if not title or not file_json: return messagebox.showerror("Ошибка", "Название и файл books.json обязательны!")

        # Получаем сырые теги из полей (с возможными пустотами)
        raw_tags = [var.get().strip() for var in self.view.categories_view.cat_tag_vars]

        # ВЫЗОВ АЛГОРИТМА ПЕРЕСЧЕТА
        str_tags, self.state.books = self.book_service.recalculate_tags_after_deletion(
            raw_tags,
            self.state.books
        )

        # НОВОЕ: Если были удалены пустые теги, длина массива изменится.
        # В этом случае НЕМЕДЛЕННО перезаписываем файл книг на диск!
        if len(raw_tags) != len(str_tags):
            self.save_books()

        if self.editing_category_index == "base":
            self.state.base_category_data = Category(title=title, is_base=True, file_json=file_json, img=img, pdf=pdf, str_tags=str_tags)
            if self._save_categories():
                self._refresh_all_ui()
                self.cancel_category_form()
                messagebox.showinfo("Успех", "Базовая категория сохранена!")
            return

        if any(c.title == title for i, c in enumerate(self.state.categories) if i != self.editing_category_index):
            return messagebox.showerror("Ошибка", "Категория с таким названием уже есть!")
        if not storage.validate_and_create_dirs([img, pdf]): return

        new_cat = Category(title=title, file_json=file_json, img=img, pdf=pdf, str_tags=str_tags)
        if self.editing_category_index is None:
            self.state.categories.append(new_cat)
        else:
            old_title = self.state.categories[self.editing_category_index].title
            self.state.categories[self.editing_category_index] = new_cat
            if self.state.current_category and self.state.current_category.title == old_title:
                self.state.current_category = new_cat

        if self._save_categories():
            self._refresh_all_ui()
            self.cancel_category_form()
            messagebox.showinfo("Успех", f"Категория «{title}» сохранена!")

    def cancel_category_form(self):
        self.view.categories_view.refresh_table(self.state.categories, self.state.current_category)

    # ====================== КНИГИ ======================
    def _load_books(self):
        paths = self.get_current_paths()
        self.state.books = self.book_service.load_books(paths["books"], self.get_str_tags())

    def save_books(self):
        if self.book_service.save_books(self.get_current_paths()["books"], self.state.books):
            self.state.is_modified = False
            self.view.edit_view.reset_save_btn()
            return True
        return False

    def mark_unsaved(self):
        self.state.is_modified = True
        self.view.edit_view.mark_unsaved()

    def check_unsaved_changes(self):
        if not self.state.is_modified: return True
        result = messagebox.askyesnocancel("Несохраненные изменения", "Сохранить перед продолжением?", icon="warning")
        if result is True: return self.save_books()
        elif result is False:
            self.state.is_modified = False
            self.view.edit_view.reset_save_btn()
            return True
        return False

    def add_book(self):
        show_book_form(self.view.root, Book(title=""), True, None, self.get_str_tags(), self._handle_book_save, self.book_service.resolve_tags_to_strings)

    def edit_selected(self):
        idx = self.view.edit_view.get_selected_index()
        if idx is None: return messagebox.showwarning("Внимание", "Выберите книгу")
        show_book_form(self.view.root, self.state.books[idx], False, idx, self.get_str_tags(), self._handle_book_save, self.book_service.resolve_tags_to_strings)

    def delete_selected(self):
        idx = self.view.edit_view.get_selected_index()
        if idx is None: return
        if messagebox.askyesno("Подтверждение", "Удалить книгу?"):
            del self.state.books[idx]
            self.apply_edit_search()
            self.apply_filters()
            self.update_all_comboboxes()
            self.mark_unsaved()

    def _handle_book_save(self, entries, tags_var, form_window):
        year_str = entries["year"].get().strip()
        year_val = int(year_str) if year_str else None
        filename_val = entries["filename"].get().strip()
        cover_val = entries["cover"].get().strip()

        if not cover_val and filename_val:
            paths = self.get_current_paths()
            cover_val = cover_service.create_cover_from_pdf(self.get_pdf_path(filename_val), paths["img"])

        input_tags = [t.strip() for t in tags_var.get().split(",") if t.strip()]
        tag_indices, tags_changed = self.book_service.resolve_tags_to_indices(input_tags, self.get_str_tags())
        if tags_changed: self._save_current_str_tags(self.get_str_tags())

        new_book = Book(title=entries["title"].get().strip(), author=entries["author"].get().strip(), publisher=entries["publisher"].get().strip(), year=year_val, filename=filename_val, cover=cover_val, tags=tag_indices)

        if not new_book.title or not new_book.filename: return messagebox.showerror("Ошибка", "Название и имя PDF обязательны!")

        if entries.get("is_new", True): self.state.books.append(new_book)
        else: self.state.books[entries["index"]] = new_book

        self.apply_edit_search()
        self.apply_filters()
        self.update_all_comboboxes()
        self.mark_unsaved()
        form_window.destroy()

    # ====================== ЕДИНАЯ ТОЧКА ОБНОВЛЕНИЯ UI ======================
    def _refresh_all_ui(self):
        """Централизованный метод обновления всех таблиц и фильтров"""
        self.apply_filters()
        self.apply_edit_search()
        self.update_all_comboboxes()
        self.view.books_view.update_category_label(self.state.current_category)
        self.view.categories_view.refresh_table(self.state.categories, self.state.current_category)

    # ====================== ФИЛЬТРЫ И СОРТИРОВКА ======================
    def apply_filters(self):
        query = self.view.books_view.search_var.get().lower().strip()
        publisher = self.filter_service.clean_combobox_value(self.view.books_view.publisher_var.get().strip())
        year = self.filter_service.clean_combobox_value(self.view.books_view.year_var.get().strip())

        self.state.filtered_books = self.filter_service.apply_filters(
            books=self.state.books,
            query=query, publisher=publisher, year=year, selected_tags=self.state.selected_tags
        )
        col = getattr(self.view.books_view, "view_sort_col", "")
        rev = getattr(self.view.books_view, "view_sort_reverse", False)
        self.state.filtered_books = self.filter_service.sort_books(self.state.filtered_books, col, rev)
        self.view.books_view.refresh_table(self.state.filtered_books, self.get_img_path, self.get_str_tags())

    def apply_edit_search(self):
        query = self.view.edit_view.edit_search_var.get().lower().strip()
        if not query:
            self.view.edit_view.refresh_table(self.state.books, self.get_img_path, self.get_str_tags(), None)
        else:
            visible_indices = [i for i, book in enumerate(self.state.books) if query in book.title.lower()]
            self.view.edit_view.refresh_table(self.state.books, self.get_img_path, self.get_str_tags(), visible_indices)

    def reset_filters(self):
        self.view.books_view.reset_filters()

    def update_all_comboboxes(self):
        pub_counts = {}
        for b in self.state.books:
            if b.publisher: pub_counts[b.publisher] = pub_counts.get(b.publisher, 0) + 1
        pubs = sorted([f"{p} ({c})" for p, c in pub_counts.items()])

        year_counts = {}
        for b in self.state.books:
            if b.year is not None: year_counts[str(b.year)] = year_counts.get(str(b.year), 0) + 1
        years = sorted([f"{y} ({c})" for y, c in year_counts.items()], reverse=True)

        self.view.books_view.update_comboboxes(pubs, years)

    # ====================== ДЕЙСТВИЯ ИНТЕРФЕЙСА ======================
    def on_double_click(self, event):
        book_id = self.view.books_view.get_selected_book_id()
        if not book_id: return
        book = next((b for b in self.state.books if id(b) == book_id), None)
        if not book: return
        pdf_path = self.get_pdf_path(book.filename)
        if not pdf_path or not os.path.exists(pdf_path): return messagebox.showerror("Не найдено", f"Файл не найден:\n{pdf_path}")
        storage.open_pdf(pdf_path)

    def show_tag_selector(self):
        str_tags = self.get_str_tags()
        if not str_tags: return messagebox.showinfo("Информация", "Список тегов пуст.")
        from ..views.dialogs.tag_selector import show_tag_selector
        show_tag_selector(self.view.root, str_tags, self.state.selected_tags, self.view.books_view.handle_tag_selection)

    def toggle_theme(self):
        if self.state.current_theme == "litera":
            self.state.current_theme = "darkly"
            self.view.books_view.theme_btn.configure(text="☀️ Светлая тема")
        else:
            self.state.current_theme = "litera"
            self.view.books_view.theme_btn.configure(text="🌙 Темная тема")
        self.view.root.style.theme_use(self.state.current_theme)
        self.view.books_view._apply_treeview_styles()
        self.view.edit_view._apply_treeview_styles()
        self.view.books_view.refresh_table(self.state.filtered_books, self.get_img_path, self.get_str_tags())
        self.view.edit_view.refresh_table(self.state.books, self.get_img_path, self.get_str_tags(), None)

    def on_books_tab_activated(self):
        self.update_all_comboboxes()
        self.apply_filters()
        self.view.books_view.update_category_label(self.state.current_category)
