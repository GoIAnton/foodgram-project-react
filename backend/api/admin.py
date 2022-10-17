from django.contrib import admin

from . import models


class UserAdmin(admin.ModelAdmin):
    list_filter = (
        'email',
        'username',
    )


class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'author',
    )
    list_filter = (
        'author',
        'name',
        'tags',
    )


class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'measurement_unit',
    )
    list_filter = (
        'name',
    )


admin.site.register(models.User, UserAdmin)
admin.site.register(models.Tag)
admin.site.register(models.Ingredient, IngredientAdmin)
admin.site.register(models.Recipe, RecipeAdmin)
admin.site.register(models.IngredientRecipe)
admin.site.register(models.Follow)
admin.site.register(models.ShoppingCart)
admin.site.register(models.Favorited)
