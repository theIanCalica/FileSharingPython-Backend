from django.urls import path, include
from rest_framework.routers import DefaultRouter
from user_api.views import *
from file_management.views import *

# Set up the router for viewsets
router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")

# Define urlpatterns with both router and custom paths
urlpatterns = [
    path("check-unique/", check_unique, name="check_unique"),
    path("register/", UserRegister.as_view(), name="register"),
    path("login/", UserLogin.as_view(), name="login"),
    path("logout/", UserLogout.as_view(), name="logout"),
    path("user-count/", get_user_count, name="user-count"),
    path("change-password/", change_password, name="change_password"),
    path("upload/", file_upload_view, name="file_upload"),
    path("files/<int:pk>/delete/", file_delete_view, name="file-delete"),
    path("files/", file_list_view, name="file-list"),
    path("files/<int:pk>/decrypt/", decrypt_file, name="decrypt-file"),
    path("get-tot-file-size/", get_tot_size, name="get-tot-file-size"),
    # urls for contact create, read, and update
    path("contact/", create_contact, name="create-contact"),
    path("contact-list/", contact_list, name="contact-list"),
    path("contact/<int:pk>/update", update_contact, name="update-contact"),
    path("contact-count/", get_contact_count, name="contact-count"),
    path("deactivated-count/", get_deactivated_count, name="deactivated-count"),
    path("files/share/", share_file, name="share_file"),  # Create share
    path(
        "files/shared/", list_shared_files, name="list_shared_files"
    ),  # Read shared files
    path(
        "files/shared/delete/<int:pk>/", remove_shared_file, name="delete_shared_file"
    ),  # Delete share
    path(
        "files/link-share/", create_link_share, name="create_link_share"
    ),  # Create link share
    path(
        "reset-password-request", reset_password_request, name="reset-password-request"
    ),
    path("reset-password/", reset_password, name="reset-password"),
    path("email-send", send_email_with_attachment, name="email-send"),
    path(
        "profile/change-picture/", change_profile_picture, name="change_profile_picture"
    ),
    # for admin
    path("get-files/", get_files, name="get-files"),
]

# Include the router-generated URLs
urlpatterns += router.urls
