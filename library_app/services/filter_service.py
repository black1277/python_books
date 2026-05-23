from ..models.book import Book

class FilterService:
    @staticmethod
    def apply_filters(
        books: list[Book],
        query: str = "",
        publisher: str = "",
        year: str = "",
        selected_tags: set[int] | None = None,
    ) -> list[Book]:
        query = query.lower().strip()
        return [
            book for book in books
            if (
                (not query or query in book.title.lower() or query in book.author.lower())
                and (not selected_tags or selected_tags & set(book.tags))
                and (not publisher or book.publisher == publisher)
                and (not year or str(book.year if book.year is not None else "") == year)
            )
        ]

    @staticmethod
    def sort_books(books: list[Book], column: str, reverse: bool = False) -> list[Book]:
        if not column:
            return books

        def get_sort_key(book: Book):
            val = getattr(book, column, "")
            if column == "year":
                try:
                    return int(val) if val is not None else 0
                except (ValueError, TypeError):
                    return 0
            return str(val).lower() if val else ""

        return sorted(books, key=get_sort_key, reverse=reverse)

    @staticmethod
    def clean_combobox_value(val: str) -> str:
        if not val:
            return ""
        if " (" in val:
            return val.rsplit(" (", 1)[0]
        return val