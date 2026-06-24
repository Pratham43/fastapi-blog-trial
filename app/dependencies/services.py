from app.services.user_service import UserService
from app.services.post_service import PostService


def get_post_service():
    return PostService()


def get_user_service():
    return UserService()