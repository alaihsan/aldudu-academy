// Language translations for Aldudu Academy
const translations = {
    id: {
        meta: { language: "Indonesian", code: "id", flag: "🇮🇩" },
        common: {
            home: "Beranda",
            dashboard: "Dasbor",
            courses: "Kelas",
            quizzes: "Kuis",
            assignments: "Tugas",
            grades: "Nilai",
            discussions: "Diskusi",
            settings: "Pengaturan",
            profile: "Profil",
            logout: "Keluar",
            login: "Masuk",
            register: "Daftar",
            save: "Simpan",
            cancel: "Batal",
            delete: "Hapus",
            edit: "Edit",
            add: "Tambah",
            back: "Kembali",
            next: "Lanjut",
            submit: "Kirim",
            loading: "Memuat...",
            search: "Cari",
            filter: "Filter",
            close: "Tutup",
            yes: "Ya",
            no: "Tidak",
            ok: "Oke",
            language: "Bahasa"
        },
        nav: {
            my_courses: "Kelas Saya",
            teaching: "Mengajar",
            gradebook: "Buku Nilai",
            students: "Murid",
            teachers: "Guru",
            admin_panel: "Panel Admin",
            reports: "Laporan",
            help: "Bantuan",
            report_issue: "Laporkan Masalah",
            tickets: "Tiket",
            issues: "Masalah"
        }
    },
    'en-US': {
        meta: { language: "English (US)", code: "en-US", flag: "🇺🇸" },
        common: {
            home: "Home",
            dashboard: "Dashboard",
            courses: "Courses",
            quizzes: "Quizzes",
            assignments: "Assignments",
            grades: "Grades",
            discussions: "Discussions",
            settings: "Settings",
            profile: "Profile",
            logout: "Sign Out",
            login: "Log In",
            register: "Sign Up",
            save: "Save",
            cancel: "Cancel",
            delete: "Delete",
            edit: "Edit",
            add: "Add",
            back: "Back",
            next: "Next",
            submit: "Submit",
            loading: "Loading...",
            search: "Search",
            filter: "Filter",
            close: "Close",
            yes: "Yes",
            no: "No",
            ok: "OK",
            language: "Language"
        },
        nav: {
            my_courses: "My Courses",
            teaching: "Teaching",
            gradebook: "Gradebook",
            students: "Students",
            teachers: "Teachers",
            admin_panel: "Admin Panel",
            reports: "Reports",
            help: "Help",
            report_issue: "Report Issue",
            tickets: "Tickets",
            issues: "Issues"
        }
    },
    'jv-MA': {
        meta: { language: "Jawa (Malang)", code: "jv-MA", flag: "🇮🇩" },
        common: {
            home: "Omah",
            dashboard: "Papan Kontrol",
            courses: "Kelas",
            quizzes: "Kuis",
            assignments: "Tugas",
            grades: "Nilai",
            discussions: "Diskusi",
            settings: "Setelan",
            profile: "Profil",
            logout: "Metu",
            login: "Mlebu",
            register: "Daftar",
            save: "Simpen",
            cancel: "Batal",
            delete: "Busak",
            edit: "Edit",
            add: "Tambah",
            back: "Mbalik",
            next: "Terus",
            submit: "Kirim",
            loading: "Ngemu...",
            search: "Goleki",
            filter: "Saring",
            close: "Tutup",
            yes: "Iyo",
            no: "Gak",
            ok: "Oke",
            language: "Basa"
        }
    },
    su: {
        meta: { language: "Sundanese", code: "su", flag: "🇮🇩" },
        common: {
            home: "Imah",
            dashboard: "Papan Kontrol",
            courses: "Kelas",
            quizzes: "Kuis",
            assignments: "Tugas",
            grades: "Nilai",
            discussions: "Diskusi",
            settings: "Setelan",
            profile: "Profil",
            logout: "Kaluar",
            login: "Asup",
            register: "Daptar",
            save: "Simpen",
            cancel: "Batal",
            delete: "Hapus",
            edit: "Edit",
            add: "Tambah",
            back: "Balik",
            next: "Tuluy",
            submit: "Kirim",
            loading: "Ngamuatan...",
            search: "Cari",
            filter: "Saring",
            close: "Tutup",
            yes: "Enya",
            no: "Henteu",
            ok: "Oke",
            language: "Basa"
        }
    }
};

// Current language
let currentLang = 'id';

// Get translation by key path (e.g., 'common.home', 'quiz.start_quiz')
function t(key, defaultValue = null) {
    const keys = key.split('.');
    let value = translations[currentLang];
    
    for (const k of keys) {
        if (value && typeof value === 'object' && k in value) {
            value = value[k];
        } else {
            value = defaultValue || key;
            break;
        }
    }
    
    return value;
}

// Set language and update UI
async function setLanguage(langCode) {
    const supportedLanguages = ['id', 'en-US', 'jv-MA', 'su'];
    if (!supportedLanguages.includes(langCode)) {
        console.error('Unsupported language:', langCode);
        return false;
    }

    try {
        const response = await fetch('/api/set-language', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ language: langCode })
        });

        const data = await response.json();

        if (data.success) {
            currentLang = langCode;
            localStorage.setItem('preferred_language', langCode);

            // Update RTL and Font
            const meta = translations[langCode]?.meta;
            if (meta?.rtl) {
                document.documentElement.setAttribute('dir', 'rtl');
            } else {
                document.documentElement.setAttribute('dir', 'ltr');
            }

            if (meta?.font) {
                document.body.style.fontFamily = meta.font;
            } else {
                document.body.style.fontFamily = '';
            }

            document.documentElement.setAttribute('lang', langCode);

            // Update all elements with data-i18n attribute
            document.querySelectorAll('[data-i18n]').forEach(el => {
                const key = el.getAttribute('data-i18n');
                const translated = t(key);

                if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
                    if (el.getAttribute('placeholder')) {
                        el.placeholder = translated;
                    } else {
                        el.value = translated;
                    }
                } else {
                    el.textContent = translated;
                }
            });

            // Update all elements with data-i18n-placeholder attribute
            document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
                const key = el.getAttribute('data-i18n-placeholder');
                el.placeholder = t(key);
            });

            // Dispatch event for other components to listen
            window.dispatchEvent(new CustomEvent('languageChanged', {
                detail: { language: langCode, translations: translations[langCode] }
            }));

            // Refresh sidebar and settings language selector
            initLanguageSelector();
            if (typeof renderSettingsLanguage === 'function') {
                renderSettingsLanguage();
            }

            return true;
        } else {
            console.error('Failed to set language:', data.message);
            return false;
        }
    } catch (error) {
        console.error('Error setting language:', error);
        return false;
    }
}

// Initialize language on page load
function initLanguage() {
    // Try to get from localStorage first
    const savedLang = localStorage.getItem('preferred_language');
    if (savedLang && translations[savedLang]) {
        currentLang = savedLang;
    }
    
    // Apply RTL and Font
    const meta = translations[currentLang]?.meta;
    if (meta?.rtl) {
        document.documentElement.setAttribute('dir', 'rtl');
    } else {
        document.documentElement.setAttribute('dir', 'ltr');
    }
    
    if (meta?.font) {
        document.body.style.fontFamily = meta.font;
    }
    
    document.documentElement.setAttribute('lang', currentLang);
    
    // Initial translation
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        const translated = t(key);
        
        if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
            if (el.getAttribute('placeholder')) {
                el.placeholder = translated;
            } else {
                el.value = translated;
            }
        } else {
            el.textContent = translated;
        }
    });
    
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        el.placeholder = t(key);
    });

    // Initialize the selector if container exists
    initLanguageSelector();
}

// Track portal menu element and click-outside handler for cleanup
let _langPortalMenu = null;
let _langClickOutsideHandler = null;

// Language selector component - Vanilla JS (Portal pattern)
function initLanguageSelector() {
    const container = document.getElementById('language-selector-container');
    if (!container) return;

    const languages = [
        { code: 'id', name: 'Indonesia', flag: '🇮🇩' },
        { code: 'en-US', name: 'English (US)', flag: '🇺🇸' },
        { code: 'jv-MA', name: 'Jawa (Malang)', flag: '🇮🇩' },
        { code: 'su', name: 'Sunda', flag: '🇮🇩' }
    ];

    const current = languages.find(l => l.code === currentLang) || languages[0];

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
                ${languages.map(lang => `
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
                const menuHeight = 300;
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
    translations,
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
