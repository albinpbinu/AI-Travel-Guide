TESTIMONIALS = [
    {
        'name': 'Ariana K.', 'trip': 'Munnar, Kerala', 'rating': 5,
        'avatar': 'https://i.pravatar.cc/80?img=32',
        'quote': 'The AI itinerary nailed our pace preference — relaxed mornings, adventure afternoons. Saved hours of planning.',
    },
    {
        'name': 'Rohit S.', 'trip': 'Goa Beach Trip', 'rating': 5,
        'avatar': 'https://i.pravatar.cc/80?img=12',
        'quote': 'Budget breakdown was spot on. We stayed within ₹2,000 of the estimate for the whole trip.',
    },
    {
        'name': 'Priya M.', 'trip': 'Jaipur Heritage Tour', 'rating': 4,
        'avatar': 'https://i.pravatar.cc/80?img=45',
        'quote': 'Loved the "why this destination" explanations — it actually felt personalized, not generic.',
    },
]

HOW_IT_WORKS = [
    {'icon': 'fa-pen-to-square', 'title': 'Enter travel details', 'text': 'Budget, dates, travel style, and interests.'},
    {'icon': 'fa-brain', 'title': 'AI analyzes preferences', 'text': 'Hybrid scoring across budget, interest, distance, weather, and history.'},
    {'icon': 'fa-route', 'title': 'Optimized itinerary generated', 'text': 'Day-wise plan with hotels, food, transport, and budget breakdown.'},
    {'icon': 'fa-file-arrow-down', 'title': 'Download or save', 'text': 'Export as PDF, save to your dashboard, or share with travel companions.'},
]


def get_admin_context(stats):
    popular = stats.get('popular') or []
    popular_labels = [p['destination_name'] for p in popular] or ['Munnar', 'Goa', 'Jaipur', 'Manali', 'Alleppey']
    popular_values = [p['c'] for p in popular] or [0, 0, 0, 0, 0]
    return {
        'stat_cards': [
            {'label': 'Registered Users', 'value': stats['users'], 'icon': 'fa-users', 'delta': ''},
            {'label': 'Trips Generated', 'value': stats['trips'], 'icon': 'fa-route', 'delta': ''},
            {'label': 'Avg Trip Budget (₹)', 'value': stats['avg_budget'], 'icon': 'fa-wallet', 'delta': ''},
            {'label': 'Active Destinations', 'value': stats['destinations'], 'icon': 'fa-map-location-dot', 'delta': ''},
        ],
        'user_growth': {
            'labels': ['Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug'],
            'values': [max(0, stats['users'] - 5), max(0, stats['users'] - 4), max(0, stats['users'] - 3),
                       max(0, stats['users'] - 2), max(0, stats['users'] - 1), stats['users']],
        },
        'popular_destinations': {
            'labels': popular_labels,
            'values': popular_values,
        },
    }
