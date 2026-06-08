/**
 * Aldudu Academy - Dashboard JavaScript
 * Robust initialization for stable navigation
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
                        ${this.state.isTeacher ? `<button type="button" onclick="event.preventDefault(); Dashboard.openEditClass(${c.id})" class="absolute top-5 right-5 p-2.5 bg-white/20 hover:bg-white text-white hover:text-gray-900 rounded-2xl backdrop-blur-md shadow-lg transition-all duration-300 z-20"><svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg></button>` : ''}
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
                            <button type="button" onclick="event.preventDefault(); Dashboard.copyCode('${c.classCode}')" class="btn-duo btn-duo-ghost w-12 h-12 p-0"><svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m-7 10h7m-7-4h7"/></svg></button>
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
                // Specific field highlighting
                if (data.field === 'email') {
                    const emailInput = document.getElementById('email');
                    if (emailInput) {
                        emailInput.classList.add('border-red-500', 'ring-4', 'ring-red-100');
                        emailInput.focus();
                        emailInput.addEventListener('input', () => {
                            emailInput.classList.remove('border-red-500', 'ring-4', 'ring-red-100');
                        }, { once: true });
                    }
                } else if (data.field === 'password') {
                    const passwordInput = document.getElementById('password');
                    if (passwordInput) {
                        passwordInput.classList.add('border-red-500', 'ring-4', 'ring-red-100');
                        passwordInput.focus();
                        passwordInput.addEventListener('input', () => {
                            passwordInput.classList.remove('border-red-500', 'ring-4', 'ring-red-100');
                        }, { once: true });
                    }
                }
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

        const schoolId = e.target.school_id.value;
        if (!schoolId) {
            errorDiv.textContent = 'Pilih sekolah terlebih dahulu';
            errorDiv.classList.remove('hidden');
            submitBtn.disabled = false;
            submitBtn.innerText = 'Daftar Akun';
            return;
        }

        const payload = {
            name: e.target.name.value,
            email: e.target.email.value,
            password: e.target.password.value,
            role: e.target.role.value,
            school_id: parseInt(schoolId)
        };

        try {
            const res = await fetch('/api/register-user', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            if (data.success) {
                alert('Pendaftaran berhasil! Silakan cek email untuk verifikasi.');
                window.toggleAuthMode(null, 'login');
                e.target.reset();
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
        
        // Handle color dots
        const color = course.color || '#58cc02';
        this.elements.editColorInput.value = color;
        
        const dots = this.elements.editClassModal.querySelectorAll('.color-dot');
        dots.forEach(dot => {
            const isMatch = dot.getAttribute('data-color') === color;
            dot.classList.toggle('ring-2', isMatch);
            dot.classList.toggle('ring-[#1cb0f6]', isMatch);
            dot.classList.toggle('shadow-md', isMatch);
            dot.classList.toggle('shadow-sm', !isMatch);
        });
        
        this.elements.editClassModal.classList.remove('hidden');
    },

    selectColor(btn, color) {
        // Update hidden input
        const container = btn.parentElement;
        const input = container.querySelector('input[type="hidden"]');
        if (input) input.value = color;

        // Update visual selection
        container.querySelectorAll('.color-dot').forEach(dot => {
            dot.classList.remove('ring-2', 'ring-[#1cb0f6]', 'shadow-md');
            dot.classList.add('shadow-sm');
        });
        btn.classList.add('ring-2', 'ring-[#1cb0f6]', 'shadow-md');
        btn.classList.remove('shadow-sm');
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

// Close archive modal function (global)
function closeArchiveModal() {
    const modal = document.getElementById('archive-select-modal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

// Initial run
document.addEventListener('DOMContentLoaded', () => Dashboard.init());
