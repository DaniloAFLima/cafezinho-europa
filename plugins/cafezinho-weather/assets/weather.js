(function () {
    'use strict';

    var ICONS = {
        sun:        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6l1.4 1.4M17 17l1.4 1.4M5.6 18.4l1.4-1.4M17 7l1.4-1.4"/></svg>',
        'sun-cloud':'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="10" r="3"/><path d="M9 6V4M9 14v2M5 10H3M15 10h-2M6.5 6.5L5 5M11.5 6.5L13 5M6.5 13.5L5 15"/><path d="M10 18a4 4 0 010-8 6 6 0 0111.6-1.8A4 4 0 0122 18z"/></svg>',
        cloud:      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><path d="M6 17a4 4 0 010-8 6 6 0 0111.6-1.8A4 4 0 0118 17z"/></svg>',
        fog:        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"><line x1="3" y1="8"  x2="21" y2="8"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="16" x2="21" y2="16"/></svg>',
        drizzle:    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><path d="M6 14a4 4 0 010-8 6 6 0 0111.6-1.8A4 4 0 0118 14z"/><path d="M9 17v2M13 17v2M17 17v2"/></svg>',
        rain:       '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><path d="M6 14a4 4 0 010-8 6 6 0 0111.6-1.8A4 4 0 0118 14z"/><path d="M8 17l-1 4M12 17l-1 4M16 17l-1 4"/></svg>',
        shower:     '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><path d="M6 15a4 4 0 010-8 6 6 0 0111.6-1.8A4 4 0 0118 15z"/><path d="M9 18l-1 3M13 18l-1 3M17 18l-1 3"/></svg>',
        snow:       '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><path d="M6 14a4 4 0 010-8 6 6 0 0111.6-1.8A4 4 0 0118 14z"/><circle cx="8" cy="19" r="0.8"/><circle cx="12" cy="20" r="0.8"/><circle cx="16" cy="19" r="0.8"/></svg>',
        thunder:    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><path d="M6 14a4 4 0 010-8 6 6 0 0111.6-1.8A4 4 0 0118 14z"/><path d="M11 15l-2 4h3l-1 4 4-6h-3l1-3z"/></svg>',
        thunderstorm:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><path d="M6 14a4 4 0 010-8 6 6 0 0111.6-1.8A4 4 0 0118 14z"/><path d="M11 15l-2 4h3l-1 4 4-6h-3l1-3z"/></svg>'
    };

    function esc(s) {
        return String(s).replace(/[&<>"]/g, function (c) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
        });
    }

    function renderPanel(panel, payload) {
        var daysHtml = payload.days.map(function (d) {
            var icon = ICONS[d.icon] || ICONS.cloud;
            return '<div class="cw__day">' +
                       '<div class="cw__day-label">' + esc(d.label) + '</div>' +
                       '<div class="cw__day-temps">' + d.max + '<span class="deg">°</span><span class="min">' + d.min + '°</span></div>' +
                       '<div class="cw__day-desc">' + icon + ' ' + esc(d.desc) + '</div>' +
                   '</div>';
        }).join('');
        panel.innerHTML =
            '<div class="cw__panel-head">' +
                '<div class="cw__panel-city"><em>' + esc(payload.country) + '</em>' + esc(payload.city) + '</div>' +
                '<div class="cw__panel-meta">' + esc(payload.updated) + '</div>' +
            '</div>' +
            '<div class="cw__days">' + daysHtml + '</div>' +
            '<div class="cw__panel-foot">' +
                '<span>Fonte · Open-Meteo</span>' +
            '</div>';
        var svgs = panel.querySelectorAll('svg');
        for (var i = 0; i < svgs.length; i++) {
            svgs[i].classList.add('cw__day-icon');
        }
    }

    function setActive(widget, slug) {
        var tabs = widget.querySelectorAll('.cw__tab');
        for (var i = 0; i < tabs.length; i++) {
            var on = tabs[i].dataset.slug === slug;
            tabs[i].classList.toggle('is-active', on);
            tabs[i].setAttribute('aria-selected', on ? 'true' : 'false');
        }
    }

    function clearActive(widget) {
        var tabs = widget.querySelectorAll('.cw__tab');
        for (var i = 0; i < tabs.length; i++) {
            tabs[i].classList.remove('is-active');
            tabs[i].setAttribute('aria-selected', 'false');
        }
    }

    function init(widget) {
        var panel = widget.querySelector('.cw__panel');
        if (!panel) return;
        var currentSlug = null;

        widget.addEventListener('click', function (e) {
            var btn = e.target.closest('.cw__tab');
            if (!btn || !widget.contains(btn)) return;
            var slug = btn.dataset.slug;
            var payloadRaw = btn.dataset.payload;

            if (slug === currentSlug && panel.dataset.open === 'true') {
                panel.dataset.open = 'false';
                clearActive(widget);
                currentSlug = null;
                return;
            }
            try {
                var payload = JSON.parse(payloadRaw);
                renderPanel(panel, payload);
                panel.dataset.open = 'true';
                setActive(widget, slug);
                currentSlug = slug;
            } catch (err) {
                panel.dataset.open = 'false';
            }
        });

        document.addEventListener('click', function (e) {
            if (!widget.contains(e.target) && panel.dataset.open === 'true') {
                panel.dataset.open = 'false';
                clearActive(widget);
                currentSlug = null;
            }
        });

        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && panel.dataset.open === 'true') {
                panel.dataset.open = 'false';
                clearActive(widget);
                currentSlug = null;
            }
        });
    }

    function boot() {
        var widgets = document.querySelectorAll('.cw');
        for (var i = 0; i < widgets.length; i++) {
            init(widgets[i]);
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', boot);
    } else {
        boot();
    }
})();
