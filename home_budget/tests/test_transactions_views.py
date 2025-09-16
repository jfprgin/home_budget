from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from home_budget.models import Profile, Category, Transaction

User = get_user_model()


def get_auth_headers(user):
    refresh = RefreshToken.for_user(user)
    return {'HTTP_AUTHORIZATION': f'Bearer {refresh.access_token}'}


class TransactionAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.profile = Profile.objects.create(user=self.user)

        self.category_expense = Category.objects.create(name='Food', user=self.profile)
        self.category_income = Category.objects.create(name='Salary', user=self.profile)

        self.list_url = reverse('transaction-list')
        self.week_url = reverse('transaction-week')
        self.month_url = reverse('transaction-month')
        self.year_url = reverse('transaction-year')
        self.custom_url = reverse('transaction-custom')
        self.expense_url = reverse('transaction-expenses')
        self.income_url = reverse('transaction-incomes')

        self.headers = get_auth_headers(self.user)

    def test_create_expense_transaction(self):
        data = {
            'description': 'Grocery shopping',
            'amount': 52.67,
            'type': 'expense',
            'category_id': self.category_expense.id,
        }
        response = self.client.post(self.list_url, data, **self.headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        transaction = Transaction.objects.first()
        self.assertEqual(transaction.description, 'Grocery shopping')
        self.assertEqual(transaction.amount, Decimal('52.67'))
        self.assertEqual(transaction.type, 'expense')
        self.assertEqual(transaction.category, self.category_expense)
        self.assertEqual(transaction.user, self.profile)

    def test_create_income_transaction(self):
        data = {
            'description': 'Monthly Salary',
            'amount': 1550.00,
            'type': 'income',
            'category_id': self.category_income.id,
        }
        response = self.client.post(self.list_url, data, **self.headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        transaction = Transaction.objects.first()
        self.assertEqual(transaction.description, 'Monthly Salary')
        self.assertEqual(transaction.amount, Decimal('1550.00'))
        self.assertEqual(transaction.type, 'income')
        self.assertEqual(transaction.category, self.category_income)
        self.assertEqual(transaction.user, self.profile)

    def test_user_cannot_see_others_transactions(self):
        other_user = User.objects.create_user(username='otheruser', password='pass456')
        other_profile = Profile.objects.create(user=other_user)
        other_category = Category.objects.create(name='Travel', user=other_profile)
        Transaction.objects.create(
            description='Flight ticket',
            amount=300.00,
            type='expense',
            category=other_category,
            user=other_profile
        )

        response = self.client.get(self.list_url, **self.headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)

    def test_filter_transactions_by_type(self):
        Transaction.objects.create(user=self.profile, description='Expense1', amount=50, type='expense',
                                   category=self.category_expense)
        Transaction.objects.create(user=self.profile, description='Income1', amount=200, type='income',
                                   category=self.category_income)

        response = self.client.get(self.list_url + '?type=expense', **self.headers)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['type'], 'expense')

        response = self.client.get(self.list_url + '?type=income', **self.headers)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['type'], 'income')

    def test_filter_transactions_by_amount(self):
        Transaction.objects.create(user=self.profile, description='Food', amount=100, type='expense',
                                   category=self.category_expense)
        Transaction.objects.create(user=self.profile, description='Salary', amount=1500, type='income',
                                   category=self.category_income)

        response = self.client.get(
            f"{self.list_url}?category={self.category_expense.id}&min_amount=50&max_amount=200",
            **self.headers
        )
        self.assertEqual(response.status_code, 200)
        for tx in response.data['results']:
            self.assertEqual(tx['category']['id'], self.category_expense.id)
            self.assertTrue(50 <= float(tx['amount']) <= 200)

    def test_get_expenses_endpoint(self):
        Transaction.objects.create(user=self.profile, description='Expense1', amount=50, type='expense',
                                   category=self.category_expense)
        Transaction.objects.create(user=self.profile, description='Income1', amount=200, type='income',
                                   category=self.category_income)

        response = self.client.get(self.expense_url, **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['type'], 'expense')

    def test_get_incomes_endpoint(self):
        Transaction.objects.create(user=self.profile, description='Expense1', amount=50, type='expense',
                                   category=self.category_expense)
        Transaction.objects.create(user=self.profile, description='Income1', amount=200, type='income',
                                   category=self.category_income)

        response = self.client.get(self.income_url, **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['type'], 'income')

    def test_summary_endpoints(self):
        Transaction.objects.create(user=self.profile, description='Expense1', amount=50, type='expense',
                                   category=self.category_expense)
        Transaction.objects.create(user=self.profile, description='Income1', amount=200, type='income',
                                   category=self.category_income)

        for url in [self.week_url, self.month_url, self.year_url]:
            response = self.client.get(url, **self.headers)
            self.assertEqual(response.status_code, 200)
            self.assertIn('total_expense', response.data)
            self.assertIn('total_income', response.data)
            self.assertIn('balance', response.data)
            self.assertEqual(response.data['total_expense'], Decimal('50.00'))
            self.assertEqual(response.data['total_income'], Decimal('200.00'))
            self.assertEqual(response.data['balance'], Decimal('150.00'))

    def test_custom_summary_endpoint(self):
        Transaction.objects.create(user=self.profile, description='Expense1', amount=50, type='expense',
                                   category=self.category_expense)
        Transaction.objects.create(user=self.profile, description='Income1', amount=200, type='income',
                                   category=self.category_income)

        data = {'start': '2025-01-01', 'end': '2025-12-31'}
        response = self.client.get(self.custom_url, data, **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total_expense'], Decimal('50.00'))
        self.assertEqual(response.data['total_income'], Decimal('200.00'))
        self.assertEqual(response.data['balance'], Decimal('150.00'))

        # out of range
        data = {'start': '2023-01-01', 'end': '2023-12-31'}
        response = self.client.get(self.custom_url, data, **self.headers)
        self.assertEqual(response.data['total_expense'], Decimal('0.00'))
        self.assertEqual(response.data['total_income'], Decimal('0.00'))
        self.assertEqual(response.data['balance'], Decimal('0.00'))

    def test_create_transaction_invalid_category(self):
        data = {
            'description': 'Invalid Category Test',
            'amount': 100.00,
            'type': 'expense',
            'category_id': 9999,  # Non-existent category ID
        }
        response = self.client.post(self.list_url, data, **self.headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('category_id', response.data)
        self.assertEqual(response.data['category_id'][0], "Category does not exist or does not belong to the user.")
        self.assertEqual(Transaction.objects.count(), 0)

    def test_create_transaction_without_category(self):
        data = {
            'description': 'Freelance work',
            'amount': 500.00,
            'type': 'income',
        }

        response = self.client.post(self.list_url, data, **self.headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        transaction = Transaction.objects.first()
        self.assertEqual(transaction.description, 'Freelance work')
        self.assertEqual(transaction.amount, Decimal('500.00'))
        self.assertEqual(transaction.type, 'income')
        self.assertIsNone(transaction.category)  # Ensure no category is assigned
        self.assertEqual(transaction.user, self.profile)  # Ensure it's linked to the correct user

    def test_create_transaction_with_empty_category(self):
        data = {
            'description': 'Gift received',
            'amount': 150.00,
            'type': 'income',
            'category_id': '',  # Explicitly setting category_id to null
        }

        response = self.client.post(self.list_url, data, **self.headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        transaction = Transaction.objects.first()
        self.assertEqual(transaction.description, 'Gift received')
        self.assertEqual(transaction.amount, Decimal('150.00'))
        self.assertEqual(transaction.type, 'income')
        self.assertIsNone(transaction.category)  # Ensure no category is assigned
        self.assertEqual(transaction.user, self.profile)  # Ensure it's linked to the correct user
