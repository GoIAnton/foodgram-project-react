[![Foodgram](https://github.com/GoIAnton/foodgram-project-react/actions/workflows/foodgram_workflow.yml/badge.svg)](https://github.com/GoIAnton/foodgram-project-react/actions/workflows/foodgram_workflow.yml)

### Foodgram

### IP сервера: 

51.250.19.47

### Описание:
На этом сервисе пользователи смогут публиковать рецепты, подписываться на публикации других пользователей, добавлять понравившиеся рецепты в список «Избранное», а перед походом в магазин скачивать сводный список продуктов, необходимых для приготовления одного или нескольких выбранных блюд.

## Проект исполнен в:

**Версия python** = 3.7
**Версия Django** = 2.2.16
**Версия Djangorestframework** = 3.12.4

### Как запустить проект: 

Клонировать репозиторий и перейти в него в командной строке:
```
git clone https://github.com/GoIAnton/foodgram-project-react.git
```

Переход в папку с docker-compose:
```
cd infra/
```

Создание .env
```
cp .env.example .env
```

Запуск docker-compose:
```
docker-compose up
```

Миграции -> создание суперюзера -> собрать статику нужной папке -> заполнить БД ингредиентами и тегами:
```
docker-compose exec backend python manage.py makemigrations
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py createsuperuser
docker-compose exec backend python manage.py collectstatic --no-input
docker-compose exec backend python manage.py load_ingredients
docker-compose exec backend python manage.py load_tags
```

### Об авторе:

Начинающий бекэнд разработчик на Python
Мой github:
https://github.com/GoIAnton
