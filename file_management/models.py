from django.db import models
from django.contrib.auth.models import User


class File(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="files")
    file_name = models.CharField(max_length=255)
    file_url = models.URLField(
        max_length=200, null=True
    )  # Store the URL of the uploaded file
    public_id = models.CharField(max_length=255, unique=True)
    upload_date = models.DateTimeField(auto_now_add=True)
    file_type = models.CharField(max_length=255, default="unknown")
    key = models.TextField()  # Store the encoded key
    nonce = models.TextField()  # Store the encoded nonce
    ciphertext = models.TextField()  # Store the encoded ciphertext
    tag = models.TextField()
    file_size = models.PositiveIntegerField(null=True)

    def __str__(self):
        return self.file_name


class SharedFile(models.Model):
    file = models.ForeignKey(
        File, on_delete=models.CASCADE, related_name="shared_files"
    )
    shared_with = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="shared_files"
    )
    shared_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.file.file_name} shared with {self.shared_with.username}"


class LinkShare(models.Model):
    file = models.ForeignKey(File, on_delete=models.CASCADE, related_name="link_shares")
    share_link = models.CharField(max_length=255, unique=True)
    expiration_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Link for {self.file.file_name}"
