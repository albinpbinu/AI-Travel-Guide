from datetime import datetime, date

from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, send_file, abort, session
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from flask_wtf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash

from services.recommendation import rank_destinations, build_itinerary
from services.gemini_service import build_ai_plan
from services.weather_service import get_weather_snapshot
from services.pdf_service import build_itinerary_pdf
from services.nearby_service import get_nearby_essentials
from services.content import TESTIMONIALS, HOW_IT_WORKS, get_admin_context
from utils.uploads import save_upload
from database.db import (
    init_db, create_user, get_user_by_email, get_user_by_id,
    update_user_profile, update_user_password, list_users, delete_user,
    create_password_reset, get_password_reset, consume_password_reset,
    list_destinations, get_destination, create_destination, update_destination, delete_destination,
    toggle_favorite, list_favorites, is_favorite,
    list_hotels, list_restaurants, create_hotel, delete_hotel, create_restaurant, delete_restaurant,
    add_review, list_reviews, toggle_review_like,
    create_trip, list_trips, get_trip, delete_trip,
    log_search, recent_searches, admin_stats,
)
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
init_db(app)
csrf = CSRFProtect(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class User(UserMixin):
    def __init__(self, row):
        self.id = str(row['id'])
        self.name = row['name']
        self.email = row['email']
        self.profile_picture = row['profile_picture'] if 'profile_picture' in row.keys() else None


@login_manager.user_loader
def load_user(user_id):
    row = get_user_by_id(app, user_id)
    return User(row) if row else None


def _search_history_terms():
    if not current_user.is_authenticated:
        return []
    return [s['query'] for s in recent_searches(int(current_user.id))]


@app.route('/')
def index():
    return render_template(
        'index.html',
        destinations=list_destinations(),
        testimonials=TESTIMONIALS,
        how_it_works=HOW_IT_WORKS,
    )


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        if not name or not email:
            return render_template('register.html', error='Name and email are required.', form=request.form)
        if get_user_by_email(app, email) is not None:
            return render_template('register.html', error='An account with this email already exists.', form=request.form)
        if len(password) < 8:
            return render_template('register.html', error='Password must be at least 8 characters.', form=request.form)
        if password != confirm:
            return render_template('register.html', error='Passwords do not match.', form=request.form)

        phone = request.form.get('phone', '').strip()
        country = request.form.get('country', '').strip()
        user_id = create_user(app, name, email, phone, country, generate_password_hash(password))

        picture_url = save_upload(request.files.get('profile_picture'))
        if picture_url:
            update_user_profile(user_id, name, phone, country, profile_picture=picture_url)

        flash('Account created successfully. Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        row = get_user_by_email(app, email)
        if row and check_password_hash(row['password_hash'], password):
            user = User(row)
            login_user(user, remember=bool(request.form.get('remember')))
            flash(f'Welcome back, {user.name.split(" ")[0]}!', 'success')
            return redirect(url_for('dashboard'))
        return render_template('login.html', error='Invalid email or password. Demo login: demo@travelguide.ai / demo1234.')
    return render_template('login.html')


@app.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        row = get_user_by_email(app, email)
        if not row:
            return render_template('forgot_password.html', error='No account found with that email.')
        token = create_password_reset(row['id'])
        reset_link = url_for('reset_password', token=token, _external=True)
        return render_template('forgot_password.html', reset_link=reset_link)
    return render_template('forgot_password.html')


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    reset_row = get_password_reset(token)
    if not reset_row:
        flash('This reset link is invalid or has expired.', 'error')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        if len(password) < 8:
            return render_template('reset_password.html', error='Password must be at least 8 characters.')
        if password != confirm:
            return render_template('reset_password.html', error='Passwords do not match.')
        update_user_password(reset_row['user_id'], generate_password_hash(password))
        consume_password_reset(token)
        flash('Password updated. Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('reset_password.html')


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        country = request.form.get('country', '').strip()
        picture_url = save_upload(request.files.get('profile_picture'))
        update_user_profile(int(current_user.id), name, phone, country, profile_picture=picture_url)
        flash('Profile updated.', 'success')
        return redirect(url_for('profile'))
    user = get_user_by_id(app, current_user.id)
    return render_template('profile.html', user=user)


@app.route('/profile/password', methods=['POST'])
@login_required
def change_password():
    user_row = get_user_by_id(app, current_user.id)
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm = request.form.get('confirm_password', '')

    if not check_password_hash(user_row['password_hash'], current_password):
        flash('Current password is incorrect.', 'error')
    elif len(new_password) < 8:
        flash('New password must be at least 8 characters.', 'error')
    elif new_password != confirm:
        flash('New passwords do not match.', 'error')
    else:
        update_user_password(int(current_user.id), generate_password_hash(new_password))
        flash('Password updated successfully.', 'success')
    return redirect(url_for('profile'))


@app.route('/dashboard')
@login_required
def dashboard():
    weather = get_weather_snapshot('Munnar')
    recommendation = rank_destinations(
        profile={'budget': 25000, 'interests': ['nature', 'food']}, duration=5,
        search_history=_search_history_terms(),
    )
    trips = list_trips(int(current_user.id))
    favorites = list_favorites(int(current_user.id))

    today = date.today()
    upcoming_trips = []
    for t in trips:
        if t['travel_date']:
            try:
                travel_date = datetime.strptime(t['travel_date'], '%Y-%m-%d').date()
                if travel_date >= today:
                    upcoming_trips.append({**t, 'days_left': (travel_date - today).days})
            except ValueError:
                pass

    budgets = [t['budget'] for t in trips if t['budget']]
    dashboard_ctx = {
        'saved_trips': trips[:5],
        'upcoming_trips': upcoming_trips[:5],
        'favorites': favorites,
        'stats': {
            'trips_planned': len(trips),
            'destinations_explored': len({t['destination_name'] for t in trips if t['destination_name']}),
            'avg_budget': round(sum(budgets) / len(budgets)) if budgets else 0,
        },
    }
    return render_template('dashboard.html', weather=weather, recommendation=recommendation, ctx=dashboard_ctx)


@app.route('/plan-trip')
@login_required
def plan_form():
    return render_template('plan.html')


@app.route('/plan', methods=['POST'])
@login_required
def plan_trip():
    form_data = request.form.to_dict(flat=True)
    history_terms = _search_history_terms()
    ranked = rank_destinations(profile=form_data, duration=int(form_data.get('duration', 5) or 5), search_history=history_terms)
    plan = build_ai_plan(form_data, ranked)
    itinerary = build_itinerary(ranked, form_data)

    session['last_itinerary'] = {
        'form_data': form_data, 'ranked': ranked, 'plan': plan, 'itinerary': itinerary,
    }
    if form_data.get('destination_preference'):
        log_search(int(current_user.id), form_data['destination_preference'])

    return render_template('itinerary.html', itinerary=itinerary, plan=plan, ranked=ranked, form_data=form_data)


@app.route('/api/plan', methods=['POST'])
@csrf.exempt
def api_plan():
    payload = request.get_json(silent=True) or {}
    ranked = rank_destinations(payload, duration=int(payload.get('duration', 5) or 5))
    response = build_ai_plan(payload, ranked)
    return jsonify(response)


@app.route('/trips/save', methods=['POST'])
@login_required
def save_trip():
    data = session.get('last_itinerary')
    if not data:
        flash('Generate an itinerary first, then save it.', 'error')
        return redirect(url_for('plan_form'))
    create_trip(int(current_user.id), data)
    flash('Trip saved to your dashboard.', 'success')
    return redirect(url_for('dashboard'))


@app.route('/trips/<int:trip_id>/delete', methods=['POST'])
@login_required
def delete_trip_route(trip_id):
    delete_trip(trip_id, int(current_user.id))
    flash('Trip removed.', 'success')
    return redirect(url_for('dashboard'))


@app.route('/trips/<int:trip_id>/pdf')
@login_required
def trip_pdf(trip_id):
    trip = get_trip(trip_id, int(current_user.id))
    if not trip:
        abort(404)
    context = {**trip['data'], 'title': trip['title']}
    buf = build_itinerary_pdf(context)
    return send_file(buf, mimetype='application/pdf', as_attachment=True, download_name=f"itinerary-{trip_id}.pdf")


@app.route('/itinerary/pdf')
@login_required
def itinerary_pdf():
    data = session.get('last_itinerary')
    if not data:
        flash('Generate an itinerary first.', 'error')
        return redirect(url_for('plan_form'))
    top = data['ranked'][0]['name'] if data.get('ranked') else 'Trip'
    buf = build_itinerary_pdf({**data, 'title': f'Itinerary — {top}'})
    return send_file(buf, mimetype='application/pdf', as_attachment=True, download_name='itinerary.pdf')


@app.route('/destination/<int:destination_id>')
def destination_detail(destination_id):
    destination = get_destination(destination_id)
    if not destination:
        abort(404)
    user_id = int(current_user.id) if current_user.is_authenticated else None
    reviews = list_reviews(destination_id, current_user_id=user_id)
    favorited = is_favorite(user_id, destination_id) if user_id else False
    nearby_pois = get_nearby_essentials(destination.get('lat'), destination.get('lng'))
    return render_template(
        'destination.html', d=destination, reviews=reviews, favorited=favorited,
        hotels=list_hotels(destination_id), restaurants=list_restaurants(destination_id),
        nearby_pois=nearby_pois,
    )


@app.route('/destination/<int:destination_id>/favorite', methods=['POST'])
@login_required
def favorite_destination(destination_id):
    added = toggle_favorite(int(current_user.id), destination_id)
    flash('Added to favorites.' if added else 'Removed from favorites.', 'success')
    return redirect(request.referrer or url_for('destination_detail', destination_id=destination_id))


@app.route('/destination/<int:destination_id>/review', methods=['POST'])
@login_required
def review_destination(destination_id):
    try:
        rating = max(1, min(5, int(request.form.get('rating', 5))))
    except ValueError:
        rating = 5
    comment = request.form.get('comment', '').strip()
    photo_url = save_upload(request.files.get('photo'))
    add_review(int(current_user.id), destination_id, rating, comment, photo_url=photo_url)
    flash('Thanks for your review!', 'success')
    return redirect(url_for('destination_detail', destination_id=destination_id))


@app.route('/reviews/<int:review_id>/like', methods=['POST'])
@login_required
def like_review(review_id):
    toggle_review_like(review_id, int(current_user.id))
    return redirect(request.referrer or url_for('index'))


@app.route('/search')
def search():
    filters = {
        'q': request.args.get('q', '').strip(),
        'state': request.args.get('state', '').strip(),
        'category': request.args.get('category', '').strip(),
        'max_budget': request.args.get('max_budget', type=int),
        'min_rating': request.args.get('min_rating', type=float),
    }
    if current_user.is_authenticated and filters['q']:
        log_search(int(current_user.id), filters['q'])
    results = list_destinations({k: v for k, v in filters.items() if v})
    return render_template('search.html', results=results, filters=filters)


@app.route('/admin')
def admin_dashboard():
    return render_template('admin.html', ctx=get_admin_context(admin_stats()), destinations=list_destinations())


@app.route('/admin/users')
def admin_users():
    return render_template('admin_users.html', users=list_users())


@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
def admin_delete_user(user_id):
    delete_user(user_id)
    flash('User deleted.', 'success')
    return redirect(url_for('admin_users'))


@app.route('/admin/destinations/new', methods=['GET', 'POST'])
def admin_new_destination():
    if request.method == 'POST':
        payload = _destination_form_payload(request.form)
        create_destination(payload)
        flash('Destination added.', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_destination_form.html', destination=None)


@app.route('/admin/destinations/<int:destination_id>/edit', methods=['GET', 'POST'])
def admin_edit_destination(destination_id):
    destination = get_destination(destination_id)
    if not destination:
        abort(404)
    if request.method == 'POST':
        payload = _destination_form_payload(request.form)
        update_destination(destination_id, payload)
        flash('Destination updated.', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template(
        'admin_destination_form.html', destination=destination,
        hotels=list_hotels(destination_id), restaurants=list_restaurants(destination_id),
    )


@app.route('/admin/destinations/<int:destination_id>/delete', methods=['POST'])
def admin_delete_destination(destination_id):
    delete_destination(destination_id)
    flash('Destination deleted.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/destinations/<int:destination_id>/hotels', methods=['POST'])
def admin_add_hotel(destination_id):
    create_hotel(destination_id, request.form.get('name', '').strip(), request.form.get('category', 'Budget'),
                 int(request.form.get('price') or 0), 4.5)
    return redirect(url_for('admin_edit_destination', destination_id=destination_id))


@app.route('/admin/hotels/<int:hotel_id>/delete', methods=['POST'])
def admin_delete_hotel(hotel_id):
    delete_hotel(hotel_id)
    return redirect(request.referrer or url_for('admin_dashboard'))


@app.route('/admin/destinations/<int:destination_id>/restaurants', methods=['POST'])
def admin_add_restaurant(destination_id):
    create_restaurant(destination_id, request.form.get('name', '').strip(), request.form.get('cuisine', '').strip(),
                       request.form.get('price_range', 'Mid'), 4.5)
    return redirect(url_for('admin_edit_destination', destination_id=destination_id))


@app.route('/admin/restaurants/<int:restaurant_id>/delete', methods=['POST'])
def admin_delete_restaurant(restaurant_id):
    delete_restaurant(restaurant_id)
    return redirect(request.referrer or url_for('admin_dashboard'))


def _destination_form_payload(form):
    return {
        'name': form.get('name', '').strip(),
        'state': form.get('state', '').strip(),
        'category': form.get('category', '').strip(),
        'budget': int(form.get('budget') or 0),
        'rating': float(form.get('rating') or 4.5),
        'weather_text': form.get('weather_text', 'Pleasant'),
        'image': form.get('image', '').strip(),
        'description': form.get('description', '').strip(),
        'lat': float(form['lat']) if form.get('lat') else None,
        'lng': float(form['lng']) if form.get('lng') else None,
    }


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
