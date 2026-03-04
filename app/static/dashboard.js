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
        isInitialized: false
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
            
            generatedCode: document.querySelector('#generated-class-code span'),
            closeCodeBtn: document.getElementById('close-code-modal-button')
        };
    },

    bindEvents() {
        // Prevent multiple bindings
        if (this.state.isInitialized) return;

        this.elements.loginForm?.addEventListener('submit', (e) => this.handleLogin(e));
        
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
        const courses = this.state.courses;
        if (courses.length === 0) {
            this.elements.emptyState?.classList.remove('hidden');
            return;
        }
        this.elements.emptyState?.classList.add('hidden');
        
        this.elements.classGrid.innerHTML = courses.map(c => `
            <div class="group bg-white rounded-[2.5rem] border border-gray-100 shadow-premium hover:shadow-2xl transition-all duration-500 overflow-hidden flex flex-col h-full transform hover:-translate-y-3">
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
    },

    updateStats() {
        if (this.elements.totalClasses) this.elements.totalClasses.textContent = this.state.courses.length;
        if (this.elements.totalStudents) this.elements.totalStudents.textContent = this.state.courses.reduce((acc, c) => acc + c.studentCount, 0);
    },

    async handleLogin(e) {
        e.preventDefault();
        try {
            const res = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email: e.target.email.value, password: e.target.password.value })
            });
            const data = await res.json();
            if (data.success) window.location.reload();
            else { this.elements.loginError.textContent = data.message; this.elements.loginError.classList.remove('hidden'); }
        } catch (err) { console.error('Login error', err); }
    },

    async handleLogout() {
        await fetch('/api/logout', { method: 'POST' });
        window.location.reload();
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
        try {
            const res = await fetch(`/api/courses/${this.state.editingCourseId}`, { method: 'DELETE' });
            if (res.ok) { this.elements.deleteClassModal.classList.add('hidden'); await this.loadInitialData(); }
        } catch (err) { console.error('Delete error', err); }
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

    copyCode(code) {
        navigator.clipboard.writeText(code);
        alert('Kode kelas disalin!');
    }
};

// Initial run
document.addEventListener('DOMContentLoaded', () => Dashboard.init());
