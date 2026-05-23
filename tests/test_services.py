import unittest
from unittest.mock import mock_open, patch, MagicMock
from library_app.services import storage
from library_app.services.book_service import BookService
from library_app.models.book import Book

class TestStorage(unittest.TestCase):

    @patch("os.path.exists", return_value=True) # ВАЖНО: Говорим, что файл существует
    @patch("builtins.open", new_callable=mock_open, read_data='[{"title": "Test"}]')
    def test_load_json_success(self, mock_file, mock_exists):
        data = storage.load_json("fake.json")
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["title"], "Test")

    @patch("os.path.exists", return_value=False) # ВАЖНО: Файла нет
    def test_load_json_file_not_found(self, mock_exists):
        data = storage.load_json("missing.json")
        self.assertEqual(data, [])

    @patch("library_app.services.storage._create_backup", return_value=True)
    @patch("os.path.exists", return_value=True)
    @patch("builtins.open", new_callable=mock_open)
    def test_save_json_success(self, mock_file, mock_exists, mock_backup):
        result = storage.save_json("fake.json", [{"title": "Test"}])
        self.assertTrue(result)
        mock_backup.assert_called_once_with("fake.json")
        mock_file.assert_called_once()

    @patch("os.path.exists", return_value=True)
    @patch("os.path.getmtime", return_value=1000000)
    @patch("os.listdir", return_value=["books_1.json", "books_2.json", "books_3.json"]) # ВАЖНО: 3 файла (лимит)
    @patch("os.remove")
    @patch("shutil.copy2")
    def test_backup_creates_and_limits(self, mock_copy, mock_remove, mock_listdir, mock_getmtime, mock_exists):
        storage.MAX_BACKUPS_PER_FILE = 3
        storage._create_backup("books.json")
        
        mock_remove.assert_called_once() # Должен удалиться самый старый
        mock_copy.assert_called_once()   # И создаться новый

    @patch("os.path.exists", return_value=True) # ВАЖНО: Файл существует
    @patch("builtins.open", new_callable=mock_open, read_data='[{"title": "Test", "year": 2020}]')
    def test_load_json_with_model(self, mock_file, mock_exists):
        data = storage.load_json("books.json", model=Book)
        self.assertIsInstance(data[0], Book)
        self.assertEqual(data[0].year, 2020)
        
    @patch("library_app.services.storage.messagebox") # Подменяем окна ошибок
    @patch("os.path.exists", return_value=True)
    @patch("builtins.open", new_callable=mock_open, read_data='{invalid json syntax}')
    def test_load_json_invalid_format(self, mock_file, mock_exists, mock_msgbox):
        """Тест: что происходит, если JSON файл испорчен"""
        data = storage.load_json("broken.json")
        self.assertEqual(data, [])
        # Проверяем, что программа попыталась сообщить об ошибке
        mock_msgbox.showerror.assert_called_once()

    # ВАЖНО: Путь к функциям должен указывать на то, где они ИСПОЛЬЗУЮТСЯ, 
    # а не там, где они ОПРЕДЕЛЕНЫ (library_app.services.storage.os...), 
    # чтобы подмена сработала внутри модуля.
    @patch("library_app.services.storage.os.makedirs")
    @patch("library_app.services.storage.os.path.isdir", return_value=False) # <--- ДОБАВИЛИ: Говорим, что папок нет
    @patch("library_app.services.storage.messagebox")
    def test_validate_and_create_dirs_accept(self, mock_msgbox, mock_isdir, mock_makedirs):
        """Тест: пользователь соглашается создать отсутствующие папки"""
        mock_msgbox.askyesno.return_value = True
        result = storage.validate_and_create_dirs(["img", "pdf"])
        
        self.assertTrue(result)
        self.assertEqual(mock_makedirs.call_count, 2) # Вызван для обеих папок

    @patch("library_app.services.storage.messagebox")
    def test_validate_and_create_dirs_reject(self, mock_msgbox):
        """Тест: пользователь отказывается создавать папки"""
        mock_msgbox.askyesno.return_value = False
        result = storage.validate_and_create_dirs(["missing_dir"])
        
        self.assertFalse(result)
        
    @patch("library_app.services.storage.messagebox")
    @patch("library_app.services.storage._create_backup", return_value=True)
    @patch("os.path.exists", return_value=True)
    @patch("builtins.open", side_effect=PermissionError("Отказано в доступе"))
    def test_save_json_permission_error(self, mock_file, mock_exists, mock_backup, mock_msgbox):
        """Тест: что происходит, если нет прав на запись файла"""
        result = storage.save_json("protected.json", [{"title": "Test"}])
        
        self.assertFalse(result) # Должно вернуться False (неуспех)
        # Должно показать ошибку пользователю, а не крашиться
        mock_msgbox.showerror.assert_called_once()
        
    @patch("library_app.services.storage.os.makedirs")
    @patch("library_app.services.storage.os.path.isdir", return_value=True) # Папки УЖЕ есть
    @patch("library_app.services.storage.messagebox")
    def test_validate_and_create_dirs_already_exist(self, mock_msgbox, mock_isdir, mock_makedirs):
        """Тест: если папки существуют, не задаем вопросов и не создаем их"""
        result = storage.validate_and_create_dirs(["img", "pdf"])
        
        self.assertTrue(result)
        mock_makedirs.assert_not_called() # Ничего создавать не должно
        mock_msgbox.askyesno.assert_not_called() # Окно вопроса НЕ должно появляться

    @patch("os.path.exists", return_value=True)
    @patch("os.listdir", return_value=[]) # Бэкапов пока нет
    @patch("os.remove")
    @patch("shutil.copy2")
    def test_backup_creates_without_deleting(self, mock_copy, mock_remove, mock_listdir, mock_exists):
        """Тест: создание первого бэкапа (удалять еще ничего не нужно)"""
        result = storage._create_backup("books.json")
        
        self.assertTrue(result)
        mock_copy.assert_called_once()   # Файл скопировался
        mock_remove.assert_not_called()  # Ничего не удалялось!
        
    @patch("library_app.services.storage.os.startfile")
    def test_open_pdf_success(self, mock_startfile):
        """Тест: вызов системного открытия PDF"""
        storage.open_pdf("test.pdf")
        mock_startfile.assert_called_once_with("test.pdf")

    @patch("library_app.services.storage.os.startfile", side_effect=FileNotFoundError)
    @patch("library_app.services.storage.messagebox")
    def test_open_pdf_not_found(self, mock_msgbox, mock_startfile):
        """Тест: если PDF файл для открытия не найден"""
        storage.open_pdf("missing.pdf")
        mock_msgbox.showerror.assert_called_once()
        
    @patch("library_app.services.storage.messagebox")
    @patch("os.path.exists", return_value=True)
    @patch("builtins.open", new_callable=mock_open, read_data='') # Пустая строка
    def test_load_json_empty_file(self, mock_file, mock_exists, mock_msgbox):
        """Тест: файл существует, но внутри ничего нет (пустота)"""
        data = storage.load_json("empty.json")
        self.assertEqual(data, [])
        mock_msgbox.showerror.assert_called_once()
        
    def test_recalculate_tags_empty_in_middle(self):
        """Тест: пустой тег в середине массива"""
        raw_tags = ["Фантастика", "", "Ужасы"]
        book1 = Book(title="Книга 1", tags=[0, 2]) # Должна стать [0, 1]
        book2 = Book(title="Книга 2", tags=[1])     # Ссылка на пустой тег, должна стать []
        
        cleaned_tags, updated_books = BookService.recalculate_tags_after_deletion(raw_tags, [book1, book2])
        
        self.assertEqual(cleaned_tags, ["Фантастика", "Ужасы"])
        self.assertEqual(updated_books[0].tags, [0, 1])
        self.assertEqual(updated_books[1].tags, [])

    def test_recalculate_tags_multiple_empty(self):
        """Тест: несколько пустых тегов подряд"""
        raw_tags = ["А", "", "", "Б", "В"]
        book = Book(title="Книга", tags=[0, 3, 4]) # Должна стать [0, 1, 2]
        
        cleaned_tags, updated_books = BookService.recalculate_tags_after_deletion(raw_tags, [book])
        
        self.assertEqual(cleaned_tags, ["А", "Б", "В"])
        self.assertEqual(updated_books[0].tags, [0, 1, 2])

    def test_recalculate_tags_no_empty(self):
        """Тест: пустых тегов нет, ничего не должно измениться"""
        raw_tags = ["Тег1", "Тег2"]
        book = Book(title="Книга", tags=[1])
        
        cleaned_tags, updated_books = BookService.recalculate_tags_after_deletion(raw_tags, [book])
        
        self.assertEqual(cleaned_tags, ["Тег1", "Тег2"])
        self.assertEqual(updated_books[0].tags, [1])