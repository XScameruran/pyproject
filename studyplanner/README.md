# StudyPlanner

Умный планировщик учёбы на Django (templates + Bootstrap 5).

## Быстрый старт

1) Создать и активировать виртуальное окружение:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2) Установить зависимости:

```powershell
pip install -r requirements.txt
```

3) Применить миграции:

```powershell
python manage.py migrate
```

4) Создать демо-данные:

```powershell
python manage.py load_demo
```

5) Запустить сервер:

```powershell
python manage.py runserver
```

Приложение доступно на `http://127.0.0.1:8000/`.

## Структура

- `studyplanner/` — проект Django
- `planner/` — приложение
- `planner/templates/` — HTML шаблоны
- `planner/static/` — статические файлы

## Основные маршруты

- `/` — Dashboard
- `/courses/` — Курсы
- `/tasks/` — Задачи
- `/calendar/` — Календарь
- `/stats/` — Статистика