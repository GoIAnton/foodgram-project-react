from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (CustomUserViewSet, GetSubscribeVeiwSet, IngredientViewSet,
                    RecipeViewSet, TagViewSet, download_shopping_cart,
                    favorited, shopping_cart, subscribe)

router_v1 = DefaultRouter()
router_v1.register(
    'users',
    CustomUserViewSet,
    basename='users'
)
router_v1.register(
    'tags',
    TagViewSet,
    basename='tags'
)
router_v1.register(
    'ingredients',
    IngredientViewSet,
    basename='ingredients'
)
router_v1.register(
    'recipes',
    RecipeViewSet,
    basename='recipes'
)

urlpatterns = [
    # path('l/', load_data),
    path('auth/', include('djoser.urls.authtoken')),
    path(
        'recipes/<int:recipe_id>/favorite/',
        favorited,
    ),
    path(
        'recipes/<int:recipe_id>/shopping_cart/',
        shopping_cart,
    ),
    path(
        'recipes/download_shopping_cart/',
        download_shopping_cart,
    ),
    path(
        'users/<int:user_id>/subscribe/',
        subscribe,
    ),
    path(
        'users/subscriptions/',
        GetSubscribeVeiwSet.as_view({'get': 'list'}),
    ),
    path('', include(router_v1.urls)),
]
