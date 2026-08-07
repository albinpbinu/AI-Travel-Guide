# System Architecture

## Overview

The application follows a modular Flask architecture separated into:
- Presentation layer: templates and static assets
- Application service layer: recommendation, Gemini, weather, PDF, nearby-POI lookup
- Persistence layer: Postgres (Neon free tier), schema defined in `database/db.py`
- File storage: Cloudinary (profile pictures, review photos)
- Security layer: Flask-Login sessions, Flask-WTF CSRF protection, password hashing

## Key modules
- `app.py` — route entrypoint (also the WSGI target imported by `api/index.py` for Vercel)
- `services/recommendation.py` — hybrid recommendation ranking engine
- `services/gemini_service.py` — optional Gemini-backed plan narrative, with a deterministic local fallback
- `services/weather_service.py` — optional OpenWeather integration, with a local fallback
- `services/nearby_service.py` — live OpenStreetMap Overpass API lookup for nearby essentials
- `services/pdf_service.py` — reportlab-based itinerary PDF export
- `database/db.py` — all Postgres schema + queries
- `utils/uploads.py` — Cloudinary upload helper

## Deployment
Hosted on Vercel's free tier as a Python serverless function (`api/index.py` imports the
Flask `app` object). Database and file storage are external (Neon, Cloudinary) since
serverless functions have no persistent local disk. See `README.md` for setup steps.
