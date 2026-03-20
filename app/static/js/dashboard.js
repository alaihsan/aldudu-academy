/**
 * Aldudu Academy Dashboard
 * Handles classroom view, filtering, and course management
 */

const Dashboard = {
    currentView: 'home',
    sortMode: 'manual',

    init() {
        // Check if classroom view should be shown
        const urlParams = new URLSearchParams(window.location.search);
        const view = urlParams.get('view');

        if (view === 'classroom') {
            this.currentView = 'classroom';
            this.showClassroomView();
        }

        // Initialize event listeners
        this.initEventListeners();
        this.loadDashboard();
    },

    showClassroomView() {
        const classroomSection = document.getElementById('classroom-view');
        const classSection = document.querySelector('section:nth-of-type(2)');

        if (classroomSection && classSection) {
            classSection.classList.add('hidden');
            classroomSection.classList.remove('hidden');
        }
    },

    initEventListeners() {
        // Filter dropdown
        const filterSelect = document.getElementById('classroom-filter');
        if (filterSelect) {
            filterSelect.addEventListener('change', () => this.filterClassroomItems());
        }

        // Sort dropdown
        const sortSelect = document.getElementById('classroom-sort');
        if (sortSelect) {
            sortSelect.addEventListener('change', () => this.sortClassroomItems());
        }

        // Sort mode buttons
        const sortButtons = document.querySelectorAll('.sort-btn');
        sortButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
            });
        });

        // Handle logout
        const logoutBtn = document.getElementById('user-dropdown-logout');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => {
                document.getElementById('logout-modal').classList.remove('hidden');
            });
        }

        // Enroll section
        const enrollForm = document.getElementById('enroll-form');
        if (enrollForm) {
            enrollForm.addEventListener('submit', (e) => this.handleEnroll(e));
        }
    },

    setSortMode(mode) {
        this.sortMode = mode;

        const buttons = document.querySelectorAll('.sort-btn');
        buttons.forEach(btn => {
            btn.classList.remove('bg-primary-600', 'text-white');
            btn.classList.add('text-gray-600', 'hover:bg-gray-100');
        });

        const activeBtn = document.getElementById(`sort-${mode}`);
        if (activeBtn) {
            activeBtn.classList.add('bg-primary-600', 'text-white');
            activeBtn.classList.remove('text-gray-600', 'hover:bg-gray-100');
        }
    },

    filterClassroomItems() {
        const filterSelect = document.getElementById('classroom-filter');
        const filterValue = filterSelect?.value || 'all';

        // Placeholder: Filter logic would go here
        // For now, this just shows the selected filter
        console.log('Filtering by:', filterValue);
    },

    sortClassroomItems() {
        const sortSelect = document.getElementById('classroom-sort');
        const sortValue = sortSelect?.value || 'due-asc';

        // Placeholder: Sort logic would go here
        // For now, this just shows the selected sort
        console.log('Sorting by:', sortValue);
    },

    loadDashboard() {
        // This would be called on page load to fetch data from the backend
        // Placeholder for future implementation
    },

    handleEnroll(e) {
        e.preventDefault();
        const codeInput = document.getElementById('class-code-input');
        const code = codeInput?.value?.trim();

        if (!code) return;

        // Would make API call here to enroll in class
        // Placeholder for future implementation
        console.log('Enrolling in class with code:', code);
    },

    handleLogout() {
        document.getElementById('logout-modal').classList.remove('hidden');
    },
};

// Initialize dashboard on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    Dashboard.init();
});
