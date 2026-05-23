import tkinter as tk
import ttkbootstrap as ttkb


def show_tag_selector(parent, str_tags, selected_tags_indices, apply_callback):
    selector = ttkb.Toplevel(parent)
    selector.title("Выбор тегов")
    selector.geometry("750x500")
    selector.grab_set()

    ttkb.Label(selector, text="Выберите теги:", font=("Segoe UI", 12, "bold")).pack(
        pady=(15, 8)
    )

    if not str_tags:
        ttkb.Label(selector, text="Теги пока отсутствуют", foreground="gray").pack(
            pady=20
        )
        ttkb.Button(
            selector, text="Закрыть", bootstyle="secondary", command=selector.destroy
        ).pack(pady=10)
        return

    main_frame = ttkb.Frame(selector)
    main_frame.pack(fill="both", expand=True, padx=15, pady=5)
    canvas = tk.Canvas(main_frame, highlightthickness=0)
    scrollbar = ttkb.Scrollbar(
        main_frame, orient="vertical", command=canvas.yview, bootstyle="round"
    )
    scrollable_frame = ttkb.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", tags="frame")

    def on_canvas_configure(event):
        canvas.itemconfig("frame", width=event.width)

    canvas.bind("<Configure>", on_canvas_configure)

    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    canvas.bind_all("<MouseWheel>", _on_mousewheel)
    canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
    canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

    def _on_closing():
        canvas.unbind_all("<MouseWheel>")
        canvas.unbind_all("<Button-4>")
        canvas.unbind_all("<Button-5>")
        selector.destroy()

    selector.protocol("WM_DELETE_WINDOW", _on_closing)

    check_vars = {
        i: tk.BooleanVar(value=(i in selected_tags_indices))
        for i in range(len(str_tags))
    }

    num_cols = 4
    for i, tag in enumerate(str_tags):
        row_idx = i // num_cols
        col_idx = i % num_cols
        ttkb.Checkbutton(
            scrollable_frame, text=tag, variable=check_vars[i], bootstyle="primary"
        ).grid(row=row_idx, column=col_idx, sticky="w", padx=10, pady=4)
    for c in range(num_cols):
        scrollable_frame.columnconfigure(c, weight=1)

    btn_frame = ttkb.Frame(selector)
    btn_frame.pack(fill="x", pady=15, padx=15)
    ttkb.Button(
        btn_frame, text="Отмена", bootstyle="secondary", width=12, command=_on_closing
    ).pack(side="right", padx=5)

    def on_apply():
        selected = {i for i, var in check_vars.items() if var.get()}
        apply_callback(selected, _on_closing)

    ttkb.Button(
        btn_frame, text="Применить", bootstyle="success", width=12, command=on_apply
    ).pack(side="right", padx=5)