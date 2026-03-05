/**
 * Aldudu Academy - Sidebar & Global Scripts
 */

function initSidebar() {
    const profileBtn = document.getElementById('user-profile-btn');
    const logoutModal = document.getElementById('logout-modal');
    const closeLogoutBtn = document.getElementById('close-logout-modal');
    
    if (profileBtn && logoutModal) {
        // Clone to clean up old listeners
        const newProfileBtn = profileBtn.cloneNode(true);
        profileBtn.parentNode.replaceChild(newProfileBtn, profileBtn);
        
        newProfileBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            logoutModal.classList.remove('hidden');
        });
    }

    if (closeLogoutBtn && logoutModal) {
        closeLogoutBtn.addEventListener('click', function() {
            logoutModal.classList.add('hidden');
        });
    }

    // Close on click outside the card
    window.addEventListener('click', function(e) {
        if (e.target === logoutModal) {
            logoutModal.classList.add('hidden');
        }
    });
}

async function handleGlobalLogout() {
    try {
        const res = await fetch('/api/logout', { method: 'POST' });
        if (res.ok) {
            // Success animation or direct redirect
            window.location.href = '/';
        }
    } catch (err) {
        console.error('Logout failed', err);
    }
}

// Run on normal load
document.addEventListener('DOMContentLoaded', initSidebar);

// Run on HTMX swap
document.body.addEventListener('htmx:afterSwap', initSidebar);
