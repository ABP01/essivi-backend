import sys
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile

def compress_image(image_field, max_size=(1024, 1024), quality=85):
    """
    Compresses an image, resizes it, and converts it to WebP.
    """
    if not image_field:
        return None

    # Open the image using Pillow
    img = Image.open(image_field)
    
    # Convert RGBA to RGB if necessary
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')

    # Resize if larger than max_size
    img.thumbnail(max_size, Image.Resampling.LANCZOS)

    # Save to BytesIO buffer as WebP
    output = BytesIO()
    img.save(output, format='WEBP', quality=quality)
    output.seek(0)

    # Change the file extension
    new_name = image_field.name.rsplit('.', 1)[0] + '.webp'

    # Create a new Django InMemoryUploadedFile
    return InMemoryUploadedFile(
        output,
        'ImageField',
        new_name,
        'image/webp',
        sys.getsizeof(output),
        None
    )
