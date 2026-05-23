import unittest
from library_app.models.book import Book
from library_app.models.category import Category

class TestModels(unittest.TestCase):
    def test_book_creation_defaults(self):
        book = Book(title="Test Book")
        self.assertEqual(book.title, "Test Book")
        self.assertEqual(book.author, "")
        self.assertIsNone(book.year) # Важно: год по умолчанию None, а не 0
        self.assertEqual(book.tags, [])

    def test_category_creation_defaults(self):
        cat = Category(title="Фантастика")
        self.assertEqual(cat.title, "Фантастика")
        self.assertEqual(cat.file_json, "books.json")
        self.assertFalse(cat.is_base)
        self.assertEqual(cat.str_tags, [])
        
    def test_book_tags_independence(self):
        """Проверяем, что изменение тегов одной книги не влияет на другую"""
        book1 = Book(title="Book 1")
        book2 = Book(title="Book 2")
        
        book1.tags.append(99)
        
        # Список book2 должен остаться пустым!
        self.assertEqual(book1.tags, [99])
        self.assertEqual(book2.tags, [])