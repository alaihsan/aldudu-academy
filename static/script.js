document.addEventListener('DOMContentLoaded', function() {
    
    // --- ELEMEN DOM ---
    const loginPage = document.getElementById('login-page');
    const appPage = document.getElementById('app-page');
    const loginForm = document.getElementById('login-form');
    const loginError = document.getElementById('login-error');
    const logoutButton = document.getElementById('logout-button');
    const welcomeMessage = document.getElementById('welcome-message');
    const academicYearSelect = document.getElementById('academic-year');
    const contentTitle = document.getElementById('content-title');
    const classGrid = document.getElementById('class-grid');
    
    const enrollSection = document.getElementById('enroll-section');
    const enrollForm = document.getElementById('enroll-form');
    const classCodeInput = document.getElementById('class-code-input');
    const enrollMessage = document.getElementById('enroll-message');

    const addClassModal = document.getElementById('add-class-modal');
    const addClassForm = document.getElementById('add-class-form');
    const modalCancelButton = document.getElementById('modal-cancel-button');
    const modalError = document.getElementById('modal-error');
    const courseNameInput = document.getElementById('course-name');
    
    const showCodeModal = document.getElementById('show-code-modal');
    const generatedClassCode = document.getElementById('generated-class-code');
    const closeCodeModalButton = document.getElementById('close-code-modal-button');
    const copyFeedback = document.getElementById('copy-feedback');

    // --- STATE APLIKASI ---
    let currentUser = null;

    // --- FUNGSI-FUNGSI API ---
    async function apiRequest(url, options = {}) {
        try {
            const response = await fetch(url, options);
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ message: 'Terjadi kesalahan pada server.' }));
                throw new Error(errorData.message);
            }
            if (response.status === 204) return null;
            return await response.json();
        } catch (error) {
            console.error(`API Request Error to ${url}:`, error);
            throw error;
        }
    }

    // --- FUNGSI-FUNGSI UTAMA ---
    const handleLogin = async (e) => {
        e.preventDefault();
        loginError.classList.add('hidden');
        try {
            const data = await apiRequest('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email: loginForm.email.value, password: loginForm.password.value })
            });
            if (data.success) {
                currentUser = data.user;
                await initializeDashboard();
            }
        } catch (error) {
            loginError.textContent = error.message || "Terjadi kesalahan saat login.";
            loginError.classList.remove('hidden');
        }
    };

    const handleLogout = async () => {
        try {
            await apiRequest('/api/logout', { method: 'POST' });
            currentUser = null;
            showLoginPage();
        } catch (error) {
            alert('Gagal untuk logout. Silakan refresh halaman.');
        }
    };
    
    const showAppPage = () => {
        loginPage.classList.add('hidden');
        appPage.classList.remove('hidden');
    };

    const showLoginPage = () => {
        appPage.classList.add('hidden');
        loginPage.classList.remove('hidden');
        loginForm.reset();
    };
    
    const initializeDashboard = async () => {
        showAppPage();
        welcomeMessage.textContent = `Selamat datang, ${currentUser.name}!`;

        if (currentUser.role === 'murid') {
            enrollSection.classList.remove('hidden');
        } else {
            enrollSection.classList.add('hidden');
        }
        
        try {
            const data = await apiRequest('/api/initial-data');
            renderAcademicYears(data.academicYears);
            renderClassCards(data.courses);
            updateContentTitle();
        } catch(error) {
            classGrid.innerHTML = `<p class="form-error">Gagal memuat data awal. Coba refresh halaman.</p>`;
        }
    };

    const handleYearChange = async () => {
        const selectedYearId = academicYearSelect.value;
        updateContentTitle();
        classGrid.innerHTML = `<p>Memuat kelas...</p>`;
        try {
            const data = await apiRequest(`/api/courses/year/${selectedYearId}`);
            renderClassCards(data.courses);
        } catch(error) {
            classGrid.innerHTML = `<p class="form-error">Gagal memuat data kelas untuk tahun ajaran ini.</p>`;
        }
    };

    // --- Logika Modal ---
    const showAddClassModal = () => addClassModal.classList.remove('hidden');
    const hideAddClassModal = () => { addClassModal.classList.add('hidden'); addClassForm.reset(); modalError.classList.add('hidden'); };
    
    const handleAddClassSubmit = async (e) => {
        e.preventDefault();
        modalError.classList.add('hidden');
        const courseName = courseNameInput.value.trim();
        const academicYearId = academicYearSelect.value;
        try {
            const data = await apiRequest('/api/courses', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: courseName, academic_year_id: academicYearId })
            });
            if (data.success) {
                hideAddClassModal();
                appendNewClassCard(data.course);
                generatedClassCode.textContent = data.course.class_code;
                showCodeModal.classList.remove('hidden');
            }
        } catch (error) {
            modalError.textContent = error.message || "Gagal menyimpan kelas.";
            modalError.classList.remove('hidden');
        }
    };

    // --- Logika Enroll ---
    const handleEnrollSubmit = async (e) => {
        e.preventDefault();
        enrollMessage.className = 'enroll-message hidden';
        const classCode = classCodeInput.value.trim();
        try {
            const data = await apiRequest('/api/enroll', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ class_code: classCode })
            });
            if (data.success) {
                enrollMessage.textContent = data.message;
                enrollMessage.className = 'enroll-message success';
                appendNewClassCard(data.course);
                enrollForm.reset();
            }
        } catch (error) {
            enrollMessage.textContent = error.message || "Gagal bergabung ke kelas.";
            enrollMessage.className = 'enroll-message error';
        }
        enrollMessage.classList.remove('hidden');
    };

    // --- Render Functions ---
    const updateContentTitle = () => {
        const sel = academicYearSelect;
        const opt = sel.options[sel.selectedIndex];
        const baseTitle = currentUser?.role === 'guru' ? "Kelas yang Anda Ajar" : "Kelas yang Anda Ikuti";
        if (opt) {
            contentTitle.textContent = `${baseTitle} di Tahun Ajaran ${opt.text}`;
        } else {
            contentTitle.textContent = baseTitle;
        }
    };
    
    const renderAcademicYears = (years) => {
        academicYearSelect.innerHTML = '';
        if (years && years.length > 0) {
            years.forEach(year => {
                const opt = document.createElement('option');
                opt.value = year.id;
                opt.textContent = year.year;
                academicYearSelect.appendChild(opt);
            });
        }
    };

    const renderClassCards = (courses) => {
        classGrid.innerHTML = '';
        if (courses && courses.length > 0) {
            courses.forEach(createAndAppendClassCard);
        }
        appendAddClassButtonIfNeeded();
    };

    const appendNewClassCard = (cls) => {
        const addClassButton = document.getElementById('add-class-button');
        if (addClassButton) addClassButton.remove();
        createAndAppendClassCard(cls);
        appendAddClassButtonIfNeeded();
    };

    /**
     * PERBAIKAN UTAMA: Membuat kartu kelas menggunakan DOM manipulation
     * untuk mencegah error dan memastikan struktur yang benar.
     */
    const createAndAppendClassCard = (cls) => {
        const card = document.createElement('div');
        card.className = 'class-card';

        // 1. Buat Header
        const header = document.createElement('div');
        header.className = 'class-card-header';
        const title = document.createElement('h3');
        title.className = 'class-card-title';
        title.textContent = cls.name;
        header.appendChild(title);

        // 2. Buat Body
        const body = document.createElement('div');
        body.className = 'class-card-body';
        const teacherInfo = document.createElement('p');
        teacherInfo.className = 'class-card-info';
        teacherInfo.textContent = `Wali Kelas: ${cls.teacher}`;
        const studentInfo = document.createElement('p');
        studentInfo.className = 'class-card-info';
        studentInfo.textContent = `${cls.studentCount} Murid`;
        body.append(teacherInfo, studentInfo);

        // 3. Buat Footer
        const footer = document.createElement('div');
        footer.className = 'class-card-footer';
        const link = document.createElement('a');
        link.href = `/kelas/${cls.id}`;
        link.className = 'btn btn-secondary';
        link.textContent = 'Masuk Kelas';
        footer.appendChild(link);

        // 4. Rakit kartu
        card.append(header, body);

        // 5. Tambahkan bagian kode kelas (jika guru)
        if (cls.is_teacher) {
            const codeSection = document.createElement('div');
            codeSection.className = 'class-card-code-section';
            codeSection.innerHTML = `
                <p>Kode Kelas</p>
                <div class="class-card-code-wrapper">
                    <span class="class-card-code">${cls.class_code}</span>
                    <button class="copy-code-btn" title="Salin Kode">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" style="width:18px; height:18px;">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 17.25v3.375c0 .621-.504 1.125-1.125 1.125h-9.75a1.125 1.125 0 01-1.125-1.125V7.875c0-.621.504-1.125 1.125-1.125H6.75a9.06 9.06 0 011.5.124m7.5 10.376h3.375c.621 0 1.125-.504 1.125-1.125V11.25c0-4.46-3.243-8.161-7.5-8.876a9.06 9.06 0 00-1.5-.124H9.375c-.621 0-1.125.504-1.125 1.125v3.5m7.5 10.375H9.375a1.125 1.125 0 01-1.125-1.125v-9.25m9.75 0h-3.25a1.125 1.125 0 01-1.125-1.125V3.75c0-.621.504-1.125 1.125-1.125h3.25c.621 0 1.125.504 1.125 1.125v3.25a1.125 1.125 0 01-1.125 1.125z" />
                        </svg>
                    </button>
                </div>`;
            card.appendChild(codeSection);
        }
        
        // 6. Tambahkan footer di paling akhir
        card.appendChild(footer);
        
        // 7. Masukkan kartu ke dalam grid
        classGrid.appendChild(card);
    };

    const appendAddClassButtonIfNeeded = () => {
        if (currentUser && currentUser.role === 'guru') {
            const addCard = document.createElement('div');
            addCard.id = 'add-class-button';
            addCard.className = 'add-class-card';
            addCard.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" /></svg><span>Tambah Kelas Baru</span>`;
            classGrid.appendChild(addCard);
        }
    };

    // --- INISIALISASI ---
    const initializeApp = async () => {
        loginForm.addEventListener('submit', handleLogin);
        logoutButton.addEventListener('click', handleLogout);
        academicYearSelect.addEventListener('change', handleYearChange);
        addClassForm.addEventListener('submit', handleAddClassSubmit);
        modalCancelButton.addEventListener('click', hideAddClassModal);
        enrollForm.addEventListener('submit', handleEnrollSubmit);
        
        classGrid.addEventListener('click', e => {
            if (e.target.closest('#add-class-button')) showAddClassModal();
            const copyBtn = e.target.closest('.copy-code-btn');
            if (copyBtn) {
                const codeElement = copyBtn.parentElement.querySelector('.class-card-code');
                if (codeElement) navigator.clipboard.writeText(codeElement.textContent).then(() => {
                    copyBtn.title = 'Disalin!';
                    setTimeout(() => { copyBtn.title = 'Salin Kode'; }, 2000);
                });
            }
        });

        closeCodeModalButton.addEventListener('click', () => showCodeModal.classList.add('hidden'));
        generatedClassCode.addEventListener('click', () => {
            navigator.clipboard.writeText(generatedClassCode.textContent).then(() => {
                copyFeedback.textContent = 'Kode disalin!';
                setTimeout(() => copyFeedback.textContent = '', 2000);
            });
        });

        try {
            const session = await apiRequest('/api/session');
            if (session.isAuthenticated) {
                currentUser = session.user;
                await initializeDashboard();
            } else {
                showLoginPage();
            }
        } catch (error) {
            showLoginPage();
        }
    };

    initializeApp();
});
