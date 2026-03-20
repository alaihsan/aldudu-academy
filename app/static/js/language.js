/**
 * Aldudu Academy — Language Manager
 * Supports: Indonesia, English, Arabic (RTL), Javanese, Sundanese, Balinese, Minangkabau
 */

const LANG_SUPPORTED = ['id', 'en', 'ar', 'jv', 'su', 'ban', 'min'];

const LANG_META = {
    id:  { name: 'Indonesia',   flag: '🇮🇩', dir: 'ltr', wait: 'Mohon Tunggu...',       sub: 'Mengganti bahasa aplikasi...' },
    en:  { name: 'English',     flag: '🇬🇧', dir: 'ltr', wait: 'Please Wait...',         sub: 'Changing application language...' },
    ar:  { name: 'العربية',     flag: '🇸🇦', dir: 'rtl', wait: 'يرجى الانتظار...',       sub: 'تغيير لغة التطبيق...' },
    jv:  { name: 'Jawa',        flag: '🇮🇩', dir: 'ltr', wait: 'Mangga Antawis...',       sub: 'Ganti basa aplikasi...' },
    su:  { name: 'Sunda',       flag: '🇮🇩', dir: 'ltr', wait: 'Mangga Antosan...',       sub: 'Ngarobih basa aplikasi...' },
    ban: { name: 'Bali',        flag: '🇮🇩', dir: 'ltr', wait: 'Sueca Antiang...',        sub: 'Genti basa aplikasi...' },
    min: { name: 'Padang',      flag: '🇮🇩', dir: 'ltr', wait: 'Tunggu Sabantuak...',     sub: 'Mangganti bahaso aplikasi...' },
};

const translations = {
    id: {
        common: {
            dashboard: 'Dasbor', courses: 'Kelas', quizzes: 'Kuis', assignments: 'Tugas',
            grades: 'Nilai', discussions: 'Diskusi', settings: 'Pengaturan', profile: 'Profil',
            logout: 'Keluar', save: 'Simpan', cancel: 'Batal', delete: 'Hapus', edit: 'Edit',
            add: 'Tambah', back: 'Kembali', next: 'Lanjut', submit: 'Kirim', close: 'Tutup',
            yes: 'Ya', no: 'Tidak', ok: 'Oke', search: 'Cari', filter: 'Filter',
            language: 'Bahasa', loading: 'Memuat...',
        },
        filter: {
            all_items: 'Semua Item', recent: 'Terbaru', assignments: 'Tugas', quizzes: 'Kuis', files: 'File',
            due_soon: 'Tenggat Waktu: Terdekat', due_latest: 'Tenggat Waktu: Terjauh', recently_added: 'Ditambahkan: Terbaru',
        },
        nav: {
            home: 'Rumah', classroom: 'Ruang Kelas', dashboard: 'Dashboard', admin_panel: 'Panel Admin', user_management: 'Manajemen User',
            course_nav: 'Navigasi Kelas', materials: 'Materi & Tugas', kbm_notes: 'Catatan KBM',
            gradebook: 'Buku Nilai', my_grades: 'Nilai Saya', help: 'Bantuan & Masalah',
            issues: 'Manajemen Masalah', settings: 'Pengaturan',
        },
        profile: {
            settings: 'Pengaturan', history: 'Riwayat Akses', privacy: 'Privacy & Policy',
            sponsor: 'Sponsor', logout: 'Keluar', all_in_settings: 'Pengaturan untuk semua menu', my_grades: 'Nilai Saya',
        },
        logout_modal: {
            title: 'Keluar Sesi?', body: 'Anda perlu login kembali untuk mengakses data Anda.',
            confirm: 'Ya, Keluar Sekarang', cancel: 'Tetap Di Sini',
        },
    },
    en: {
        common: {
            dashboard: 'Dashboard', courses: 'Courses', quizzes: 'Quizzes', assignments: 'Assignments',
            grades: 'Grades', discussions: 'Discussions', settings: 'Settings', profile: 'Profile',
            logout: 'Logout', save: 'Save', cancel: 'Cancel', delete: 'Delete', edit: 'Edit',
            add: 'Add', back: 'Back', next: 'Next', submit: 'Submit', close: 'Close',
            yes: 'Yes', no: 'No', ok: 'OK', search: 'Search', filter: 'Filter',
            language: 'Language', loading: 'Loading...',
        },
        filter: {
            all_items: 'All Items', recent: 'Recent', assignments: 'Assignments', quizzes: 'Quizzes', files: 'Files',
            due_soon: 'Due Date: Soonest', due_latest: 'Due Date: Latest', recently_added: 'Recently Added',
        },
        nav: {
            home: 'Home', classroom: 'Classroom', dashboard: 'Dashboard', admin_panel: 'Admin Panel', user_management: 'User Management',
            course_nav: 'Course Navigation', materials: 'Materials & Tasks', kbm_notes: 'Teaching Notes',
            gradebook: 'Gradebook', my_grades: 'My Grades', help: 'Help & Issues',
            issues: 'Issue Management', settings: 'Settings',
        },
        profile: {
            settings: 'Settings', history: 'Access History', privacy: 'Privacy & Policy',
            sponsor: 'Sponsor', logout: 'Logout', all_in_settings: 'Settings for all menus', my_grades: 'My Grades',
        },
        logout_modal: {
            title: 'Sign Out?', body: 'You need to log in again to access your data.',
            confirm: 'Yes, Sign Out', cancel: 'Stay Here',
        },
    },
    ar: {
        common: {
            dashboard: 'لوحة التحكم', courses: 'الدورات', quizzes: 'الاختبارات', assignments: 'الواجبات',
            grades: 'الدرجات', discussions: 'المناقشات', settings: 'الإعدادات', profile: 'الملف الشخصي',
            logout: 'تسجيل خروج', save: 'حفظ', cancel: 'إلغاء', delete: 'حذف', edit: 'تعديل',
            add: 'إضافة', back: 'رجوع', next: 'التالي', submit: 'إرسال', close: 'إغلاق',
            yes: 'نعم', no: 'لا', ok: 'موافق', search: 'بحث', filter: 'تصفية',
            language: 'اللغة', loading: 'جاري التحميل...',
        },
        filter: {
            all_items: 'جميع العناصر', recent: 'الأخيرة', assignments: 'الواجبات', quizzes: 'الاختبارات', files: 'الملفات',
            due_soon: 'موعد الاستحقاق: الأقرب', due_latest: 'موعد الاستحقاق: الأبعد', recently_added: 'تم الإضافة مؤخراً',
        },
        nav: {
            home: 'الرئيسية', classroom: 'الفصل الدراسي', dashboard: 'لوحة التحكم', admin_panel: 'لوحة الإدارة', user_management: 'إدارة المستخدمين',
            course_nav: 'تنقل الدورة', materials: 'المواد والمهام', kbm_notes: 'ملاحظات التدريس',
            gradebook: 'سجل الدرجات', my_grades: 'درجاتي', help: 'المساعدة والمشاكل',
            issues: 'إدارة المشاكل', settings: 'الإعدادات',
        },
        profile: {
            settings: 'الإعدادات', history: 'سجل الوصول', privacy: 'الخصوصية والسياسة',
            sponsor: 'الراعي', logout: 'تسجيل خروج',
        },
        logout_modal: {
            title: 'تسجيل الخروج؟', body: 'ستحتاج إلى تسجيل الدخول مرة أخرى للوصول إلى بياناتك.',
            confirm: 'نعم، تسجيل الخروج', cancel: 'ابقَ هنا',
        },
    },
    jv: {
        common: {
            dashboard: 'Papan Kontrol', courses: 'Kelas', quizzes: 'Kuis', assignments: 'Tugas',
            grades: 'Nilai', discussions: 'Diskusi', settings: 'Setelan', profile: 'Profil',
            logout: 'Metu', save: 'Simpen', cancel: 'Batal', delete: 'Busak', edit: 'Edit',
            add: 'Tambah', back: 'Mbalik', next: 'Terus', submit: 'Kirim', close: 'Tutup',
            yes: 'Iya', no: 'Ora', ok: 'Oke', search: 'Goleki', filter: 'Saring',
            language: 'Basa', loading: 'Ngemu...',
        },
        filter: {
            all_items: 'Kabeh Bab', recent: 'Anyar', assignments: 'Tugas', quizzes: 'Kuis', files: 'File',
            due_soon: 'Wektu Rampung: Ing Cetha', due_latest: 'Wektu Rampung: Ing Sawyane', recently_added: 'Ditambah Anyaran',
        },
        nav: {
            home: 'Omah', classroom: 'Kalas', dashboard: 'Dashboard', admin_panel: 'Panel Admin', user_management: 'Manajemen User',
            course_nav: 'Navigasi Kelas', materials: 'Materi & Tugas', kbm_notes: 'Cathetan KBM',
            gradebook: 'Buku Nilai', my_grades: 'Nilaiku', help: 'Bantuan & Masalah',
            issues: 'Manajemen Masalah', settings: 'Setelan',
        },
        profile: {
            settings: 'Setelan', history: 'Riwayat Akses', privacy: 'Privasi & Kebijakan',
            sponsor: 'Sponsor', logout: 'Metu',
        },
        logout_modal: {
            title: 'Metu Sesi?', body: 'Sampeyan kudu login maneh kanggo ngakses data sampeyan.',
            confirm: 'Ya, Metu Saiki', cancel: 'Tetep Ing Kene',
        },
    },
    su: {
        common: {
            dashboard: 'Papan Kontrol', courses: 'Kelas', quizzes: 'Kuis', assignments: 'Tugas',
            grades: 'Nilai', discussions: 'Diskusi', settings: 'Setelan', profile: 'Profil',
            logout: 'Kaluar', save: 'Simpen', cancel: 'Batal', delete: 'Hapus', edit: 'Edit',
            add: 'Tambah', back: 'Balik', next: 'Tuluy', submit: 'Kirim', close: 'Tutup',
            yes: 'Enya', no: 'Henteu', ok: 'Oke', search: 'Cari', filter: 'Saring',
            language: 'Basa', loading: 'Ngamuatan...',
        },
        filter: {
            all_items: 'Sadaya Item', recent: 'Panganyar', assignments: 'Tugas', quizzes: 'Kuis', files: 'File',
            due_soon: 'Deadline: Pangdeukatan', due_latest: 'Deadline: Pangjauh', recently_added: 'Ditambah Panganyar',
        },
        nav: {
            home: 'Pondok', classroom: 'Ruang Kelas', dashboard: 'Dashboard', admin_panel: 'Panel Admin', user_management: 'Manajemen User',
            course_nav: 'Navigasi Kelas', materials: 'Materi & Tugas', kbm_notes: 'Catetan KBM',
            gradebook: 'Buku Nilai', my_grades: 'Nilai Abdi', help: 'Bantuan & Masalah',
            issues: 'Manajemen Masalah', settings: 'Setelan',
        },
        profile: {
            settings: 'Setelan', history: 'Riwayat Aksés', privacy: 'Privasi & Kawijakan',
            sponsor: 'Sponsor', logout: 'Kaluar',
        },
        logout_modal: {
            title: 'Kaluar Sési?', body: 'Anjeun kedah login deui pikeun ngaksés data anjeun.',
            confirm: 'Muhun, Kaluar Ayeuna', cancel: 'Tetep Di Dieu',
        },
    },
    ban: {
        common: {
            dashboard: 'Papan Kontrol', courses: 'Kelas', quizzes: 'Kuis', assignments: 'Tugas',
            grades: 'Nilai', discussions: 'Diskusi', settings: 'Setelan', profile: 'Profil',
            logout: 'Metu', save: 'Simpen', cancel: 'Batal', delete: 'Busak', edit: 'Edit',
            add: 'Tambah', back: 'Mawali', next: 'Lanjud', submit: 'Kirim', close: 'Tutup',
            yes: 'Inggih', no: 'Nenten', ok: 'Oke', search: 'Rereh', filter: 'Saring',
            language: 'Basa', loading: 'Ngemu...',
        },
        filter: {
            all_items: 'Kabeh Item', recent: 'Anyaran', assignments: 'Tugas', quizzes: 'Kuis', files: 'File',
            due_soon: 'Deadline: Keto', due_latest: 'Deadline: Kajauhan', recently_added: 'Ditambah Anyaran',
        },
        nav: {
            home: 'Rumah', classroom: 'Ruang Kalas', dashboard: 'Dashboard', admin_panel: 'Panel Admin', user_management: 'Manajemen User',
            course_nav: 'Navigasi Kelas', materials: 'Materi & Tugas', kbm_notes: 'Catetan KBM',
            gradebook: 'Buku Nilai', my_grades: 'Nilai Titiange', help: 'Bantuan & Masalah',
            issues: 'Manajemen Masalah', settings: 'Setelan',
        },
        profile: {
            settings: 'Setelan', history: 'Sejarah Akses', privacy: 'Privasi & Kebijakan',
            sponsor: 'Sponsor', logout: 'Metu',
        },
        logout_modal: {
            title: 'Metu Sesi?', body: 'Iraga perlu login buin apang nyidaang ngakses data iraga.',
            confirm: 'Inggih, Metu Jani', cancel: 'Kantun Dini',
        },
    },
    min: {
        common: {
            dashboard: 'Papan Kontrol', courses: 'Kelas', quizzes: 'Kuis', assignments: 'Tugas',
            grades: 'Nilai', discussions: 'Diskusi', settings: 'Setelan', profile: 'Profil',
            logout: 'Kalua', save: 'Simpan', cancel: 'Batal', delete: 'Hapuih', edit: 'Edit',
            add: 'Tambah', back: 'Baliak', next: 'Lanjuik', submit: 'Kirim', close: 'Tutuik',
            yes: 'Iyo', no: 'Indak', ok: 'Oke', search: 'Cari', filter: 'Saring',
            language: 'Bahaso', loading: 'Samantaro...',
        },
        filter: {
            all_items: 'Sakiek Item', recent: 'Baruo', assignments: 'Tugas', quizzes: 'Kuis', files: 'File',
            due_soon: 'Deadline: Paliang Dakek', due_latest: 'Deadline: Paliang Jauh', recently_added: 'Ditambah Baruo',
        },
        nav: {
            home: 'Rumah', classroom: 'Ruang Kalas', dashboard: 'Dashboard', admin_panel: 'Panel Admin', user_management: 'Manajemen User',
            course_nav: 'Navigasi Kelas', materials: 'Materi & Tugas', kbm_notes: 'Catatan KBM',
            gradebook: 'Buku Nilai', my_grades: 'Nilai Ambo', help: 'Bantuan & Masalah',
            issues: 'Manajemen Masalah', settings: 'Setelan',
        },
        profile: {
            settings: 'Setelan', history: 'Riwayat Akses', privacy: 'Privasi & Kabijakan',
            sponsor: 'Sponsor', logout: 'Kalua',
        },
        logout_modal: {
            title: 'Kalua Sesi?', body: 'Anda paralu login baliak untuak mangakses data anda.',
            confirm: 'Iyo, Kalua Kini', cancel: 'Tetap Di Siko',
        },
    },
};

// ─── State ───────────────────────────────────────────────────────────────────

let _currentLang = 'id';
let _switchTimeout = null;

// ─── Translation helper ───────────────────────────────────────────────────────

function t(key, fallback = null) {
    const keys = key.split('.');
    let node = translations[_currentLang] || translations['id'];
    for (const k of keys) {
        if (node && typeof node === 'object' && k in node) node = node[k];
        else return fallback !== null ? fallback : key;
    }
    return node;
}

// ─── Loading Overlay ──────────────────────────────────────────────────────────

const _OVERLAY_INNER = `
    <div class="lang-loader-card">
        <div class="lang-loader-rings">
            <div class="lang-ring lang-ring-1"></div>
            <div class="lang-ring lang-ring-2"></div>
            <div class="lang-ring lang-ring-3"></div>
            <div class="lang-ring-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <circle cx="12" cy="12" r="10"/>
                    <path d="M2 12h20M12 2a15.3 15.3 0 010 20M12 2a15.3 15.3 0 000 20"/>
                </svg>
            </div>
        </div>
        <div id="lang-loader-flag" class="lang-loader-flag"></div>
        <p id="lang-loader-title" class="lang-loader-title"></p>
        <p id="lang-loader-sub" class="lang-loader-sub"></p>
        <div class="lang-progress-track">
            <div id="lang-progress-bar" class="lang-progress-bar"></div>
        </div>
    </div>
`;

function _getOrCreateOverlay() {
    let el = document.getElementById('lang-loading-overlay');
    if (!el) {
        el = document.createElement('div');
        el.id = 'lang-loading-overlay';
        document.body.appendChild(el);
    }
    if (!el.querySelector('.lang-loader-card')) {
        el.innerHTML = _OVERLAY_INNER;
    }
    return el;
}

function showLangLoader(targetLangCode) {
    const meta = LANG_META[_currentLang] || LANG_META['id'];
    const targetMeta = LANG_META[targetLangCode] || LANG_META['id'];

    const overlay = _getOrCreateOverlay();
    document.getElementById('lang-loader-flag').textContent = targetMeta.flag;
    document.getElementById('lang-loader-title').textContent = meta.wait;
    document.getElementById('lang-loader-sub').textContent = targetMeta.name;

    const bar = document.getElementById('lang-progress-bar');
    bar.style.transition = 'none';
    bar.style.width = '0%';

    overlay.classList.remove('lang-overlay-out');
    overlay.classList.add('lang-overlay-in');

    // Progress animation up to ~90% in 6s (leaves room for actual completion)
    requestAnimationFrame(() => {
        requestAnimationFrame(() => {
            bar.style.transition = 'width 6s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
            bar.style.width = '90%';
        });
    });
}

function hideLangLoader() {
    const overlay = document.getElementById('lang-loading-overlay');
    if (!overlay) return;
    const bar = document.getElementById('lang-progress-bar');
    if (bar) {
        bar.style.transition = 'width 0.3s ease';
        bar.style.width = '100%';
    }
    setTimeout(() => {
        overlay.classList.remove('lang-overlay-in');
        overlay.classList.add('lang-overlay-out');
    }, 300);
}

// ─── Apply translations to DOM ────────────────────────────────────────────────

function _applyTranslations(lang) {
    const dict = translations[lang] || translations['id'];
    if (!dict) return;

    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        const keys = key.split('.');
        let val = dict;
        for (const k of keys) {
            if (val && typeof val === 'object' && k in val) val = val[k];
            else { val = null; break; }
        }
        if (val && typeof val === 'string') {
            if ((el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') && el.placeholder) {
                el.placeholder = val;
            } else {
                el.textContent = val;
            }
        }
    });

    // RTL support
    const meta = LANG_META[lang] || LANG_META['id'];
    document.documentElement.setAttribute('dir', meta.dir);
    document.documentElement.setAttribute('lang', lang);

    // Update lang flag in sidebar button if exists
    const flagEl = document.getElementById('sidebar-lang-flag');
    if (flagEl) flagEl.textContent = meta.flag;
    const nameEl = document.getElementById('sidebar-lang-name');
    if (nameEl) nameEl.textContent = meta.name;
}

// ─── Switch Language (main public function) ───────────────────────────────────

async function switchLanguage(code) {
    if (!LANG_SUPPORTED.includes(code)) return;
    if (code === _currentLang) {
        // Close dropdown and submenu
        const menu = document.getElementById('user-dropdown-menu');
        if (menu) menu.classList.add('hidden');
        const sub = document.getElementById('lang-submenu');
        if (sub) sub.classList.add('hidden');
        return;
    }

    // Close dropdowns
    const menu = document.getElementById('user-dropdown-menu');
    if (menu) menu.classList.add('hidden');

    // Show elegant loader
    showLangLoader(code);

    // Hard timeout — hide loader & proceed after 7s regardless
    if (_switchTimeout) clearTimeout(_switchTimeout);
    _switchTimeout = setTimeout(() => {
        hideLangLoader();
    }, 7000);

    const startTime = Date.now();
    const MIN_DISPLAY = 1800; // ms

    try {
        const res = await fetch('/api/set-language', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ language: code }),
            signal: AbortSignal.timeout(6000),
        });
        const data = await res.json();
        if (!data.success) throw new Error(data.message || 'Failed');
    } catch (e) {
        // Even if API fails, switch locally
        console.warn('Lang API error:', e);
    }

    // Save locally always
    localStorage.setItem('preferred_language', code);
    _currentLang = code;

    // Wait minimum display time
    const elapsed = Date.now() - startTime;
    const remaining = Math.max(0, MIN_DISPLAY - elapsed);
    await new Promise(r => setTimeout(r, remaining));

    clearTimeout(_switchTimeout);

    // Reload page for comprehensive switch (server + client)
    window.location.reload();
}

// ─── Initialise on page load ──────────────────────────────────────────────────

function initLanguage() {
    const serverLang = document.documentElement.getAttribute('data-user-lang');

    if (serverLang && LANG_SUPPORTED.includes(serverLang)) {
        // Server (DB) is always authoritative for logged-in users
        _currentLang = serverLang;
    } else {
        // Unauthenticated page: fall back to localStorage
        const stored = localStorage.getItem('preferred_language');
        _currentLang = (stored && LANG_SUPPORTED.includes(stored)) ? stored : 'id';
    }
    localStorage.setItem('preferred_language', _currentLang);

    _applyTranslations(_currentLang);
    _renderLangSubmenu();
    // Update sidebar flag to correct emoji
    const meta = LANG_META[_currentLang] || LANG_META['id'];
    const flagEl = document.getElementById('sidebar-lang-flag');
    if (flagEl) flagEl.textContent = meta.flag;
    const nameEl = document.getElementById('sidebar-lang-name');
    if (nameEl) nameEl.textContent = meta.name;
}

// ─── Render language submenu in sidebar ──────────────────────────────────────

function _renderLangSubmenu() {
    const container = document.getElementById('lang-submenu');
    if (!container) return;

    const items = [
        { code: 'id',  label: 'Indonesia',  flag: '🇮🇩' },
        { code: 'en',  label: 'English',     flag: '🇬🇧' },
        { code: 'ar',  label: 'العربية',     flag: '🇸🇦' },
        { code: 'jv',  label: 'Jawa',        flag: '🇮🇩' },
        { code: 'su',  label: 'Sunda',       flag: '🇮🇩' },
        { code: 'ban', label: 'Bali',        flag: '🇮🇩' },
        { code: 'min', label: 'Padang',      flag: '🇮🇩' },
    ];

    container.innerHTML = items.map(lang => `
        <button onclick="LanguageManager.switch('${lang.code}')"
                class="w-full flex items-center space-x-3 px-5 py-2.5 transition-colors ${_currentLang === lang.code ? 'bg-blue-50' : 'hover:bg-gray-50'}">
            <span class="text-lg leading-none">${lang.flag}</span>
            <span class="text-sm font-semibold ${_currentLang === lang.code ? 'text-blue-600' : 'text-gray-600'}">${lang.label}</span>
            ${_currentLang === lang.code ? `
                <svg class="w-4 h-4 text-blue-500 ml-auto" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"/>
                </svg>` : ''}
        </button>
    `).join('');
}

function toggleLangSubmenu() {
    const sub = document.getElementById('lang-submenu');
    if (!sub) return;
    const chevron = document.getElementById('lang-chevron');
    const isOpen = !sub.classList.contains('hidden');
    sub.classList.toggle('hidden', isOpen);
    if (chevron) chevron.style.transform = isOpen ? '' : 'rotate(180deg)';
}

// ─── Public API ───────────────────────────────────────────────────────────────

window.LanguageManager = {
    get current() { return _currentLang; },
    switch: switchLanguage,
    t,
    init: initLanguage,
    toggleSubmenu: toggleLangSubmenu,
};

// Auto-init
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initLanguage);
} else {
    initLanguage();
}
