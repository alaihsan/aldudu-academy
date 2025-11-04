document.addEventListener('DOMContentLoaded', function() {
        
    // --- LOGIKA UNTUK DROPDOWN "ADD TOPICS" ---
    const addTopicsButton = document.getElementById('add-topics-button');
    const topicsDropdownMenu = document.getElementById('topics-dropdown-menu');

    if (addTopicsButton) {
        addTopicsButton.addEventListener('click', function(e) {
            e.stopPropagation(); // Mencegah window click listener di bawah
            
            // Toggle menu visibility
            topicsDropdownMenu.classList.toggle('hidden'); 
            
            // Toggle button's "pressed" state
            addTopicsButton.classList.toggle('btn-pressed'); 
        });
    }

    // Sembunyikan dropdown jika klik di luar
    window.addEventListener('click', function(e) {
        if (topicsDropdownMenu && !topicsDropdownMenu.classList.contains('hidden')) {
            if (!addTopicsButton.contains(e.target)) {
                topicsDropdownMenu.classList.add('hidden'); // Sembunyikan menu
                
                // Kembalikan tombol ke normal
                addTopicsButton.classList.remove('btn-pressed'); 
            }
        }
    });
    // --- AKHIR LOGIKA DROPDOWN ---
    
    // --- Elemen Modal Kuis ---
    const quizModal = document.getElementById('create-quiz-modal');
    const showQuizModalButton = document.getElementById('show-create-quiz-modal');
    const quizCancelButton = document.getElementById('quiz-cancel-button');
    const quizForm = document.getElementById('create-quiz-form');
    const quizNameInput = document.getElementById('quiz-name-input');
    const quizModalError = document.getElementById('quiz-modal-error');

    // --- Elemen Modal Link ---
    const linkModal = document.getElementById('create-link-modal');
    const showLinkModalButton = document.getElementById('show-create-link-modal');
    const linkCancelButton = document.getElementById('link-cancel-button');
    const linkForm = document.getElementById('create-link-form');
    const linkNameInput = document.getElementById('link-name-input');
    const linkUrlInput = document.getElementById('link-url-input');
    const linkModalError = document.getElementById('link-modal-error');

    // --- Elemen Modal File ---
    const fileModal = document.getElementById('create-file-modal');
    const showFileModalButton = document.getElementById('show-create-file-modal');
    const fileCancelButton = document.getElementById('file-cancel-button');
    const fileForm = document.getElementById('create-file-form');
    const fileNameInput = document.getElementById('file-name-input');
    const fileDescriptionInput = document.getElementById('file-description-input');
    const fileUploadInput = document.getElementById('file-upload-input');
    const fileStartDateInput = document.getElementById('file-start-date-input');
    const fileEndDateInput = document.getElementById('file-end-date-input');
    const fileModalError = document.getElementById('file-modal-error');

    const mainContainer = document.querySelector('main.container');
    const courseId = mainContainer.dataset.courseId;

    // --- Fungsi untuk tampil/sembunyi modal ---
    const showQuizModal = () => {
        quizModal.classList.remove('hidden');
        quizNameInput.value = ''; // Kosongkan input
        quizModalError.classList.add('hidden'); // Sembunyikan error
    };

    const hideQuizModal = () => {
        quizModal.classList.add('hidden');
    };

    const showLinkModal = () => {
        linkModal.classList.remove('hidden');
        linkNameInput.value = ''; // Kosongkan input
        linkUrlInput.value = ''; // Kosongkan input
        linkModalError.classList.add('hidden'); // Sembunyikan error
    };

    const hideLinkModal = () => {
        linkModal.classList.add('hidden');
    };

    const showFileModal = () => {
        fileModal.classList.remove('hidden');
        fileNameInput.value = '';
        fileDescriptionInput.value = '';
        fileUploadInput.value = '';
        fileStartDateInput.value = '';
        fileEndDateInput.value = '';
        fileModalError.classList.add('hidden');
    };

    const hideFileModal = () => {
        fileModal.classList.add('hidden');
    };

    // --- Event Listeners ---
    // Pastikan tombol ada (hanya guru yang melihat)
    if (showQuizModalButton) {
        // Listener ini sekarang terpasang pada <a> "Add Quiz"
        showQuizModalButton.addEventListener('click', function(e) {
            e.preventDefault(); // Mencegah <a> melakukan navigasi
            showQuizModal();

            if (topicsDropdownMenu) {
                topicsDropdownMenu.classList.add('hidden'); // Sembunyikan menu
            }

            // Pastikan tombol kembali normal saat item diklik
            if (addTopicsButton) {
                addTopicsButton.classList.remove('btn-pressed');
            }
        });
    }

    // Pastikan tombol link ada
    if (showLinkModalButton) {
        showLinkModalButton.addEventListener('click', function(e) {
            e.preventDefault(); // Mencegah <a> melakukan navigasi
            showLinkModal();

            if (topicsDropdownMenu) {
                topicsDropdownMenu.classList.add('hidden'); // Sembunyikan menu
            }

            // Pastikan tombol kembali normal saat item diklik
            if (addTopicsButton) {
                addTopicsButton.classList.remove('btn-pressed');
            }
        });
    }

    // Pastikan quizCancelButton ada sebelum menambahkan listener
    if(quizCancelButton) {
        quizCancelButton.addEventListener('click', hideQuizModal);
    }

    // Pastikan linkCancelButton ada sebelum menambahkan listener
    if(linkCancelButton) {
        linkCancelButton.addEventListener('click', hideLinkModal);
    }

    if (showFileModalButton) {
        showFileModalButton.addEventListener('click', function(e) {
            e.preventDefault();
            showFileModal();

            if (topicsDropdownMenu) {
                topicsDropdownMenu.classList.add('hidden');
            }

            if (addTopicsButton) {
                addTopicsButton.classList.remove('btn-pressed');
            }
        });
    }

    if(fileCancelButton) {
        fileCancelButton.addEventListener('click', hideFileModal);
    }

    // --- Event Listener untuk Submit Form ---
    // Pastikan quizForm ada sebelum menambahkan listener
    if(quizForm) {
        quizForm.addEventListener('submit', async function(e) {
            e.preventDefault(); // Mencegah form submit biasa
            const quizName = quizNameInput.value.trim();
            
            if (!quizName) {
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
                    body: JSON.stringify({ name: quizName })
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.message || 'Gagal menyimpan kuis.');
                }

                // Tambahkan kuis baru ke daftar di halaman
                // --- Jika Sukses ---
                hideQuizModal();

                // Alihkan (redirect) halaman ke detail kuis yang baru dibuat
                window.location.href = `/quiz/${data.quiz.id}`;
                
            } catch (error) {
                quizModalError.textContent = error.message;
                quizModalError.classList.remove('hidden');
            }
        });
    }

    // --- Event Listener untuk Submit Form Link ---
    // Pastikan linkForm ada sebelum menambahkan listener
    if(linkForm) {
        linkForm.addEventListener('submit', async function(e) {
            e.preventDefault(); // Mencegah form submit biasa
            const linkName = linkNameInput.value.trim();
            const linkUrl = linkUrlInput.value.trim();

            if (!linkName) {
                linkModalError.textContent = 'Nama link tidak boleh kosong.';
                linkModalError.classList.remove('hidden');
                return;
            }

            if (!linkUrl) {
                linkModalError.textContent = 'URL link tidak boleh kosong.';
                linkModalError.classList.remove('hidden');
                return;
            }

            try {
                const response = await fetch(`/api/courses/${courseId}/links`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ name: linkName, url: linkUrl })
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.message || 'Gagal menyimpan link.');
                }

                // Sukses: Sembunyikan modal dan reload halaman untuk menampilkan link baru
                hideLinkModal();
                window.location.reload();

            } catch (error) {
                linkModalError.textContent = error.message;
                linkModalError.classList.remove('hidden');
            }
        });
    }

    if(fileForm) {
        fileForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const fileName = fileNameInput.value.trim();
            const fileDescription = fileDescriptionInput.value.trim();
            const file = fileUploadInput.files[0];
            const startDate = fileStartDateInput.value;
            const endDate = fileEndDateInput.value;

            if (!fileName || !file) {
                fileModalError.textContent = 'Nama file dan file upload tidak boleh kosong.';
                fileModalError.classList.remove('hidden');
                return;
            }

            const formData = new FormData();
            formData.append('name', fileName);
            formData.append('description', fileDescription);
            formData.append('file', file);
            formData.append('start_date', startDate);
            formData.append('end_date', endDate);

            try {
                const response = await fetch(`/api/courses/${courseId}/files`, {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.message || 'Gagal menyimpan file.');
                }

                hideFileModal();
                window.location.reload();

            } catch (error) {
                fileModalError.textContent = error.message;
                fileModalError.classList.remove('hidden');
            }
        });
    }

    // --- LOGIKA UNTUK VIEW SWITCHER ---
    const gridViewBtn = document.getElementById('grid-view-btn');
    const rowViewBtn = document.getElementById('row-view-btn');
    const topicsContainer = document.getElementById('topics-container');

    if (gridViewBtn && rowViewBtn && topicsContainer) {
        gridViewBtn.addEventListener('click', () => {
            if (!gridViewBtn.classList.contains('active')) {
                gridViewBtn.classList.add('active');
                rowViewBtn.classList.remove('active');
                topicsContainer.classList.remove('topics-row-view');
                topicsContainer.classList.add('topics-grid-view');
            }
        });

        rowViewBtn.addEventListener('click', () => {
            if (!rowViewBtn.classList.contains('active')) {
                rowViewBtn.classList.add('active');
                gridViewBtn.classList.remove('active');
                topicsContainer.classList.remove('topics-grid-view');
                topicsContainer.classList.add('topics-row-view');
            }
        });
    }
});