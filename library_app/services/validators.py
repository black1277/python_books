from datetime import datetime

# Константы для валидации
INVALID_FILENAME_CHARS = r'\/:*?"<>|'
MIN_BOOK_YEAR = 1900


def make_printable_length_validator(max_len: int):
    """Фабрика: разрешает только печатные символы с ограничением длины."""
    def validate(new_value: str) -> bool:
        return len(new_value) <= max_len and new_value.isprintable()
    return validate


def make_filename_validator(max_len: int):
    """Фабрика: валидация имени файла (длина, печатность, отсутствие системных символов)."""
    def validate(new_value: str) -> bool:
        if len(new_value) > max_len or not new_value.isprintable():
            return False
        return not any(char in INVALID_FILENAME_CHARS for char in new_value)
    return validate


def validate_year_input(new_value: str) -> bool:
    """Для real-time ввода: только цифры, максимум 4 символа."""
    if not new_value:
        return True
    return new_value.isdigit() and len(new_value) <= 4


def validate_book_data_on_save(data: dict) -> list[str]:
    """
    Сложная (комплексная) валидация перед сохранением.
    На вход ожидает словарь вида: {'title': '...', 'year': '...', 'filename': '...'}
    Возвращает список строк с ошибками. Если список пуст — данные валидны.
    """
    errors = []

    # 1. Проверка на пустоту
    if not data.get("title", "").strip():
        errors.append("Поле 'Title' не может быть пустым.")

    # 2. Логическая проверка года
    year_str = data.get("year", "").strip()
    if year_str:
        if year_str.isdigit():
            year_int = int(year_str)
            current_year = datetime.now().year
            if not (MIN_BOOK_YEAR <= year_int <= current_year + 1):
                errors.append(
                    f"Год должен быть в диапазоне от {MIN_BOOK_YEAR} до {current_year + 1}."
                )
        else:
            errors.append("Год должен содержать только цифры.")

    # 3. Проверка имени файла и расширения
    filename = data.get("filename", "").strip()
    if not filename:
        errors.append("Поле 'Filename' не может быть пустым.")
    else:
        if any(char in INVALID_FILENAME_CHARS for char in filename):
            errors.append(
                f"Имя файла содержит недопустимые символы: {INVALID_FILENAME_CHARS}"
            )
        elif not filename.lower().endswith(".pdf"):
            errors.append("Файл должен иметь расширение .pdf")

    return errors