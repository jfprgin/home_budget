from calendar import monthrange
from datetime import date
from datetime import timedelta

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiTypes, OpenApiParameter
from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response

from ..filters import TransactionFilter
from ..models import Transaction
from ..serializers import TransactionSerializer, CustomSummarySerializer
from ..services import aggregate_user_transactions


@extend_schema_view(
    list=extend_schema(
        tags=["Transactions"],
        description="Returns all transactions belonging to the authenticated user.",
        responses={200: TransactionSerializer(many=True)},
    ),
    create=extend_schema(
        tags=["Transactions"],
        description="Creates a new transaction associated with the authenticated user's profile.",
        request=TransactionSerializer,
        responses={201: TransactionSerializer},
    ),
    retrieve=extend_schema(
        tags=["Transactions"],
        description="Returns the details of a transaction by ID.",
        responses={200: TransactionSerializer},
    ),
    update=extend_schema(
        tags=["Transactions"],
        description="Updates a transaction owned by the authenticated user.",
        request=TransactionSerializer,
        responses={200: TransactionSerializer},
    ),
    partial_update=extend_schema(
        tags=["Transactions"],
        description="Partially updates a transaction owned by the authenticated user.",
        request=TransactionSerializer,
        responses={200: TransactionSerializer},
    ),
    destroy=extend_schema(
        tags=["Transactions"],
        description="Deletes a transaction owned by the authenticated user.",
        responses={204: None},
    ),
)
class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = TransactionFilter
    search_fields = ['description']

    @extend_schema(
        parameters=[
            OpenApiParameter("id", OpenApiTypes.INT, description="Transaction ID")
        ]
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Transaction.objects.filter(user=self.request.user.profile)
        return Transaction.objects.none()

    @extend_schema(
        tags=["Transactions"],
        description="Returns all transactions belonging to the authenticated user.",
        responses={200: TransactionSerializer(many=True)},
    )
    @action(detail=False, methods=['get'])
    def expenses(self, request):
        queryset = self.get_queryset().filter(type='expense')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=["Transactions"],
        description="Returns all income transactions belonging to the authenticated user.",
        responses={200: TransactionSerializer(many=True)},
    )
    @action(detail=False, methods=['get'])
    def incomes(self, request):
        queryset = self.get_queryset().filter(type='income')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=["Transactions"],
        description="Returns a summary of transactions for the current week.",
        responses={200: OpenApiTypes.OBJECT},
    )
    @action(detail=False, methods=['get'])
    def week(self, request):
        today = date.today()
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=6)
        summary = aggregate_user_transactions(self.get_queryset(), start, end)
        return Response(summary)

    @extend_schema(
        tags=["Transactions"],
        description="Returns a summary of transactions for the current month.",
        responses={200: OpenApiTypes.OBJECT},
    )
    @action(detail=False, methods=['get'])
    def month(self, request):
        today = date.today()
        start = date(today.year, today.month, 1)
        end = date(today.year, today.month, monthrange(today.year, today.month)[1])
        summary = aggregate_user_transactions(self.get_queryset(), start, end)
        return Response(summary)

    @extend_schema(
        tags=["Transactions"],
        description="Returns a summary of transactions for the current year.",
        responses={200: OpenApiTypes.OBJECT},
    )
    @action(detail=False, methods=['get'])
    def year(self, request):
        today = date.today()
        start = date(today.year, 1, 1)
        end = date(today.year, 12, 31)
        summary = aggregate_user_transactions(self.get_queryset(), start, end)
        return Response(summary)

    @extend_schema(
        tags=["Transactions"],
        parameters=[
            OpenApiParameter("start", OpenApiTypes.DATE, description="Start date in YYYY-MM-DD format", required=True),
            OpenApiParameter("end", OpenApiTypes.DATE, description="End date in YYYY-MM-DD format", required=True),
        ],
        description="Returns a summary of transactions for a custom date range specified by 'start' and 'end' query parameters.",
        request=CustomSummarySerializer,
        responses={200: OpenApiTypes.OBJECT},
    )
    @action(detail=False, methods=['get'])
    def custom(self, request):
        serializer = CustomSummarySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        start = serializer.validated_data['start']
        end = serializer.validated_data['end']

        summary = aggregate_user_transactions(self.get_queryset(), start, end)
        return Response(summary)
