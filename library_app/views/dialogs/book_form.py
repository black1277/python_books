import tkinter as tk
import ttkbootstrap as ttkb
from ttkbootstrap.dialogs import Messagebox

# Импортируем наш сервис валидации
from ...services.validators import (
    make_printable_length_validator,
    make_filename_validator,
    validate_year_input,
    validate_book_data_on_save
)


def _append_tag_to_var(var, tag_to_add):
    # Эта функция остается тут, так как она специфична для работы с tk.StringVar
    current_text = var.get()
    current_tags = [t.strip().lower() for t in current_text.split(",") if t.strip()]
    if tag_to_add.lower() not in current_tags:
        var.set(
            (current_text.rstrip() + ", " + tag_to_add)
            if current_text.strip()
            else tag_to_add
        )


def show_book_form(
    parent, book, is_new, index, str_tags, save_callback, resolve_tags_func
):
    form = ttkb.Toplevel(parent)
    form.title("Новая книга" if is_new else "Редактировать книгу")
    form.geometry("750x850")
    form.grab_set()

    entries = {}
    row = 0

    # Ссылаемся на функции из сервиса
    validation_rules = {
        "title": make_printable_length_validator(200),
        "author": make_printable_length_validator(100),
        "publisher": make_printable_length_validator(100),
        "year": validate_year_input,
        "filename": make_filename_validator(255),
        "cover": make_printable_length_validator(255),
    }

    for field_name, label in [
        ("title", "Title"),
        ("author", "Author"),
        ("publisher", "Publisher"),
        ("year", "Year"),
        ("filename", "Filename"),
        ("cover", "Cover"),
    ]:
        ttkb.Label(form, text=f"{label}:", font=("Segoe UI", 10, "bold")).grid(
            row=row, column=0, sticky="e", padx=15, pady=7
        )
        val = getattr(book, field_name)
        entry = ttkb.Entry(form, width=80, bootstyle="primary")
        entry.grid(row=row, column=1, padx=15, pady=7, sticky="w")
        entry.insert(0, str(val) if val is not None else "")

        if field_name in validation_rules:
            vcmd = (form.register(validation_rules[field_name]), "%P")
            entry.configure(validate="key", validatecommand=vcmd)

        entries[field_name] = entry
        row += 1

    entries["is_new"] = is_new
    entries["index"] = index

    # --- БЛОК ТЕГОВ ---
    ttkb.Label(form, text="Теги (через запятую):", font=("Segoe UI", 10, "bold")).grid(
        row=row, column=0, sticky="e", padx=15, pady=7
    )
    tags_var = tk.StringVar(
        value=", ".join(resolve_tags_func(str_tags, book.tags or []))
    )
    tags_entry = ttkb.Entry(form, textvariable=tags_var, width=80, bootstyle="primary")
    tags_entry.grid(row=row, column=1, padx=15, pady=7, sticky="w")

    tags_vcmd = (form.register(make_printable_length_validator(500)), "%P")
    tags_entry.configure(validate="key", validatecommand=tags_vcmd)
    row += 1

    if str_tags:
        btn_frame = ttkb.Labelframe(form, text="Быстрый выбор тегов из словаря:")
        btn_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=15, pady=(0, 5))
        inner_frame = ttkb.Frame(btn_frame)
        inner_frame.pack(fill="x", padx=5, pady=5)

        cols = 6
        for i, tag in enumerate(str_tags):
            r, c = divmod(i, cols)
            cmd = lambda t=tag: _append_tag_to_var(tags_var, t)
            ttkb.Button(
                inner_frame, text=tag, bootstyle="info-outline",
                padding=(5, 2), command=cmd,
            ).grid(row=r, column=c, sticky="ew", padx=1, pady=2)

        for c in range(cols):
            inner_frame.columnconfigure(c, weight=1)
        row += 1

    # --- КНОПКА СОХРАНЕНИЯ ---
    def validate_and_save():
        # 1. Собираем сырые данные в словарь
        form_data = {
            "title": entries["title"].get(),
            "year": entries["year"].get(),
            "filename": entries["filename"].get(),
        }

        # 2. Отдаем словарь в сервис валидации
        errors = validate_book_data_on_save(form_data)

        # 3. Обрабатываем результат
        if errors:
            Messagebox.show_warning(
                title="Ошибка валидации", message="\n\n".join(errors), parent=form
            )
            return

        save_callback(entries, tags_var, form)

    ttkb.Button(
        form, text="Сохранить", bootstyle="success", command=validate_and_save,
    ).grid(row=row, column=1, pady=20, sticky="e", padx=15)