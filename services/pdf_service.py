import io

import qrcode
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak

ACCENT = colors.HexColor('#5b8cff')
DARK = colors.HexColor('#101728')
MUTED = colors.HexColor('#5b6472')


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle('TGTitle', parent=styles['Title'], textColor=DARK, fontSize=24))
    styles.add(ParagraphStyle('TGHeading', parent=styles['Heading2'], textColor=ACCENT, spaceBefore=14))
    styles.add(ParagraphStyle('TGBody', parent=styles['BodyText'], textColor=DARK, leading=15))
    styles.add(ParagraphStyle('TGMuted', parent=styles['BodyText'], textColor=MUTED, fontSize=9))
    return styles


def _qr_image(top):
    if top and top.get('lat') and top.get('lng'):
        data = f"https://www.openstreetmap.org/?mlat={top['lat']}&mlon={top['lng']}#map=12/{top['lat']}/{top['lng']}"
    else:
        data = "https://www.openstreetmap.org"
    qr = qrcode.QRCode(box_size=6, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return Image(buf, width=3 * cm, height=3 * cm)


def build_itinerary_pdf(context):
    """context: {form_data, ranked, plan, itinerary, title}"""
    styles = _styles()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm)
    story = []

    ranked = context.get('ranked') or []
    plan = context.get('plan') or {}
    itinerary = context.get('itinerary') or []
    form_data = context.get('form_data') or {}
    top = ranked[0] if ranked else {}

    story.append(Paragraph('TravelGuide AI', styles['TGTitle']))
    story.append(Paragraph(context.get('title', 'Your AI-Generated Itinerary'), styles['TGHeading']))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(plan.get('trip_summary', 'Information unavailable.'), styles['TGBody']))
    story.append(Spacer(1, 0.4 * cm))

    start_date = itinerary[0]['date'] if itinerary and itinerary[0].get('date') else 'Information unavailable.'
    end_date = itinerary[-1]['date'] if itinerary and itinerary[-1].get('date') else 'Information unavailable.'
    summary_rows = [
        ['Destination', top.get('name', 'Information unavailable.')],
        ['Dates', f"{start_date} to {end_date}"],
        ['Budget', f"Rs {form_data.get('budget', top.get('budget', 'Information unavailable.'))}"],
        ['Duration', f"{form_data.get('duration', len(itinerary))} day(s)"],
        ['Travel type', form_data.get('travel_type', 'Information unavailable.')],
        ['Confidence score', f"{round(plan.get('confidence_score', 0) * 100)}%"],
    ]
    table = Table(summary_rows, colWidths=[5 * cm, 10 * cm])
    table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), DARK),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e6ef')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
    ]))
    story.append(table)
    story.append(Spacer(1, 0.3 * cm))
    story.append(_qr_image(top))
    story.append(Paragraph('Scan for map location', styles['TGMuted']))
    story.append(PageBreak())

    story.append(Paragraph('Day-wise Schedule', styles['TGHeading']))
    for day in itinerary:
        date_suffix = f" ({day['date']})" if day.get('date') else ''
        story.append(Paragraph(f"Day {day['day']}{date_suffix} — {day['destination']}", styles['Heading4']))
        for slot in ('morning', 'afternoon', 'evening', 'night'):
            story.append(Paragraph(f"<b>{slot.capitalize()}:</b> {day[slot]}", styles['TGBody']))
        story.append(Spacer(1, 0.25 * cm))

    story.append(Paragraph('Budget Breakdown', styles['TGHeading']))
    breakdown = plan.get('budget_breakdown', {})
    rows = [['Category', 'Amount (Rs)']] + [[k, str(v)] for k, v in breakdown.get('categories', {}).items()]
    rows.append(['Total', str(breakdown.get('total', 'Information unavailable.'))])
    budget_table = Table(rows, colWidths=[8 * cm, 5 * cm])
    budget_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), ACCENT),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#e2e6ef')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    story.append(budget_table)
    story.append(Spacer(1, 0.4 * cm))

    hotels = plan.get('hotel_recommendations', [])
    if hotels:
        story.append(Paragraph('Recommended Hotels', styles['TGHeading']))
        for h in hotels:
            story.append(Paragraph(f"<b>{h['name']}</b> — {h['category']}, Rs {h['price_per_night']}/night, {h['rating']}/5", styles['TGBody']))

    restaurants = plan.get('restaurant_recommendations', [])
    if restaurants:
        story.append(Paragraph('Recommended Restaurants', styles['TGHeading']))
        for r in restaurants:
            story.append(Paragraph(f"<b>{r['name']}</b> — {r['cuisine']}, {r['price_range']}, {r['rating']}/5", styles['TGBody']))

    story.append(Paragraph('Packing Checklist', styles['TGHeading']))
    for item in plan.get('packing_list', []):
        story.append(Paragraph(f"&#9744;  {item}", styles['TGBody']))

    story.append(Paragraph('Emergency Contacts', styles['TGHeading']))
    for label, number in plan.get('emergency_numbers', {}).items():
        story.append(Paragraph(f"<b>{label}:</b> {number}", styles['TGBody']))

    story.append(Paragraph('Why these locations were selected', styles['TGHeading']))
    for reason in plan.get('why_selected', []):
        story.append(Paragraph(f"- {reason}", styles['TGBody']))

    doc.build(story)
    buf.seek(0)
    return buf
