from api.models import Tag
from django.core.management.base import BaseCommand


class Command(BaseCommand):

    def handle(self, *args, **options):
        data = ({'name': 'завтрак', 'color': '#1bfd9c', 'slug': 'breakfast'},
                {'name': 'обед', 'color': '#0180d4', 'slug': 'lunch'},
                {'name': 'ужин', 'color': '#e4a32f', 'slug': 'dinner'},
                {'name': 'суп', 'color': '#fbbaf7', 'slug': 'soup'},
                {'name': 'гарнир', 'color': '#cc3333', 'slug': 'garnish'},)
        for item in data:
            name = item['name']
            color = item['color']
            slug = item['slug']
            Tag.objects.get_or_create(
                name=name,
                color=color,
                slug=slug,
            )
