@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo  Установка бота поручений
echo  ========================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo  [ОШИБКА] Python не найден.
    echo  Установите его командой:  winget install --id Python.Python.3.12 -e
    echo  Затем закройте это окно и запустите setup.bat ещё раз.
    goto :end
)

python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"
if errorlevel 1 (
    echo  [ОШИБКА] Нужен Python 3.10 или новее. Установите Python 3.12.
    goto :end
)

if not exist .venv (
    echo  1/3  Создаю окружение Python...
    python -m venv .venv || goto :fail
) else (
    echo  1/3  Окружение уже есть.
)

echo  2/3  Ставлю библиотеки...
.venv\Scripts\python -m pip install --quiet --upgrade pip || goto :fail
.venv\Scripts\python -m pip install --quiet -r requirements.txt || goto :fail

if not exist .env (
    copy /y .env.example .env >nul
    echo  3/3  Создан файл .env — впишите в него токен бота.
) else (
    echo  3/3  Файл .env уже есть, не трогаю.
)

echo.
echo  Готово. Дальше: заполните .env и запустите start.bat
goto :end

:fail
echo.
echo  [ОШИБКА] Установка прервалась. Пришлите текст выше тому, кто помогает с ботом.

:end
echo.
pause
