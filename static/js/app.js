document.addEventListener('DOMContentLoaded', function () {
    initTheme();
    initAOS();
    initHeroAnimation();
    initCounters();
    initPasswordMeter();
    initChatWidget();
});

/* ---------- Theme ---------- */
function initTheme() {
    const root = document.documentElement;
    const toggle = document.getElementById('themeToggle');
    const stored = localStorage.getItem('tg-theme') || 'dark';
    root.setAttribute('data-theme', stored);
    setToggleIcon(stored);

    if (toggle) {
        toggle.addEventListener('click', function () {
            const next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
            root.setAttribute('data-theme', next);
            localStorage.setItem('tg-theme', next);
            setToggleIcon(next);
        });
    }
}

function setToggleIcon(theme) {
    const toggle = document.getElementById('themeToggle');
    if (!toggle) return;
    const icon = toggle.querySelector('i');
    if (icon) icon.className = theme === 'dark' ? 'fa-solid fa-moon' : 'fa-solid fa-sun';
}

/* ---------- AOS scroll reveal ---------- */
function initAOS() {
    if (window.AOS) {
        AOS.init({ duration: 700, once: true, offset: 60, easing: 'ease-out-cubic' });
    }
}

/* ---------- GSAP hero entrance ---------- */
function initHeroAnimation() {
    if (!window.gsap) return;
    const tl = gsap.timeline({ defaults: { ease: 'power3.out' } });
    if (document.querySelector('.hero-badge')) {
        tl.from('.hero-badge', { y: -16, opacity: 0, duration: 0.5 })
          .from('.hero-title', { y: 26, opacity: 0, duration: 0.7 }, '-=0.25')
          .from('.hero-sub', { y: 20, opacity: 0, duration: 0.6 }, '-=0.4')
          .from('.hero-cta > *', { y: 16, opacity: 0, duration: 0.5, stagger: 0.12 }, '-=0.35')
          .from('.hero-panel', { x: 30, opacity: 0, duration: 0.7 }, '-=0.6');
    }
}

/* ---------- Animated counters ---------- */
function initCounters() {
    const counters = document.querySelectorAll('[data-counter]');
    if (!counters.length) return;
    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (!entry.isIntersecting) return;
            animateCounter(entry.target);
            observer.unobserve(entry.target);
        });
    }, { threshold: 0.4 });
    counters.forEach((el) => observer.observe(el));
}

function animateCounter(el) {
    const target = parseFloat(el.dataset.counter);
    const duration = 1200;
    const start = performance.now();
    const decimals = el.dataset.decimals ? parseInt(el.dataset.decimals, 10) : 0;
    function tick(now) {
        const progress = Math.min((now - start) / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        const value = target * eased;
        el.textContent = decimals ? value.toFixed(decimals) : Math.round(value).toLocaleString();
        if (progress < 1) requestAnimationFrame(tick);
        else el.textContent = decimals ? target.toFixed(decimals) : target.toLocaleString();
    }
    requestAnimationFrame(tick);
}

/* ---------- Password strength meter ---------- */
function initPasswordMeter() {
    const input = document.querySelector('.pw-input');
    const meterBar = document.querySelector('.password-meter span');
    const label = document.querySelector('.password-meter-label');
    if (!input || !meterBar) return;

    input.addEventListener('input', function () {
        const value = input.value;
        let score = 0;
        if (value.length >= 8) score += 25;
        if (/[A-Z]/.test(value)) score += 25;
        if (/[0-9]/.test(value)) score += 25;
        if (/[^A-Za-z0-9]/.test(value)) score += 25;

        meterBar.style.width = score + '%';
        let color = '#f87171';
        let text = 'Weak';
        if (score >= 75) { color = '#34d399'; text = 'Strong'; }
        else if (score >= 50) { color = '#fbbf24'; text = 'Medium'; }
        meterBar.style.background = color;
        if (label) label.textContent = value ? text : '';
    });
}

/* ---------- Chat widget ---------- */
function initChatWidget() {
    const toggle = document.getElementById('chatToggle');
    const panel = document.getElementById('chatPanel');
    const form = document.getElementById('chatForm');
    const input = document.getElementById('chatInput');
    const body = document.getElementById('chatBody');
    if (!toggle || !panel) return;

    toggle.addEventListener('click', () => panel.classList.toggle('open'));

    if (form) {
        form.addEventListener('submit', function (e) {
            e.preventDefault();
            const text = input.value.trim();
            if (!text) return;
            appendChatMessage(body, text, 'user');
            input.value = '';
            setTimeout(() => {
                appendChatMessage(body, canned_response(text), 'bot');
                body.scrollTop = body.scrollHeight;
            }, 400);
            body.scrollTop = body.scrollHeight;
        });
    }
}

function appendChatMessage(body, text, role) {
    const el = document.createElement('div');
    el.className = 'chat-msg ' + role;
    el.textContent = text;
    body.appendChild(el);
}

function canned_response(text) {
    const lower = text.toLowerCase();
    if (lower.includes('weather')) return 'Check the weather widget on your dashboard for live forecasts and packing tips.';
    if (lower.includes('budget')) return 'Your itinerary page has a full budget breakdown with hotel, food, transport and ticket costs.';
    if (lower.includes('pack')) return 'Your packing list adapts to destination weather and trip duration — see the itinerary page.';
    if (lower.includes('emergency') || lower.includes('safety')) return 'Emergency numbers and safety notes are included with every generated itinerary.';
    return 'I can help with itinerary questions, packing, weather, and budget. This assistant is a UI preview pending live Gemini wiring.';
}
