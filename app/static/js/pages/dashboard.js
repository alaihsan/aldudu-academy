/**
 * Aldudu Academy - Dashboard JavaScript
 * Course grid: load, render, sort, archive. Login/register handlers live
 * in auth/login_register.js; class create/edit modal + manual reorder
 * live in dashboard_class_modal.js (both loaded right after this file).
 */

// Fallback if DOMPurify CDN fails to load
if (typeof DOMPurify === 'undefined') {
    window.DOMPurify = {
        sanitize: function(html, opts) {
            // Basic HTML entity escaping for dynamic values is handled
            // by escapeHtml() below; for full HTML strings passed here,
            // return as-is since the content comes from our own API.
            return html;
        }
    };
}

function escapeHtml(str) {
    if (typeof str !== 'string') return str;
    return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

var Dashboard = {
    state: {
        currentUser: null,
        isTeacher: false,
        courses: [],
        selectedYearId: null,
        editingCourseId: null,
        isInitialized: false,
        pendingDeletes: {}, // map of courseId -> {timeout, courseData}
        sortMode: localStorage.getItem('courseSortMode') || 'asc', // manual, asc, desc
        isEditingOrder: false
    },

    async init() {
        this.cacheElements();

        // If elements don't exist (not on dashboard page), stop
        if (!this.elements.classGrid && !document.getElementById('register-form')) return;

        this.bindEvents();
        await this.checkAuth();
        await this.loadSchoolsDropdown();
        this.state.isInitialized = true;

        // Attach to window for global access
        window.Dashboard = this;

        // Finalize all pending deletions on page exit/refresh
        window.addEventListener('beforeunload', () => {
            Object.keys(this.state.pendingDeletes).forEach(courseId => {
                // Use keepalive to ensure the request completes after the page is closed
                fetch(`/api/courses/${courseId}`, {
                    method: 'DELETE',
                    keepalive: true
                });
            });
        });

        this.updateSortButtons();
    },

    cacheElements() {
        this.elements = {
            loginPage: document.getElementById('login-page'),
            appPage: document.getElementById('app-page'),
            loginForm: document.getElementById('login-form'),
            loginError: document.getElementById('login-error'),
            
            userNameSidebar: document.getElementById('user-name-sidebar'),
            userRoleSidebar: document.getElementById('user-role-sidebar'),
            userAvatarSidebar: document.getElementById('user-avatar-sidebar'),
            teacherNav: document.getElementById('teacher-nav'),
            logoutBtn: document.getElementById('logout-button-sidebar'),
            welcomeTitle: document.getElementById('welcome-title'),
            
            totalClasses: document.getElementById('total-classes'),
            totalStudents: document.getElementById('total-students'),
            
            enrollSection: document.getElementById('enroll-section'),
            enrollForm: document.getElementById('enroll-form'),
            classGrid: document.getElementById('class-grid'),
            classSkeleton: document.getElementById('class-skeleton'),
            emptyState: document.getElementById('empty-state'),
            createClassBtn: document.getElementById('create-class-btn'),
            emptyCreateBtn: document.getElementById('empty-create-btn'),
            
            addClassModal: document.getElementById('add-class-modal'),
            editClassModal: document.getElementById('edit-class-modal'),
            showCodeModal: document.getElementById('show-code-modal'),
            
            addClassForm: document.getElementById('add-class-form'),
            addColorInput: document.getElementById('add-color-input'),
            addCancelBtn: document.getElementById('add-cancel-button'),
            
            editClassForm: document.getElementById('edit-class-form'),
            editCourseName: document.getElementById('edit-course-name'),
            editColorInput: document.getElementById('edit-color-input'),
            editCancelBtn: document.getElementById('edit-cancel-button'),
            
            generatedCode: document.querySelector('#generated-class-code span'),
            closeCodeBtn: document.getElementById('close-code-modal-button')
        };
    },

    bindEvents() {
        // Prevent multiple bindings
        if (this.state.isInitialized) return;

        this.elements.loginForm?.addEventListener('submit', (e) => this.handleLogin(e));
        
        // Add register form listener
        const registerForm = document.getElementById('register-form');
        registerForm?.addEventListener('submit', (e) => this.handleRegister(e));
        
        const openAddModal = (e) => { e?.preventDefault(); this.elements.addClassModal.classList.remove('hidden'); };
        this.elements.createClassBtn?.addEventListener('click', openAddModal);
        
        // Only allow teachers to open create class modal from empty state
        if (this.elements.emptyCreateBtn) {
            this.elements.emptyCreateBtn.addEventListener('click', (e) => {
                if (this.state.isTeacher) {
                    openAddModal(e);
                }
            });
        }
        
        this.elements.addCancelBtn?.addEventListener('click', () => this.elements.addClassModal.classList.add('hidden'));
        this.elements.editCancelBtn?.addEventListener('click', () => this.elements.editClassModal.classList.add('hidden'));
        this.elements.closeCodeBtn?.addEventListener('click', () => this.elements.showCodeModal.classList.add('hidden'));
        
        this.elements.addClassForm?.addEventListener('submit', (e) => this.handleCreateClass(e));
        this.elements.editClassForm?.addEventListener('submit', (e) => this.handleUpdateClass(e));
        this.elements.enrollForm?.addEventListener('submit', (e) => this.handleEnroll(e));
        
        // Click-away listener to finish sorting session
        document.addEventListener('mousedown', (e) => {
            if (this.state.isEditingOrder) {
                const grid = this.elements.classGrid;
                const manualBtn = document.getElementById('sort-manual');
                // If click is outside grid AND outside manual sort button, finish session
                if (grid && !grid.contains(e.target) && manualBtn && !manualBtn.contains(e.target)) {
                    this.finishSorting();
                }
            }
        });

        // Archive button handler - show modal with class selection for teachers
        document.querySelectorAll('.archive-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                this.showArchiveClassModal();
            });
        });
    },

    async showArchiveClassModal() {
        const modal = document.getElementById('archive-select-modal');
        const classList = document.getElementById('archive-class-list');

        if (!modal || !classList) return;

        // Show loading state
        classList.innerHTML = `
            <div class="flex items-center justify-center py-8">
                <svg class="animate-spin h-8 w-8 text-amber-600" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
            </div>
        `;

        modal.classList.remove('hidden');

        try {
            const res = await fetch('/api/courses');
            const data = await res.json();

            if (data.success && data.courses && data.courses.length > 0) {
                classList.innerHTML = data.courses.map(course => `
                    <a href="/kelas/${course.id}/arsip" class="block px-5 py-4 bg-gray-50 hover:bg-amber-50 border border-gray-100 hover:border-amber-200 rounded-2xl transition-all group">
                        <div class="flex items-center gap-3">
                            <div class="w-10 h-10 rounded-xl flex items-center justify-center text-lg" style="background-color: ${course.color}20; color: ${course.color}">
                                📚
                            </div>
                            <div class="flex-1">
                                <h4 class="font-bold text-gray-900 group-hover:text-amber-700 transition-colors">${course.name}</h4>
                                <p class="text-xs text-gray-500">${course.teacher_name || 'Guru'}</p>
                            </div>
                            <svg class="w-5 h-5 text-gray-400 group-hover:text-amber-600 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                            </svg>
                        </div>
                    </a>
                `).join('');
            } else {
                classList.innerHTML = `
                    <div class="text-center py-8">
                        <div class="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-3">
                            <svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/>
                            </svg>
                        </div>
                        <p class="text-gray-600 font-bold text-sm">Belum ada kelas</p>
                        <p class="text-gray-400 text-xs mt-1">Buat kelas terlebih dahulu</p>
                    </div>
                `;
            }
        } catch (error) {
            console.error('Error loading courses:', error);
            classList.innerHTML = `
                <div class="text-center py-8">
                    <p class="text-red-600 font-bold text-sm">Gagal memuat daftar kelas</p>
                    <p class="text-gray-400 text-xs mt-1">Silakan coba lagi</p>
                </div>
            `;
        }
    },

    async checkAuth() {
        try {
            const res = await fetch('/api/session');
            const data = await res.json();
            if (data.isAuthenticated) {
                if (data.user.role === 'super_admin') {
                    window.location.href = '/superadmin/dashboard';
                    return;
                }
                this.state.currentUser = data.user;
                // Fix: Check role correctly - 'guru' and 'admin' are teachers
                this.state.isTeacher = data.user.role === 'guru' || data.user.role === 'admin';
                this.setupUI();
                await this.loadInitialData();
            } else {
                this.elements.loginPage?.classList.remove('hidden');
                this.elements.appPage?.classList.add('hidden');
            }
        } catch (err) { console.error('Auth check failed', err); }
    },

    async loadSchoolsDropdown() {
        const select = document.getElementById('register-school');
        if (!select) return;

        try {
            const res = await fetch('/api/schools');
            const data = await res.json();
            if (data.success) {
                select.innerHTML = '<option value="">Pilih sekolah Anda...</option>';
                data.schools.forEach(school => {
                    const option = document.createElement('option');
                    option.value = school.id;
                    option.textContent = school.name;
                    select.appendChild(option);
                });
            }
        } catch (err) {
            console.error('Failed to load schools:', err);
        }
    },

    setupUI() {
        if (!this.elements.appPage) return;
        this.elements.loginPage?.classList.add('hidden');
        this.elements.appPage.classList.remove('hidden');
        
        // Trigger Entrance Animations
        const sidebar = this.elements.appPage.querySelector('aside');
        const mainContent = this.elements.appPage.querySelector('main');
        const header = this.elements.appPage.querySelector('header');
        
        if (sidebar) sidebar.classList.add('animate-slide-right-premium');
        if (mainContent) mainContent.classList.add('animate-premium-entrance', 'delay-200');
        if (header) header.classList.add('animate-premium-entrance', 'delay-100');

        const user = this.state.currentUser;
        if (this.elements.userNameSidebar) this.elements.userNameSidebar.textContent = user.name;
        if (this.elements.welcomeTitle) this.elements.welcomeTitle.textContent = `Selamat Datang, ${user.name.split(' ')[0]}!`;
        
        if (this.state.isTeacher) {
            this.elements.teacherNav?.classList.remove('hidden');
            this.elements.createClassBtn?.classList.remove('hidden');
            this.elements.enrollSection?.classList.add('hidden');
        } else {
            this.elements.enrollSection?.classList.remove('hidden');
            // Hide create buttons for students (murid)
            this.elements.createClassBtn?.classList.add('hidden');
        }
    },

    async loadInitialData() {
        try {
            this.elements.classGrid.innerHTML = '';
            this.elements.classSkeleton?.classList.remove('hidden');
            
            const res = await fetch('/api/initial-data');
            const data = await res.json();
            this.state.selectedYearId = data.currentYearId;
            this.state.courses = data.courses;
            this.renderCourses();
            this.updateStats();
        } catch (err) { console.error('Load initial data failed', err); }
        finally { this.elements.classSkeleton?.classList.add('hidden'); }
    },

    renderCourses() {
        // Filter out courses that are pending deletion
        const pendingIds = Object.keys(this.state.pendingDeletes).map(id => parseInt(id));
        let courses = [...this.state.courses.filter(c => !pendingIds.includes(c.id))];
        
        // Apply Sorting
        if (this.state.sortMode === 'asc') {
            courses.sort((a, b) => a.name.localeCompare(b.name));
        } else if (this.state.sortMode === 'desc') {
            courses.sort((a, b) => b.name.localeCompare(a.name));
        }
        
        const updateDOM = () => {
            // Update grid class for wiggle animation
            if (this.state.sortMode === 'manual' && this.state.isEditingOrder) {
                this.elements.classGrid?.classList.add('is-manual-sorting');
            } else {
                this.elements.classGrid?.classList.remove('is-manual-sorting');
            }

            if (courses.length === 0) {
                this.elements.emptyState?.classList.remove('hidden');
                // Hide create button in empty state for students
                if (!this.state.isTeacher && this.elements.emptyCreateBtn) {
                    this.elements.emptyCreateBtn.classList.add('hidden');
                } else if (this.elements.emptyCreateBtn) {
                    this.elements.emptyCreateBtn.classList.remove('hidden');
                }
                this.elements.classGrid.innerHTML = '';
                return;
            }
            this.elements.emptyState?.classList.add('hidden');

            this.elements.classGrid.innerHTML = DOMPurify.sanitize(courses.map(c => `
                <div data-id="${c.id}" style="view-transition-name: course-${c.id}" class="card-duo group overflow-hidden flex flex-col h-full transform transition-all duration-300">
                    <div class="h-40 relative overflow-hidden flex items-center justify-center p-8 -m-6 mb-6" style="background-color: ${c.color || '#0284c7'}">
                        <div class="absolute inset-0 opacity-20">
                            <svg class="w-full h-full" fill="currentColor" viewBox="0 0 100 100" preserveAspectRatio="none"><path d="M0 100 C 20 0 50 0 100 100 Z" /></svg>
                        </div>
                        <h3 class="relative z-10 text-2xl font-black text-white text-center leading-tight drop-shadow-md">${escapeHtml(c.name)}</h3>
                    </div>
                    <div class="flex-1 flex flex-col space-y-6">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center space-x-3">
                                <div class="w-10 h-10 rounded-xl bg-[#f7f7f7] flex items-center justify-center text-[#afafaf] group-hover:text-[#1cb0f6] transition-all"><svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/></svg></div>
                                <div class="min-w-0"><p class="text-[10px] font-black text-[#afafaf] uppercase tracking-widest leading-none mb-1">Pengajar</p><p class="text-sm font-black text-[#4b4b4b] truncate">${escapeHtml(c.teacher.name)}</p></div>
                            </div>
                            <div class="px-4 py-2 bg-[#dcfce7] text-[#58cc02] rounded-xl text-[10px] font-black uppercase tracking-widest border-2 border-[#e5e5e5]/10">${c.studentCount} Murid</div>
                        </div>
                        <div class="flex items-center p-4 bg-[#f7f7f7] rounded-xl border-2 border-[#e5e5e5]">
                            <div class="w-8 h-8 rounded-lg bg-white flex items-center justify-center shadow-sm mr-3 text-[#1cb0f6]"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"/></svg></div>
                            <div><p class="text-[10px] font-black text-[#afafaf] uppercase tracking-widest leading-none mb-1">Kode Akses</p><p class="text-sm font-black text-[#1cb0f6] tracking-widest font-mono">${escapeHtml(c.classCode)}</p></div>
                        </div>
                        <div class="mt-auto flex items-center gap-3 pt-4 border-t-2 border-[#f7f7f7]">
                            <a href="/kelas/${c.id}" class="btn-duo btn-duo-blue flex-1 h-12 text-sm">BUKA KELAS</a>
                            <button type="button" onclick="event.preventDefault(); Dashboard.copyCode(event, '${c.classCode}')" class="btn-duo btn-duo-ghost w-12 h-12 p-0"><svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m-7 10h7m-7-4h7"/></svg></button>
                        </div>
                    </div>
                </div>
            `).join(''), { ADD_ATTR: ['style', 'data-id', 'view-transition-name'] });

            this.initSortable();
        };

        // iPhone-style dynamic transition
        if (document.startViewTransition) {
            document.startViewTransition(() => updateDOM());
        } else {
            updateDOM();
        }
    },

    initSortable() {
        if (!this.elements.classGrid || typeof Sortable === 'undefined') return;
        
        if (this.sortableInstance) {
            this.sortableInstance.destroy();
            this.sortableInstance = null;
        }

        // Only enable Sortable if sortMode is 'manual' AND isEditingOrder is true
        if (this.state.sortMode !== 'manual' || !this.state.isEditingOrder) return;

        this.sortableInstance = new Sortable(this.elements.classGrid, {
            animation: 350, // Smoother animation like iOS
            easing: "cubic-bezier(0.16, 1, 0.3, 1)", // Premium snappy feel
            ghostClass: 'sortable-ghost',
            chosenClass: 'sortable-chosen',
            dragClass: 'sortable-drag',
            forceFallback: false,
            onStart: () => {
                this.elements.classGrid.classList.add('is-dragging');
            },
            onEnd: () => {
                this.elements.classGrid.classList.remove('is-dragging');
                this.handleReorder();
            }
        });
    },

    async handleReorder() {
        const itemIds = Array.from(this.elements.classGrid.querySelectorAll('[data-id]'))
            .map(el => parseInt(el.getAttribute('data-id')));
        
        try {
            const res = await fetch('/api/courses/reorder', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ course_ids: itemIds })
            });
            const data = await res.json();
            if (!data.success) {
                console.error('Reorder failed:', data.message);
                await this.loadInitialData(); // Revert to server state
            }
        } catch (err) {
            console.error('Reorder error:', err);
            await this.loadInitialData(); // Revert to server state
        }
    },

    updateStats() {
        if (this.elements.totalClasses) this.elements.totalClasses.textContent = this.state.courses.length;
        if (this.elements.totalStudents) this.elements.totalStudents.textContent = this.state.courses.reduce((acc, c) => acc + c.studentCount, 0);
    },
};

// Close archive modal function (global)
function closeArchiveModal() {
    const modal = document.getElementById('archive-select-modal');
    if (modal) {
        modal.classList.add('hidden');
    }
}
