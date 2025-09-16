from django_filters import rest_framework as filters

from .models import Transaction


class TransactionFilter(filters.FilterSet):
    start_date = filters.DateFilter(field_name="date", lookup_expr='gte')
    end_date = filters.DateFilter(field_name="date", lookup_expr='lte')
    min_amount = filters.NumberFilter(field_name="amount", lookup_expr='gte')
    max_amount = filters.NumberFilter(field_name="amount", lookup_expr='lte')

    class Meta:
        model = Transaction
        fields = ['start_date', 'end_date', 'min_amount', 'max_amount', 'type', 'category']
