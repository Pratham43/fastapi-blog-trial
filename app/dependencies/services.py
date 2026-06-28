from app.services.auth_service import AuthService
from app.services.post_service import PostService
from app.services.user_service import UserService



def get_auth_service():
    return AuthService()


def get_user_service():
    return UserService()


def get_post_service():
    return PostService()

