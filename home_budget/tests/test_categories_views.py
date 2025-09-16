from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from home_budget.models import Category, Profile

User = get_user_model()


def get_auth_headers(user):
    refresh = RefreshToken.for_user(user)
    return {'HTTP_AUTHORIZATION': f'Bearer {refresh.access_token}'}


class CategoryAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.profile = Profile.objects.create(user=self.user)

        self.list_url = reverse('category-list')

    def test_create_category(self):
        headers = get_auth_headers(self.user)
        data = {'name': 'Party'}

        count_before = Category.objects.count()
        response = self.client.post(self.list_url, data, **headers)
        count_after = Category.objects.count()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(count_after, count_before + 1)
        category = Category.objects.filter(user=self.profile, name='Party').first()
        self.assertIsNotNone(category)
        self.assertEqual(category.name, 'Party')
        self.assertEqual(category.user, self.profile)

    def test_user_cannot_see_others_categories(self):
        other_user = User.objects.create_user(username='otheruser', password='pass456')
        other_profile = Profile.objects.create(user=other_user)

        Category.objects.create(name='Travel', user=other_profile)

        headers = get_auth_headers(self.user)
        response = self.client.get(self.list_url, **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)

    def test_user_can_only_see_their_categories(self):
        other_user = User.objects.create_user(username='otheruser', password='pass456')
        other_profile = Profile.objects.create(user=other_user)

        Category.objects.create(name='Travel', user=other_profile)
        Category.objects.create(name='Food', user=self.profile)

        headers = get_auth_headers(self.user)
        response = self.client.get(self.list_url, **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Food')

    def test_list_categories(self):
        headers = get_auth_headers(self.user)
        Category.objects.create(user=self.profile, name='Groceries')
        Category.objects.create(user=self.profile, name='Utilities')

        response = self.client.get(self.list_url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        category_names = {cat['name'] for cat in response.data['results']}
        self.assertSetEqual(category_names, {'Groceries', 'Utilities'})

    def test_update_category(self):
        headers = get_auth_headers(self.user)
        category = Category.objects.create(user=self.profile, name='Old Name')
        detail_url = reverse('category-detail', args=[category.id])
        data = {'name': 'New Name'}

        response = self.client.put(detail_url, data, **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        category.refresh_from_db()
        self.assertEqual(category.name, 'New Name')

    def test_delete_category(self):
        headers = get_auth_headers(self.user)
        category = Category.objects.create(user=self.profile, name='To Be Deleted')
        detail_url = reverse('category-detail', args=[category.id])
        count_before = Category.objects.count()
        response = self.client.delete(detail_url, **headers)
        count_after = Category.objects.count()
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(count_after, count_before - 1)
        self.assertFalse(Category.objects.filter(id=category.id).exists())
