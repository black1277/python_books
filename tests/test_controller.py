import unittest
from unittest.mock import MagicMock, patch
from library_app.controllers.app_controller import AppController
from library_app.models.book import Book
from library_app.models.category import Category

class TestController(unittest.TestCase):
    
    def setUp(self):
        """Создаем фейковый View для каждого теста"""
        self.mock_view = MagicMock()
        
        # Имитируем структуру нашего нового MainWindow
        self.mock_view.books_view = MagicMock()
        self.mock_view.edit_view = MagicMock()
        self.mock_view.categories_view = MagicMock()
        self.mock_view.switch_to_tab = MagicMock()
        
        # Имитируем дефолтные значения переменных UI
        self.mock_view.books_view.search_var.get.return_value = ""
        self.mock_view.books_view.publisher_var.get.return_value = ""
        self.mock_view.books_view.year_var.get.return_value = ""
        self.mock_view.books_view.selected_tags = set()

        self.mock_view.edit_view.edit_search_var.get.return_value = ""        
        # Имитируем дефолтные значения для сортировки
        self.mock_view.books_view.view_sort_col = ""
        self.mock_view.books_view.view_sort_reverse = False
        
        # Запускаем "заглушки" для файловой системы
        self.patcher_load = patch("library_app.controllers.app_controller.storage.load_json", return_value=[])
        self.patcher_save = patch("library_app.controllers.app_controller.storage.save_json", return_value=True)
        
        self.mock_load = self.patcher_load.start() 
        self.mock_save = self.patcher_save.start() 
        
        # Создаем контроллер (заглушки уже активны)
        self.controller = AppController(self.mock_view)

    def tearDown(self):
        """Отключаем заглушки"""
        self.patcher_load.stop()
        self.patcher_save.stop()

    def test_resolve_tags_to_indices(self):
        """Проверяем конвертацию строковых тегов в индексы через BookService"""
        self.controller.state.base_category_data.str_tags = ["Фантастика", "Ужасы"]
        indices, changed = self.controller.book_service.resolve_tags_to_indices(
            ["Ужасы"], 
            self.controller.state.base_category_data.str_tags
        )
        self.assertEqual(indices, [1])

    def test_resolve_tags_adds_new_tag(self):
        """Проверяем, что новый тег добавляется в переданный список"""
        tags_list = ["Фантастика"]
        indices, changed = self.controller.book_service.resolve_tags_to_indices(["Детектив"], tags_list)
        
        self.assertEqual(indices, [1])
        self.assertTrue(changed)
        self.assertIn("Детектив", tags_list)

    def test_filter_by_search_query(self):
        """Тест фильтрации по тексту"""

        self.controller.state.books = [
            Book(title="Война и мир", author="Толстой"),
            Book(title="Мастер и Маргарита", author="Булгаков"),
            Book(title="Анна Каренина", author="Толстой")
        ]
        
        self.mock_view.books_view.search_var.get.return_value = "толстой"
        self.controller.apply_filters()
        
        self.assertEqual(len(self.controller.state.filtered_books), 2)
        self.assertEqual(self.controller.state.filtered_books[0].title, "Война и мир")

    def test_filter_by_year(self):
        """Тест фильтрации по году (число)"""

        self.controller.state.books = [
            Book(title="Книга 1", year=2020),
            Book(title="Книга 2", year=2021),
            Book(title="Книга 3", year=None) 
        ]
        
        self.mock_view.books_view.year_var.get.return_value = "2020"
        self.controller.apply_filters()
        
        self.assertEqual(len(self.controller.state.filtered_books), 1)
        self.assertEqual(self.controller.state.filtered_books[0].year, 2020)

    def test_sort_view_books_ascending(self):
        """Тест сортировки по году (по возрастанию) через FilterService"""
        books_to_sort = [
            Book(title="C", year=2022),
            Book(title="A", year=2020),
            Book(title="B", year=2021)
        ]
        
        # ИСПРАВЛЕНО: Сортировка теперь делегируется FilterService
        sorted_books = self.controller.filter_service.sort_books(books_to_sort, "year", False)
        
        titles = [b.title for b in sorted_books]
        self.assertEqual(titles, ["A", "B", "C"])

    def test_sort_view_books_descending(self):
        """Тест сортировки по заголовку (по убыванию) через FilterService"""
        books_to_sort = [
            Book(title="Яблоко"),
            Book(title="Апельсин"),
            Book(title="Банан")
        ]
        

        sorted_books = self.controller.filter_service.sort_books(books_to_sort, "title", True)
        
        titles = [b.title for b in sorted_books]
        self.assertEqual(titles, ["Яблоко", "Банан", "Апельсин"])

    def test_use_selected_category_index_zero(self):
        """РЕГРЕССИОННЫЙ ТЕСТ: Баг, когда индекс 0 воспринимался как False"""
        cat = Category(title="Моя категория")
        self.controller.state.categories = [cat]
        
        self.mock_view.categories_view.get_selected_id.return_value = 0
        self.controller.check_unsaved_changes = MagicMock(return_value=True)
        
        with patch("library_app.controllers.app_controller.storage.validate_and_create_dirs", return_value=True):
            with patch.object(self.controller, '_load_books'): 
                self.controller.use_selected_category()
        
        self.assertEqual(self.controller.state.current_category.title, "Моя категория")
        
    def test_clean_combobox_value_with_count(self):
        """Тест: корректная очистка строки 'АСТ (5)' от счетчика"""
        self.assertEqual(self.controller.filter_service.clean_combobox_value("АСТ (5)"), "АСТ")
        self.assertEqual(self.controller.filter_service.clean_combobox_value("2020 (15)"), "2020")

    def test_clean_combobox_value_without_count(self):
        """Тест: строка без счетчика не должна ломаться"""
        self.assertEqual(self.controller.filter_service.clean_combobox_value("Мир"), "Мир")
        self.assertEqual(self.controller.filter_service.clean_combobox_value(""), "")

    @patch("library_app.controllers.app_controller.messagebox")
    def test_check_unsaved_changes_no_changes(self, mock_msgbox):
        """Тест: если нет изменений, диалог не должен появляться"""
        self.controller.state.is_modified = False
        result = self.controller.check_unsaved_changes()
        
        self.assertTrue(result)
        mock_msgbox.askyesnocancel.assert_not_called()

    @patch("library_app.controllers.app_controller.messagebox")
    def test_check_unsaved_changes_discard(self, mock_msgbox):
        """Тест: пользователь нажимает 'Нет' (отменить изменения)"""
        self.controller.state.is_modified = True
        mock_msgbox.askyesnocancel.return_value = False
        
        result = self.controller.check_unsaved_changes()
        
        self.assertTrue(result) 
        self.assertFalse(self.controller.state.is_modified) 
        self.mock_view.edit_view.reset_save_btn.assert_called_once()

    @patch("library_app.controllers.app_controller.messagebox")
    def test_check_unsaved_changes_cancel(self, mock_msgbox):
        """Тест: пользователь нажимает 'Отмена' (прервать действие)"""
        self.controller.state.is_modified = True
        mock_msgbox.askyesnocancel.return_value = None
        
        result = self.controller.check_unsaved_changes()
        
        self.assertFalse(result) 
        self.assertTrue(self.controller.state.is_modified)

    @patch("library_app.controllers.app_controller.messagebox")
    def test_delete_selected_book(self, mock_msgbox):
        """Тест: удаление книги из списка"""
        self.controller.state.books = [Book(title="Книга 1"), Book(title="Книга 2")]
        
        self.mock_view.edit_view.get_selected_index.return_value = 0
        mock_msgbox.askyesno.return_value = True
        
        self.controller.delete_selected()
        
        self.assertEqual(len(self.controller.state.books), 1)
        self.assertEqual(self.controller.state.books[0].title, "Книга 2")
        self.mock_view.edit_view.mark_unsaved.assert_called_once()

    @patch("library_app.controllers.app_controller.messagebox")
    def test_delete_selected_no_selection(self, mock_msgbox):
        """Тест: попытка удалить, когда ничего не выбрано"""
        self.mock_view.edit_view.get_selected_index.return_value = None
        
        self.controller.delete_selected()
        
        mock_msgbox.askyesno.assert_not_called()

    @patch("library_app.controllers.app_controller.messagebox")
    def test_reset_to_base_paths(self, mock_msgbox):
        """Тест: сброс к базовой категории"""
        fake_cat = Category(title="Какая-то категория")
        self.controller.state.current_category = fake_cat
        self.controller.check_unsaved_changes = MagicMock(return_value=True)
        
        with patch.object(self.controller, '_refresh_all_ui'):
            self.controller.reset_to_base_paths()
        
        self.assertIsNone(self.controller.state.current_category)

        
    def test_apply_filters_sorts_ascending_by_default(self):
        """Тест: клик по новой колонке сортирует по возрастанию"""
        self.controller.state.books = [
            Book(title="Вишня", year=2020),
            Book(title="Апельсин", year=2021),
            Book(title="Банан", year=2019)
        ]
        
        # Имитируем, что View изменил свои переменные после клика пользователя
        self.mock_view.books_view.view_sort_col = "title"
        self.mock_view.books_view.view_sort_reverse = False
        
        self.controller.apply_filters()
        
        titles = [b.title for b in self.controller.state.filtered_books]
        self.assertEqual(titles, ["Апельсин", "Банан", "Вишня"])

    def test_apply_filters_sorts_descending_on_second_click(self):
        """Тест: повторный клик по той же колонке сортирует по убыванию"""
        self.controller.state.books = [
            Book(title="Вишня", year=2020),
            Book(title="Апельсин", year=2021),
            Book(title="Банан", year=2019)
        ]
        
        # Имитируем повторный клик (направление изменилось на True)
        self.mock_view.books_view.view_sort_col = "year"
        self.mock_view.books_view.view_sort_reverse = True
        
        self.controller.apply_filters()
        
        years = [b.year for b in self.controller.state.filtered_books]
        self.assertEqual(years, [2021, 2020, 2019])

    def test_apply_filters_combines_search_and_sort(self):
        """Тест: сортировка работает вместе с текстовым фильтром"""
        self.controller.state.books = [
            Book(title="Книга А", author="Пушкин"),
            Book(title="Книга Б", author="Лермонтов"),
            Book(title="Статья А", author="Есенин")
        ]
        
        # Включили поиск по "Книга" (должно остаться 2 книги)
        self.mock_view.books_view.search_var.get.return_value = "книга"
        # Включили сортировку по автору
        self.mock_view.books_view.view_sort_col = "author"
        self.mock_view.books_view.view_sort_reverse = False
        
        self.controller.apply_filters()
        
        # Проверяем, что фильтр сработал
        self.assertEqual(len(self.controller.state.filtered_books), 2)
        # Проверяем, что сортировка сработала внутри отфильтрованного списка
        authors = [b.author for b in self.controller.state.filtered_books]
        self.assertEqual(authors, ["Лермонтов", "Пушкин"]) # По алфавиту