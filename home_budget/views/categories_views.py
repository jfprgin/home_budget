from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from rest_framework import viewsets, permissions, filters

from ..models import Category
from ..serializers import CategorySerializer


@extend_schema_view(
    list=extend_schema(
        tags=["Categories"],
        description="Returns all categories belonging to the authenticated user.",
        responses={200: CategorySerializer(many=True)},
    ),
    create=extend_schema(
        tags=["Categories"],
        parameters=[
            OpenApiParameter("name", str, description="Name of the category", required=True)
        ],
        description="Creates a new category associated with the authenticated user's profile.",
        request=CategorySerializer,
        responses={201: CategorySerializer},
    ),
    retrieve=extend_schema(
        tags=["Categories"],
        description="Returns the details of a category by ID.",
        responses={200: CategorySerializer},
    ),
    update=extend_schema(
        tags=["Categories"],
        description="Updates a category owned by the authenticated user.",
        request=CategorySerializer,
        responses={200: CategorySerializer},
    ),
    partial_update=extend_schema(
        tags=["Categories"],
        description="Partially updates a category owned by the authenticated user.",
        request=CategorySerializer,
        responses={200: CategorySerializer},
    ),
    destroy=extend_schema(
        tags=["Categories"],
        description="Deletes a category owned by the authenticated user.",
        responses={204: None},
    ),
)
class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name']
    filterset_fields = ['name']

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return Category.objects.filter(user=user.profile)  # Ensure the user has a profile
        return Category.objects.none()  # Return no categories for anonymous users
