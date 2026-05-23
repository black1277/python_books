import ttkbootstrap as ttkb

from .books_view import BooksView
from .edit_view import EditView
from .categories_view import CategoriesView


class MainWindow:
    def __init__(self, root, controller):
        self.root = root
        self._controller = controller  # Используем приватную переменную _controller

        self.root.title("Моя Библиотека")
        self.root.geometry("1300x750")

        self.notebook = ttkb.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        view_frame = ttkb.Frame(self.notebook)
        edit_frame = ttkb.Frame(self.notebook)
        categories_frame = ttkb.Frame(self.notebook)

        self.notebook.add(view_frame, text="📚 Просмотр книг")
        self.notebook.add(edit_frame, text="✏️ Управление книгами")
        self.notebook.add(categories_frame, text="📁 Категории")

        # Инициализация под-вьюшек (пока передаем None)
        self.books_view = BooksView(view_frame, self._controller, self.notebook)
        self.edit_view = EditView(edit_frame, self._controller, self.notebook)
        self.categories_view = CategoriesView(categories_frame, self._controller)

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_change)

    # --- МАГИЯ ЗДЕСЬ ---
    @property
    def controller(self):
        """Геттер: возвращаем контроллер, когда кто-то делает view.controller"""
        return self._controller

    @controller.setter
    def controller(self, value):
        """Сеттер: срабатывает, когда в main.py делается view.controller = controller"""
        self._controller = value
        # Автоматически прокидываем контроллер во все дочерние view!
        self.books_view.controller = value
        self.edit_view.controller = value
        self.categories_view.controller = value
    # ------------------

    def _on_tab_change(self, event):
        # ЗАЩИТА: Если контроллер еще не привязан (первая миллисекунда жизни окна) - игнорируем
        if not self._controller:
            return
        selected = self.notebook.select()
        # Индексы: 0 = view, 1 = edit, 2 = categories
        if selected == str(self.notebook.tabs()[0]):
            self._controller.on_books_tab_activated()
        elif selected == str(self.notebook.tabs()[2]):
            self._controller._refresh_all_ui()

    def switch_to_tab(self, tab_name):
        if tab_name == "books":
            self.notebook.select(0)
        elif tab_name == "categories":
            self.notebook.select(2)
