# API Documentation

## GET /
Returns the homepage with popular destinations and hero section.

## POST /api/plan
Accepts JSON payload containing user preferences and returns an AI plan response.

Example request:

```json
{
  "budget": 25000,
  "duration": 5,
  "travel_type": "Family",
  "destination_preference": "Hill Station"
}
```

Example response:

```json
{
  "trip_summary": "AI-generated recommendation...",
  "confidence_score": 0.88,
  "why_selected": ["Budget alignment..."],
  "alternative_destinations": ["Goa", "Jaipur"],
  "safety_note": "Follow local advisories..."
}
```
