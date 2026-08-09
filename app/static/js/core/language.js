// Language Manager for Aldudu Academy
//
// Translations live in app/static/translations/<code>.json (one file per
// language, 7 languages, all sharing the same key set) — this file only
// knows how to fetch/cache them and apply data-i18n bindings. Adding a
// language or a key means editing the JSON files, not this script.
const SUPPORTED_LANGUAGES = [
    { code: 'id', name: 'Indonesia', flag: '🇮🇩' },
    { code: 'en', name: 'English', flag: '🇺🇸' },
    { code: 'jv', name: 'Basa Jawa', flag: '🇮🇩' },
    { code: 'su', name: 'Basa Sunda', flag: '🇮🇩' },
    { code: 'ban', name: 'Basa Bali', flag: '🇮🇩' },
    { code: 'min', name: 'Baso Minang', flag: '🇮🇩' },
    { code: 'ar', name: 'العربية', flag: '🇸🇦' },
];
const RTL_LANGUAGES = ['ar'];
const SUPPORTED_LANGUAGE_CODES = SUPPORTED_LANGUAGES.map(l => l.code);

const _translationsCache = {};

// window.INITIAL_LANG is set inline by base.html (server-rendered, from
// current_user.preferred_language) before this script loads, so the very
// first paint already matches the user's saved preference instead of
// always starting from Indonesian and flashing once JS catches up.
let currentLang = (window.INITIAL_LANG && SUPPORTED_LANGUAGE_CODES.includes(window.INITIAL_LANG))
    ? window.INITIAL_LANG
    : 'id';

async function loadTranslations(langCode) {
    if (_translationsCache[langCode]) {
        return _translationsCache[langCode];
    }
    try {
        const response = await fetch(`/static/translations/${langCode}.json`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        _translationsCache[langCode] = data;
        return data;
    } catch (error) {
        console.error(`Failed to load translations for "${langCode}":`, error);
        return {};
    }
}

// Get translation by key path (e.g., 'common.home', 'quiz.start_quiz')
function t(key, defaultValue = null) {
    const dict = _translationsCache[currentLang] || {};
    const keys = key.split('.');
    let value = dict;

    for (const k of keys) {
        if (value && typeof value === 'object' && k in value) {
            value = value[k];
        } else {
            return defaultValue !== null ? defaultValue : key;
        }
    }

    return typeof value === 'string' ? value : (defaultValue !== null ? defaultValue : key);
}

function applyTranslations() {
    document.documentElement.setAttribute('lang', currentLang);
    document.documentElement.setAttribute('dir', RTL_LANGUAGES.includes(currentLang) ? 'rtl' : 'ltr');

    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        const translated = t(key);

        if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
            if (el.hasAttribute('placeholder')) {
                el.placeholder = translated;
            } else {
                el.value = translated;
            }
        } else {
            el.textContent = translated;
        }
    });

    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        el.placeholder = t(el.getAttribute('data-i18n-placeholder'));
    });
}

// Set language, persist it, and update UI
async function setLanguage(langCode) {
    if (!SUPPORTED_LANGUAGE_CODES.includes(langCode)) {
        console.error('Unsupported language:', langCode);
        return false;
    }

    await loadTranslations(langCode);

    try {
        const response = await fetch('/api/set-language', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ language: langCode })
        });
        const data = await response.json();

        if (!data.success) {
            console.error('Failed to set language:', data.message);
            return false;
        }
    } catch (error) {
        console.error('Error setting language:', error);
        return false;
    }

    currentLang = langCode;
    localStorage.setItem('preferred_language', langCode);
    applyTranslations();

    window.dispatchEvent(new CustomEvent('languageChanged', {
        detail: { language: langCode, translations: _translationsCache[langCode] }
    }));

    // Refresh sidebar and settings language selector
    initLanguageSelector();
    if (typeof renderSettingsLanguage === 'function') {
        renderSettingsLanguage();
    }
    if (window.LanguageManager) {
        window.LanguageManager.currentLang = currentLang;
    }

    return true;
}

// Initialize language on page load
async function initLanguage() {
    // localStorage (an explicit in-browser choice) wins over the
    // server-rendered INITIAL_LANG, but only if it's still a valid code.
    const savedLang = localStorage.getItem('preferred_language');
    if (savedLang && SUPPORTED_LANGUAGE_CODES.includes(savedLang)) {
        currentLang = savedLang;
    }

    await loadTranslations(currentLang);
    applyTranslations();
    initLanguageSelector();

    if (window.LanguageManager) {
        window.LanguageManager.currentLang = currentLang;
    }

    // Fires even on plain init (not just user-driven changes) so listeners
    // set up by a page's own script (e.g. settings.js's language dropdown)
    // that run before this async fetch resolves still end up in sync.
    window.dispatchEvent(new CustomEvent('languageChanged', {
        detail: { language: currentLang, translations: _translationsCache[currentLang] }
    }));
}

// Track portal menu element and click-outside handler for cleanup
let _langPortalMenu = null;
let _langClickOutsideHandler = null;

// Language selector component - Vanilla JS (Portal pattern)
function initLanguageSelector() {
    const container = document.getElementById('language-selector-container');
    if (!container) return;

    const current = SUPPORTED_LANGUAGES.find(l => l.code === currentLang) || SUPPORTED_LANGUAGES[0];

    // ── 1. Render toggle button inside sidebar container ──
    container.innerHTML = `
        <button id="lang-dropdown-toggle" class="w-full flex items-center justify-between px-4 py-3 bg-gray-50 hover:bg-gray-100 rounded-2xl transition-all border border-gray-100 group">
            <div class="flex items-center space-x-3">
                <span class="text-xl group-hover:scale-110 transition-transform">${current.flag}</span>
                <span class="text-sm font-bold text-gray-700">${current.name}</span>
            </div>
            <svg id="lang-dropdown-arrow" class="w-4 h-4 text-gray-400 group-hover:text-primary-500 transition-transform duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M19 9l-7 7-7-7"/>
            </svg>
        </button>
    `;

    // ── 2. Create portal menu on document.body (escapes sidebar stacking context) ──
    if (_langPortalMenu) {
        _langPortalMenu.remove();
    }
    _langPortalMenu = document.createElement('div');
    _langPortalMenu.id = 'lang-portal-menu';
    _langPortalMenu.style.cssText = 'display:none; position:fixed; z-index:99999;';
    _langPortalMenu.innerHTML = `
        <div class="bg-white rounded-2xl shadow-2xl border border-gray-100 overflow-hidden py-2" style="min-width:200px;">
            <div class="max-h-64 overflow-y-auto">
                ${SUPPORTED_LANGUAGES.map(lang => `
                    <button data-lang-code="${lang.code}"
                            class="w-full px-4 py-3 text-left hover:bg-blue-50 flex items-center space-x-3 transition-colors ${currentLang === lang.code ? 'bg-blue-50 text-blue-600' : 'text-gray-600'}">
                        <span class="text-xl">${lang.flag}</span>
                        <span class="text-sm font-bold">${lang.name}</span>
                        ${currentLang === lang.code ? '<div class="ml-auto w-2 h-2 rounded-full bg-blue-500"></div>' : ''}
                    </button>
                `).join('')}
            </div>
        </div>
    `;
    document.body.appendChild(_langPortalMenu);

    // ── 3. Bind language selection on portal buttons ──
    _langPortalMenu.querySelectorAll('button[data-lang-code]').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const code = btn.getAttribute('data-lang-code');
            _langPortalMenu.style.display = 'none';
            const arrow = document.getElementById('lang-dropdown-arrow');
            if (arrow) arrow.classList.remove('rotate-180');
            setLanguage(code);
        });
    });

    // ── 4. Bind toggle button ──
    const toggle = document.getElementById('lang-dropdown-toggle');
    const arrow = document.getElementById('lang-dropdown-arrow');

    if (toggle) {
        toggle.onclick = (e) => {
            e.stopPropagation();
            const isOpen = _langPortalMenu.style.display !== 'none';

            if (isOpen) {
                _langPortalMenu.style.display = 'none';
                arrow?.classList.remove('rotate-180');
            } else {
                // Calculate position from toggle button
                const rect = toggle.getBoundingClientRect();
                const spaceBelow = window.innerHeight - rect.bottom - 12;
                const spaceAbove = rect.top - 12;

                _langPortalMenu.style.width = Math.max(rect.width, 220) + 'px';
                _langPortalMenu.style.left = rect.left + 'px';

                if (spaceBelow >= 150 || spaceBelow >= spaceAbove) {
                    // Drop DOWN
                    _langPortalMenu.style.top = (rect.bottom + 8) + 'px';
                    _langPortalMenu.style.bottom = 'auto';
                } else {
                    // Drop UP
                    _langPortalMenu.style.bottom = (window.innerHeight - rect.top + 8) + 'px';
                    _langPortalMenu.style.top = 'auto';
                }

                _langPortalMenu.style.display = 'block';
                arrow?.classList.add('rotate-180');
            }
        };
    }

    // ── 5. Click-outside to close ──
    if (_langClickOutsideHandler) {
        window.removeEventListener('click', _langClickOutsideHandler);
    }
    _langClickOutsideHandler = (e) => {
        if (_langPortalMenu &&
            !container.contains(e.target) &&
            !_langPortalMenu.contains(e.target)) {
            _langPortalMenu.style.display = 'none';
            const arr = document.getElementById('lang-dropdown-arrow');
            if (arr) arr.classList.remove('rotate-180');
        }
    };
    window.addEventListener('click', _langClickOutsideHandler);
}

// Export for use in other modules
window.setLanguage = setLanguage;
window.LanguageManager = {
    SUPPORTED_LANGUAGES,
    currentLang,
    t,
    setLanguage,
    initLanguage,
    initLanguageSelector
};

// Auto-initialize
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initLanguage);
} else {
    initLanguage();
}

// Handle HTMX swaps
document.body.addEventListener('htmx:afterSwap', () => {
    initLanguage(); // Re-translate and re-bind events
});
