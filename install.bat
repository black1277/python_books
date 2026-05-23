@echo off
echo [INFO] Создание виртуального окружения...
python -m venv venv

if %errorlevel% neq 0 (
    echo [ERROR] Не удалось создать виртуальное окружение. Проверьте, установлен ли Python и добавлен ли он в PATH.
    pause
    exit /b
)

echo [INFO] Активация виртуального окружения...
call .\venv\Scripts\activate.bat

echo [INFO] Установка зависимостей из requirements.txt...
pip install -r requirements.txt

echo.
echo [SUCCESS] Установка завершена!
pause