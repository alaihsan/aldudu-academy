/**
 * Aldudu Academy - Sidebar & Global Scripts
 */

function initSidebar() {
    const profileBtn = document.getElementById('user-profile-btn');
    const menuPopup = document.getElementById('user-menu-popup');
    const arrow = document.getElementById('profile-arrow');

    if (profileBtn && menuPopup) {
        // Remove existing listener to prevent clones
        const newProfileBtn = profileBtn.cloneNode(true);
        profileBtn.parentNode.replaceChild(newProfileBtn, profileBtn);

        newProfileBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            const isHidden = menuPopup.classList.contains('hidden');
            menuPopup.classList.toggle('hidden');
            if (arrow) arrow.style.transform = isHidden ? 'rotate(180deg)' : 'rotate(0deg)';
        });
    }

    window.addEventListener('click', function() {
        if (menuPopup) {
            menuPopup.classList.add('hidden');
            if (arrow) arrow.style.transform = 'rotate(0deg)';
        }
    });
}

async function handleGlobalLogout() {
    if (confirm('Apakah Anda yakin ingin keluar?')) {
        try {
            const res = await fetch('/api/logout', { method: 'POST' });
            if (res.ok) window.location.href = '/';
        } catch (err) {
            console.error('Logout failed', err);
        }
    }
}

// Run on normal load
document.addEventListener('DOMContentLoaded', initSidebar);

// Run on HTMX swap
document.body.addEventListener('htmx:afterSwap', initSidebar);
