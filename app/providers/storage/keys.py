class StorageKeys:

    PROFILE_PICTURES = "profile_pics"

    @classmethod
    def profile_image(cls, filename: str) -> str:
        return f"{cls.PROFILE_PICTURES}/{filename}"