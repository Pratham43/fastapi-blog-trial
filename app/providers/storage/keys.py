class StorageKeys:

    PROFILE_PICTURES = "profile_pics"
    POSTS = "posts"

    @classmethod
    def profile_image(cls, filename: str) -> str:
        return f"{cls.PROFILE_PICTURES}/{filename}"

    @classmethod
    def post_image(cls, filename: str) -> str:
        return f"{cls.POSTS}/{filename}"