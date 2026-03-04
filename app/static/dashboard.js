/**
 * Aldudu Academy - Dashboard JavaScript
 * Handles all dashboard interactions
 */

document.addEventListener('DOMContentLoaded', function() {
  // Initialize dashboard
  Dashboard.init();
});

const Dashboard = {
  state: {
    currentUser: null,
    academicYears: [],
    courses: [],
    selectedYearId: null,
    isTeacher: false
  },

  // Initialize dashboard
  async init() {
    this.cacheElements();
    this.bindEvents();
    await this.checkAuth();
  },

  // Cache DOM elements
  cacheElements() {
    // Sections
    this.elements = {
      loginSection: document.getElementById('login-section'),
      dashboardWrapper: document.querySelector('.dashboard-wrapper'),
      
      // Forms
      loginForm: document.getElementById('login-form'),
      joinClassForm: document.getElementById('join-class-form'),
      createClassForm: document.getElementById('create-class-form'),
      editClassForm: document.getElementById('edit-class-form'),
      
      // Buttons
      logoutBtn: document.getElementById('logout-btn'),
      createClassBtn: document.getElementById('create-class-btn'),
      createFirstClassBtn: document.getElementById('create-first-class-btn'),
      saveClassBtn: document.getElementById('save-class'),
      saveEditBtn: document.getElementById('save-edit'),
      copyCodeBtn: document.getElementById('copy-code-btn'),
      
      // Modals
      createClassModal: document.getElementById('create-class-modal'),
      successModal: document.getElementById('success-modal'),
      editClassModal: document.getElementById('edit-class-modal'),
      
      // Modal close buttons
      closeCreateModal: document.getElementById('close-create-modal'),
      closeSuccessModal: document.getElementById('close-success-modal'),
      closeEditModal: document.getElementById('close-edit-modal'),
      cancelCreate: document.getElementById('cancel-create'),
      cancelEdit: document.getElementById('cancel-edit'),
      closeSuccess: document.getElementById('close-success'),
      
      // Inputs
      yearSelect: document.getElementById('year-select'),
      classCodeDisplay: document.getElementById('class-code-display'),
      classCode: document.getElementById('class-code'),
      copyFeedback: document.getElementById('copy-feedback'),
      
      // Color pickers
      classColorPicker: document.getElementById('class-color-picker'),
      editColorPicker: document.getElementById('edit-color-picker'),
      selectedColorInput: document.getElementById('selected-color'),
      editSelectedColorInput: document.getElementById('edit-selected-color'),
      
      // Edit inputs
      editClassId: document.getElementById('edit-class-id'),
      editClassName: document.getElementById('edit-class-name'),
      
      // Displays
      classesList: document.getElementById('classes-list'),
      emptyState: document.getElementById('empty-state'),
      totalClasses: document.getElementById('total-classes'),
      totalStudents: document.getElementById('total-students'),
      totalQuizzes: document.getElementById('total-quizzes'),
      activeYear: document.getElementById('active-year'),
      
      // User info
      userAvatar: document.querySelector('.user-avatar'),
      userName: document.querySelector('.user-name'),
      userRole: document.querySelector('.user-role')
    };
  },

  // Bind event listeners
  bindEvents() {
    // Auth
    this.elements.loginForm?.addEventListener('submit', (e) => this.handleLogin(e));
    this.elements.logoutBtn?.addEventListener('click', () => this.handleLogout());
    
    // Create class
    this.elements.createClassBtn?.addEventListener('click', () => this.openCreateModal());
    this.elements.createFirstClassBtn?.addEventListener('click', () => this.openCreateModal());
    this.elements.createClassForm?.addEventListener('submit', (e) => this.handleCreateClass(e));
    this.elements.closeCreateModal?.addEventListener('click', () => this.closeCreateModal());
    this.elements.cancelCreate?.addEventListener('click', () => this.closeCreateModal());
    
    // Edit class
    this.elements.editClassForm?.addEventListener('submit', (e) => this.handleEditClass(e));
    this.elements.closeEditModal?.addEventListener('click', () => this.closeEditModal());
    this.elements.cancelEdit?.addEventListener('click', () => this.closeEditModal());
    
    // Success modal
    this.elements.closeSuccessModal?.addEventListener('click', () => this.closeSuccessModal());
    this.elements.closeSuccess?.addEventListener('click', () => this.closeSuccessModal());
    this.elements.copyCodeBtn?.addEventListener('click', () => this.copyClassCode());
    this.elements.classCodeDisplay?.addEventListener('click', () => this.copyClassCode());
    
    // Join class
    this.elements.joinClassForm?.addEventListener('submit', (e) => this.handleJoinClass(e));
    
    // Year selector
    this.elements.yearSelect?.addEventListener('change', (e) => this.handleYearChange(e));
    
    // Color pickers
    this.setupColorPicker(this.elements.classColorPicker, this.elements.selectedColorInput);
    this.setupColorPicker(this.elements.editColorPicker, this.elements.editSelectedColorInput);
    
    // Close modals on overlay click
    this.elements.createClassModal?.querySelector('.modal-overlay')?.addEventListener('click', () => this.closeCreateModal());
    this.elements.successModal?.querySelector('.modal-overlay')?.addEventListener('click', () => this.closeSuccessModal());
    this.elements.editClassModal?.querySelector('.modal-overlay')?.addEventListener('click', () => this.closeEditModal());
  },

  // Check authentication status
  async checkAuth() {
    try {
      const response = await fetch('/api/session');
      const data = await response.json();
      
      if (data.isAuthenticated) {
        this.state.currentUser = data.user;
        this.state.isTeacher = data.user.role === 'GURU';
        this.showDashboard();
        await this.loadInitialData();
      } else {
        this.showLogin();
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      this.showLogin();
    }
  },

  // Show dashboard section
  showDashboard() {
    if (this.elements.loginSection) {
      this.elements.loginSection.classList.add('hidden');
    }
    if (this.elements.dashboardWrapper) {
      this.elements.dashboardWrapper.classList.remove('hidden');
    }
    
    // Update user info
    if (this.state.currentUser) {
      if (this.elements.userAvatar) {
        this.elements.userAvatar.textContent = this.state.currentUser.name.charAt(0).toUpperCase();
      }
      if (this.elements.userName) {
        this.elements.userName.textContent = this.state.currentUser.name;
      }
      if (this.elements.userRole) {
        this.elements.userRole.textContent = this.state.currentUser.role === 'GURU' ? 'Guru' : 'Murid';
      }
    }
  },

  // Show login section
  showLogin() {
    if (this.elements.loginSection) {
      this.elements.loginSection.classList.remove('hidden');
    }
    if (this.elements.dashboardWrapper) {
      this.elements.dashboardWrapper.classList.add('hidden');
    }
  },

  // Handle login
  async handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById('login-email')?.value;
    const password = document.getElementById('login-password')?.value;
    
    if (!email || !password) {
      this.showNotification('Email dan password harus diisi', 'error');
      return;
    }
    
    try {
      const response = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      
      const data = await response.json();
      
      if (data.success) {
        this.state.currentUser = data.user;
        this.state.isTeacher = data.user.role === 'GURU';
        this.showDashboard();
        await this.loadInitialData();
        this.showNotification('Login berhasil!', 'success');
      } else {
        this.showNotification(data.message || 'Email atau password salah', 'error');
      }
    } catch (error) {
      console.error('Login failed:', error);
      this.showNotification('Terjadi kesalahan. Silakan coba lagi.', 'error');
    }
  },

  // Handle logout
  async handleLogout() {
    if (!confirm('Apakah Anda yakin ingin logout?')) return;
    
    try {
      await fetch('/api/logout', { method: 'POST' });
      this.state.currentUser = null;
      this.state.courses = [];
      this.state.academicYears = [];
      this.showLogin();
      this.showNotification('Anda telah logout', 'success');
    } catch (error) {
      console.error('Logout failed:', error);
      this.showNotification('Gagal logout', 'error');
    }
  },

  // Load initial data
  async loadInitialData() {
    try {
      const response = await fetch('/api/initial-data');
      const data = await response.json();
      
      this.state.academicYears = data.academicYears || [];
      this.state.courses = data.courses || [];
      
      // Populate year selector
      this.populateYearSelector(data.academicYears);
      
      // Find active year
      const activeYear = data.academicYears?.find(y => y.isActive);
      if (activeYear) {
        this.state.selectedYearId = activeYear.id;
        this.elements.yearSelect.value = activeYear.id;
        if (this.elements.activeYear) {
          this.elements.activeYear.textContent = activeYear.year;
        }
      }
      
      // Load courses for selected year
      await this.loadCourses(this.state.selectedYearId);
      
    } catch (error) {
      console.error('Failed to load initial data:', error);
      this.showNotification('Gagal memuat data', 'error');
    }
  },

  // Populate year selector
  populateYearSelector(years) {
    if (!this.elements.yearSelect) return;
    
    this.elements.yearSelect.innerHTML = years.map(year => 
      `<option value="${year.id}">${year.year}</option>`
    ).join('');
  },

  // Handle year change
  async handleYearChange(e) {
    const yearId = e.target.value;
    this.state.selectedYearId = yearId;
    await this.loadCourses(yearId);
  },

  // Load courses for a year
  async loadCourses(yearId) {
    if (!yearId) return;
    
    try {
      const response = await fetch(`/api/courses/year/${yearId}`);
      const data = await response.json();
      
      this.state.courses = data.courses || [];
      this.renderCourses(data.courses);
      this.updateStats(data.courses);
      
    } catch (error) {
      console.error('Failed to load courses:', error);
      this.showNotification('Gagal memuat kelas', 'error');
    }
  },

  // Render courses grid
  renderCourses(courses) {
    if (!this.elements.classesList) return;
    
    if (!courses || courses.length === 0) {
      this.elements.classesList.classList.add('hidden');
      if (this.elements.emptyState) {
        this.elements.emptyState.classList.remove('hidden');
      }
      return;
    }
    
    this.elements.classesList.classList.remove('hidden');
    if (this.elements.emptyState) {
      this.elements.emptyState.classList.add('hidden');
    }
    
    this.elements.classesList.innerHTML = courses.map(course => `
      <div class="class-card" data-course-id="${course.id}">
        <div class="class-card-header" style="background: linear-gradient(135deg, ${course.color || '#1a73e8'} 0%, ${this.darkenColor(course.color || '#1a73e8')} 100%)">
          <h3 class="class-card-title">${this.escapeHtml(course.name)}</h3>
          ${this.state.isTeacher ? `
            <button class="edit-course-btn" onclick="Dashboard.openEditModal(${course.id}, '${this.escapeHtml(course.name)}', '${course.color || '#1a73e8'}')" title="Edit kelas">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
                <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
              </svg>
            </button>
          ` : ''}
        </div>
        <div class="class-card-body">
          <div class="class-card-info">
            <div class="class-card-info-item">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/>
                <circle cx="12" cy="7" r="4"/>
              </svg>
              <span>${this.escapeHtml(course.teacher?.name || 'Guru')}</span>
            </div>
            <div class="class-card-info-item">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/>
                <circle cx="9" cy="7" r="4"/>
                <path d="M23 21v-2a4 4 0 00-3-3.87"/>
                <path d="M16 3.13a4 4 0 010 7.75"/>
              </svg>
              <span>${course.studentCount || 0} Murid</span>
            </div>
          </div>
        </div>
        <div class="class-card-footer">
          <div class="class-code-wrapper">
            <span class="class-code-label">Kode:</span>
            <span class="class-code">${course.classCode || 'N/A'}</span>
          </div>
          <button class="copy-code-btn" onclick="Dashboard.copyToClipboard('${course.classCode || ''}')" title="Salin kode">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
              <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/>
            </svg>
          </button>
        </div>
      </div>
    `).join('');
  },

  // Update statistics
  updateStats(courses) {
    if (this.elements.totalClasses) {
      this.elements.totalClasses.textContent = courses?.length || 0;
    }
    
    // Calculate total students
    const totalStudents = courses?.reduce((sum, course) => sum + (course.studentCount || 0), 0) || 0;
    if (this.elements.totalStudents) {
      this.elements.totalStudents.textContent = totalStudents;
    }
    
    // Total quizzes would need additional API call
    if (this.elements.totalQuizzes) {
      this.elements.totalQuizzes.textContent = '-';
    }
  },

  // Open create class modal
  openCreateModal() {
    if (this.elements.createClassModal) {
      this.elements.createClassModal.classList.remove('hidden');
    }
    // Reset form
    if (this.elements.createClassForm) {
      this.elements.createClassForm.reset();
    }
    // Reset color picker
    this.resetColorPicker(this.elements.classColorPicker, this.elements.selectedColorInput);
  },

  // Close create class modal
  closeCreateModal() {
    if (this.elements.createClassModal) {
      this.elements.createClassModal.classList.add('hidden');
    }
  },

  // Handle create class
  async handleCreateClass(e) {
    e.preventDefault();
    
    const name = document.getElementById('new-class-name')?.value;
    const color = this.elements.selectedColorInput?.value || '#1a73e8';
    
    if (!name) {
      this.showNotification('Nama kelas harus diisi', 'error');
      return;
    }
    
    // Get active year ID
    const activeYear = this.state.academicYears?.find(y => y.isActive);
    if (!activeYear) {
      this.showNotification('Tidak ada tahun ajaran aktif', 'error');
      return;
    }
    
    try {
      const response = await fetch('/api/courses', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: name,
          academic_year_id: activeYear.id,
          color: color
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        this.closeCreateModal();
        this.showSuccessModal(data.course);
        await this.loadCourses(this.state.selectedYearId);
        this.showNotification('Kelas berhasil dibuat', 'success');
      } else {
        this.showNotification(data.message || 'Gagal membuat kelas', 'error');
      }
    } catch (error) {
      console.error('Create class failed:', error);
      this.showNotification('Terjadi kesalahan. Silakan coba lagi.', 'error');
    }
  },

  // Open edit modal
  openEditModal(courseId, courseName, courseColor) {
    if (this.elements.editClassId) {
      this.elements.editClassId.value = courseId;
    }
    if (this.elements.editClassName) {
      this.elements.editClassName.value = courseName;
    }
    if (this.elements.editSelectedColorInput) {
      this.elements.editSelectedColorInput.value = courseColor || '#1a73e8';
    }
    
    // Update color picker
    this.resetColorPicker(this.elements.editColorPicker, this.elements.editSelectedColorInput);
    if (this.elements.editColorPicker) {
      const swatch = this.elements.editColorPicker.querySelector(`[data-color="${courseColor || '#1a73e8'}"]`);
      if (swatch) {
        swatch.classList.add('selected');
      }
    }
    
    if (this.elements.editClassModal) {
      this.elements.editClassModal.classList.remove('hidden');
    }
  },

  // Close edit modal
  closeEditModal() {
    if (this.elements.editClassModal) {
      this.elements.editClassModal.classList.add('hidden');
    }
  },

  // Handle edit class
  async handleEditClass(e) {
    e.preventDefault();
    
    const courseId = this.elements.editClassId?.value;
    const name = this.elements.editClassName?.value;
    const color = this.elements.editSelectedColorInput?.value;
    
    if (!courseId || !name) {
      this.showNotification('Data tidak valid', 'error');
      return;
    }
    
    try {
      const response = await fetch(`/api/courses/${courseId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, color })
      });
      
      const data = await response.json();
      
      if (data.success) {
        this.closeEditModal();
        await this.loadCourses(this.state.selectedYearId);
        this.showNotification('Kelas berhasil diperbarui', 'success');
      } else {
        this.showNotification(data.message || 'Gagal memperbarui kelas', 'error');
      }
    } catch (error) {
      console.error('Edit class failed:', error);
      this.showNotification('Terjadi kesalahan. Silakan coba lagi.', 'error');
    }
  },

  // Show success modal
  showSuccessModal(course) {
    if (this.elements.classCode) {
      this.elements.classCode.textContent = course.classCode || 'N/A';
    }
    if (this.elements.successModal) {
      this.elements.successModal.classList.remove('hidden');
    }
    if (this.elements.copyFeedback) {
      this.elements.copyFeedback.textContent = 'Klik kode untuk menyalin';
    }
  },

  // Close success modal
  closeSuccessModal() {
    if (this.elements.successModal) {
      this.elements.successModal.classList.add('hidden');
    }
  },

  // Copy class code
  copyClassCode() {
    const code = this.elements.classCode?.textContent || '';
    this.copyToClipboard(code);
  },

  // Copy to clipboard utility
  copyToClipboard(text) {
    if (!text) return;
    
    navigator.clipboard.writeText(text).then(() => {
      if (this.elements.copyFeedback) {
        this.elements.copyFeedback.textContent = '✓ Kode berhasil disalin!';
        setTimeout(() => {
          this.elements.copyFeedback.textContent = 'Klik kode untuk menyalin';
        }, 2000);
      }
      this.showNotification('Kode berhasil disalin', 'success');
    }).catch(err => {
      console.error('Copy failed:', err);
      this.showNotification('Gagal menyalin kode', 'error');
    });
  },

  // Handle join class
  async handleJoinClass(e) {
    e.preventDefault();
    
    const classCode = this.elements.joinClassForm?.querySelector('input')?.value;
    
    if (!classCode) {
      this.showNotification('Kode kelas harus diisi', 'error');
      return;
    }
    
    if (this.state.isTeacher) {
      this.showNotification('Guru tidak dapat bergabung dengan kelas', 'error');
      return;
    }
    
    try {
      const response = await fetch('/api/enroll', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ class_code: classCode.trim().toUpperCase() })
      });
      
      const data = await response.json();
      
      if (data.success) {
        this.elements.joinClassForm?.reset();
        await this.loadCourses(this.state.selectedYearId);
        this.showNotification('Berhasil bergabung dengan kelas', 'success');
      } else {
        this.showNotification(data.message || 'Kode kelas tidak valid', 'error');
      }
    } catch (error) {
      console.error('Join class failed:', error);
      this.showNotification('Terjadi kesalahan. Silakan coba lagi.', 'error');
    }
  },

  // Setup color picker
  setupColorPicker(container, input) {
    if (!container || !input) return;
    
    const swatches = container.querySelectorAll('.color-swatch');
    swatches.forEach(swatch => {
      swatch.addEventListener('click', () => {
        // Remove selected from all
        swatches.forEach(s => s.classList.remove('selected'));
        // Add selected to clicked
        swatch.classList.add('selected');
        // Update input value
        input.value = swatch.dataset.color;
      });
    });
  },

  // Reset color picker
  resetColorPicker(container, input) {
    if (!container || !input) return;
    
    const swatches = container.querySelectorAll('.color-swatch');
    swatches.forEach(s => s.classList.remove('selected'));
    
    // Select first swatch
    if (swatches.length > 0) {
      swatches[0].classList.add('selected');
      input.value = swatches[0].dataset.color;
    }
  },

  // Darken color for gradient
  darkenColor(color) {
    // Simple color darkening
    const hex = color.replace('#', '');
    const r = Math.max(0, parseInt(hex.substr(0, 2), 16) - 20);
    const g = Math.max(0, parseInt(hex.substr(2, 2), 16) - 20);
    const b = Math.max(0, parseInt(hex.substr(4, 2), 16) - 20);
    return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
  },

  // Escape HTML
  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  },

  // Show notification
  showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
      <div class="notification-content">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          ${type === 'success' 
            ? '<polyline points="20,6 9,17 4,12"/>'
            : type === 'error'
            ? '<circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>'
            : '<circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>'
          }
        </svg>
        <span>${this.escapeHtml(message)}</span>
      </div>
    `;
    
    // Add styles
    notification.style.cssText = `
      position: fixed;
      top: 24px;
      right: 24px;
      padding: 16px 20px;
      border-radius: 12px;
      background: ${type === 'success' ? '#e8f5e9' : type === 'error' ? '#ffebee' : '#e3f2fd'};
      color: ${type === 'success' ? '#2e7d32' : type === 'error' ? '#c62828' : '#1976d2'};
      border: 1px solid ${type === 'success' ? '#4caf50' : type === 'error' ? '#f44336' : '#2196f3'};
      box-shadow: 0 4px 16px rgba(0,0,0,0.15);
      z-index: 10000;
      animation: slideInRight 0.3s ease;
      display: flex;
      align-items: center;
      gap: 12px;
      font-weight: 500;
      font-size: 14px;
    `;
    
    document.body.appendChild(notification);
    
    // Remove after 3 seconds
    setTimeout(() => {
      notification.style.animation = 'slideOutRight 0.3s ease';
      setTimeout(() => notification.remove(), 300);
    }, 3000);
  }
};

// Add animations
const style = document.createElement('style');
style.textContent = `
  @keyframes slideInRight {
    from { transform: translateX(100%); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
  }
  @keyframes slideOutRight {
    from { transform: translateX(0); opacity: 1; }
    to { transform: translateX(100%); opacity: 0; }
  }
  .notification-content {
    display: flex;
    align-items: center;
    gap: 12px;
  }
`;
document.head.appendChild(style);
