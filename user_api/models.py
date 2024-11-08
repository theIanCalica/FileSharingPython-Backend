from django.db import models
from django.contrib.auth.models import User
import cloudinary
import cloudinary.uploader
import cloudinary.api


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    public_id = models.CharField(
        max_length=255, blank=True, null=True, default="pf8iioqsmo9unsmegxrv"
    )
    url = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        default="https://res.cloudinary.com/dzydn2faa/image/upload/v1730799486/pf8iioqsmo9unsmegxrv.jpg",
    )

    def save_profile_picture(self, file):
        # Check if the current profile picture is not the default
        if self.public_id and self.public_id != "pf8iioqsmo9unsmegxrv":
            cloudinary.uploader.destroy(self.public_id)  # Delete old picture if custom

        # Upload the new file to Cloudinary
        result = cloudinary.uploader.upload(file, folder="profile_pictures")

        # Update URL and public_id with the new image information
        self.public_id = result.get("public_id")
        self.url = result.get("url")
        self.save()


class Contact(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("resolved", "Resolved"),
    ]
    name = models.CharField(max_length=255)
    email = models.EmailField()
    message = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Message from {self.name} ({self.email})"
