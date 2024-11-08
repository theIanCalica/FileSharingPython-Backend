from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
UserModel = get_user_model()

def validate_username(data):
  username = data['username'].strip()
  if not username:
    raise ValidationError('A Username is needed')
  return True

def validate_password(data):
  password = data['password'].strip()
  if not password:
    raise ValidationError("A Password is needed")
  return True

def register_validation(data):
  first_name = data['first_name'].strip()
  last_name = data['last_name'].strip()
  username = data['username'].strip()
  email = data['email'].strip()
  password = data['password'].strip()
  
  if not first_name:
    raise ValidationError("First Name is required")

  if not last_name:
    raise ValidationError("Last Name is required")

  if not username or UserModel.objects.filter(username=username).exists():
    raise ValidationError("Choose another username")
  
  if not email or UserModel.objects.filter(email=email).exists():
        raise ValidationError('choose another email')
  
  if not password or len(password) < 8:
        raise ValidationError('choose another password, min 8 characters')
  return data