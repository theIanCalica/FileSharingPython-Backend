from django.contrib import admin
from file_management.models import *

# Register your models here.
admin.site.register(File)
admin.site.register(SharedFile)
admin.site.register(LinkShare)


