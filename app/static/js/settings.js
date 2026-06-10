function initSettingsPage() {
    const state = {
        courses: [],
        deletingCourseId: null
    };

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
        const msgEl = document.getElementById('password-message');

        if (!old_password || !new_password) {
            showMsg(msgEl, 'Semua field wajib diisi', 'error'); return;
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
            }
            showMsg(msgEl, data.message, data.success ? 'success' : 'error');
        } catch { showMsg(msgEl, 'Kesalahan koneksi ke server', 'error'); }
    });

    function showMsg(el, text, type) {
        if (!el) return;
        el.textContent = text;
        el.className = `p-4 rounded-2xl text-sm font-black text-center ${type === 'success' ? 'bg-[#dcfce7] text-[#58cc02]' : 'bg-red-50 text-[#ff4b4b]'}`;
        el.classList.remove('hidden');
        setTimeout(() => el.classList.add('hidden'), 4000);
    }

    // --- CLASS MANAGEMENT ---
    async function loadCourses() {
        const listEl = document.getElementById('settings-class-list');
        if (!listEl) return;

        try {
            const res = await fetch('/api/courses');
            const data = await res.json();
            if (data.success) {
                state.courses = data.courses;
                renderCourses();
            }
        } catch (err) {
            console.error('Failed to load courses', err);
        }
    }

    function renderCourses() {
        const listEl = document.getElementById('settings-class-list');
        if (!listEl || state.courses.length === 0) {
            if (listEl) listEl.innerHTML = '<p class="text-sm font-bold text-[#afafaf] text-center py-4">Belum ada kelas yang dibuat.</p>';
            return;
        }

        listEl.innerHTML = state.courses.map(c => `
            <div class="flex items-center justify-between p-4 bg-[#f7f7f7] dark:bg-gray-800 border-2 border-[#e5e5e5] dark:border-gray-700 rounded-2xl group transition-all">
                <div class="flex items-center gap-4">
                    <div class="w-10 h-10 rounded-xl flex items-center justify-center text-white shadow-sm" style="background-color: ${c.color || '#58cc02'}">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/></svg>
                    </div>
                    <div>
                        <p class="font-black text-[#4b4b4b] dark:text-white leading-tight">${c.name}</p>
                        <p class="text-[10px] font-black text-[#afafaf] uppercase tracking-widest mt-0.5">${c.class_code}</p>
                    </div>
                </div>
                <button onclick="window.openDeleteModal(${c.id}, '${c.name.replace(/'/g, "\\'")}')" class="p-3 text-[#afafaf] hover:text-[#ff4b4b] hover:bg-white dark:hover:bg-gray-900 rounded-xl transition-all shadow-sm border border-transparent hover:border-slate-200 dark:hover:border-gray-700">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                </button>
            </div>
        `).join('');
    }

    window.openDeleteModal = (id, name) => {
        state.deletingCourseId = id;
        document.getElementById('delete-course-name-display').textContent = name;
        document.getElementById('delete-confirm-input').value = '';
        document.getElementById('delete-final-btn').disabled = true;
        document.getElementById('delete-final-btn').classList.add('opacity-50', 'cursor-not-allowed');
        document.getElementById('delete-class-modal').classList.remove('hidden');
    };

    window.closeDeleteModal = () => {
        document.getElementById('delete-class-modal').classList.add('hidden');
        state.deletingCourseId = null;
    };

    // Confirm input listener
    document.getElementById('delete-confirm-input')?.addEventListener('input', (e) => {
        const btn = document.getElementById('delete-final-btn');
        const isValid = e.target.value.toLowerCase() === 'setuju';
        btn.disabled = !isValid;
        btn.classList.toggle('opacity-50', !isValid);
        btn.classList.toggle('cursor-not-allowed', !isValid);
    });

    document.getElementById('delete-final-btn')?.addEventListener('click', async () => {
        if (!state.deletingCourseId) return;
        const btn = document.getElementById('delete-final-btn');
        const errorEl = document.getElementById('delete-modal-error');
        
        btn.disabled = true;
        btn.textContent = 'MENGHAPUS...';

        try {
            const res = await fetch(`/api/courses/${state.deletingCourseId}`, { method: 'DELETE' });
            const data = await res.json();
            if (data.success) {
                state.courses = state.courses.filter(c => c.id !== state.deletingCourseId);
                renderCourses();
                window.closeDeleteModal();
                alert('Kelas berhasil dihapus.');
            } else {
                errorEl.textContent = data.message || 'Gagal menghapus kelas';
                errorEl.classList.remove('hidden');
            }
        } catch (err) {
            errorEl.textContent = 'Kesalahan koneksi ke server';
            errorEl.classList.remove('hidden');
        } finally {
            btn.disabled = false;
            btn.textContent = 'HAPUS SEKARANG';
        }
    });

    // --- THEME & UI ---
    function renderSettingsLanguage() {
        const dropdown = document.getElementById('settings-language-dropdown');
        if (!dropdown || !window.LanguageManager) return;
        dropdown.value = window.LanguageManager.currentLang;
    }

    function updateThemeUI() {
        const isDark = window.ThemeManager.isDark();
        const lightBtn = document.getElementById('theme-light-btn');
        const darkBtn = document.getElementById('theme-dark-btn');
        const activeText = document.getElementById('theme-active-text');

        if (!lightBtn || !darkBtn || !activeText) return;

        [lightBtn, darkBtn].forEach(btn => {
            btn.classList.remove('border-[#1cb0f6]', 'bg-[#ddf4ff]', 'dark:bg-gray-700');
            btn.classList.add('btn-duo-ghost');
        });

        if (isDark) {
            darkBtn.classList.remove('btn-duo-ghost');
            darkBtn.classList.add('border-[#1cb0f6]', 'bg-[#ddf4ff]', 'dark:bg-gray-700');
            activeText.textContent = 'Tema aktif: Gelap';
        } else {
            lightBtn.classList.remove('btn-duo-ghost');
            lightBtn.classList.add('border-[#1cb0f6]', 'bg-[#ddf4ff]');
            activeText.textContent = 'Tema aktif: Terang';
        }
    }

    // Init
    loadCourses();
    renderSettingsLanguage();
    updateThemeUI();
    window.addEventListener('languageChanged', renderSettingsLanguage);
    window.addEventListener('theme:change', updateThemeUI);

    // Logout
    document.getElementById('user-dropdown-logout')?.addEventListener('click', () => {
        if (window.handleSALogout) window.handleSALogout();
        else if (window.showLogoutModal) window.showLogoutModal();
        else window.location.href = '/logout';
    });
}
// init-on-ready: jalan saat full load & re-eksekusi setelah swap htmx
if (document.readyState !== 'loading') initSettingsPage();
else document.addEventListener('DOMContentLoaded', initSettingsPage);
