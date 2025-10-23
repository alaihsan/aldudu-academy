document.addEventListener('DOMContentLoaded', function() {
    
    // --- ELEMEN DOM ---
    const loginPage = document.getElementById('login-page');
    const appPage = document.getElementById('app-page');
    const loginForm = document.getElementById('login-form');
    const classGrid = document.getElementById('class-grid');
    
    // Elemen Enroll Murid
    const enrollSection = document.getElementById('enroll-section');
    const enrollForm = document.getElementById('enroll-form');

    // Elemen Modal Tambah Kelas
    const addClassModal = document.getElementById('add-class-modal');
    const addClassForm = document.getElementById('add-class-form');
    const addCancelButton = document.getElementById('add-cancel-button');
    
    // Elemen Modal Tampilkan Kode
    const showCodeModal = document.getElementById('show-code-modal');
    const generatedClassCode = document.getElementById('generated-class-code');
    const closeCodeModalButton = document.getElementById('close-code-modal-button');
    const copyFeedback = document.getElementById('copy-feedback');

    // Elemen Modal Edit Kelas
    const editClassModal = document.getElementById('edit-class-modal');
    const editClassForm = document.getElementById('edit-class-form');
    const editCancelButton = document.getElementById('edit-cancel-button');
    const editCourseNameInput = document.getElementById('edit-course-name');
    const colorPicker = document.getElementById('color-picker');
    const PRESET_COLORS = ['#0282c6', '#0ea5e9', '#10b981', '#f97316', '#ef4444', '#8b5cf6', '#d946ef', '#ec4899'];

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
            if (response.status === 204 || (response.headers.get('Content-Length') === '0')) return { success: true };
            return await response.json();
        } catch (error) {
            console.error(`API Request Error to ${url}:`, error);
            throw error;
        }
    }

    // --- FUNGSI-FUNGSI UTAMA ---
    const handleLogin = async (e) => {
        e.preventDefault();
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
            document.getElementById('login-error').textContent = error.message || "Terjadi kesalahan.";
            document.getElementById('login-error').classList.remove('hidden');
        }
    };

    const handleLogout = async () => {
        await apiRequest('/api/logout', { method: 'POST' });
        currentUser = null;
        showLoginPage();
    };
    
    const showAppPage = () => { loginPage.classList.add('hidden'); appPage.classList.remove('hidden'); };
    const showLoginPage = () => { appPage.classList.add('hidden'); loginPage.classList.remove('hidden'); loginForm.reset(); };
    
    const initializeDashboard = async () => {
        showAppPage();
        document.getElementById('welcome-message').textContent = `Selamat datang, ${currentUser.name}!`;
        if (currentUser.role === 'murid') enrollSection.classList.remove('hidden');
        else enrollSection.classList.add('hidden');
        try {
            const data = await apiRequest('/api/initial-data');
            renderAcademicYears(data.academicYears);
            renderClassCards(data.courses);
            updateContentTitle();
        } catch(error) {
            classGrid.innerHTML = `<p class="form-error">Gagal memuat data awal.</p>`;
        }
    };

    const handleYearChange = async () => {
        updateContentTitle();
        classGrid.innerHTML = `<p>Memuat kelas...</p>`;
        try {
            const data = await apiRequest(`/api/courses/year/${document.getElementById('academic-year').value}`);
            renderClassCards(data.courses);
        } catch(error) {
            classGrid.innerHTML = `<p class="form-error">Gagal memuat data kelas.</p>`;
        }
    };

    // --- Logika Modal ---
    const showAddClassModal = () => addClassModal.classList.remove('hidden');
    const hideAddClassModal = () => { addClassModal.classList.add('hidden'); addClassForm.reset(); };
    const showEditModal = (course) => {
        editClassModal.dataset.courseId = course.id;
        editCourseNameInput.value = course.name;
        renderColorPicker(course.color);
        editClassModal.classList.remove('hidden');
    };
    const hideEditModal = () => {
        editClassModal.classList.add('hidden');
        editClassForm.reset();
        delete editClassModal.dataset.courseId;
    };
    
    const handleAddClassSubmit = async (e) => {
        e.preventDefault();
        try {
            const data = await apiRequest('/api/courses', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: document.getElementById('course-name').value.trim(), academic_year_id: document.getElementById('academic-year').value })
            });
            if (data.success) {
                hideAddClassModal();
                appendNewClassCard(data.course);
                generatedClassCode.textContent = data.course.class_code;
                showCodeModal.classList.remove('hidden');
            }
        } catch (error) {
            document.getElementById('add-modal-error').textContent = error.message || "Gagal menyimpan kelas.";
            document.getElementById('add-modal-error').classList.remove('hidden');
        }
    };

    const handleEditClassSubmit = async (e) => {
        e.preventDefault();
        const courseId = editClassModal.dataset.courseId;
        const newName = editCourseNameInput.value.trim();
        const newColor = colorPicker.querySelector('.selected')?.dataset.color || '#0282c6';
        
        try {
            const data = await apiRequest(`/api/courses/${courseId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: newName, color: newColor })
            });
            if (data.success) {
                const card = document.querySelector(`.class-card[data-course-id="${courseId}"]`);
                if (card) {
                    card.querySelector('.class-card-title').textContent = data.course.name;
                    card.querySelector('.class-card-header').style.backgroundColor = data.course.color;
                    card.dataset.courseName = data.course.name;
                    card.dataset.courseColor = data.course.color;
                }
                hideEditModal();
            }
        } catch (error) {
            document.getElementById('edit-modal-error').textContent = error.message || "Gagal menyimpan perubahan.";
            document.getElementById('edit-modal-error').classList.remove('hidden');
        }
    };

    // --- Logika Enroll ---
    const handleEnrollSubmit = async (e) => {
        e.preventDefault();
        const enrollMsgEl = document.getElementById('enroll-message');
        enrollMsgEl.className = 'enroll-message hidden';
        try {
            const data = await apiRequest('/api/enroll', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ class_code: document.getElementById('class-code-input').value.trim() })
            });
            if (data.success) {
                enrollMsgEl.textContent = data.message;
                enrollMsgEl.className = 'enroll-message success';
                appendNewClassCard(data.course);
                enrollForm.reset();
            }
        } catch (error) {
            enrollMsgEl.textContent = error.message || "Gagal bergabung.";
            enrollMsgEl.className = 'enroll-message error';
        }
        enrollMsgEl.classList.remove('hidden');
    };

    // --- Render Functions ---
    const updateContentTitle = () => {
        const sel = document.getElementById('academic-year');
        const opt = sel.options[sel.selectedIndex];
        const baseTitle = currentUser?.role === 'guru' ? "Kelas yang Anda Ajar" : "Kelas yang Anda Ikuti";
        document.getElementById('content-title').textContent = opt ? `${baseTitle} di Tahun Ajaran ${opt.text}` : baseTitle;
    };
    
    const renderAcademicYears = (years) => {
        const sel = document.getElementById('academic-year');
        sel.innerHTML = '';
        if (years?.length > 0) years.forEach(year => {
            const opt = document.createElement('option');
            opt.value = year.id;
            opt.textContent = year.year;
            sel.appendChild(opt);
        });
    };

    const renderColorPicker = (selectedColor) => {
        colorPicker.innerHTML = '';
        PRESET_COLORS.forEach(color => {
            const swatch = document.createElement('div');
            swatch.className = 'color-swatch';
            swatch.style.backgroundColor = color;
            swatch.dataset.color = color;
            if (color === selectedColor) {
                swatch.classList.add('selected');
            }
            colorPicker.appendChild(swatch);
        });
    };

    const renderClassCards = (courses) => {
        classGrid.innerHTML = '';
        if (courses?.length > 0) courses.forEach(createAndAppendClassCard);
        appendAddClassButtonIfNeeded();
    };

    const appendNewClassCard = (cls) => {
        document.getElementById('add-class-button')?.remove();
        createAndAppendClassCard(cls);
        appendAddClassButtonIfNeeded();
    };

    const createAndAppendClassCard = (cls) => {
        const card = document.createElement('div');
        card.className = 'class-card';
        card.dataset.courseId = cls.id;
        card.dataset.courseName = cls.name;
        card.dataset.courseColor = cls.color;

        const header = document.createElement('div');
        header.className = 'class-card-header';
        header.style.backgroundColor = cls.color;
        header.innerHTML = `<h3 class="class-card-title">${cls.name}</h3>`;

        const body = document.createElement('div');
        body.className = 'class-card-body';
        body.innerHTML = `<p class="class-card-info">Wali Kelas: ${cls.teacher}</p><p class="class-card-info">${cls.studentCount} Murid</p>`;
        
        const footer = document.createElement('div');
        footer.className = 'class-card-footer';
        footer.innerHTML = `<a href="/kelas/${cls.id}" class="btn btn-secondary">Masuk Kelas</a>`;

        card.append(header, body);

        if (cls.is_teacher) {
            const editBtn = document.createElement('button');
            editBtn.className = 'edit-course-btn';
            editBtn.title = 'Edit Kelas';
            editBtn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L6.832 19.82a4.5 4.5 0 01-1.897 1.13l-2.685.8.8-2.685a4.5 4.5 0 011.13-1.897L16.863 4.487zm0 0L19.5 7.125" /></svg>`;
            card.appendChild(editBtn);

            const codeSection = document.createElement('div');
            codeSection.className = 'class-card-code-section';
            const copyIconSVG = `<svg class="copy-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" style="width:18px; height:18px;"><path stroke-linecap="round" stroke-linejoin="round" d="M15.75 17.25v3.375c0 .621-.504 1.125-1.125 1.125h-9.75a1.125 1.125 0 01-1.125-1.125V7.875c0-.621.504-1.125 1.125-1.125H6.75a9.06 9.06 0 011.5.124m7.5 10.376h3.375c.621 0 1.125-.504 1.125-1.125V11.25c0-4.46-3.243-8.161-7.5-8.876a9.06 9.06 0 00-1.5-.124H9.375c-.621 0-1.125.504-1.125 1.125v3.5m7.5 10.375H9.375a1.125 1.125 0 01-1.125-1.125v-9.25m9.75 0h-3.25a1.125 1.125 0 01-1.125-1.125V3.75c0-.621.504-1.125 1.125-1.125h3.25c.621 0 1.125.504 1.125 1.125v3.25a1.125 1.125 0 01-1.125 1.125z" /></svg>`;
            const checkIconSVG = `<svg class="check-icon icon-hidden" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" style="width:18px; height:18px;"><path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" /></svg>`;
            codeSection.innerHTML = `<p>Kode Kelas</p><div class="class-card-code-wrapper"><span class="class-card-code">${cls.class_code}</span><button class="copy-code-btn" title="Salin Kode">${copyIconSVG}${checkIconSVG}</button></div>`;
            card.appendChild(codeSection);
        }
        
        card.appendChild(footer);
        classGrid.appendChild(card);
    };

    const appendAddClassButtonIfNeeded = () => {
        if (currentUser?.role === 'guru') {
            const addCard = document.createElement('div');
            addCard.id = 'add-class-button';
            addCard.className = 'add-class-card';
            addCard.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" /></svg><span>Tambah Kelas Baru</span>`;
            classGrid.appendChild(addCard);
        }
    };
    
    // ---
    // Logika untuk Modal Kuis di course_detail.html
    // Diletakkan di sini agar script.js bisa digunakan di kedua halaman
    // ---
    
    // Elemen Modal Kuis
    const quizModal = document.getElementById('create-quiz-modal');
    const showQuizModalButton = document.getElementById('show-create-quiz-modal');
    const quizCancelButton = document.getElementById('quiz-cancel-button');
    const quizForm = document.getElementById('create-quiz-form');
    const quizNameInput = document.getElementById('quiz-name-input');
    const quizModalError = document.getElementById('quiz-modal-error');
    
    // Elemen baru untuk modal kuis
    const categorySelectWrapper = document.getElementById('category-select-wrapper');
    const categoryInputWrapper = document.getElementById('category-input-wrapper');
    const categorySelect = document.getElementById('quiz-category');
    const categoryCancelButton = document.getElementById('category-cancel-button');
    const categoryNewInput = document.getElementById('quiz-category-new');
    const quizDueStart = document.getElementById('quiz-due-start');
    const quizDueFinish = document.getElementById('quiz-due-finish');
    const quizPoints = document.getElementById('quiz-points');
    const quizGradeType = document.getElementById('quiz-grade-type');

    // Cek jika elemen ada (hanya ada di course_detail.html)
    if (quizModal) {
        
        // Fungsi untuk tampil/sembunyi modal
        const showQuizModal = () => {
            quizModal.classList.remove('hidden');
            quizNameInput.value = ''; // Kosongkan input
            quizModalError.classList.add('hidden'); // Sembunyikan error
            
            // Reset form kategori saat modal dibuka
            if(categorySelectWrapper) categorySelectWrapper.classList.remove('hidden');
            if(categoryInputWrapper) categoryInputWrapper.classList.add('hidden');
            if(categorySelect) categorySelect.value = '';
            if(categoryNewInput) categoryNewInput.value = '';
        };
        
        const hideQuizModal = () => {
            quizModal.classList.add('hidden');
        };

        // Event Listeners
        if (showQuizModalButton) {
            showQuizModalButton.addEventListener('click', function(e) {
                e.preventDefault(); 
                showQuizModal();
                
                // Sembunyikan dropdown "Add Topics" jika ada
                const topicsDropdownMenu = document.getElementById('topics-dropdown-menu');
                const addTopicsButton = document.getElementById('add-topics-button');
                if (topicsDropdownMenu) topicsDropdownMenu.classList.add('hidden');
                if (addTopicsButton) addTopicsButton.classList.remove('btn-pressed'); 
            });
        }
        
        if(quizCancelButton) {
            quizCancelButton.addEventListener('click', hideQuizModal);
        }
        
        // Listener untuk dropdown kategori
        if (categorySelect) {
            categorySelect.addEventListener('change', function() {
                if (this.value === '_create_new_') {
                    categorySelectWrapper.classList.add('hidden');
                    categoryInputWrapper.classList.remove('hidden');
                    categoryNewInput.focus();
                }
            });
        }

        // Listener untuk tombol cancel kategori
        if (categoryCancelButton) {
            categoryCancelButton.addEventListener('click', function() {
                categorySelectWrapper.classList.remove('hidden');
                categoryInputWrapper.classList.add('hidden');
                categorySelect.value = ''; 
            });
        }

        // Event Listener untuk Submit Form Kuis
        if(quizForm) {
            quizForm.addEventListener('submit', async function(e) {
                e.preventDefault(); 
                const mainContainer = document.querySelector('main.container');
                const courseId = mainContainer?.dataset.courseId;
                if (!courseId) return;

                // Kumpulkan semua data baru
                const quizName = quizNameInput.value.trim();
                
                let categoryValue = categorySelect.value;
                if (categoryValue === '_create_new_') {
                    categoryValue = categoryNewInput.value.trim();
                }

                const payload = {
                    name: quizName,
                    start_date: quizDueStart.value || null,
                    end_date: quizDueFinish.value || null,
                    points: parseInt(quizPoints.value, 10) || 100,
                    category: categoryValue,
                    grade_type: quizGradeType.value
                };

                if (!payload.name) {
                    quizModalError.textContent = 'Nama kuis tidak boleh kosong.';
                    quizModalError.classList.remove('hidden');
                    return;
                }

                try {
                    const response = await fetch(`/api/courses/${courseId}/quizzes`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(payload)
                    });

                    const data = await response.json();

                    if (!response.ok) {
                        throw new Error(data.message || 'Gagal menyimpan kuis.');
                    }
                    
                    hideQuizModal();
                    // Redirect ke halaman detail kuis yang baru dibuat
                    window.location.href = `/quiz/${data.quiz.id}`;
                    
                } catch (error) {
                    quizModalError.textContent = error.message;
                    quizModalError.classList.remove('hidden');
                }
            });
        }
    }


    // --- INISIALISASI ---
    const initializeApp = async () => {
        // Pasang semua event listener sekali saja
        loginForm.addEventListener('submit', handleLogin);
        document.getElementById('logout-button').addEventListener('click', handleLogout);
        document.getElementById('academic-year').addEventListener('change', handleYearChange);
        addClassForm.addEventListener('submit', handleAddClassSubmit);
        addCancelButton.addEventListener('click', hideAddClassModal);
        enrollForm.addEventListener('submit', handleEnrollSubmit);
        
        classGrid.addEventListener('click', e => {
            if (e.target.closest('#add-class-button')) showAddClassModal();
            const editBtn = e.target.closest('.edit-course-btn');
            if (editBtn) {
                const card = editBtn.closest('.class-card');
                showEditModal({
                    id: card.dataset.courseId,
                    name: card.dataset.courseName,
                    color: card.dataset.courseColor
                });
            }
            const copyBtn = e.target.closest('.copy-code-btn');
            if (copyBtn) {
                const codeElement = copyBtn.parentElement.querySelector('.class-card-code');
                const copyIcon = copyBtn.querySelector('.copy-icon');
                const checkIcon = copyBtn.querySelector('.check-icon');
                if (codeElement && copyIcon && checkIcon) navigator.clipboard.writeText(codeElement.textContent).then(() => {
                    copyIcon.classList.add('icon-hidden');
                    checkIcon.classList.remove('icon-hidden');
                    setTimeout(() => {
                        copyIcon.classList.remove('icon-hidden');
                        checkIcon.classList.add('icon-hidden');
                    }, 2000);
                });
            }
        });

        editClassForm.addEventListener('submit', handleEditClassSubmit);
        editCancelButton.addEventListener('click', hideEditModal);
        colorPicker.addEventListener('click', e => {
            if (e.target.classList.contains('color-swatch')) {
                colorPicker.querySelector('.selected')?.classList.remove('selected');
                e.target.classList.add('selected');
            }
        });

        closeCodeModalButton.addEventListener('click', () => showCodeModal.classList.add('hidden'));
        generatedClassCode.addEventListener('click', () => {
            navigator.clipboard.writeText(generatedClassCode.textContent).then(() => {
                copyFeedback.textContent = 'Kode disalin!';
                setTimeout(() => copyFeedback.textContent = '', 2000);
            });
        });

        // Cek sesi login
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

    // Hanya inisialisasi jika kita berada di halaman utama (index.html)
    // Kita bisa mengecek keberadaan loginForm
    if (loginForm) {
        initializeApp();
    }

});