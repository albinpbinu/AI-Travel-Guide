import cloudinary
import cloudinary.uploader
from flask import current_app

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
_configured = False


def _ensure_configured():
    global _configured
    if _configured:
        return
    cloudinary.config(
        cloud_name=current_app.config['CLOUDINARY_CLOUD_NAME'],
        api_key=current_app.config['CLOUDINARY_API_KEY'],
        api_secret=current_app.config['CLOUDINARY_API_SECRET'],
        secure=True,
    )
    _configured = True


def save_upload(file_storage, folder='travelguide'):
    """Uploads an image to Cloudinary. Returns the resulting secure HTTPS
    URL, or None if no valid file was given or Cloudinary isn't configured."""
    if not file_storage or not file_storage.filename:
        return None
    ext = file_storage.filename.rsplit('.', 1)[-1].lower() if '.' in file_storage.filename else ''
    if ext not in ALLOWED_EXTENSIONS:
        return None
    if not current_app.config.get('CLOUDINARY_CLOUD_NAME'):
        return None

    _ensure_configured()
    result = cloudinary.uploader.upload(file_storage, folder=folder)
    return result.get('secure_url')
