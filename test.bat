@color 0e
@title "Titles"


@echo ==========================================
@echo off
chcp 65001>nul
if exist ".\venv\Scripts\activate.bat" (
    call .\venv\Scripts\activate.bat
    echo Виртуальное окружение активировано!
    pytest tests/ -v
) else (
    echo Ошибка: виртуальное окружение не найдено!
    exit /b 1
)
chcp 866>nul
pause
