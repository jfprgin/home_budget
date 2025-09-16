from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from home_budget.models import Category, Transaction, Profile

User = get_user_model()


def get_auth_headers(user):
    refresh = RefreshToken.for_user(user)
    return {
        'HTTP_AUTHORIZATION': f'Bearer {str(refresh.access_token)}',
    }


class AuthAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com',
        )

        self.register_url = reverse('register')
        self.login_url = reverse('token_obtain_pair')
        self.logout_url = reverse('logout')
        self.profile_url = reverse('user_profile')
        self.change_password_url = reverse('change_password')

    def test_register_user(self):
        data = {
            'username': 'newuser',
            'password': 'newpass123',
            'password2': 'newpass123',
            'email': 'new@example.com',
        }

        count_before = User.objects.count()
        response = self.client.post(self.register_url, data)
        count_after = User.objects.count()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(count_after, count_before + 1)
        self.assertTrue(User.objects.filter(username='newuser').exists())
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_register_user_password_mismatch(self):
        data = {
            'username': 'newuser',
            'password': 'newpass123',
            'password2': 'mismatch',
            'email': 'new@example.com',
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)

    def test_login_user(self):
        data = {
            'username': 'testuser',
            'password': 'testpass123',
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_invalid_credentials(self):
        data = {
            'username': 'testuser',
            'password': 'wrongpass',
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('detail', response.data)

    def test_logout_blacklists_token(self):
        refresh = RefreshToken.for_user(self.user)
        access = str(refresh.access_token)

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        response = self.client.post(self.logout_url, {'refresh': str(refresh)})
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)

    def test_double_logout(self):
        refresh = RefreshToken.for_user(self.user)
        access = str(refresh.access_token)

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        data = {'refresh': str(refresh)}

        # First logout
        response = self.client.post(self.logout_url, data)
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)

        # Second logout should fail
        response = self.client.post(self.logout_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalidtoken')
        response = self.client.post(self.logout_url, {'refresh': 'invalidtoken'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('detail', response.data)

    def test_refresh_token_invalid_after_logout(self):
        refresh = RefreshToken.for_user(self.user)
        access = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')

        # Logout
        response = self.client.post(self.logout_url, {'refresh': str(refresh)})
        self.assertEqual(response.status_code, 205)

        # Try using the blacklisted refresh token
        response = self.client.post(reverse('token_refresh'), {'refresh': str(refresh)})
        self.assertEqual(response.status_code, 401)
        self.assertIn('detail', response.data)
        self.assertEqual(response.data['detail'], 'Token is blacklisted')

    def test_change_password_success(self):
        headers = get_auth_headers(self.user)
        data = {
            "current_password": "testpass123",
            "new_password": "newsecurepass456",
            "new_password2": "newsecurepass456"
        }

        response = self.client.post(self.change_password_url, data, **headers)
        print(response.status_code, response.data)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

        # Make sure user can login with new password
        login_url = reverse('token_obtain_pair')
        login_response = self.client.post(login_url, {
            "username": self.user.username,
            "password": "newsecurepass456"
        })
        self.assertEqual(login_response.status_code, 200)
        self.assertIn("access", login_response.data)

    def test_change_password_wrong_current(self):
        headers = get_auth_headers(self.user)
        data = {
            "current_password": "wrongpassword",
            "new_password": "newsecurepass456",
            "new_password2": "newsecurepass456"
        }

        response = self.client.post(self.change_password_url, data, **headers)
        self.assertEqual(response.status_code, 400)
        self.assertIn("current_password", response.data)

    def test_change_password_mismatch(self):
        headers = get_auth_headers(self.user)
        data = {
            "current_password": "testpass123",
            "new_password": "newsecurepass456",
            "new_password2": "doesnotmatch"
        }

        response = self.client.post(self.change_password_url, data, **headers)
        self.assertEqual(response.status_code, 400)
        self.assertIn("non_field_errors", response.data)


class UserProfileTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com',
        )
        self.profile = Profile.objects.create(user=self.user, balance=100.00)

        self.profile_url = reverse('user_profile')

        self.category_1 = Category.objects.create(name='Groceries', user=self.user.profile)
        self.category_2 = Category.objects.create(name='Entertainment', user=self.user.profile)

        self.transaction_1 = Transaction.objects.create(
            user=self.user.profile,
            category=self.category_1,
            description="Bought groceries",
            amount=50.00,
            type="expense"
        )
        self.transaction_2 = Transaction.objects.create(
            user=self.user.profile,
            category=self.category_2,
            description="Movie ticket",
            amount=20.00,
            type="expense"
        )

        self.client.credentials(HTTP_AUTHORIZATION=get_auth_headers(self.user)['HTTP_AUTHORIZATION'])

    def test_profile_with_multiple_categories_and_transactions(self):
        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['username'], self.user.username)

        self.assertEqual(len(response.data['categories']), 2)
        self.assertEqual(len(response.data['transactions']), 2)

        categories = [category['name'] for category in response.data['categories']]
        self.assertIn('Groceries', categories)
        self.assertIn('Entertainment', categories)

        self.assertIn('Bought groceries', [t['description'] for t in response.data['transactions']])
        self.assertIn('Movie ticket', [t['description'] for t in response.data['transactions']])

    def test_profile_with_empty_categories_and_transactions(self):
        Category.objects.filter(user=self.user.profile).delete()
        Transaction.objects.filter(user=self.user.profile).delete()

        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['username'], self.user.username)

        self.assertEqual(response.data['categories'], [])
        self.assertEqual(response.data['transactions'], [])

    def test_profile_unauthenticated(self):
        self.client.credentials()
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('detail', response.data)
        self.assertEqual(response.data['detail'], 'Authentication credentials were not provided.')
        self.assertIn('detail', response.data)
