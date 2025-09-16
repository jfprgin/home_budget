from datetime import datetime, time

from django.db.models import Sum, Case, When, DecimalField, Value


def aggregate_user_transactions(queryset, start_date, end_date):
    """
    Aggregate total income and expenses for a given user for a queryset within a date range.
    Returns a dict with total_expense, total_income, and balance.
    """
    start_datetime = datetime.combine(start_date, time.min)
    end_datetime = datetime.combine(end_date, time.max)

    filtered_queryset = queryset.filter(date__range=(start_datetime, end_datetime))
    summary = filtered_queryset.aggregate(
        total_expense=Sum(
            Case(
                When(type='expense', then='amount'),
                default=Value(0),
                output_field=DecimalField()
            )
        ),
        total_income=Sum(
            Case(
                When(type='income', then='amount'),
                default=Value(0),
                output_field=DecimalField()
            )
        )
    )

    total_expense = summary['total_expense'] or 0
    total_income = summary['total_income'] or 0

    return {
        'total_expense': total_expense,
        'total_income': total_income,
        'balance': total_income - total_expense
    }
