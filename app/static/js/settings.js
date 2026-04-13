document.addEventListener('DOMContentLoaded', function() {
    // Save profile
    document.getElementById('save-profile-btn')?.addEventListener('click', async () => {
        const name = document.getElementById('settings-name').value.trim();
        const msgEl = document.getElementById('profile-message');
        if (!name) { showMsg(msgEl, 'Nama tidak boleh kosong', 'error'); return; }

        try {
            const res = await fetch('/api/profile', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name })
            });
            const data = await res.json();
            showMsg(msgEl, data.message, data.success ? 'success' : 'error');
        } catch { showMsg(msgEl, 'Kesalahan koneksi ke server', 'error'); }
    });

    // Change password
    document.getElementById('change-password-btn')?.addEventListener('click', async () => {
        const old_password = document.getElementById('old-password').value;
        const new_password = document.getElementById('new-password').value;
        const confirm_password = document.getElementById('confirm-password').value;
        const msgEl = document.getElementById('password-message');

        if (!old_password || !new_password || !confirm_password) {
            showMsg(msgEl, 'Semua field wajib diisi', 'error'); return;
        }
        if (new_password !== confirm_password) {
            showMsg(msgEl, 'Password baru dan konfirmasi tidak cocok', 'error'); return;
        }
        if (new_password.length < 6) {
            showMsg(msgEl, 'Password minimal 6 karakter', 'error'); return;
        }

        try {
            const res = await fetch('/api/change-password', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ old_password, new_password })
            });
            const data = await res.json();
            if (data.success) {
                document.getElementById('old-password').value = '';
                document.getElementById('new-password').value = '';
                document.getElementById('confirm-password').value = '';
            }
            showMsg(msgEl, data.message, data.success ? 'success' : 'error');
        } catch { showMsg(msgEl, 'Kesalahan koneksi ke server', 'error'); }
    });

    function showMsg(el, text, type) {
        el.textContent = text;
        el.className = `p-4 rounded-2xl text-sm font-bold text-center ${type === 'success' ? 'bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-400' : 'bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400'}`;
        el.classList.remove('hidden');
        setTimeout(() => el.classList.add('hidden'), 4000);
    }

    // Render language dropdown
    function renderSettingsLanguage() {
        const dropdown = document.getElementById('settings-language-dropdown');
        if (!dropdown || !window.LanguageManager) return;

        const currentLang = window.LanguageManager.currentLang;
        dropdown.value = currentLang;
    }

    renderSettingsLanguage();
    window.addEventListener('languageChanged', renderSettingsLanguage);

    // Theme section UI updates
    function updateThemeUI() {
        const isDark = window.ThemeManager.isDark();
        const lightBtn = document.getElementById('theme-light-btn');
        const darkBtn = document.getElementById('theme-dark-btn');
        const activeText = document.getElementById('theme-active-text');
        const activeDot = document.getElementById('theme-active-dot');

        if (!lightBtn || !darkBtn || !activeText) return;

        // Reset both buttons
        [lightBtn, darkBtn].forEach(btn => {
            btn.classList.remove('border-primary-500', 'dark:border-primary-400', 'bg-primary-50', 'dark:bg-primary-900/20');
            btn.classList.add('border-gray-200', 'dark:border-gray-700');
        });

        // Highlight active theme
        if (isDark) {
            darkBtn.classList.remove('border-gray-200', 'dark:border-gray-700');
            darkBtn.classList.add('border-primary-500', 'dark:border-primary-400', 'bg-primary-50', 'dark:bg-primary-900/20');
            activeText.textContent = 'Tema aktif: Gelap';
        } else {
            lightBtn.classList.remove('border-gray-200', 'dark:border-gray-700');
            lightBtn.classList.add('border-primary-500', 'dark:border-primary-400', 'bg-primary-50', 'dark:bg-primary-900/20');
            activeText.textContent = 'Tema aktif: Terang';
        }
    }

    // Initial update
    updateThemeUI();

    // Listen for theme changes
    window.addEventListener('theme:change', updateThemeUI);
});
