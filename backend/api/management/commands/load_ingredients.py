import json
import os

from api.models import Ingredient
from django.core.management.base import BaseCommand


class Command(BaseCommand):

    def handle(self, *args, **options):
        print(os.path.abspath(__file__))
        f = open('/app/ingredients.json')
        json_string = f.read()
        f.close()
        data = json.loads(json_string)
        for item in data:
            name = item['name']
            measurement_unit = item['measurement_unit']
            Ingredient.objects.get_or_create(
                name=name,
                measurement_unit=measurement_unit,
            )
