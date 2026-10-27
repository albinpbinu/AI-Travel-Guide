import json
import secrets
from datetime import datetime, timedelta, timezone

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

_pool = None


def _resolve_app(app):
    if app is not None:
        return app
    from flask import current_app
    return current_app._get_current_object()


def _get_pool(app):
    global _pool
    if _pool is None:
        _pool = ConnectionPool(
            conninfo=app.config['DATABASE_URL'],
            min_size=1, max_size=5,
            kwargs={'row_factory': dict_row},
        )
    return _pool


def get_db(app=None):
    """Returns a pooled connection as a context manager: `with get_db() as conn:`.
    Reusing a small pool instead of opening a fresh connection per query avoids
    hammering Neon's new-connection rate limit under repeated requests, and the
    context manager still commits/rolls back and safely returns the connection
    to the pool (not closes it) on exit, even if a query raises mid-function."""
    app = _resolve_app(app)
    return _get_pool(app).connection()


def now():
    return datetime.now(timezone.utc).isoformat()


SEED_DESTINATIONS = [
    {
        'name': 'Munnar', 'state': 'Kerala', 'category': 'Hill Station',
        'budget': 28000, 'interest_match': 0.92, 'distance': 0.85, 'weather': 0.81,
        'rating': 4.8, 'history': 0.9, 'lat': 10.0889, 'lng': 77.0595,
        'weather_text': 'Pleasant', 'image': 'https://images.unsplash.com/photo-1646818978594-880ef94bde44?auto=format&fit=crop&w=1200&q=80',
        'description': 'Rolling tea plantations, misty hills, and a cool climate year-round.',
        'nearby_attractions': ['Eravikulam National Park', 'Mattupetty Dam', 'Tea Museum'],
        'hotels': [
            {'name': 'Windermere Estate', 'category': 'Luxury', 'price': 9500, 'rating': 4.8},
            {'name': 'Munnar Tea Valley Resort', 'category': 'Resort', 'price': 5200, 'rating': 4.5},
            {'name': 'Zostel Munnar', 'category': 'Hostel', 'price': 900, 'rating': 4.3},
        ],
        'restaurants': [
            {'name': 'Saravana Bhavan', 'cuisine': 'South Indian', 'price_range': 'Budget', 'rating': 4.4},
            {'name': 'Rapsy Restaurant', 'cuisine': 'Kerala', 'price_range': 'Mid', 'rating': 4.6},
        ],
    },
    {
        'name': 'Goa', 'state': 'Goa', 'category': 'Beach',
        'budget': 35000, 'interest_match': 0.80, 'distance': 0.78, 'weather': 0.79,
        'rating': 4.6, 'history': 0.7, 'lat': 15.2993, 'lng': 74.1240,
        'weather_text': 'Sunny', 'image': 'https://images.unsplash.com/photo-1519046904884-53103b34b206?auto=format&fit=crop&w=1200&q=80',
        'description': 'Golden beaches, Portuguese heritage, and a buzzing nightlife scene.',
        'nearby_attractions': ['Baga Beach', 'Fort Aguada', 'Basilica of Bom Jesus'],
        'hotels': [
            {'name': 'Taj Fort Aguada', 'category': 'Luxury', 'price': 12000, 'rating': 4.7},
            {'name': 'Baga Beach Resort', 'category': 'Resort', 'price': 4800, 'rating': 4.3},
            {'name': 'The Hosteller Goa', 'category': 'Hostel', 'price': 700, 'rating': 4.2},
        ],
        'restaurants': [
            {'name': "Fisherman's Wharf", 'cuisine': 'Seafood', 'price_range': 'Mid', 'rating': 4.5},
            {'name': "Britto's", 'cuisine': 'Goan', 'price_range': 'Mid', 'rating': 4.3},
        ],
    },
    {
        'name': 'Jaipur', 'state': 'Rajasthan', 'category': 'Historical',
        'budget': 32000, 'interest_match': 0.76, 'distance': 0.70, 'weather': 0.72,
        'rating': 4.7, 'history': 0.6, 'lat': 26.9124, 'lng': 75.7873,
        'weather_text': 'Warm', 'image': 'https://images.unsplash.com/photo-1599661046289-e31897846e41?auto=format&fit=crop&w=1200&q=80',
        'description': 'The Pink City — majestic forts, palaces, and vibrant bazaars.',
        'nearby_attractions': ['Amber Fort', 'Hawa Mahal', 'City Palace'],
        'hotels': [
            {'name': 'Rambagh Palace', 'category': 'Luxury', 'price': 15000, 'rating': 4.9},
            {'name': 'Hotel Pearl Palace', 'category': 'Budget', 'price': 2200, 'rating': 4.5},
            {'name': 'Zostel Jaipur', 'category': 'Hostel', 'price': 850, 'rating': 4.2},
        ],
        'restaurants': [
            {'name': 'Chokhi Dhani', 'cuisine': 'Rajasthani', 'price_range': 'Mid', 'rating': 4.6},
            {'name': 'Laxmi Misthan Bhandar', 'cuisine': 'North Indian', 'price_range': 'Budget', 'rating': 4.4},
        ],
    },
    {
        'name': 'Manali', 'state': 'Himachal Pradesh', 'category': 'Adventure',
        'budget': 26000, 'interest_match': 0.84, 'distance': 0.65, 'weather': 0.6,
        'rating': 4.6, 'history': 0.55, 'lat': 32.2432, 'lng': 77.1892,
        'weather_text': 'Cold', 'image': 'https://images.unsplash.com/photo-1626621341517-bbf3d9990a23?auto=format&fit=crop&w=1200&q=80',
        'description': 'Snow-capped peaks, river rafting, and Himalayan adventure sports.',
        'nearby_attractions': ['Solang Valley', 'Rohtang Pass', 'Hadimba Temple'],
        'hotels': [
            {'name': 'The Himalayan', 'category': 'Luxury', 'price': 8500, 'rating': 4.7},
            {'name': 'Snow Valley Resorts', 'category': 'Resort', 'price': 4200, 'rating': 4.4},
            {'name': 'Zostel Old Manali', 'category': 'Hostel', 'price': 800, 'rating': 4.3},
        ],
        'restaurants': [
            {'name': 'Cafe 1947', 'cuisine': 'Continental', 'price_range': 'Mid', 'rating': 4.5},
            {'name': "Johnson's Cafe", 'cuisine': 'Multi-cuisine', 'price_range': 'Mid', 'rating': 4.4},
        ],
    },
    {
        'name': 'Alleppey', 'state': 'Kerala', 'category': 'Nature',
        'budget': 24000, 'interest_match': 0.88, 'distance': 0.9, 'weather': 0.83,
        'rating': 4.7, 'history': 0.5, 'lat': 9.4981, 'lng': 76.3388,
        'weather_text': 'Humid', 'image': 'https://images.unsplash.com/photo-1593693411515-c20261bcad6e?auto=format&fit=crop&w=1200&q=80',
        'description': 'Tranquil backwaters, houseboats, and coconut-lined canals.',
        'nearby_attractions': ['Alleppey Backwaters', 'Marari Beach', 'Krishnapuram Palace'],
        'hotels': [
            {'name': 'Punnamada Backwater Resort', 'category': 'Resort', 'price': 6200, 'rating': 4.6},
            {'name': 'Lake Palace Resort', 'category': 'Luxury', 'price': 9800, 'rating': 4.7},
            {'name': 'Alleppey Backpackers', 'category': 'Hostel', 'price': 750, 'rating': 4.1},
        ],
        'restaurants': [
            {'name': 'Chakara Restaurant', 'cuisine': 'Kerala Seafood', 'price_range': 'Mid', 'rating': 4.5},
            {'name': 'Harbour Restaurant', 'cuisine': 'Kerala', 'price_range': 'Budget', 'rating': 4.2},
        ],
    },
    {
        'name': 'Varanasi', 'state': 'Uttar Pradesh', 'category': 'Religious',
        'budget': 20000, 'interest_match': 0.85, 'distance': 0.6, 'weather': 0.65,
        'rating': 4.6, 'history': 0.6, 'lat': 25.3176, 'lng': 82.9739,
        'weather_text': 'Warm', 'image': 'https://images.unsplash.com/photo-1762513839526-c596f5e99a9a?auto=format&fit=crop&w=1200&q=80',
        'description': 'Ancient spiritual capital on the Ganges — sunrise boat rides, evening aarti ceremonies, and centuries of living tradition.',
        'nearby_attractions': ['Dashashwamedh Ghat', 'Kashi Vishwanath Temple', 'Sarnath'],
        'hotels': [
            {'name': 'BrijRama Palace', 'category': 'Luxury', 'price': 11000, 'rating': 4.7},
            {'name': 'Ganges View Hotel', 'category': 'Budget', 'price': 2500, 'rating': 4.4},
            {'name': 'Zostel Varanasi', 'category': 'Hostel', 'price': 700, 'rating': 4.2},
        ],
        'restaurants': [
            {'name': 'Kashi Chaat Bhandar', 'cuisine': 'Street Food', 'price_range': 'Budget', 'rating': 4.5},
            {'name': 'Brown Bread Bakery', 'cuisine': 'Multi-cuisine', 'price_range': 'Mid', 'rating': 4.3},
        ],
    },
    {
        'name': 'Rishikesh', 'state': 'Uttarakhand', 'category': 'Adventure',
        'budget': 18000, 'interest_match': 0.88, 'distance': 0.65, 'weather': 0.75,
        'rating': 4.7, 'history': 0.5, 'lat': 30.0869, 'lng': 78.2676,
        'weather_text': 'Pleasant', 'image': 'https://images.unsplash.com/photo-1718431108073-7f61fb5dfefb?auto=format&fit=crop&w=1200&q=80',
        'description': 'Yoga capital of the world and gateway to Himalayan adventure — white-water rafting, bungee jumping, and riverside ashrams.',
        'nearby_attractions': ['Laxman Jhula', 'Triveni Ghat', 'Beatles Ashram'],
        'hotels': [
            {'name': 'Ananda in the Himalayas', 'category': 'Luxury', 'price': 13500, 'rating': 4.8},
            {'name': 'Divine Ganga Cottage', 'category': 'Resort', 'price': 3200, 'rating': 4.4},
            {'name': 'Zostel Rishikesh', 'category': 'Hostel', 'price': 750, 'rating': 4.3},
        ],
        'restaurants': [
            {'name': 'Chotiwala', 'cuisine': 'North Indian', 'price_range': 'Budget', 'rating': 4.3},
            {'name': 'Ganga Beach Cafe', 'cuisine': 'Multi-cuisine', 'price_range': 'Mid', 'rating': 4.5},
        ],
    },
    {
        'name': 'Ranthambore', 'state': 'Rajasthan', 'category': 'Wildlife',
        'budget': 30000, 'interest_match': 0.83, 'distance': 0.55, 'weather': 0.6,
        'rating': 4.6, 'history': 0.4, 'lat': 26.0173, 'lng': 76.5026,
        'weather_text': 'Warm', 'image': 'https://images.unsplash.com/photo-1700562554203-5b8644512759?auto=format&fit=crop&w=1200&q=80',
        'description': "One of India's premier tiger reserves — thrilling jeep safaris through dry deciduous forest and ancient ruins.",
        'nearby_attractions': ['Ranthambore Fort', 'Padam Talao', 'Trinetra Ganesh Temple'],
        'hotels': [
            {'name': 'Sher Bagh', 'category': 'Luxury', 'price': 16000, 'rating': 4.8},
            {'name': 'Tiger Den Resort', 'category': 'Resort', 'price': 4500, 'rating': 4.3},
            {'name': 'RTDC Vinayak', 'category': 'Budget', 'price': 1800, 'rating': 4.0},
        ],
        'restaurants': [
            {'name': "Dev Vilas", 'cuisine': 'Rajasthani', 'price_range': 'Mid', 'rating': 4.3},
            {'name': "Deo's Kitchen", 'cuisine': 'Multi-cuisine', 'price_range': 'Mid', 'rating': 4.2},
        ],
    },
    {
        'name': 'Havelock Island', 'state': 'Andaman and Nicobar Islands', 'category': 'Beach',
        'budget': 45000, 'interest_match': 0.90, 'distance': 0.5, 'weather': 0.85,
        'rating': 4.8, 'history': 0.3, 'lat': 12.0067, 'lng': 92.9875,
        'weather_text': 'Sunny', 'image': 'https://images.unsplash.com/photo-1672231862286-bdf67abb806c?auto=format&fit=crop&w=1200&q=80',
        'description': 'Pristine white-sand beaches and turquoise waters — Radhanagar Beach, world-class diving, and total island calm.',
        'nearby_attractions': ['Radhanagar Beach', 'Elephant Beach', 'Kalapathar Beach'],
        'hotels': [
            {'name': 'Taj Exotica Andamans', 'category': 'Luxury', 'price': 18000, 'rating': 4.8},
            {'name': 'Barefoot at Havelock', 'category': 'Resort', 'price': 7500, 'rating': 4.6},
            {'name': 'Wild Orchid', 'category': 'Budget', 'price': 2800, 'rating': 4.2},
        ],
        'restaurants': [
            {'name': 'Full Moon Cafe', 'cuisine': 'Seafood', 'price_range': 'Mid', 'rating': 4.5},
            {'name': 'Anju Coco Resort Restaurant', 'cuisine': 'Multi-cuisine', 'price_range': 'Budget', 'rating': 4.2},
        ],
    },
]

MOOD_KEYWORDS = {
    'peaceful': 'Nature', 'relax': 'Nature', 'calm': 'Nature', 'quiet': 'Nature',
    'adventure': 'Adventure', 'thrill': 'Adventure', 'trek': 'Adventure', 'rafting': 'Adventure',
    'beach': 'Beach', 'sea': 'Beach', 'coast': 'Beach', 'island': 'Beach', 'diving': 'Beach',
    'mountain': 'Hill Station', 'hill': 'Hill Station', 'snow': 'Hill Station',
    'history': 'Historical', 'heritage': 'Historical', 'culture': 'Historical', 'fort': 'Historical',
    'food': 'Food', 'cuisine': 'Food',
    'wildlife': 'Wildlife', 'nature': 'Nature', 'safari': 'Wildlife', 'tiger': 'Wildlife',
    'religious': 'Religious', 'spiritual': 'Religious', 'temple': 'Religious', 'pilgrimage': 'Religious',
    'yoga': 'Adventure', 'ganges': 'Religious',
}


def init_db(app):
    with get_db(app) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    phone TEXT,
                    country TEXT,
                    password_hash TEXT NOT NULL,
                    profile_picture TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS destinations (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    state TEXT,
                    category TEXT,
                    budget INTEGER NOT NULL,
                    interest_match REAL NOT NULL,
                    distance REAL NOT NULL,
                    weather REAL NOT NULL,
                    rating REAL NOT NULL,
                    history REAL NOT NULL,
                    lat REAL, lng REAL,
                    weather_text TEXT,
                    image TEXT,
                    description TEXT,
                    nearby_attractions TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS hotels (
                    id SERIAL PRIMARY KEY,
                    destination_id INTEGER NOT NULL REFERENCES destinations(id) ON DELETE CASCADE,
                    name TEXT NOT NULL,
                    category TEXT,
                    price_per_night INTEGER,
                    rating REAL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS restaurants (
                    id SERIAL PRIMARY KEY,
                    destination_id INTEGER NOT NULL REFERENCES destinations(id) ON DELETE CASCADE,
                    name TEXT NOT NULL,
                    cuisine TEXT,
                    price_range TEXT,
                    rating REAL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS trips (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    title TEXT NOT NULL,
                    destination_name TEXT,
                    budget INTEGER,
                    duration_days INTEGER,
                    travel_date TEXT,
                    return_date TEXT,
                    status TEXT NOT NULL DEFAULT 'saved',
                    data TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS favorites (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    destination_id INTEGER NOT NULL REFERENCES destinations(id) ON DELETE CASCADE,
                    created_at TEXT NOT NULL,
                    UNIQUE(user_id, destination_id)
                );

                CREATE TABLE IF NOT EXISTS reviews (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    destination_id INTEGER NOT NULL REFERENCES destinations(id) ON DELETE CASCADE,
                    rating INTEGER NOT NULL,
                    comment TEXT,
                    photo_url TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS review_likes (
                    id SERIAL PRIMARY KEY,
                    review_id INTEGER NOT NULL REFERENCES reviews(id) ON DELETE CASCADE,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    UNIQUE(review_id, user_id)
                );

                CREATE TABLE IF NOT EXISTS search_history (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    query TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS password_resets (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    token TEXT UNIQUE NOT NULL,
                    created_at TEXT NOT NULL,
                    used INTEGER NOT NULL DEFAULT 0
                );

                -- Holds the plan a user just generated, until they save it or
                -- export a PDF. Too big for the session cookie, and serverless
                -- containers have no disk to park it on.
                CREATE TABLE IF NOT EXISTS itinerary_stash (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    data TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
            """)

            cur.execute("SELECT 1 FROM users WHERE email = %s", ('demo@travelguide.ai',))
            if cur.fetchone() is None:
                from werkzeug.security import generate_password_hash
                cur.execute(
                    "INSERT INTO users (name, email, phone, country, password_hash, created_at) VALUES (%s, %s, %s, %s, %s, %s)",
                    ('Demo User', 'demo@travelguide.ai', '', 'India', generate_password_hash('demo1234'), now())
                )

            cur.execute("SELECT COUNT(*) AS c FROM destinations")
            if cur.fetchone()['c'] == 0:
                for d in SEED_DESTINATIONS:
                    cur.execute(
                        """INSERT INTO destinations
                           (name, state, category, budget, interest_match, distance, weather, rating, history,
                            lat, lng, weather_text, image, description, nearby_attractions, created_at)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
                        (d['name'], d['state'], d['category'], d['budget'], d['interest_match'], d['distance'],
                         d['weather'], d['rating'], d['history'], d['lat'], d['lng'], d['weather_text'], d['image'],
                         d['description'], json.dumps(d['nearby_attractions']), now())
                    )
                    destination_id = cur.fetchone()['id']
                    for h in d.get('hotels', []):
                        cur.execute(
                            "INSERT INTO hotels (destination_id, name, category, price_per_night, rating, created_at) VALUES (%s, %s, %s, %s, %s, %s)",
                            (destination_id, h['name'], h['category'], h['price'], h['rating'], now())
                        )
                    for r in d.get('restaurants', []):
                        cur.execute(
                            "INSERT INTO restaurants (destination_id, name, cuisine, price_range, rating, created_at) VALUES (%s, %s, %s, %s, %s, %s)",
                            (destination_id, r['name'], r['cuisine'], r['price_range'], r['rating'], now())
                        )


def _destination_row_to_dict(row):
    if row is None:
        return None
    d = dict(row)
    d['nearby_attractions'] = json.loads(d['nearby_attractions']) if d.get('nearby_attractions') else []
    return d


# ---------- Users ----------

def create_user(app, name, email, phone, country, password_hash):
    with get_db(app) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (name, email, phone, country, password_hash, created_at) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
                (name, email, phone, country, password_hash, now())
            )
            return cur.fetchone()['id']


def get_user_by_email(app, email):
    with get_db(app) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE email = %s", (email,))
            return cur.fetchone()


def get_user_by_id(app, user_id):
    with get_db(app) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            return cur.fetchone()


def update_user_profile(user_id, name, phone, country, profile_picture=None):
    with get_db() as conn:
        with conn.cursor() as cur:
            if profile_picture:
                cur.execute(
                    "UPDATE users SET name=%s, phone=%s, country=%s, profile_picture=%s WHERE id=%s",
                    (name, phone, country, profile_picture, user_id)
                )
            else:
                cur.execute(
                    "UPDATE users SET name=%s, phone=%s, country=%s WHERE id=%s",
                    (name, phone, country, user_id)
                )


def update_user_password(user_id, password_hash):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE users SET password_hash=%s WHERE id=%s", (password_hash, user_id))


def list_users():
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT u.*, (SELECT COUNT(*) FROM trips t WHERE t.user_id = u.id) AS trip_count
                   FROM users u ORDER BY u.created_at DESC"""
            )
            return [dict(r) for r in cur.fetchall()]


def delete_user(user_id):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM users WHERE id = %s", (user_id,))


# ---------- Password reset (dev-mode: no SMTP, token surfaced directly) ----------

def create_password_reset(user_id):
    token = secrets.token_urlsafe(32)
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO password_resets (user_id, token, created_at, used) VALUES (%s, %s, %s, 0)",
                (user_id, token, now())
            )
    return token


def get_password_reset(token):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM password_resets WHERE token = %s", (token,))
            row = cur.fetchone()
    if not row:
        return None
    row = dict(row)
    created = datetime.fromisoformat(row['created_at'])
    if row['used'] or datetime.now(timezone.utc) - created > timedelta(hours=1):
        return None
    return row


def consume_password_reset(token):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE password_resets SET used = 1 WHERE token = %s", (token,))


# ---------- Destinations ----------

def list_destinations(filters=None):
    query = "SELECT * FROM destinations WHERE 1=1"
    params = []
    filters = filters or {}
    if filters.get('state'):
        query += " AND state = %s"
        params.append(filters['state'])
    if filters.get('category'):
        query += " AND category = %s"
        params.append(filters['category'])
    if filters.get('max_budget'):
        query += " AND budget <= %s"
        params.append(filters['max_budget'])
    if filters.get('min_rating'):
        query += " AND rating >= %s"
        params.append(filters['min_rating'])
    if filters.get('q'):
        query += " AND (name ILIKE %s OR state ILIKE %s OR category ILIKE %s OR description ILIKE %s)"
        like = f"%{filters['q']}%"
        params += [like, like, like, like]
    query += " ORDER BY rating DESC"

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()
    return [_destination_row_to_dict(r) for r in rows]


def get_destination(destination_id):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM destinations WHERE id = %s", (destination_id,))
            row = cur.fetchone()
    return _destination_row_to_dict(row) if row else None


def create_destination(payload):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO destinations
                   (name, state, category, budget, interest_match, distance, weather, rating, history,
                    lat, lng, weather_text, image, description, nearby_attractions, created_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
                (payload['name'], payload['state'], payload['category'], payload['budget'],
                 payload.get('interest_match', 0.75), payload.get('distance', 0.7), payload.get('weather', 0.7),
                 payload.get('rating', 4.5), payload.get('history', 0.5), payload.get('lat'), payload.get('lng'),
                 payload.get('weather_text', 'Pleasant'), payload.get('image', ''), payload.get('description', ''),
                 json.dumps(payload.get('nearby_attractions', [])), now())
            )
            return cur.fetchone()['id']


def update_destination(destination_id, payload):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE destinations SET name=%s, state=%s, category=%s, budget=%s, rating=%s, weather_text=%s,
                   image=%s, description=%s WHERE id=%s""",
                (payload['name'], payload['state'], payload['category'], payload['budget'], payload['rating'],
                 payload.get('weather_text', 'Pleasant'), payload.get('image', ''), payload.get('description', ''),
                 destination_id)
            )


def delete_destination(destination_id):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM destinations WHERE id = %s", (destination_id,))


def recalc_destination_rating(destination_id):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT AVG(rating) AS avg_rating FROM reviews WHERE destination_id = %s", (destination_id,))
            avg = cur.fetchone()
            if avg and avg['avg_rating'] is not None:
                cur.execute("UPDATE destinations SET rating = %s WHERE id = %s", (round(float(avg['avg_rating']), 2), destination_id))


# ---------- Hotels & Restaurants ----------

def list_hotels(destination_id):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM hotels WHERE destination_id = %s ORDER BY rating DESC", (destination_id,))
            return [dict(r) for r in cur.fetchall()]


def list_restaurants(destination_id):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM restaurants WHERE destination_id = %s ORDER BY rating DESC", (destination_id,))
            return [dict(r) for r in cur.fetchall()]


def create_hotel(destination_id, name, category, price, rating):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO hotels (destination_id, name, category, price_per_night, rating, created_at) VALUES (%s, %s, %s, %s, %s, %s)",
                (destination_id, name, category, price, rating, now())
            )


def delete_hotel(hotel_id):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM hotels WHERE id = %s", (hotel_id,))


def create_restaurant(destination_id, name, cuisine, price_range, rating):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO restaurants (destination_id, name, cuisine, price_range, rating, created_at) VALUES (%s, %s, %s, %s, %s, %s)",
                (destination_id, name, cuisine, price_range, rating, now())
            )


def delete_restaurant(restaurant_id):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM restaurants WHERE id = %s", (restaurant_id,))


# ---------- Favorites ----------

def toggle_favorite(user_id, destination_id):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM favorites WHERE user_id = %s AND destination_id = %s", (user_id, destination_id))
            existing = cur.fetchone()
            if existing:
                cur.execute("DELETE FROM favorites WHERE id = %s", (existing['id'],))
                return False
            cur.execute(
                "INSERT INTO favorites (user_id, destination_id, created_at) VALUES (%s, %s, %s)",
                (user_id, destination_id, now())
            )
            return True


def list_favorites(user_id):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT d.* FROM favorites f JOIN destinations d ON d.id = f.destination_id
                   WHERE f.user_id = %s ORDER BY f.created_at DESC""",
                (user_id,)
            )
            rows = cur.fetchall()
    return [_destination_row_to_dict(r) for r in rows]


def is_favorite(user_id, destination_id):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM favorites WHERE user_id = %s AND destination_id = %s", (user_id, destination_id))
            return cur.fetchone() is not None


# ---------- Reviews ----------

def add_review(user_id, destination_id, rating, comment, photo_url=None):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO reviews (user_id, destination_id, rating, comment, photo_url, created_at) VALUES (%s, %s, %s, %s, %s, %s)",
                (user_id, destination_id, rating, comment, photo_url, now())
            )
    recalc_destination_rating(destination_id)


def list_reviews(destination_id, current_user_id=None):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT r.*, u.name AS user_name,
                          (SELECT COUNT(*) FROM review_likes rl WHERE rl.review_id = r.id) AS like_count
                   FROM reviews r JOIN users u ON u.id = r.user_id
                   WHERE r.destination_id = %s ORDER BY r.created_at DESC""",
                (destination_id,)
            )
            reviews = [dict(r) for r in cur.fetchall()]
            if current_user_id:
                cur.execute("SELECT review_id FROM review_likes WHERE user_id = %s", (current_user_id,))
                liked_ids = {row['review_id'] for row in cur.fetchall()}
                for r in reviews:
                    r['liked_by_me'] = r['id'] in liked_ids
    return reviews


def toggle_review_like(review_id, user_id):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM review_likes WHERE review_id = %s AND user_id = %s", (review_id, user_id))
            existing = cur.fetchone()
            if existing:
                cur.execute("DELETE FROM review_likes WHERE id = %s", (existing['id'],))
                return False
            cur.execute("INSERT INTO review_likes (review_id, user_id) VALUES (%s, %s)", (review_id, user_id))
            return True


# ---------- Trips ----------

def stash_itinerary(user_id, payload):
    """Persist a freshly generated plan and return its id. Only the most recent
    one per user is kept — older rows are disposable once superseded."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO itinerary_stash (user_id, data, created_at) VALUES (%s, %s, %s) RETURNING id",
                (user_id, json.dumps(payload), now())
            )
            stash_id = cur.fetchone()['id']
            cur.execute(
                "DELETE FROM itinerary_stash WHERE user_id = %s AND id <> %s", (user_id, stash_id)
            )
            return stash_id


def load_itinerary(stash_id, user_id):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT data FROM itinerary_stash WHERE id = %s AND user_id = %s", (stash_id, user_id)
            )
            row = cur.fetchone()
    return json.loads(row['data']) if row else None


def create_trip(user_id, itinerary_payload):
    form_data = itinerary_payload.get('form_data', {})
    ranked = itinerary_payload.get('ranked', [])
    top = ranked[0] if ranked else {}
    title = f"{top.get('name', 'Trip')} — {form_data.get('travel_type', 'Custom')}"

    return_date = None
    travel_date = form_data.get('travel_date')
    duration = form_data.get('duration')
    if travel_date and duration:
        try:
            return_date = (datetime.strptime(travel_date, '%Y-%m-%d') + timedelta(days=int(duration))).strftime('%Y-%m-%d')
        except ValueError:
            return_date = None

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO trips (user_id, title, destination_name, budget, duration_days, travel_date,
                   return_date, status, data, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
                (user_id, title, top.get('name'), form_data.get('budget'), duration,
                 travel_date, return_date, 'saved',
                 json.dumps(itinerary_payload), now())
            )
            return cur.fetchone()['id']


def list_trips(user_id):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM trips WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
            rows = cur.fetchall()
    trips = []
    for r in rows:
        trip = dict(r)
        trip['data'] = json.loads(trip['data'])
        trips.append(trip)
    return trips


def get_trip(trip_id, user_id=None):
    with get_db() as conn:
        with conn.cursor() as cur:
            if user_id is not None:
                cur.execute("SELECT * FROM trips WHERE id = %s AND user_id = %s", (trip_id, user_id))
            else:
                cur.execute("SELECT * FROM trips WHERE id = %s", (trip_id,))
            row = cur.fetchone()
    if not row:
        return None
    trip = dict(row)
    trip['data'] = json.loads(trip['data'])
    return trip


def delete_trip(trip_id, user_id):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM trips WHERE id = %s AND user_id = %s", (trip_id, user_id))


# ---------- Search history ----------

def log_search(user_id, query):
    if not query:
        return
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO search_history (user_id, query, created_at) VALUES (%s, %s, %s)",
                (user_id, query, now())
            )


def recent_searches(user_id, limit=5):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT query, created_at FROM search_history WHERE user_id = %s ORDER BY created_at DESC LIMIT %s",
                (user_id, limit)
            )
            return [dict(r) for r in cur.fetchall()]


# ---------- Admin stats ----------

def admin_stats():
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS c FROM users")
            users = cur.fetchone()['c']
            cur.execute("SELECT COUNT(*) AS c FROM trips")
            trips = cur.fetchone()['c']
            cur.execute("SELECT COUNT(*) AS c FROM destinations")
            destinations = cur.fetchone()['c']
            cur.execute("SELECT AVG(budget) AS avg_budget FROM trips WHERE budget IS NOT NULL")
            avg_budget_row = cur.fetchone()
            avg_budget = round(avg_budget_row['avg_budget']) if avg_budget_row['avg_budget'] else 0
            cur.execute(
                """SELECT destination_name, COUNT(*) AS c FROM trips WHERE destination_name IS NOT NULL
                   GROUP BY destination_name ORDER BY c DESC LIMIT 5"""
            )
            popular = cur.fetchall()
    return {
        'users': users, 'trips': trips, 'destinations': destinations, 'avg_budget': avg_budget,
        'popular': [dict(p) for p in popular],
    }
