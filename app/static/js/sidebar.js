/**
 * Sidebar Manager
 * Handles sidebar hide/unhide functionality with icon-only mode
 */

const SidebarManager = {
    sidebar: null,
    unhideBtn: null,
    isCollapsed: false,

    init() {
        this.sidebar = document.getElementById('main-sidebar');
        this.createUnhideButton();
        this.loadState();
        this.attachEventListeners();
    },

    createUnhideButton() {
        // Create unhide button that appears when sidebar is collapsed
        this.unhideBtn = document.createElement('button');
        this.unhideBtn.id = 'sidebar-unhide-btn';
        this.unhideBtn.className = 'fixed left-0 top-1/2 -translate-y-1/2 z-50 bg-white border border-gray-200 shadow-lg p-3 rounded-r-xl hover:bg-gray-50 transition-all hidden';
        this.unhideBtn.title = 'Tampilkan Sidebar';
        this.unhideBtn.innerHTML = `
            <svg class="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M13 5l7 7-7 7M5 5l7 7-7 7"/>
            </svg>
        `;
        this.unhideBtn.onclick = () => this.toggle();
        document.body.appendChild(this.unhideBtn);
    },

    toggle() {
        if (!this.sidebar) return;

        this.isCollapsed = !this.isCollapsed;
        this.saveState();
        this.updateUI();
    },

    updateUI() {
        if (!this.sidebar) return;

        if (this.isCollapsed) {
            // Collapse sidebar - show only icons
            this.sidebar.classList.remove('w-64');
            this.sidebar.classList.add('w-20');
            this.sidebar.classList.add('sidebar-collapsed');

            // Hide text spans
            this.sidebar.querySelectorAll('span:not(.sidebar-hide)').forEach(span => {
                span.classList.add('hidden');
            });

            // Hide logo text
            const logoText = this.sidebar.querySelector('.sidebar-logo-text');
            if (logoText) logoText.classList.add('hidden');

            // Hide toggle button in sidebar
            const toggleBtn = this.sidebar.querySelector('.sidebar-toggle-btn');
            if (toggleBtn) {
                toggleBtn.innerHTML = `
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M13 5l7 7-7 7M5 5l7 7-7 7"/>
                    </svg>
                `;
                toggleBtn.title = 'Tampilkan Sidebar';
            }

            // Show unhide button
            this.unhideBtn.classList.remove('hidden');

            // Center icons
            this.sidebar.querySelectorAll('nav a').forEach(link => {
                link.classList.add('justify-center');
                link.classList.remove('space-x-3');
            });
        } else {
            // Expand sidebar - show full
            this.sidebar.classList.remove('w-20');
            this.sidebar.classList.add('w-64');
            this.sidebar.classList.remove('sidebar-collapsed');

            // Show text spans
            this.sidebar.querySelectorAll('span').forEach(span => {
                span.classList.remove('hidden');
            });

            // Show logo text
            const logoText = this.sidebar.querySelector('.sidebar-logo-text');
            if (logoText) logoText.classList.remove('hidden');

            // Update toggle button
            const toggleBtn = this.sidebar.querySelector('.sidebar-toggle-btn');
            if (toggleBtn) {
                toggleBtn.innerHTML = `
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7"/>
                    </svg>
                `;
                toggleBtn.title = 'Sembunyikan Sidebar';
            }

            // Hide unhide button
            this.unhideBtn.classList.add('hidden');

            // Restore link layout
            this.sidebar.querySelectorAll('nav a').forEach(link => {
                link.classList.remove('justify-center');
                link.classList.add('space-x-3');
            });
        }

        // Save state to localStorage
        this.saveState();
    },

    saveState() {
        localStorage.setItem('sidebarCollapsed', this.isCollapsed.toString());
    },

    loadState() {
        const saved = localStorage.getItem('sidebarCollapsed');
        if (saved === 'true') {
            this.isCollapsed = true;
            this.updateUI();
        }
    },

    attachEventListeners() {
        // Handle toggle button in sidebar
        const toggleBtn = this.sidebar?.querySelector('.sidebar-toggle-btn');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => this.toggle());
        }

        // Keyboard shortcut (Ctrl/Cmd + B)
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
                e.preventDefault();
                this.toggle();
            }
        });
    }
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    SidebarManager.init();
});

// Export for global access
window.SidebarManager = SidebarManager;
