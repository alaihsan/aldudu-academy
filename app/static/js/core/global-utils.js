/**
 * Aldudu Academy - Global Utilities
 * Extracted from base.html inline scripts
 */

// Floating Issue Button Logic
document.addEventListener('DOMContentLoaded', function() {
    const floatBtn = document.getElementById('floating-issue-btn');
    const floatModal = document.getElementById('floating-issue-modal');
    const closeFloat = document.getElementById('close-floating-issue');
    const floatForm = document.getElementById('floating-issue-form');

    if (floatBtn && floatModal) {
        floatBtn.addEventListener('click', () => {
            floatModal.classList.toggle('hidden');
            if (!floatModal.classList.contains('hidden')) {
                document.getElementById('float-issue-title').focus();
            }
        });

        closeFloat.addEventListener('click', () => {
            floatModal.classList.add('hidden');
        });

        floatForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const submitBtn = document.getElementById('submit-floating-issue');
            const originalText = submitBtn.innerText;

            submitBtn.disabled = true;
            submitBtn.innerText = 'MENGIRIM...';

            const title = document.getElementById('float-issue-title').value;
            const description = document.getElementById('float-issue-desc').value;

            try {
                const res = await fetch('/api/issues', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ title, description, priority: 'MEDIUM' })
                });
                const data = await res.json();

                if (data.success) {
                    alert('Laporan berhasil dikirim!');
                    floatForm.reset();
                    floatModal.classList.add('hidden');

                    if (window.IssuesManager && typeof window.IssuesManager.loadIssues === 'function') {
                        window.IssuesManager.loadIssues();
                    } else if (window.location.pathname.includes('/issues')) {
                        if (typeof loadIssues === 'function') loadIssues();
                    }
                } else {
                    alert('Gagal: ' + data.message);
                }
            } catch (err) {
                alert('Terjadi kesalahan koneksi.');
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerText = originalText;
            }
        });
    }
});

// Global modal toggle (dipakai banyak halaman: admin, dll)
function toggleModal(id, show) {
    const m = document.getElementById(id);
    if (!m) return;
    if (show) m.classList.remove('hidden');
    else m.classList.add('hidden');
}

// Global Logout Function
async function handleGlobalLogout() {
    try {
        const res = await fetch('/api/logout', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await res.json();

        if (data.success) {
            window.location.href = '/login';
        } else {
            Swal.fire({
                icon: 'error',
                title: 'Gagal Logout',
                text: 'Terjadi kesalahan saat logout',
                confirmButtonColor: '#ef4444'
            });
        }
    } catch (err) {
        console.error('Logout error:', err);
        Swal.fire({
            icon: 'error',
            title: 'Gagal Logout',
            text: 'Terjadi kesalahan koneksi',
            confirmButtonColor: '#ef4444'
        });
    }
}

// Show Logout Modal
function showLogoutModal() {
    const modal = document.getElementById('logout-modal');
    if (modal) {
        modal.classList.remove('hidden');
    }
}

// Close Logout Modal
function closeLogoutModal() {
    const modal = document.getElementById('logout-modal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

// Global Elegant Modal Overrides
window.alert = function(message) {
    Swal.fire({
        title: 'Informasi',
        text: message,
        icon: 'info',
        confirmButtonText: 'OKE',
        customClass: {
            confirmButton: 'bg-primary-600 hover:bg-primary-700 text-white font-bold py-2 px-4 rounded-xl'
        }
    });
};

const originalConfirm = window.confirm;
window.confirm = function(message) {
    return originalConfirm(message);
};

// Create a global helper for elegant confirmations
window.ask = async function(title, message, icon = 'question') {
    const result = await Swal.fire({
        title: title,
        text: message,
        icon: icon,
        showCancelButton: true,
        confirmButtonColor: '#4f46e5',
        cancelButtonColor: '#94a3b8',
        confirmButtonText: 'Ya, Lanjutkan',
        cancelButtonText: 'Batal',
        reverseButtons: true
    });
    return result.isConfirmed;
};

// ─── Orkestrasi navigasi SPA (htmx) ──────────────────────────────────────────
// Skrip ini dimuat sekali (tidak ikut di-swap), jadi aman pasang listener global.

function spaUpdateActiveNav() {
    const path = window.location.pathname;
    document.querySelectorAll('#main-sidebar a.nav-link-duo[href]').forEach((a) => {
        const href = a.getAttribute('href');
        const active = href && href !== '#' && (path === href || path.startsWith(href + '/'));
        a.classList.toggle('active', !!active);
    });
}

function spaUpdateTitle() {
    const el = document.getElementById('spa-page-title');
    if (el && el.dataset.title) document.title = el.dataset.title.trim();
}

function spaScrollTop() {
    const main = document.querySelector('#app-content main');
    if (main) main.scrollTop = 0;
    window.scrollTo(0, 0);
}

// Safety net: bila navigasi boost mengembalikan halaman PENUH (halaman yang
// belum dikonversi SPA), jangan di-swap (akan rusak/nested) — lakukan navigasi
// biasa (full load). Ini menangani semua link ke halaman legacy secara otomatis.
document.body.addEventListener('htmx:beforeSwap', function (evt) {
    try {
        const xhr = evt.detail && evt.detail.xhr;
        if (!xhr) return;
        const ct = (xhr.getResponseHeader('Content-Type') || '');
        if (ct.indexOf('text/html') !== -1 && /<html[\s>]/i.test(xhr.responseText || '')) {
            evt.detail.shouldSwap = false;
            const url = (evt.detail.requestConfig && evt.detail.requestConfig.path) || xhr.responseURL;
            if (url) window.location.assign(url);
        }
    } catch (e) {}
});

// Setelah konten ter-swap & settle: rapikan judul, link aktif, scroll, i18n.
document.body.addEventListener('htmx:afterSettle', function () {
    spaUpdateTitle();
    spaUpdateActiveNav();
    spaScrollTop();
    if (typeof initLanguage === 'function') {
        try { initLanguage(); } catch (e) {}
    }
});

