import os
from PIL import Image, ImageTk
import ttkbootstrap as ttkb


def _sanitize(val):
    """Превращает None в пустую строку и экранирует скобки для Tkinter"""
    if val is None:
        return ""
    return str(val).replace("{", "\\{").replace("}", "\\}")


class EditView:
    def __init__(self, parent, controller, notebook):
        self.controller = controller
        self.notebook = notebook
        self.edit_images = {}
        self.style = ttkb.Style()
        self.setup_ui(parent)

    def _apply_treeview_styles(self):
        # Безопасная проверка: если контроллер еще не подключен (старт приложения)
        try:
            is_dark = self.controller.state.current_theme == "darkly"
        except AttributeError:
            is_dark = False
        heading_bg = "#1e1e1e" if is_dark else "#90EE90"
        heading_fg = "white" if is_dark else "black"
        bg_even = "#2b2b2b" if is_dark else "#F5F5F5"
        bg_odd = "#353535" if is_dark else "#D8D8D8"

        self.style.configure("Edit.Treeview", rowheight=100, font=("Segoe UI", 10))
        self.style.configure(
            "Edit.Treeview.Heading",
            background=heading_bg,
            foreground=heading_fg,
            font=("Segoe UI", 10, "bold"),
        )

        if hasattr(self, "edit_tree"):
            self.edit_tree.tag_configure("even_row", background=bg_even)
            self.edit_tree.tag_configure("odd_row", background=bg_odd)

    def _safe_call(self, func, *args, **kwargs):
        if self.controller and func:
            return func(*args, **kwargs)

    def setup_ui(self, frame):
        btn_frame = ttkb.Frame(frame)
        btn_frame.pack(fill="x", padx=10, pady=10)

        search_frame = ttkb.Frame(frame)
        search_frame.pack(fill="x", padx=10, pady=(10, 0))
        ttkb.Label(search_frame, text="Быстрый поиск по названию:").pack(
            side="left", padx=(0, 5)
        )
        self.edit_search_var = ttkb.StringVar()
        ttkb.Entry(search_frame, textvariable=self.edit_search_var, width=40).pack(
            side="left", fill="x", expand=True
        )
        self.edit_search_var.trace_add(
            "write", lambda *args: self._safe_call(self.controller.apply_edit_search)
        )

        ttkb.Button(
            btn_frame,
            text="Добавить книгу",
            bootstyle="success",
            command=lambda: self._safe_call(self.controller.add_book),
        ).pack(side="left", padx=5)
        ttkb.Button(
            btn_frame,
            text="Редактировать",
            bootstyle="info",
            command=lambda: self._safe_call(self.controller.edit_selected),
        ).pack(side="left", padx=5)
        ttkb.Button(
            btn_frame,
            text="Удалить",
            bootstyle="danger",
            command=lambda: self._safe_call(self.controller.delete_selected),
        ).pack(side="left", padx=5)
        self.save_btn = ttkb.Button(
            btn_frame,
            text="Сохранить в JSON",
            bootstyle="primary",
            command=lambda: self._safe_call(self.controller.save_books),
        )
        self.save_btn.pack(side="right", padx=5)

        self._apply_treeview_styles()

        self.edit_tree = ttkb.Treeview(
            frame,
            columns=("title", "author", "publisher", "year", "tags"),
            show="tree headings",
            style="Edit.Treeview",
        )

        self.edit_tree.heading("#0", text="Обложка")
        self.edit_tree.column("#0", width=90, stretch=False, anchor="center")
        for col, txt, w, anch in [
            ("title", "Название", 300, "w"),
            ("author", "Автор", 180, "w"),
            ("publisher", "Издательство", 180, "w"),
            ("year", "Год", 80, "center"),
            ("tags", "Теги", 220, "w"),
        ]:
            self.edit_tree.heading(col, text=txt)
            self.edit_tree.column(col, width=w, anchor=anch)

        self.edit_tree.bind(
            "<Double-1>", lambda event: self._safe_call(self.controller.edit_selected)
        )
        self.edit_tree.pack(fill="both", expand=True, padx=10, pady=8)

    def refresh_table(self, books, get_img_path_func, str_tags, visible_indices=None):
        for item in self.edit_tree.get_children():
            self.edit_tree.delete(item)
        self.edit_images.clear()

        indices_to_show = (
            visible_indices if visible_indices is not None else range(len(books))
        )

        for visual_idx, i_real in enumerate(indices_to_show):
            book = books[i_real]
            tag_indices = book.tags
            tags_str = ", ".join(
                [str_tags[idx] for idx in tag_indices if idx < len(str_tags)]
            )
            year_str = str(book.year) if book.year is not None else ""

            photo = None
            cover_path = get_img_path_func(book.cover)
            if cover_path and os.path.exists(cover_path):
                try:
                    img = Image.open(cover_path).convert("RGB")
                    img.thumbnail((60, 80), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    self.edit_images[str(i_real)] = photo
                except:
                    pass

            row_color_tag = "even_row" if visual_idx % 2 == 0 else "odd_row"

            # values = (
            #     book.title,
            #     book.author,
            #     book.publisher,
            #     year_str,
            #     tags_str,
            # )
            values = (
                _sanitize(book.title),
                _sanitize(book.author),
                _sanitize(book.publisher),
                _sanitize(year_str),
                _sanitize(tags_str),
            )

            self.edit_tree.insert(
                "",
                "end",
                iid=str(i_real),
                image=_sanitize(photo),
                values=values,
                tags=(row_color_tag,),
            )

    def get_selected_index(self):
        sel = self.edit_tree.selection()
        return int(sel[0]) if sel else None

    def mark_unsaved(self):
        self.save_btn.configure(bootstyle="warning")

    def reset_save_btn(self):
        self.save_btn.configure(bootstyle="primary")
