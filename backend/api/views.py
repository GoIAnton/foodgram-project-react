import io
import json
import os

from django.contrib.auth.tokens import default_token_generator
from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from djoser import signals
from djoser.conf import settings
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework import status
from rest_framework.decorators import action, api_view
from rest_framework.exceptions import NotFound
from rest_framework.filters import SearchFilter
from rest_framework.mixins import ListModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import (GenericViewSet, ModelViewSet,
                                     ReadOnlyModelViewSet)

from .models import (Favorited, Follow, Ingredient, IngredientRecipe, Recipe,
                     ShoppingCart, Tag, User)
from .paginations import CustomPagination
from .serializers import (CustomUserSerializer, IngredientSerializer,
                          RecipeSerializer, RecipeShortSerializer,
                          TagSerializer, UserSubscribeSerializer)


class CustomUserViewSet(ModelViewSet):
    serializer_class = CustomUserSerializer
    queryset = User.objects.all()
    permission_classes = settings.PERMISSIONS.user
    token_generator = default_token_generator
    lookup_field = settings.USER_ID_FIELD
    pagination_class = CustomPagination

    def permission_denied(self, request, **kwargs):
        if (
            settings.HIDE_USERS
            and request.user.is_authenticated
            and self.action in ["update", "partial_update", "list", "retrieve"]
        ):
            raise NotFound()
        super().permission_denied(request, **kwargs)

    def get_permissions(self):
        if self.action == "create":
            self.permission_classes = settings.PERMISSIONS.user_create
        elif self.action == "retrieve":
            self.permission_classes = [AllowAny]
        elif self.action == "list":
            self.permission_classes = settings.PERMISSIONS.user_list
        elif self.action == "set_password":
            self.permission_classes = settings.PERMISSIONS.set_password
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == "create":
            if settings.USER_CREATE_PASSWORD_RETYPE:
                return settings.SERIALIZERS.user_create_password_retype
            return settings.SERIALIZERS.user_create
        elif self.action == "set_password":
            if settings.SET_PASSWORD_RETYPE:
                return settings.SERIALIZERS.set_password_retype
            return settings.SERIALIZERS.set_password
        elif self.action == "me":
            return settings.SERIALIZERS.current_user

        return self.serializer_class

    def get_instance(self):
        return self.request.user

    def perform_create(self, serializer):
        user = serializer.save()
        signals.user_registered.send(
            sender=self.__class__, user=user, request=self.request
        )

    @action(detail=False)
    def me(self, request, *args, **kwargs):
        self.get_object = self.get_instance
        return self.retrieve(request, *args, **kwargs)

    @action(["post"], detail=False)
    def set_password(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        self.request.user.set_password(serializer.data["new_password"])
        self.request.user.save()

        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (SearchFilter, )
    search_fields = ('^name',)


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    pagination_class = CustomPagination

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = Recipe.objects.all()
        tags = self.request.query_params.getlist('tags', False)
        if tags:
            queryset = queryset.filter(tags__slug__in=tags).distinct()
        is_favorited = self.request.query_params.get('is_favorited', '0')
        if is_favorited == '1':
            queryset = queryset.filter(
                favorited__user=request.user
            )
        author_id = self.request.query_params.get('author', False)
        if author_id:
            author = get_object_or_404(User, id=int(author_id))
            queryset = queryset.filter(
                author=author
            )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


@api_view(['POST', 'DELETE', ])
def favorited(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    user = request.user
    if request.method == 'DELETE':
        Favorited.objects.filter(
            recipe=recipe,
            user=user
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    if Favorited.objects.filter(
        recipe=recipe,
        user=user
    ).exists():
        return Response(
            {"errors": "Рецепт уже добавлен в избранное"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    Favorited.objects.create(
        recipe=recipe,
        user=user
    )
    serializer = RecipeShortSerializer(recipe)
    return Response(data=serializer.data, status=status.HTTP_201_CREATED)


@api_view(['POST', 'DELETE', ])
def shopping_cart(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    user = request.user
    if request.method == 'DELETE':
        ShoppingCart.objects.filter(
            recipe=recipe,
            user=user
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    if ShoppingCart.objects.filter(
        recipe=recipe,
        user=user
    ).exists():
        return Response(
            {"errors": "Рецепт уже добавлен в список покупок"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    ShoppingCart.objects.create(
        recipe=recipe,
        user=user
    )
    serializer = RecipeShortSerializer(recipe)
    return Response(data=serializer.data, status=status.HTTP_201_CREATED)


@api_view(['POST', 'DELETE', ])
def subscribe(request, user_id):
    author = get_object_or_404(User, id=user_id)
    user = request.user
    if author == user:
        return Response(
            {"errors": "Нельзя подписываться на себя"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if request.method == 'DELETE':
        Follow.objects.filter(
            author=author,
            user=user
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    if Follow.objects.filter(
        author=author,
        user=user
    ).exists():
        return Response(
            {"errors": "Рецепт уже добавлен в список покупок"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    Follow.objects.create(
        author=author,
        user=user
    )
    limit = request.query_params.get('recipes_limit')
    serializer = UserSubscribeSerializer(
        author,
        context={'request': request, 'limit': limit})
    return Response(data=serializer.data, status=status.HTTP_201_CREATED)


class GetSubscribeVeiwSet(ListModelMixin, GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserSubscribeSerializer
    pagination_class = CustomPagination

    def list(self, request, *args, **kwargs):
        queryset = User.objects.all()
        queryset = queryset.filter(
            id__in=request.user.follower.values('author')
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_serializer_context(self):
        limit = self.request.query_params.get('recipes_limit')
        return {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self,
            'limit': limit
        }


@api_view(['GET', ])
def download_shopping_cart(request):
    user = request.user
    if user.is_anonymous:
        return Response(
            {'detail': 'Учетные данные не были предоставлены.'},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    ingredients = IngredientRecipe.objects.filter(
        recipe__shoppingcart__user=request.user
    ).values(
        'ingredient__name',
        'ingredient__measurement_unit'
    ).annotate(amount=Sum('amount'))
    pdf = io.BytesIO()
    pdf_obj = canvas.Canvas(pdf)
    arial = TTFont('Arial', 'arial.ttf')
    pdfmetrics.registerFont(arial)
    pdf_obj.setFont('Arial', 14)
    line_num = 760
    for ingredient in ingredients:
        pdf_obj.drawString(
            100,
            line_num,
            (f'{ingredient["ingredient__name"]} - '
             f'{ingredient["amount"]} '
             f'{ingredient["ingredient__measurement_unit"]}'),
        )
        line_num -= 20
    pdf_obj.showPage()
    pdf_obj.save()
    pdf.seek(0)
    return FileResponse(
        pdf,
        as_attachment=True,
        filename='shopping_cart.pdf',
    )


def load_data(request):
    print(os.path.abspath(__file__))
    f = open('/app/api/ingredients.json')
    json_string = f.read()
    f.close()
    data = json.loads(json_string)
    for item in data:
        name = item['name']
        measurement_unit = item['measurement_unit']
        Ingredient.objects.get_or_create(name=name,
                                         measurement_unit=measurement_unit)
