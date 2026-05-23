from dataclasses import dataclass, field

@dataclass
class Category:
    title: str
    file_json: str = "books.json"
    img: str = "./data/base/img"
    pdf: str = "./data/base/pdf"
    is_base: bool = False
    str_tags: list[str] = field(default_factory=list)
