/**
 * Aldudu Academy - Sidebar & Global Scripts
 */

const SidebarManager = {
    state: {
        isCollapsed: localStorage.getItem('sidebarCollapsed') === 'true'
    },

    init() {
        this.cacheElements();
        if (!this.elements.sidebar) return;

        this.applyState();
        this.bindEvents();
    },

    cacheElements() {
        this.elements = {
            sidebar: document.getElementById('main-sidebar'),
            mainContent: document.getElementById('main-content'),
            unhideBtn: document.getElementById('sidebar-unhide-btn'),
            profileBtn: document.getElementById('user-profile-btn'),
            logoutModal: document.getElementById('logout-modal'),
            closeLogoutBtn: document.getElementById('close-logout-modal')
        };
    },

    bindEvents() {
        if (this.elements.profileBtn) {
            this.elements.profileBtn.onclick = (e) => {
                e.stopPropagation();
                this.elements.logoutModal?.classList.remove('hidden');
            };
        }

        if (this.elements.closeLogoutBtn) {
            this.elements.closeLogoutBtn.onclick = () => {
                this.elements.logoutModal?.classList.add('hidden');
            };
        }

        window.onclick = (e) => {
            if (e.target === this.elements.logoutModal) {
                this.elements.logoutModal.classList.add('hidden');
            }
        };
    },

    toggle() {
        this.state.isCollapsed = !this.state.isCollapsed;
        localStorage.setItem('sidebarCollapsed', this.state.isCollapsed);
        this.applyState();
    },

    applyState() {
        const { sidebar, mainContent, unhideBtn } = this.elements;
        if (!sidebar) return;

        if (this.state.isCollapsed) {
            sidebar.classList.add('sidebar-collapsed');
            unhideBtn?.classList.remove('hidden');
            unhideBtn?.classList.add('lg:flex');
        } else {
            sidebar.classList.remove('sidebar-collapsed');
            unhideBtn?.classList.add('hidden');
            unhideBtn?.classList.remove('lg:flex');
        }
    }
};

async function handleGlobalLogout() {
    try {
        const res = await fetch('/api/logout', { method: 'POST' });
        if (res.ok) {
            window.location.href = '/';
        }
    } catch (err) {
        console.error('Logout failed', err);
    }
}

// Global handle for dashboard.js compatibility
if (typeof window !== 'undefined') {
    window.SidebarManager = SidebarManager;
    window.handleGlobalLogout = handleGlobalLogout;
}

// Initial Run
document.addEventListener('DOMContentLoaded', () => SidebarManager.init());
document.body.addEventListener('htmx:afterSwap', () => SidebarManager.init());
