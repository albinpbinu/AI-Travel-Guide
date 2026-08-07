import os

from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, '.env'))


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    WEATHER_API_KEY = os.getenv('WEATHER_API_KEY', '')

    # Neon (or any Postgres) connection string, e.g.
    # postgresql://user:password@host/dbname?sslmode=require
    DATABASE_URL = os.getenv('DATABASE_URL', '')

    # Cloudinary free-tier credentials for profile pictures / review photos
    CLOUDINARY_CLOUD_NAME = os.getenv('CLOUDINARY_CLOUD_NAME', '')
    CLOUDINARY_API_KEY = os.getenv('CLOUDINARY_API_KEY', '')
    CLOUDINARY_API_SECRET = os.getenv('CLOUDINARY_API_SECRET', '')

    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
    JSON_SORT_KEYS = False
