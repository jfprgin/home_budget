from typing import Optional, Dict

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Profile, Category, Transaction


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2']

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError("Passwords do not match.")

        validate_password(data['password'])

        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)

        profile = Profile.objects.create(user=user)

        # Get predefined categories from settings
        predefined_categories = settings.PREDEFINED_CATEGORIES
        for category_name in predefined_categories:
            Category.objects.create(name=category_name, user=profile)

        return user

    def to_representation(self, instance):
        refresh = RefreshToken.for_user(instance)
        return {
            'username': instance.username,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }


class LogoutRequestSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    new_password2 = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['new_password'] != data['new_password2']:
            raise serializers.ValidationError("New passwords do not match.")

        # Apply Django's built-in password validation
        validate_password(data['new_password'], self.context['request'].user)

        return data


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'user']
        read_only_fields = ['user']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user.profile
        return super().create(validated_data)


class TransactionSerializer(serializers.ModelSerializer):
    category_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    category = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Transaction
        fields = ['id', 'user', 'category', 'category_id', 'description', 'amount', 'type', 'date']
        read_only_fields = ['user', 'category']

    def get_category(self, obj) -> Optional[Dict[str, str]]:
        if obj.category:
            return {
                'id': obj.category.id,
                'name': obj.category.name
            }
        return None

    def validate_category_id(self, value):
        if value is None:
            return None
        user = self.context['request'].user
        try:
            category = Category.objects.get(id=value, user=user.profile)
        except Category.DoesNotExist:
            raise serializers.ValidationError("Category does not exist or does not belong to the user.")
        return category

    def create(self, validated_data):
        user = self.context['request'].user
        category = validated_data.pop('category_id', None)
        validated_data['user'] = user.profile
        validated_data['category'] = category
        return super().create(validated_data)


class CustomSummarySerializer(serializers.Serializer):
    start = serializers.DateField()
    end = serializers.DateField()

    def validate(self, data):
        if data['start'] > data['end']:
            raise serializers.ValidationError("Start date must be before end date.")
        return data


class UserProfileSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)
    transactions = TransactionSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'categories', 'transactions']
