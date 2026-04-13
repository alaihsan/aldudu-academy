// Logout modal event listeners
document.addEventListener('DOMContentLoaded', function() {
    // Settings logout button - show modal
    const settingsLogoutBtn = document.getElementById('user-dropdown-logout');
    if (settingsLogoutBtn) {
        settingsLogoutBtn.addEventListener('click', showLogoutModal);
    }

    // Close modal button
    const closeBtn = document.getElementById('close-logout-modal');
    if (closeBtn) {
        closeBtn.addEventListener('click', closeLogoutModal);
    }

    // Close modal on backdrop click
    const modal = document.getElementById('logout-modal');
    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === this) {
                closeLogoutModal();
            }
        });
    }

    // Close on Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeLogoutModal();
        }
    });
});
