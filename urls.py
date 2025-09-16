from django.contrib import admin
from django.urls import path, include
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from home_budget.views.auth_views import RegisterView, LogoutView, ChangePasswordView, UserProfileView
from home_budget.views.categories_views import CategoryViewSet
from home_budget.views.transactions_views import TransactionViewSet


@extend_schema(
    tags=["Auth"],
    parameters=[
        OpenApiParameter("username", str, description="User's username", required=True),
        OpenApiParameter("password", str, description="User's password", required=True),
    ],
    description="Obtain JWT access and refresh tokens by providing valid user credentials.",
    responses={200: {"access": "string", "refresh": "string"}},
)
class CustomTokenObtainPairView(TokenObtainPairView):
    pass


@extend_schema(
    tags=["Auth"],
    parameters=[
        OpenApiParameter("refresh", str, description="Valid refresh token", required=True),
    ],
    description="Refresh JWT access token using a valid refresh token.",
    responses={200: {"access": "string"}},
)
class CustomTokenRefreshView(TokenRefreshView):
    pass


categories_router = DefaultRouter()
categories_router.register(r'categories', CategoryViewSet, basename='category')

transactions_router = DefaultRouter()
transactions_router.register(r'transactions', TransactionViewSet, basename='transaction')

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),

    path('api/register/', RegisterView.as_view(), name='register'),
    path('api/logout/', LogoutView.as_view(), name='logout'),
    path('api/change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('api/profile/', UserProfileView.as_view(), name='user_profile'),

    path('api/', include(categories_router.urls)),
    path('api/', include(transactions_router.urls)),

    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/docs/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
