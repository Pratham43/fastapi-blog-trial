import uuid
from io import BytesIO

from PIL import Image, ImageOps


PROFILE_IMAGE_SIZE = (300, 300)
PROFILE_IMAGE_QUALITY = 85


def process_profile_image(content: bytes) -> tuple[bytes, str]:
    """
    Processes a profile image by:
    - fixing EXIF orientation
    - resizing/cropping to 300x300
    - converting to JPEG
    - compressing the image

    Returns:
        (processed_image_bytes, generated_filename)
    """

    with Image.open(BytesIO(content)) as original:
        image = ImageOps.exif_transpose(original)

        image = ImageOps.fit(
            image,
            PROFILE_IMAGE_SIZE,
            method=Image.Resampling.LANCZOS,
        )

        if image.mode != "RGB":
            image = image.convert("RGB")

        output = BytesIO()

        image.save(
            output,
            format="JPEG",
            quality=PROFILE_IMAGE_QUALITY,
            optimize=True,
        )

        output.seek(0)

    filename = uuid.uuid4().hex

    return output.read(), filename