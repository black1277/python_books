from ..models.book import Book
from ..services import storage

class BookService:
    @staticmethod
    def load_books(file_path: str, str_tags: list[str]) -> list[Book]:
        books = storage.load_json(file_path, model=Book)

        needs_save = False

        for book in books:
            if book.tags and isinstance(book.tags[0], str):
                book.tags = BookService.resolve_tags_to_indices(
                    [t.strip() for t in book.tags], str_tags
                )
                needs_save = True

        if needs_save:
            storage.save_json(file_path, books)

        return books

    @staticmethod
    def save_books(file_path: str, books: list[Book]) -> bool:
        return storage.save_json(file_path, books)

    @staticmethod
    def recalculate_tags_after_deletion(
        raw_tags: list[str], books: list[Book]
    ) -> tuple[list[str], list[Book]]:
        """
        Удаляет пустые теги из словаря и сдвигает индексы в книгах.
        """
        # 1. Находим индексы пустых тегов
        empty_indices = {i for i, tag in enumerate(raw_tags) if not tag.strip()}

        # Если пустых нет, возвращаем как есть (ничего делать не надо)
        if not empty_indices:
            return raw_tags, books

        # 2. Создаем новый массив без пустых значений
        cleaned_tags = [tag for tag in raw_tags if tag.strip()]

        # 3. Перебираем книги и пересчитываем их индексы
        for book in books:
            if not book.tags:
                continue

            new_book_tags = []
            for t_idx in book.tags:
                # Если книга ссылалась на пустой тег — просто удаляем эту ссылку
                if t_idx in empty_indices:
                    continue

                # Считаем, сколько пустых тегов было ДО текущего индекса.
                # Это и есть величина сдвига.
                shift = sum(1 for empty_idx in empty_indices if empty_idx < t_idx)

                # Добавляем сдвинутый индекс
                new_book_tags.append(t_idx - shift)

            book.tags = new_book_tags

        return cleaned_tags, books

    @staticmethod
    def resolve_tags_to_indices(tag_strings: list[str], str_tags: list[str]) -> list[int]:
        indices = []
        tags_changed = False
        for t in tag_strings:
            if t not in str_tags:
                str_tags.append(t)
                tags_changed = True
            indices.append(str_tags.index(t))
        return indices, tags_changed

    @staticmethod
    def resolve_tags_to_strings(str_tags: list[str], tag_indices: list[int]) -> list[str]:
        return [str_tags[i] for i in tag_indices if i < len(str_tags)]
