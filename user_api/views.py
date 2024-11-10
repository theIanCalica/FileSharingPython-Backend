from django.shortcuts import render
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth import login, logout
from rest_framework.response import Response
from rest_framework import viewsets, permissions
from django.contrib.auth.models import User
from .serializer import *
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication
from .validations import *
from django.http import JsonResponse
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import transaction
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.conf import settings
from datetime import datetime, timedelta
import jwt
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.mail import EmailMessage
import logging

logger = logging.getLogger(__name__)


# Change profile picture
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_profile_picture(request):
    user_profile = request.user.userprofile
    file = request.FILES.get("profile_picture")
    if not file:
        return Response(
            {"error": "No image provided."}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Call the model's method to save the profile picture
        user_profile.save_profile_picture(file)
        serializer = UserProfileSerializer(user_profile)
        return Response(
            {
                "message": "Profile picture updated successfully",
                "profile": serializer.data,
            },
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        return Response(
            {"error": "Failed to update profile picture"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def reset_password_request(request):
    email = request.data.get("email")

    # Attempt to find the user by email
    try:
        user = User.objects.get(email=email)

        # Generate a JWT token
        payload = {
            "user_id": user.id,
            "exp": datetime.utcnow() + timedelta(hours=1),  # Set expiration to 1 hour
        }
        reset_token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

        # Send password reset email
        send_mail(
            "Password Reset Request",
            f"Use this link to reset your password: https://filesharingpython-frontend.onrender.com/change-password/{reset_token}/",
            settings.EMAIL_HOST_USER,  # Use the configured email from settings
            [email],  # The recipient's email
            fail_silently=False,
        )

    except User.DoesNotExist:
        # Do nothing, simply respond as if it succeeded
        pass

    # Always return a success response
    return Response(
        {"message": "If this email is registered, a reset link has been sent."},
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def reset_password(request):
    user_id = request.data.get("user_id")
    new_password = request.data.get("password")

    try:
        user = User.objects.get(id=user_id)
        user.set_password(new_password)  # Set the new password
        user.save()  # Save the user
        return Response(
            {"message": "Password changed successfully."}, status=status.HTTP_200_OK
        )
    except User.DoesNotExist:
        return Response(
            {"message": "User not found."}, status=status.HTTP_404_NOT_FOUND
        )


@api_view(["GET"])
@permission_classes([IsAdminUser])
def get_user_count(request):
    user_count = User.objects.count()
    return JsonResponse({"user_count": user_count}, status=200)


@api_view(["GET"])
@permission_classes([IsAdminUser])
def get_contact_count(request):
    contact_count = Contact.objects.count()
    return JsonResponse({"contact_count": contact_count}, status=200)


@api_view(["GET"])
@permission_classes([IsAdminUser])
def get_deactivated_count(request):
    deactivated_count = User.objects.filter(is_active=False).count()
    return JsonResponse({"deactivated_count": deactivated_count}, status=200)


class UserRegister(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        clean_data = register_validation(request.data)
        serializer = UserRegisterSerializer(data=clean_data)

        # Begin an atomic transaction to handle both user and profile creation
        with transaction.atomic():
            if serializer.is_valid(raise_exception=True):
                user = serializer.create(clean_data)

                # Create a UserProfile instance for the newly created user
                profile = UserProfile.objects.create(user=user)

                # Generate tokens for the new user
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                refresh_token = str(refresh)

                # Serialize user data for the response
                user_data = UserObjSerializer(user).data
                profile_data = UserProfileSerializer(profile).data
                return Response(
                    {
                        "user": user_data,
                        "access": access_token,
                        "refresh": refresh_token,
                        "profile": profile_data,
                    },
                    status=status.HTTP_201_CREATED,
                )

        return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([AllowAny])
def check_unique(request, id=None):
    username = request.query_params.get("username")
    email = request.query_params.get("email")
    # Exclude the current user (if user_id is provided) while checking uniqueness
    is_username_unique = (
        not User.objects.filter(username=username).exclude(id=id).exists()
    )
    is_email_unique = not User.objects.filter(email=email).exclude(id=id).exists()

    return Response(
        {
            "is_username_unique": is_username_unique,
            "is_email_unique": is_email_unique,
        }
    )


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def change_password(request):
    user = request.user
    serializer = PasswordChangeSerializer(data=request.data)

    # Validate the serializer
    if serializer.is_valid():
        current_password = serializer.validated_data["current_password"]

        # Verify if the current password is correct
        if not user.check_password(current_password):
            return Response(
                {"error": "Current Password is incorrect"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Update the user's password
            user.set_password(serializer.validated_data["new_password"])
            user.save()

            return Response(
                {"message": "Password updated successfully"},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {
                    "error": "An error occurred while updating the password. Please try again."
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLogin(APIView):
    permission_classes = (permissions.AllowAny,)
    authentication_classes = (SessionAuthentication,)

    def post(self, request):
        data = request.data
        assert validate_username(data)
        assert validate_password(data)
        serializer = UserLoginSerializer(data=data)
        if serializer.is_valid(raise_exception=True):
            user = serializer.check_user(data)
            login(request, user)
            refresh = RefreshToken.for_user(user)
            user_data = UserObjSerializer(user).data
            user_profile = UserProfile.objects.get(user=user)
            profile_data = UserProfileSerializer(user_profile).data
            return Response(
                {
                    "user": user_data,
                    "profile": profile_data,
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                },
                status=status.HTTP_200_OK,
            )


class UserLogout(APIView):
    permission_classes = (permissions.AllowAny,)
    authentication_classes = ()

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_200_OK)


class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def list(self, request):
        """Retrieve all users, sorted by ID (ascending), with their user profile data."""
        users = self.get_queryset().order_by("id")  # Sort users by ID

        # Manually add UserProfile data to each user
        users_data = []
        for user in users:
            # Retrieve the related UserProfile object for each user
            try:
                user_profile = (
                    user.userprofile
                )  # This assumes the reverse relationship is named 'userprofile'
                # Add the user profile data as a dictionary or object
                profile_data = {
                    "public_id": user_profile.public_id,
                    "url": user_profile.url,
                }
            except UserProfile.DoesNotExist:
                profile_data = {}  # In case there's no profile for the user

            # Serialize the user data along with the profile data
            user_data = UserSerializer(user).data
            user_data["profile"] = (
                profile_data  # Add profile data to the user dictionary
            )
            users_data.append(user_data)

        return Response(users_data, status=status.HTTP_200_OK)

    def create(self, request):
        """Create a new user."""
        serializer = UserSerializer(data=request.data)

        if serializer.is_valid():  # Check if the serializer data is valid
            with transaction.atomic():
                user = serializer.save()  # Save the user if the data is valid
                profile = UserProfile.objects.create(user=user)  # Create the profile
                # Serialize user data for the response
                user_data = UserObjSerializer(user).data
                profile_data = UserProfileSerializer(profile).data
                return Response(
                    {
                        "message": "Successfully Created",
                        "user": user_data,
                        "profile": profile_data,
                    },
                    status=status.HTTP_201_CREATED,
                )
        else:
            # Return errors if the serializer data is invalid
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        """Update an existing user with partial data."""
        try:
            # Fetch the user by primary key
            user = User.objects.get(pk=pk)

            # Initialize the serializer with partial=True to allow incomplete data
            serializer = self.get_serializer(user, data=request.data, partial=True)

            # Validate the data (partial validation)
            if serializer.is_valid():
                # Save the updated user data
                serializer.save()

                return Response(
                    {"success": "Update successfully", "user": serializer.data},
                    status=status.HTTP_200_OK,
                )
            else:
                # If data is invalid, return errors
                return Response(
                    {"error": "Invalid data", "details": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except User.DoesNotExist:
            return Response(
                {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )

        def destroy(self, request, pk=None):
            """Delete a user by primary key (pk)."""
            try:
                user = User.objects.get(pk=pk)
                user.delete()
                return Response(
                    {"message": "User deleted successfully"},
                    status=status.HTTP_204_NO_CONTENT,
                )
            except User.DoesNotExist:
                return Response(
                    {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
                )


@api_view(["POST"])
@permission_classes([AllowAny])
def create_contact(request):
    data = request.data
    serializer = ContactSerializer(data=data)
    if serializer.is_valid(raise_exception=True):
        contact = serializer.save()

        return Response(status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAdminUser])
def contact_list(request):
    contacts = Contact.objects.all()
    serializer = ContactSerializer(contacts, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["PUT"])
@permission_classes([IsAdminUser])
def update_contact(request, pk):
    try:
        contact = Contact.objects.get(pk=pk)
    except Contact.DoesNotExist:
        return Response(
            {"detail": "Contact not found."}, status=status.HTTP_404_NOT_FOUND
        )

    serializer = ContactSerializer(contact, data=request.data)
    if serializer.is_valid(raise_exception=True):
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def send_email_with_attachment(request):
    # Parse the incoming multipart form data (file included)
    request.parsers = [MultiPartParser, FormParser]

    uploaded_file = request.FILES.get("file")

    if uploaded_file:
        # Prepare the email
        email = EmailMessage(
            "Subject here",
            "Here is the message.",
            settings.DEFAULT_FROM_EMAIL,
            ["recipient@example.com"],
        )

        # Attach the file directly without saving it to the server
        email.attach(
            uploaded_file.name, uploaded_file.read(), uploaded_file.content_type
        )
        email.send()

        return Response(
            {"message": "Email sent successfully with the attachment."}, status=200
        )
    else:
        return Response({"error": "No file provided."}, status=400)
