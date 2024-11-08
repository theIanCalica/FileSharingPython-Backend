from django.contrib.auth.models import User
from rest_framework import serializers
from .models import *
from django.contrib.auth import get_user_model, authenticate
from rest_framework.exceptions import ValidationError
from datetime import datetime
from django.utils.crypto import get_random_string
import hashlib

UserModel = get_user_model()


class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = [
            "id",
            "file_name",
            "file_url",
            "public_id",
            "upload_date",
            "user",
            "key",
            "nonce",
            "ciphertext",
            "tag",
            "file_type",
            "file_size",
        ]

    def validate_file_url(self, value):
        if not value:
            raise serializers.ValidationError("File URL cannot be empty.")
        return value

    def validate_file_name(self, value):
        if not value:
            raise serializers.ValidationError("File name cannot be empty.")
        return value

    def validate_user(self, value):
        if not value:
            raise serializers.ValidationError("User cannot be empty.")
        return value

    def validate_file(self, value):
        # Allowed file types
        allowed_extensions = [".pdf", ".docx", ".jpg", ".png", ".jpeg", ".zip"]
        if not value.name.endswith(tuple(allowed_extensions)):
            raise serializers.ValidationError(
                "Unsupported file type. Allowed types are: .pdf, .jpeg ,.docx, .jpg, .png"
            )
        return value


class SharedFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = SharedFile
        fields = ["file", "shared_with", "access_level", "shared_date"]
        read_only_fields = ["shared_date"]

        def create(self, validated_data):
            # Custom logic to handle sharing, such as checking for existing shares
            file = validated_data.get("file")
            shared_with = validated_data.get("shared_with")
            access_level = validated_data.get("access_level")

            # Optional: Check if this file is already shared with this user
            if SharedFile.objects.filter(file=file, shared_with=shared_with).exists():
                raise serializers.ValidationError(
                    "This file is already shared with this user."
                )

            shared_file = SharedFile.objects.create(**validated_data)
            return shared_file


class LinkShareSerializer(serializers.ModelSerializer):
    class Meta:
        model = LinkShare
        fields = ["file", "share_link", "expiration_date", "password", "created_at"]
        read_only_fields = ["share_link", "created_at"]

        def create(self, validated_data):
            # Generate a unique share link if not provided
            validated_data["share_link"] = validated_data.get(
                "share_link"
            ) or get_random_string(20)

            # Optional: Hash the password if provided
            password = validated_data.get("password")
            if password:
                validated_data["password"] = hashlib.sha256(
                    password.encode()
                ).hexdigest()

            # Create the LinkShare instance
            link_share = LinkShare.objects.create(**validated_data)
            return link_share

        def validate_expiration_date(self, value):
            # Optional: Check that the expiration date is in the future
            if value and value <= datetime.now():
                raise serializers.ValidationError(
                    "Expiration date must be in the future."
                )
            return value
