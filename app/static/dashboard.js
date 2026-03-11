/**
 * Aldudu Academy - Dashboard JavaScript
 * Robust initialization for stable navigation
 */

const Dashboard = {
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
        console.log('Dashboard: Initializing...');
        this.cacheElements();
        
        // If elements don't exist (not on dashboard page), stop
        if (!this.elements.classGrid) return;

        this.bindEvents();
        await this.checkAuth();
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
            deleteClassModal: document.getElementById('delete-class-modal'),
            
            addClassForm: document.getElementById('add-class-form'),
            addColorInput: document.getElementById('add-color-input'),
            addCancelBtn: document.getElementById('add-cancel-button'),
            
            editClassForm: document.getElementById('edit-class-form'),
            editCourseName: document.getElementById('edit-course-name'),
            editColorInput: document.getElementById('edit-color-input'),
            editCancelBtn: document.getElementById('edit-cancel-button'),
            
            deleteConfirmInput: document.getElementById('delete-confirm-input'),
            deleteFinalBtn: document.getElementById('delete-final-btn'),
            deleteCancelBtn: document.getElementById('delete-cancel-btn'),
            deleteModalError: document.getElementById('delete-modal-error'),
            
            generatedCode: document.querySelector('#generated-class-code span'),
            closeCodeBtn: document.getElementById('close-code-modal-button'),

            deleteToastContainer: document.getElementById('delete-toast-container')
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
        this.elements.emptyCreateBtn?.addEventListener('click', openAddModal);
        
        this.elements.addCancelBtn?.addEventListener('click', () => this.elements.addClassModal.classList.add('hidden'));
        this.elements.editCancelBtn?.addEventListener('click', () => this.elements.editClassModal.classList.add('hidden'));
        this.elements.deleteCancelBtn?.addEventListener('click', () => this.elements.deleteClassModal.classList.add('hidden'));
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
        
        this.elements.deleteConfirmInput?.addEventListener('input', (e) => {
            const isValid = e.target.value.toLowerCase().trim() === 'setuju';
            this.elements.deleteFinalBtn.disabled = !isValid;
            this.elements.deleteFinalBtn.classList.toggle('opacity-50', !isValid);
            this.elements.deleteFinalBtn.classList.toggle('cursor-not-allowed', !isValid);
        });
        
        this.elements.deleteFinalBtn?.addEventListener('click', () => this.handleDeleteClass());
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
                this.state.isTeacher = data.user.role === 'guru';
                this.setupUI();
                await this.loadInitialData();
            } else {
                this.elements.loginPage?.classList.remove('hidden');
                this.elements.appPage?.classList.add('hidden');
            }
        } catch (err) { console.error('Auth check failed', err); }
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
                this.elements.classGrid.innerHTML = '';
                return;
            }
            this.elements.emptyState?.classList.add('hidden');
            
            this.elements.classGrid.innerHTML = courses.map(c => `
                <div data-id="${c.id}" style="view-transition-name: course-${c.id}" class="group bg-white rounded-[2.5rem] border border-gray-100 shadow-premium hover:shadow-2xl transition-all duration-500 overflow-hidden flex flex-col h-full transform hover:-translate-y-3">
                    <div class="h-40 relative overflow-hidden flex items-center justify-center p-8" style="background-color: ${c.color || '#0284c7'}">
                        <div class="absolute inset-0 opacity-20 group-hover:scale-150 transition-transform duration-1000 ease-in-out">
                            <svg class="w-full h-full" fill="currentColor" viewBox="0 0 100 100" preserveAspectRatio="none"><path d="M0 100 C 20 0 50 0 100 100 Z" /></svg>
                        </div>
                        <h3 class="relative z-10 text-2xl font-black text-white text-center leading-tight drop-shadow-md group-hover:scale-105 transition-transform duration-500">${c.name}</h3>
                        ${this.state.isTeacher ? `<button type="button" onclick="event.preventDefault(); Dashboard.openEditClass(${c.id})" class="absolute top-5 right-5 p-2.5 bg-white/20 hover:bg-white text-white hover:text-gray-900 rounded-2xl backdrop-blur-md shadow-lg transition-all duration-300 z-20"><svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg></button>` : ''}
                    </div>
                    <div class="p-10 flex-1 flex flex-col space-y-8">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center space-x-4">
                                <div class="w-12 h-12 rounded-2xl bg-primary-50 flex items-center justify-center text-primary-600 group-hover:bg-primary-600 group-hover:text-white transition-all duration-500"><svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/></svg></div>
                                <div class="min-w-0"><p class="text-[10px] font-black text-gray-400 uppercase tracking-widest leading-none mb-1.5">Pengajar</p><p class="text-sm font-bold text-gray-700 truncate">${c.teacher.name}</p></div>
                            </div>
                            <div class="px-5 py-2.5 bg-green-50 text-green-600 rounded-2xl text-[11px] font-black uppercase tracking-widest border border-green-100/50 shadow-sm">${c.studentCount} Murid</div>
                        </div>
                        <div class="flex items-center p-5 bg-gray-50/50 rounded-2xl border border-gray-100 group-hover:border-primary-100 transition-all duration-500">
                            <div class="w-10 h-10 rounded-xl bg-white flex items-center justify-center shadow-sm mr-4"><svg class="w-5 h-5 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"/></svg></div>
                            <div><p class="text-[10px] font-black text-gray-400 uppercase tracking-widest leading-none mb-1.5">Kode Akses</p><p class="text-base font-mono font-black text-primary-600">${c.classCode}</p></div>
                        </div>
                        <div class="mt-auto flex items-center space-x-4 pt-6 border-t border-gray-50">
                            <a href="/kelas/${c.id}" class="flex-1 bg-gradient-to-r from-primary-600 to-primary-700 hover:from-primary-700 hover:to-primary-800 text-white py-5 rounded-[1.75rem] text-center font-bold text-sm transition-all shadow-xl shadow-primary-200 active:scale-95 btn-shine">Buka Kelas</a>
                            <button type="button" onclick="event.preventDefault(); Dashboard.copyCode('${c.classCode}')" class="p-5 bg-gray-100 hover:bg-gray-200 text-gray-500 hover:text-primary-600 rounded-[1.75rem] transition-all active:scale-90 group/btn"><svg class="w-6 h-6 transition-transform group-hover/btn:rotate-12" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m-7 10h7m-7-4h7"/></svg></button>
                        </div>
                    </div>
                </div>
            `).join('');

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

    async handleLogin(e) {
        e.preventDefault();
        const btn = document.getElementById('login-btn');
        const btnText = btn?.querySelector('.btn-text');
        const loader = btn?.querySelector('.loader-container');
        const errorDiv = this.elements.loginError;
        
        if (btn) btn.disabled = true;
        if (btnText) btnText.classList.add('opacity-0', 'translate-y-2');
        if (loader) loader.classList.remove('hidden');
        if (errorDiv) errorDiv.classList.add('hidden');

        try {
            const res = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email: e.target.email.value, password: e.target.password.value })
            });
            const data = await res.json();
            
            if (data.success) {
                if (btn) btn.classList.add('bg-green-600', 'scale-95');
                setTimeout(() => {
                    if (data.redirect) {
                        window.location.href = data.redirect;
                    } else {
                        window.location.reload();
                    }
                }, 600);
            } else {
                throw new Error(data.message || 'Email atau password salah');
            }
        } catch (err) {
            console.error('Login error', err);
            
            if (btn) {
                btn.disabled = false;
                btn.classList.add('animate-bounce', 'border-red-500');
                setTimeout(() => btn.classList.remove('animate-bounce'), 500);
            }
            if (btnText) btnText.classList.remove('opacity-0', 'translate-y-2');
            if (loader) loader.classList.add('hidden');

            if (errorDiv) {
                errorDiv.innerHTML = `
                    <div class="flex items-center space-x-3 animate-slide-up p-1">
                        <div class="flex-shrink-0 w-8 h-8 bg-red-100 text-red-600 rounded-xl flex items-center justify-center shadow-sm">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
                        </div>
                        <div class="flex-1 font-bold text-red-800 text-xs">${err.message}</div>
                    </div>
                `;
                errorDiv.classList.remove('hidden');
                errorDiv.className = "p-4 bg-red-50/80 backdrop-blur-md border border-red-100 rounded-2xl mt-4 shadow-xl shadow-red-200/20 ring-1 ring-red-200";
            }
        }
    },

    async handleLogout() {
        await fetch('/api/logout', { method: 'POST' });
        window.location.reload();
    },

    async handleRegister(e) {
        e.preventDefault();
        const errorDiv = document.getElementById('register-error');
        const submitBtn = e.target.querySelector('button[type="submit"]');
        
        submitBtn.disabled = true;
        submitBtn.innerText = 'Mendaftar...';
        errorDiv.classList.add('hidden');

        const payload = {
            name: e.target.name.value,
            email: e.target.email.value,
            password: e.target.password.value,
            role: e.target.role.value
        };

        try {
            const res = await fetch('/admin/api/users', { // Use same endpoint as admin for now
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            if (data.success) {
                alert('Pendaftaran berhasil! Silakan login.');
                window.toggleAuthMode(null, 'login');
            } else {
                errorDiv.textContent = data.message;
                errorDiv.classList.remove('hidden');
            }
        } catch (err) {
            errorDiv.textContent = 'Gagal mendaftar. Coba lagi.';
            errorDiv.classList.remove('hidden');
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerText = 'Daftar Akun';
        }
    },

    async handleCreateClass(e) {
        e.preventDefault();
        try {
            const res = await fetch('/api/courses', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    name: e.target['course-name'].value, 
                    academic_year_id: this.state.selectedYearId,
                    color: this.elements.addColorInput.value
                })
            });
            const data = await res.json();
            if (data.success) {
                this.elements.addClassModal.classList.add('hidden');
                e.target.reset();
                this.elements.generatedCode.textContent = data.course.classCode;
                this.elements.showCodeModal.classList.remove('hidden');
                await this.loadInitialData();
            }
        } catch (err) { console.error('Create error', err); }
    },

    openEditClass(id) {
        const course = this.state.courses.find(c => c.id === id);
        if (!course) return;
        this.state.editingCourseId = id;
        this.elements.editCourseName.value = course.name;
        this.elements.editColorInput.value = course.color || '#0284c7';
        this.elements.editClassModal.classList.remove('hidden');
    },

    async handleUpdateClass(e) {
        e.preventDefault();
        try {
            const res = await fetch(`/api/courses/${this.state.editingCourseId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: this.elements.editCourseName.value, color: this.elements.editColorInput.value })
            });
            if (res.ok) { this.elements.editClassModal.classList.add('hidden'); await this.loadInitialData(); }
        } catch (err) { console.error('Update error', err); }
    },

    openDeleteModal() {
        this.elements.editClassModal.classList.add('hidden');
        this.elements.deleteConfirmInput.value = '';
        this.elements.deleteFinalBtn.disabled = true;
        this.elements.deleteFinalBtn.classList.add('opacity-50', 'cursor-not-allowed');
        this.elements.deleteClassModal.classList.remove('hidden');
    },

    async handleDeleteClass() {
        if (this.elements.deleteConfirmInput.value.toLowerCase().trim() !== 'setuju') return;
        
        const courseId = this.state.editingCourseId;
        const course = this.state.courses.find(c => c.id === courseId);
        if (!course) return;

        // Visual feedback on button
        this.elements.deleteFinalBtn.disabled = true;
        this.elements.deleteFinalBtn.innerHTML = `
            <svg class="animate-spin h-5 w-5 mr-3 inline text-white" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Memproses...
        `;

        // 1. Close Modal
        this.elements.deleteClassModal.classList.add('hidden');
        
        // 2. Hide from UI immediately
        this.state.pendingDeletes[courseId] = {
            courseData: course,
            timeout: setTimeout(() => this.finalizeDeletion(courseId), 30000)
        };
        this.renderCourses();
        this.updateStats();

        // 3. Show Undo Toast
        this.showUndoToast(courseId, course.name);
        
        // Reset button state for next time
        this.elements.deleteFinalBtn.innerHTML = 'Hapus Sekarang';
        this.elements.deleteFinalBtn.disabled = true;
    },

    showUndoToast(courseId, courseName) {
        const toastId = `toast-${courseId}`;
        const toast = document.createElement('div');
        toast.id = toastId;
        toast.className = 'pointer-events-auto bg-gray-900/95 backdrop-blur-xl text-white p-8 rounded-[2.5rem] shadow-2xl border border-white/10 flex flex-col space-y-6 min-w-[480px] animate-slide-up-premium';
        
        toast.innerHTML = `
            <div class="flex items-center justify-between">
                <div class="flex items-center space-x-5 min-w-0">
                    <div class="relative flex-shrink-0">
                        <div class="w-14 h-14 bg-red-500/20 text-red-400 rounded-2xl flex items-center justify-center border border-red-500/20">
                            <svg class="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                        </div>
                        <div class="absolute -top-2 -right-2 w-8 h-8 bg-primary-600 rounded-full border-4 border-gray-900 flex items-center justify-center shadow-lg">
                            <span id="countdown-${courseId}" class="text-[10px] font-black text-white">30</span>
                        </div>
                    </div>
                    <div class="min-w-0">
                        <p class="text-base font-black tracking-tight leading-none mb-1 truncate">Kelas Berhasil Dihapus</p>
                        <p class="text-[10px] text-gray-500 font-black uppercase tracking-[0.2em] truncate">${courseName}</p>
                    </div>
                </div>
                <button onclick="Dashboard.undoDelete(${courseId})" class="flex-shrink-0 ml-6 text-primary-500 hover:text-white font-black text-[11px] uppercase tracking-[0.25em] transition-all active:scale-90 underline underline-offset-8 decoration-2 decoration-primary-500/30 hover:decoration-white">
                    Batal
                </button>
            </div>
            <div class="space-y-3">
                <div class="flex justify-between items-center text-[9px] font-black uppercase tracking-[0.2em] text-gray-500 px-1">
                    <span class="flex items-center"><span class="w-1 h-1 bg-red-500 rounded-full mr-2 animate-pulse"></span>Proses Penghapusan Permanen</span>
                    <span id="time-text-${courseId}" class="text-primary-500">30 Detik Tersisa</span>
                </div>
                <div class="h-1.5 bg-white/5 rounded-full overflow-hidden border border-white/5">
                    <div id="progress-${courseId}" class="h-full bg-gradient-to-r from-primary-600 to-primary-400 rounded-full transition-all duration-100 ease-linear shadow-[0_0_15px_rgba(59,130,246,0.3)]" style="width: 100%"></div>
                </div>
            </div>
        `;

        this.elements.deleteToastContainer.appendChild(toast);

        // Progress bar and countdown animation
        let timeLeft = 30000;
        const interval = 100;
        const progressBar = document.getElementById(`progress-${courseId}`);
        const countdownEl = document.getElementById(`countdown-${courseId}`);
        const timeTextEl = document.getElementById(`time-text-${courseId}`);
        
        const timer = setInterval(() => {
            timeLeft -= interval;
            const secondsLeft = Math.ceil(timeLeft / 1000);
            
            if (countdownEl) countdownEl.textContent = secondsLeft > 0 ? secondsLeft : 0;
            if (timeTextEl) timeTextEl.textContent = `${secondsLeft > 0 ? secondsLeft : 0} Detik Tersisa`;

            if (timeLeft <= 0) {
                clearInterval(timer);
                if (progressBar) progressBar.style.width = '0%';
            } else {
                if (progressBar) progressBar.style.width = `${(timeLeft / 30000) * 100}%`;
            }
        }, interval);
    },

    undoDelete(courseId) {
        const pending = this.state.pendingDeletes[courseId];
        if (!pending) return;

        // Clear timeout
        clearTimeout(pending.timeout);
        
        // Remove from pending
        delete this.state.pendingDeletes[courseId];
        
        // Remove Toast
        const toast = document.getElementById(`toast-${courseId}`);
        if (toast) {
            toast.classList.add('animate-slide-down-premium', 'opacity-0');
            setTimeout(() => toast.remove(), 500);
        }

        // Restore UI
        this.renderCourses();
        this.updateStats();
        
        // Success feedback
        const undoNotice = document.createElement('div');
        undoNotice.className = 'fixed top-8 left-1/2 -translate-x-1/2 z-[200] bg-green-600 text-white px-8 py-4 rounded-2xl font-black text-sm shadow-2xl animate-toast-float';
        undoNotice.textContent = 'Penghapusan Kelas Dibatalkan';
        document.body.appendChild(undoNotice);
        setTimeout(() => undoNotice.remove(), 3000);
    },

    async finalizeDeletion(courseId) {
        try {
            const res = await fetch(`/api/courses/${courseId}`, { method: 'DELETE' });
            if (res.ok) {
                // Remove from pending and permanent state
                delete this.state.pendingDeletes[courseId];
                this.state.courses = this.state.courses.filter(c => c.id !== courseId);
                
                // Final Toast Removal
                const toast = document.getElementById(`toast-${courseId}`);
                if (toast) {
                    toast.classList.add('opacity-0', 'scale-95');
                    setTimeout(() => toast.remove(), 500);
                }
                
                this.updateStats();
            } else {
                const data = await res.json();
                throw new Error(data.message || 'Gagal menghapus kelas');
            }
        } catch (err) {
            console.error('Finalize deletion failed', err);
            // Restore on failure
            this.undoDelete(courseId);
            alert(`Gagal menghapus kelas: ${err.message}. Data telah dipulihkan.`);
        }
    },

    async handleEnroll(e) {
        e.preventDefault();
        try {
            const res = await fetch('/api/enroll', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ class_code: e.target['class-code-input'].value })
            });
            const data = await res.json();
            if (data.success) { e.target.reset(); await this.loadInitialData(); alert('Berhasil bergabung!'); }
            else { alert(data.message); }
        } catch (err) { console.error('Enroll error', err); }
    },

    setSortMode(mode) {
        if (mode === 'manual') {
            // Toggle editing state if already in manual mode, or enter manual mode
            if (this.state.sortMode === 'manual') {
                this.state.isEditingOrder = !this.state.isEditingOrder;
            } else {
                this.state.sortMode = 'manual';
                this.state.isEditingOrder = true;
            }
            localStorage.setItem('courseSortMode', 'manual');
        } else {
            this.state.sortMode = mode;
            this.state.isEditingOrder = false;
            localStorage.setItem('courseSortMode', mode);
        }
        this.updateSortButtons();
        this.renderCourses();
    },

    finishSorting() {
        if (this.state.isEditingOrder) {
            this.state.isEditingOrder = false;
            this.updateSortButtons();
            this.renderCourses();
            
            // Subtle status hint
            this.showStatusHint('Urutan manual disimpan');
        }
    },

    showStatusHint(message) {
        const hint = document.createElement('div');
        hint.className = 'fixed bottom-12 left-1/2 -translate-x-1/2 bg-gray-900/90 backdrop-blur-xl text-white px-6 py-3.5 rounded-2xl text-[11px] font-black uppercase tracking-[0.2em] shadow-2xl animate-premium-entrance z-[100] border border-white/10 flex items-center space-x-3 pointer-events-none';
        hint.innerHTML = `
            <div class="w-5 h-5 bg-green-500 rounded-lg flex items-center justify-center">
                <svg class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="4" d="M5 13l4 4L19 7"/></svg>
            </div>
            <span>${message}</span>
        `;
        document.body.appendChild(hint);
        setTimeout(() => {
            hint.classList.add('opacity-0', 'translate-y-4');
            hint.style.transition = 'all 0.6s cubic-bezier(0.16, 1, 0.3, 1)';
            setTimeout(() => hint.remove(), 600);
        }, 2500);
    },

    updateSortButtons() {
        const buttons = document.querySelectorAll('.sort-btn');
        buttons.forEach(btn => {
            const mode = btn.id.replace('sort-', '');
            const manualIcon = `<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M4 6h16M4 12h16M4 18h16"/></svg>`;
            const checkIcon = `<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"/></svg>`;

            if (mode === this.state.sortMode) {
                btn.classList.add('bg-primary-600', 'text-white', 'shadow-lg', 'shadow-primary-100');
                btn.classList.remove('text-gray-400', 'hover:text-gray-600');
                
                if (mode === 'manual') {
                    if (this.state.isEditingOrder) {
                        btn.innerHTML = `${checkIcon}<span class="hidden md:inline">Selesai</span>`;
                        btn.classList.add('animate-pulse');
                        btn.title = "Selesai Mengurutkan";
                    } else {
                        btn.innerHTML = `${manualIcon}<span class="hidden md:inline">Manual</span>`;
                        btn.classList.remove('animate-pulse');
                        btn.title = "Urutan Manual (Drag & Drop)";
                    }
                }
            } else {
                btn.classList.remove('bg-primary-600', 'text-white', 'shadow-lg', 'shadow-primary-100', 'animate-pulse');
                btn.classList.add('text-gray-400', 'hover:text-gray-600');
                
                if (mode === 'manual') {
                    btn.innerHTML = `${manualIcon}<span class="hidden md:inline">Manual</span>`;
                    btn.title = "Urutan Manual (Drag & Drop)";
                }
            }
        });
    },

    copyCode(code) {
        navigator.clipboard.writeText(code).then(() => {
            // Find the button that was clicked
            const btns = document.querySelectorAll('button');
            let targetBtn = null;
            btns.forEach(b => {
                if (b.getAttribute('onclick')?.includes(code)) targetBtn = b;
            });

            if (targetBtn) {
                // Icon Success Animation
                const originalHTML = targetBtn.innerHTML;
                targetBtn.innerHTML = `
                    <svg class="w-6 h-6 text-green-600 animate-success-pop" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                    </svg>
                `;
                targetBtn.classList.add('bg-green-50', 'ring-2', 'ring-green-500', 'ring-offset-2');
                
                // Floating Toast Notification
                const toast = document.createElement('div');
                toast.className = 'fixed z-[100] bg-gray-900 text-white px-6 py-3 rounded-2xl font-bold text-sm shadow-2xl animate-toast-float flex items-center space-x-3';
                toast.innerHTML = `
                    <div class="w-6 h-6 bg-green-500 rounded-lg flex items-center justify-center">
                        <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
                    </div>
                    <span>Kode Kelas Berhasil Disalin</span>
                `;
                
                // Position toast near the button
                const rect = targetBtn.getBoundingClientRect();
                toast.style.top = `${rect.top - 60}px`;
                toast.style.left = `${rect.left + (rect.width/2) - 100}px`;
                
                document.body.appendChild(toast);
                
                setTimeout(() => {
                    targetBtn.innerHTML = originalHTML;
                    targetBtn.classList.remove('bg-green-50', 'ring-2', 'ring-green-500', 'ring-offset-2');
                    toast.remove();
                }, 2000);
            }
        });
    }
};

window.toggleAuthMode = function(e, mode) {
    if (e) e.preventDefault();
    const loginCard = document.getElementById('login-card');
    const registerCard = document.getElementById('register-card');
    
    if (mode === 'register') {
        loginCard.classList.add('hidden');
        registerCard.classList.remove('hidden');
    } else {
        registerCard.classList.add('hidden');
        loginCard.classList.remove('hidden');
    }
}

// Initial run
document.addEventListener('DOMContentLoaded', () => Dashboard.init());
