from drf_spectacular.utils import extend_schema, OpenApiTypes
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from home_budget.models import Category, Transaction
from home_budget.serializers import RegisterSerializer, ChangePasswordSerializer, UserProfileSerializer, \
    LogoutRequestSerializer, CategorySerializer, TransactionSerializer


class RegisterView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=RegisterSerializer,
        responses={201: RegisterSerializer},
        tags=["Auth"],
        operation_id="register",
        description="Register a new user. Returns access and refresh tokens."
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(serializer.to_representation(user), status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(  # <-- already added
        request=ChangePasswordSerializer,
        responses={200: OpenApiTypes.OBJECT},
        tags=["Auth"],
        operation_id="change_password",
        description="Change the authenticated user's password. Returns new access and refresh tokens."
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})  # ✅ fix here

        if serializer.is_valid():
            if not request.user.check_password(serializer.validated_data['current_password']):
                return Response({"current_password": ["Wrong password."]}, status=status.HTTP_400_BAD_REQUEST)

            request.user.set_password(serializer.validated_data['new_password'])
            request.user.save()

            refresh = RefreshToken.for_user(request.user)
            return Response({
                'message': 'Password changed successfully',
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=LogoutRequestSerializer,
        responses={205: OpenApiTypes.OBJECT},
        tags=["Auth"],
        operation_id="logout",
        description="Logout the user by blacklisting the provided refresh token."
    )
    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"detail": "Successfully logged out."}, status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response({"error": "Invalid token or token has already been blacklisted."},
                            status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: UserProfileSerializer},
        tags=["Profile"],
        operation_id="user_profile",
        description="Retrieve the authenticated user's profile information along with categories and transactions."
    )
    def get(self, request):
        user = request.user

        categories = Category.objects.filter(user=user.profile)
        transactions = Transaction.objects.filter(user=user.profile)

        user_profile_data = UserProfileSerializer(user).data
        user_profile_data['categories'] = CategorySerializer(categories, many=True).data
        user_profile_data['transactions'] = TransactionSerializer(transactions, many=True).data

        return Response(user_profile_data)
