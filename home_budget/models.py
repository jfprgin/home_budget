from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=100.00)

    class Meta:
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'

    def __str__(self):
        return f"{self.user.username}"


class CategoryQuerySet(models.QuerySet):
    def for_user(self, user):
        return self.filter(user=user.profile)


class Category(models.Model):
    name = models.CharField(max_length=255)
    user = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='categories', null=True, blank=True)

    objects = CategoryQuerySet.as_manager()

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class TransactionQuerySet(models.QuerySet):
    def for_user(self, user):
        return self.filter(user=user.profile)


class Transaction(models.Model):
    class TransactionType(models.TextChoices):
        INCOME = 'income', 'Income'
        EXPENSE = 'expense', 'Expense'

    user = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='transactions')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='transactions', null=True, blank=True)
    description = models.TextField(max_length=255, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    type = models.CharField(max_length=10, choices=TransactionType.choices)
    date = models.DateTimeField(auto_now_add=True)

    objects = TransactionQuerySet.as_manager()

    class Meta:
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        ordering = ['-date']

    def __str__(self):
        return f"{self.type}: {self.description} ({self.amount})"


