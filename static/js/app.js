document.addEventListener('DOMContentLoaded', function () {
    initTheme();
    initAOS();
    initHeroAnimation();
    initCounters();
    initPasswordMeter();
    initPasswordToggle();
    initPlanLoadingOverlay();
    initRefineSuggestions();
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

/* ---------- Password show/hide toggle ---------- */
function initPasswordToggle() {
    document.querySelectorAll('.password-toggle').forEach((btn) => {
        btn.addEventListener('click', function () {
            const field = btn.closest('.password-field');
            const input = field ? field.querySelector('input') : null;
            if (!input) return;
            const showing = input.type === 'text';
            input.type = showing ? 'password' : 'text';
            const icon = btn.querySelector('i');
            if (icon) icon.className = showing ? 'fa-solid fa-eye' : 'fa-solid fa-eye-slash';
        });
    });
}

/* ---------- Plan generation loading overlay ---------- */
function initPlanLoadingOverlay() {
    const overlay = document.getElementById('planLoadingOverlay');
    const messageEl = document.getElementById('planLoadingMessage');
    if (!overlay) return;
    const messages = [
        'Consulting our AI travel expert...',
        'Scouting hidden gems for your trip...',
        'Mapping out practical day-by-day plans...',
        'Matching hotels and restaurants to your budget...',
        'Double-checking the weather and best times to visit...',
        'Packing your itinerary with local favorites...',
    ];
    const refineMessages = [
        'Reading your change request...',
        'Reworking the affected days...',
        'Keeping the rest of your plan intact...',
        'Re-checking travel times and pacing...',
        'Updating budgets and recommendations...',
    ];
    const titleEl = overlay.querySelector('h4');

    document.querySelectorAll('[data-plan-form]').forEach((form) => {
        form.addEventListener('submit', function () {
            const custom = form.dataset.loadingTitle;
            const lines = custom ? refineMessages : messages;
            if (custom && titleEl) titleEl.textContent = custom;
            if (messageEl) messageEl.textContent = lines[0];
            overlay.classList.add('open');
            let i = 0;
            setInterval(function () {
                i = (i + 1) % lines.length;
                if (messageEl) messageEl.textContent = lines[i];
            }, 2200);
        });
    });
}

/* ---------- Refine modal suggestion chips ---------- */
function initRefineSuggestions() {
    const box = document.querySelector('#refineModal textarea[name="instruction"]');
    if (!box) return;
    document.querySelectorAll('.refine-suggestion').forEach((chip) => {
        chip.addEventListener('click', function () {
            box.value = chip.textContent.trim();
            box.focus();
        });
    });
}

/* ---------- Chat widget (Gemini-backed via /api/chat) ---------- */
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
            body.scrollTop = body.scrollHeight;

            const typing = appendChatMessage(body, 'Thinking...', 'bot');
            fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text }),
            })
                .then((res) => res.json())
                .then((data) => {
                    typing.textContent = data.reply || "Sorry, I couldn't come up with a reply.";
                    body.scrollTop = body.scrollHeight;
                })
                .catch(() => {
                    typing.textContent = 'Having trouble reaching the assistant right now — try again in a moment.';
                    body.scrollTop = body.scrollHeight;
                });
        });
    }
}

function appendChatMessage(body, text, role) {
    const el = document.createElement('div');
    el.className = 'chat-msg ' + role;
    el.textContent = text;
    body.appendChild(el);
    return el;
}
