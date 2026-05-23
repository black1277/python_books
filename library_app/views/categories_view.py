import tkinter as tk
import ttkbootstrap as ttkb


class CategoriesView:
    def __init__(self, parent, controller):
        self.controller = controller
        self.cat_form_vars = {}
        self.cat_tags_text = None
        self.setup_ui(parent)

    def _safe_call(self, func, *args, **kwargs):
        if self.controller and func:
            return func(*args, **kwargs)

    def setup_ui(self, frame):
        self.frame = frame
        self._build_table()

    def _apply_treeview_styles(self):
        """Применяет стили таблицы (зебра и активная строка) в зависимости от темы"""
        # Безопасная проверка темы
        try:
            is_dark = self.controller.state.current_theme == "darkly"
        except AttributeError:
            is_dark = False

        # Цвета для зебры
        bg_even = "#2b2b2b" if is_dark else "#F5F5F5"
        bg_odd = "#353535" if is_dark else "#D8D8D8"

        # Цвета для активной категории
        active_bg = "#1a3a1a" if is_dark else "#d4edda"
        active_fg = "#75d675" if is_dark else "#155724"

        # Применяем цвета, только если таблица уже создана
        if hasattr(self, "cat_tree"):
            self.cat_tree.tag_configure("even_row", background=bg_even)
            self.cat_tree.tag_configure("odd_row", background=bg_odd)
            self.cat_tree.tag_configure(
                "active",
                background=active_bg,
                foreground=active_fg,
                font=("Segoe UI", 10, "bold"),
            )

    def _build_table(self):
        for w in self.frame.winfo_children():
            w.destroy()

        header_frame = ttkb.Frame(self.frame)
        header_frame.pack(fill="x", padx=15, pady=(15, 5))
        ttkb.Label(
            header_frame,
            text="📁 Управление категориями",
            font=("Segoe UI", 14, "bold"),
        ).pack(side="left")
        ttkb.Label(
            header_frame,
            text="• Двойной клик для загрузки",
            font=("Segoe UI", 9),
            foreground="gray",
        ).pack(side="left", padx=20)

        btn_frame = ttkb.Frame(self.frame)
        btn_frame.pack(fill="x", padx=15, pady=5)

        ttkb.Button(
            btn_frame,
            text="📥 Использовать",
            bootstyle="success",
            command=lambda: self._safe_call(self.controller.use_selected_category),
        ).pack(side="left", padx=5)
        ttkb.Button(
            btn_frame,
            text="➕ Добавить",
            bootstyle="success",
            command=lambda: self._safe_call(self.controller.start_add_category),
        ).pack(side="left", padx=5)
        ttkb.Button(
            btn_frame,
            text="✏️ Редактировать",
            bootstyle="info",
            command=lambda: self._safe_call(self.controller.edit_selected_category),
        ).pack(side="left", padx=5)
        ttkb.Button(
            btn_frame,
            text="🗑️ Удалить",
            bootstyle="danger",
            command=lambda: self._safe_call(self.controller.delete_selected_category),
        ).pack(side="left", padx=5)
        ttkb.Button(
            btn_frame,
            text="🔄 Обновить",
            bootstyle="secondary",
            command=lambda: self._safe_call(self.controller._refresh_all_ui),
        ).pack(side="right", padx=5)

        table_frame = ttkb.Frame(self.frame)
        table_frame.pack(fill="both", expand=True, padx=15, pady=10)

        self.cat_tree = ttkb.Treeview(
            table_frame,
            columns=("title", "file_json", "img", "pdf"),
            show="headings",
            height=10,
        )
        for col, txt, w in [
            ("title", "Название категории", 200),
            ("file_json", "Файл books.json", 250),
            ("img", "Папка img", 200),
            ("pdf", "Папка pdf", 200),
        ]:
            self.cat_tree.heading(col, text=txt)
            self.cat_tree.column(col, width=w, anchor="w")

        vsb = ttkb.Scrollbar(
            table_frame, orient="vertical", command=self.cat_tree.yview
        )
        self.cat_tree.configure(yscrollcommand=vsb.set)
        self.cat_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.cat_tree.bind(
            "<Double-1>",
            lambda e: self._safe_call(self.controller.use_selected_category),
        )

        self.cat_status = ttkb.Label(
            self.frame, text="", font=("Segoe UI", 9), foreground="gray", anchor="w"
        )
        self.cat_status.pack(fill="x", padx=15, pady=(0, 10))

        # ВАЖНО: Применяем стили сразу после создания таблицы
        self._apply_treeview_styles()

    def refresh_table(self, categories, current_category):
        self._build_table()  # Пересоздаем (это уже вызовет _apply_treeview_styles)
        for item in self.cat_tree.get_children():
            self.cat_tree.delete(item)

        is_base_active = current_category is None

        # Подготавливаем данные базовой категории
        if self.controller:
            values = (
                self.controller.state.base_category_data.title,
                self.controller.state.base_category_data.file_json,
                self.controller.state.base_category_data.img,
                self.controller.state.base_category_data.pdf,
            )
        else:
            values = ("Базовая", "books.json", "img", "pdf")

        # visual_idx нужен, чтобы чередование продолжалось сквозь базовую и пользовательские категории
        visual_idx = 0

        # Определяем тег для базовой категории (активная или зебра)
        base_tag = (
            "active"
            if is_base_active
            else ("even_row" if visual_idx % 2 == 0 else "odd_row")
        )

        self.cat_tree.insert("", "end", iid="base", values=values, tags=(base_tag,))
        visual_idx += 1

        for i, cat in enumerate(categories):
            is_cat_active = cat.title == (
                current_category.title if current_category else None
            )

            # Если категория активна - красим зеленым, иначе - чередуем цвета
            if is_cat_active:
                cat_tag = "active"
            else:
                cat_tag = "even_row" if visual_idx % 2 == 0 else "odd_row"

            self.cat_tree.insert(
                "",
                "end",
                iid=str(i),
                values=(cat.title, cat.file_json, cat.img, cat.pdf),
                tags=(cat_tag,),
            )
            visual_idx += 1

        active = (
            "Базовая"
            if is_base_active
            else (current_category.title if current_category else "Базовая")
        )
        self.cat_status.configure(
            text=f"Всего пользовательских категорий: {len(categories)} | Активная: {active}"
        )

    def get_selected_id(self):
        sel = self.cat_tree.selection()
        if not sel:
            return None
        return "base" if sel[0] == "base" else int(sel[0])

    def show_category_form(
        self, category_data, editing_index, save_callback, cancel_callback, tags_string
    ):
        for widget in self.frame.winfo_children():
            widget.pack_forget()

        title_text = (
            "✏️ Редактировать категорию"
            if editing_index is not None
            else "➕ Новая категория"
        )
        self.cat_form_frame = ttkb.Labelframe(
            self.frame, text=title_text, bootstyle="info"
        )
        self.cat_form_frame.pack(fill="both", expand=True, padx=15, pady=10)

        form_inner = ttkb.Frame(self.cat_form_frame)
        form_inner.pack(fill="x", padx=10, pady=10)

        self.cat_form_vars = {}
        for i, (label_text, key, val) in enumerate(
            [
                ("Название категории *", "title", category_data.title),
                ("Файл books.json *", "file_json", category_data.file_json),
                ("Папка с обложками (img)", "img", category_data.img),
                ("Папка с PDF (pdf)", "pdf", category_data.pdf),
            ]
        ):
            ttkb.Label(form_inner, text=label_text + ":", font=("Segoe UI", 9)).grid(
                row=i, column=0, sticky="e", padx=10, pady=5
            )
            self.cat_form_vars[key] = tk.StringVar(value=val)
            ttkb.Entry(form_inner, textvariable=self.cat_form_vars[key], width=40).grid(
                row=i, column=1, padx=10, pady=5, sticky="w"
            )

        row = 4
        ttkb.Label(
            form_inner, text="Словарь тегов (1 поле = 1 тег):", font=("Segoe UI", 9)
        ).grid(row=row, column=0, sticky="ne", padx=10, pady=5)

        # --- Прокручиваемый контейнер для отдельных полей ---
        tags_outer_frame = ttkb.Frame(form_inner)
        tags_outer_frame.grid(row=row, column=1, padx=10, pady=5, sticky="nsew")

        # Даем этой строке возможность растягиваться по высоте
        form_inner.rowconfigure(row, weight=1)

        # Canvas для скролла и внутренний фрейм для размещения полей
        self.cat_tags_canvas = tk.Canvas(
            tags_outer_frame, height=150, borderwidth=0, highlightthickness=0
        )
        tags_scroll = ttkb.Scrollbar(
            tags_outer_frame, orient="vertical", command=self.cat_tags_canvas.yview
        )
        self.tags_inner_frame = ttkb.Frame(self.cat_tags_canvas)

        self.tags_inner_frame.bind(
            "<Configure>",
            lambda e: self.cat_tags_canvas.configure(
                scrollregion=self.cat_tags_canvas.bbox("all")
            ),
        )

        self.cat_tags_canvas.create_window(
            (0, 0), window=self.tags_inner_frame, anchor="nw"
        )
        self.cat_tags_canvas.configure(yscrollcommand=tags_scroll.set)

        self.cat_tags_canvas.pack(side="left", fill="both", expand=True)
        tags_scroll.pack(side="right", fill="y")

        # Привязка прокрутки колесиком мыши к канвасу
        # Функция самой прокрутки (со страховкой от уничтоженного виджета)
        def _on_mousewheel(event):
            # winfo_exists проверяет, жив ли еще виджет
            if hasattr(self, "cat_tags_canvas") and self.cat_tags_canvas.winfo_exists():
                self.cat_tags_canvas.yview_scroll(
                    int(-1 * (event.delta / 120)), "units"
                )

        # Привязываем скролл ТОЛЬКО при наведении мыши на область тегов
        def _bind_mousewheel(event):
            if hasattr(self, "cat_tags_canvas") and self.cat_tags_canvas.winfo_exists():
                self.cat_tags_canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # Отвязываем скролл, как только мышь уходит с области тегов
        def _unbind_mousewheel(event):
            if hasattr(self, "cat_tags_canvas") and self.cat_tags_canvas.winfo_exists():
                self.cat_tags_canvas.unbind_all("<MouseWheel>")

        # Привязываем события входа и выхода мыши к канвасу
        self.cat_tags_canvas.bind("<Enter>", _bind_mousewheel)
        self.cat_tags_canvas.bind("<Leave>", _unbind_mousewheel)
        # -----------------------------------------------------------

        # Заполняем поля
        self.cat_tag_vars = []
        tags_list = (
            [t.strip() for t in tags_string.strip().split("\n")] if tags_string else []
        )

        # Если тегов нет, добавляем одно пустое поле
        if not tags_list:
            tags_list = [""]

        for i, tag_text in enumerate(tags_list):
            var = tk.StringVar(value=tag_text)
            self.cat_tag_vars.append(var)

            # pady=(0, 1) - минимальное расстояние в 1 пиксель между полями
            entry = ttkb.Entry(self.tags_inner_frame, textvariable=var, width=37)
            entry.grid(row=i, column=0, sticky="ew", pady=(0, 1))

        # Позволяем полям растягиваться по ширине
        self.tags_inner_frame.columnconfigure(0, weight=1)

        form_btns = ttkb.Frame(self.cat_form_frame)
        form_btns.pack(fill="x", padx=10, pady=(0, 10))
        ttkb.Button(
            form_btns, text="💾 Сохранить", bootstyle="success", command=save_callback
        ).pack(side="right", padx=5)
        ttkb.Button(
            form_btns, text="❌ Отмена", bootstyle="secondary", command=cancel_callback
        ).pack(side="right", padx=5)
