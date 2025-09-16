from django.contrib import admin

from .models import Profile, Category, Transaction


class CategoryInline(admin.TabularInline):
    model = Category
    extra = 1  # Number of empty forms displayed (default: 1)
    fk_name = 'user'  # Ensures it references the 'user' field in Category model


class TransactionInline(admin.TabularInline):
    model = Transaction
    extra = 1
    fk_name = 'user'


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance')
    search_fields = ('user__username',)
    inlines = [CategoryInline, TransactionInline]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'user')
    list_filter = ('user',)
    search_fields = ('name',)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('description', 'amount', 'type', 'date', 'user', 'category')
    list_filter = ('type', 'user', 'category')
    search_fields = ('description', 'amount')
    date_hierarchy = 'date'
