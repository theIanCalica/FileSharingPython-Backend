from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
UserModel = get_user_model()

def validate_folderName(data):
  folder_name = data["folder_name"].strip()
  if not folder_name:
    raise ValidationError('A Folder Name is needed')
  return True

