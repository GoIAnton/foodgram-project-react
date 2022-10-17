import base64

from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers
from rest_framework.settings import api_settings

from backend.settings import ALLOWED_HOSTS

from .models import (Favorited, Follow, Ingredient, IngredientRecipe, Recipe,
                     ShoppingCart, Tag, User)


class CustomUserCreateSerializer(UserCreateSerializer):

    class Meta:
        model = User
        fields = ('email', 'password', 'username', 'first_name', 'last_name')


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed')

    def get_is_subscribed(self, obj):
        user = self.context.get('request', None).user
        if user.is_anonymous:
            return False
        author = get_object_or_404(User, username=obj.username)
        return Follow.objects.filter(user=user, author=author).exists()


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug', )


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit',)


class IngredientRecipeSerializer(serializers.ModelSerializer):
    id = serializers.CharField(
        source='ingredient.id'
    )
    name = serializers.CharField(
        read_only=True,
        source='ingredient.name'
    )
    measurement_unit = serializers.CharField(
        read_only=True,
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientRecipe
        fields = ['id', 'name', 'measurement_unit', 'amount']


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)

    def to_representation(self, value):
        if not value:
            return None

        use_url = getattr(self, 'use_url', api_settings.UPLOADED_FILES_USE_URL)
        if use_url:
            try:
                url = value.url
            except AttributeError:
                return None
            request = self.context.get('request', None)
            if request is not None:
                return 'http://' + ALLOWED_HOSTS[0] + url
            return url

        return value.name


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = IngredientRecipeSerializer(
        many=True,
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('tags', 'ingredients', 'name', 'image',
                  'text', 'cooking_time', )

    def create_ingredient_recipe(self, ingredients, recipe):
        for ingredient in ingredients:
            amount = ingredient.popitem(last=True)[1]
            ingredient_id = ingredient.popitem(last=True)[1]['id']
            ingredient = get_object_or_404(Ingredient, id=ingredient_id)
            IngredientRecipe.objects.create(
                recipe=recipe,
                ingredient=ingredient,
                amount=amount,
            )

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredient_recipe(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        if 'ingredients' in validated_data:
            IngredientRecipe.objects.filter(recipe=instance).delete()
            ingredients = validated_data.pop('ingredients')
            self.create_ingredient_recipe(ingredients, instance)
        if 'tags' in validated_data:
            instance.tags.set(
                validated_data.pop('tags')
            )
        return super().update(
            instance, validated_data
        )

    def to_representation(self, instance):
        return RecipeGetSerializer(
            instance,
            context={
                'request': self.context.get('request')
            }).data


class RecipeGetSerializer(serializers.ModelSerializer):
    author = CustomUserSerializer()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()
    ingredients = IngredientRecipeSerializer(many=True)
    tags = TagSerializer(many=True)

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image', 'text',
                  'cooking_time', )

    def get_is_favorited(self, obj):
        user = self.context.get('request', None).user
        if user.is_anonymous:
            return False
        recipe = get_object_or_404(Recipe, id=obj.id)
        return Favorited.objects.filter(
            user=user,
            recipe=recipe,
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request', None).user
        if user.is_anonymous:
            return False
        recipe = get_object_or_404(Recipe, id=obj.id)
        return ShoppingCart.objects.filter(
            user=user,
            recipe=recipe,
        ).exists()


class RecipeShortSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time', )
        read_only_fields = ('id', 'name', 'image', 'cooking_time', )


class UserSubscribeSerializer(serializers.ModelSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed',
                  'recipes', 'recipes_count', )
        read_only_fields = ('email', 'id', 'username', 'first_name',
                            'last_name', 'is_subscribed',
                            'recipes', 'recipes_count', )

    def get_recipes(self, obj):
        limit = self.context['limit']
        if limit:
            limit = int(limit)
            recipes = Recipe.objects.filter(author=obj.id)[:limit]
            return RecipeShortSerializer(recipes, many=True).data
        recipes = Recipe.objects.filter(author=obj.id)
        return RecipeShortSerializer(recipes, many=True).data

    def get_is_subscribed(self, obj):
        return True

    def get_recipes_count(self, obj):
        user = get_object_or_404(User, id=obj.id)
        return Recipe.objects.filter(author=user).count()
