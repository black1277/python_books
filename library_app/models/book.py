from dataclasses import dataclass, field

@dataclass
class Book:
    title: str
    author: str = ""
    publisher: str = ""
    year: int | None = None
    filename: str = ""
    cover: str = ""
    tags: list[int] = field(default_factory=list)