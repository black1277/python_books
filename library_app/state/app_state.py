from dataclasses import dataclass, field
from ..models.book import Book
from ..models.category import Category

@dataclass
class AppState:
    books: list[Book] = field(default_factory=list)
    filtered_books: list[Book] = field(default_factory=list)
    
    categories: list[Category] = field(default_factory=list)
    current_category: Category | None = None
    base_category_data: Category = None
    
    selected_tags: set[int] = field(default_factory=set)
    current_theme: str = "litera"
    is_modified: bool = False