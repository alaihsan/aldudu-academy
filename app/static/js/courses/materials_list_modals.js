/**
 * MaterialsList Component v2.0 — CRUD Modals
 * Object.assign(MaterialsList.prototype, {...}) split of materials-list-v2.js's
 * add/edit/archive/delete modal methods (quiz/assignment/file/link/folder).
 * Loaded right after materials_list.js on course_detail.html.
 */
Object.assign(MaterialsList.prototype, {
    attachMaterialActionListeners() {
        // Edit buttons
        this.container.querySelectorAll('.btn-edit-material').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const item = btn.closest('.material-item');
                const type = item.dataset.materialType;
                const id = parseInt(item.dataset.materialId);

                if (type === 'quiz') {
                    // Kuis: edit judul + soal di editor lengkap
                    window.open(`/quiz/${id}`, '_blank');
                } else if (['file', 'link', 'assignment'].includes(type)) {
                    // Berkas/Link/Tugas: edit judul & isi via modal
                    this.showEditMaterialModal(type, id);
                }
            });
        });

        // Delete buttons
        this.container.querySelectorAll('.btn-delete-material').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const item = btn.closest('.material-item');
                const type = item.dataset.materialType;
                const id = item.dataset.materialId;
                
                if (confirm('Hapus materi ini?')) {
                    this.deleteMaterial(type, parseInt(id));
                }
            });
        });

        // Archive buttons
        this.container.querySelectorAll('.btn-archive-material').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const item = btn.closest('.material-item');
                const id = item.dataset.materialId;
                const type = item.dataset.materialType;
                
                const typeNames = {
                    quiz: 'Kuis',
                    assignment: 'Tugas',
                    file: 'Berkas',
                    link: 'Link'
                };
                
                this.showArchiveConfirmation(parseInt(id), typeNames[type] || type);
            });
        });

        // Move to folder buttons
        this.container.querySelectorAll('.move-to-folder-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const item = btn.closest('.material-item');
                const id = item.dataset.materialId;
                const type = item.dataset.materialType;
                this.showMoveToFolderModal(parseInt(id), type);
            });
        });

        // Material item click (for all users, especially students)
        this.container.querySelectorAll('.material-item').forEach(item => {
            item.addEventListener('click', (e) => {
                // Don't fire when clicking action buttons
                if (e.target.closest('button')) return;
                const materialType = item.dataset.materialType;
                const materialId = item.dataset.materialId;
                this.onMaterialSelect(materialType, parseInt(materialId));
            });
        });
    },

    attachFolderActionListeners() {
        // Delete folder buttons
        this.container.querySelectorAll('.folder-delete-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const folderItem = btn.closest('.folder-item');
                const folderId = parseInt(folderItem.dataset.folderId);
                
                if (confirm('Hapus folder ini? Materi di dalamnya akan tetap ada.')) {
                    this.deleteFolder(folderId);
                }
            });
        });

        // Rename folder buttons
        this.container.querySelectorAll('.folder-rename-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const folderItem = btn.closest('.folder-item');
                const folderId = parseInt(folderItem.dataset.folderId);
                const folder = this.folders.find(f => f.id === folderId);
                
                if (folder) {
                    this.showRenameFolderModal(folderId, folder.name);
                }
            });
        });
    },

    showNotification(message, type = 'success') {
        const notification = document.createElement('div');
        notification.className = `fixed bottom-6 right-6 px-6 py-4 rounded-2xl shadow-2xl z-[100] animate-slide-up flex items-center gap-3 ${
            type === 'success' ? 'bg-green-600 text-white' : 'bg-red-600 text-white'
        }`;
        notification.innerHTML = `
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
            </svg>
            <span class="font-bold text-sm">${message}</span>
        `;
        document.body.appendChild(notification);
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transition = 'opacity 0.3s';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    },

    showAddMaterialModal() {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50';
        modal.innerHTML = `
            <div class="modal-content bg-white dark:bg-gray-900 rounded-[2rem] border-2 border-[#e5e5e5] dark:border-gray-700 shadow-2xl w-full max-w-lg max-h-[90vh] overflow-hidden flex flex-col animate-slide-up">
                <div class="bg-[#58cc02] px-8 py-6 text-white shrink-0">
                    <h3 class="text-xl font-black">Tambah Konten Baru</h3>
                    <p class="text-white/80 text-sm font-bold mt-1">Pilih jenis konten atau buat folder</p>
                </div>
                <div class="p-6 overflow-y-auto">
                    <!-- Folder Section -->
                    <div class="mb-5">
                        <p class="text-[10px] font-black text-[#afafaf] uppercase tracking-widest mb-3 px-1">Organisasi</p>
                        <button class="add-folder w-full text-left px-5 py-4 rounded-2xl border-2 border-[#e5e5e5] dark:border-gray-700 hover:border-[#ce82ff] hover:bg-purple-50 dark:hover:bg-gray-800 transition-all group flex items-center gap-4">
                            <div class="w-12 h-12 rounded-xl bg-purple-100 text-purple-600 flex items-center justify-center text-xl shrink-0 group-hover:bg-[#ce82ff] group-hover:text-white transition-all">📁</div>
                            <div>
                                <div class="font-black text-[#4b4b4b] dark:text-white group-hover:text-[#ce82ff] transition-colors">Buat Folder</div>
                                <div class="text-xs font-bold text-[#afafaf]">Organisir materi dalam folder</div>
                            </div>
                        </button>
                    </div>

                    <!-- Materials Section -->
                    <div>
                        <p class="text-[10px] font-black text-[#afafaf] uppercase tracking-widest mb-3 px-1">Materi & Tugas</p>
                        <div class="space-y-3">
                            <button class="add-quiz w-full text-left px-5 py-4 rounded-2xl border-2 border-[#e5e5e5] dark:border-gray-700 hover:border-[#ff9600] hover:bg-amber-50 dark:hover:bg-gray-800 transition-all group flex items-center gap-4">
                                <div class="w-12 h-12 rounded-xl bg-amber-100 text-amber-600 flex items-center justify-center text-xl shrink-0 group-hover:bg-[#ff9600] group-hover:text-white transition-all">📊</div>
                                <div>
                                    <div class="font-black text-[#4b4b4b] dark:text-white group-hover:text-[#ff9600] transition-colors">Kuis</div>
                                    <div class="text-xs font-bold text-[#afafaf]">Buat kuis interaktif</div>
                                </div>
                            </button>
                            <button class="add-assignment w-full text-left px-5 py-4 rounded-2xl border-2 border-[#e5e5e5] dark:border-gray-700 hover:border-[#58cc02] hover:bg-green-50 dark:hover:bg-gray-800 transition-all group flex items-center gap-4">
                                <div class="w-12 h-12 rounded-xl bg-green-100 text-green-600 flex items-center justify-center text-xl shrink-0 group-hover:bg-[#58cc02] group-hover:text-white transition-all">📝</div>
                                <div>
                                    <div class="font-black text-[#4b4b4b] dark:text-white group-hover:text-[#58cc02] transition-colors">Tugas</div>
                                    <div class="text-xs font-bold text-[#afafaf]">Berikan tugas kepada siswa</div>
                                </div>
                            </button>
                            <button class="add-file w-full text-left px-5 py-4 rounded-2xl border-2 border-[#e5e5e5] dark:border-gray-700 hover:border-[#1cb0f6] hover:bg-blue-50 dark:hover:bg-gray-800 transition-all group flex items-center gap-4">
                                <div class="w-12 h-12 rounded-xl bg-blue-100 text-blue-600 flex items-center justify-center text-xl shrink-0 group-hover:bg-[#1cb0f6] group-hover:text-white transition-all">📎</div>
                                <div>
                                    <div class="font-black text-[#4b4b4b] dark:text-white group-hover:text-[#1cb0f6] transition-colors">Berkas</div>
                                    <div class="text-xs font-bold text-[#afafaf]">Upload file materi</div>
                                </div>
                            </button>
                            <button class="add-link w-full text-left px-5 py-4 rounded-2xl border-2 border-[#e5e5e5] dark:border-gray-700 hover:border-indigo-500 hover:bg-indigo-50 dark:hover:bg-gray-800 transition-all group flex items-center gap-4">
                                <div class="w-12 h-12 rounded-xl bg-indigo-100 text-indigo-600 flex items-center justify-center text-xl shrink-0 group-hover:bg-indigo-600 group-hover:text-white transition-all">🔗</div>
                                <div>
                                    <div class="font-black text-[#4b4b4b] dark:text-white group-hover:text-indigo-600 transition-colors">Link</div>
                                    <div class="text-xs font-bold text-[#afafaf]">Tambahkan link eksternal</div>
                                </div>
                            </button>
                        </div>
                    </div>
                </div>
                <div class="px-6 pb-6 pt-2 shrink-0">
                    <button class="btn-duo btn-duo-ghost w-full h-14 text-sm cancel-add-material">BATAL</button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Cancel button
        modal.querySelector('.cancel-add-material').addEventListener('click', (e) => {
            e.stopPropagation();
            modal.remove();
        });

        // Add folder button
        modal.querySelector('.add-folder').addEventListener('click', (e) => {
            e.stopPropagation();
            modal.remove();
            this.showCreateFolderModal();
        });

        // Add quiz button
        modal.querySelector('.add-quiz').addEventListener('click', (e) => {
            e.stopPropagation();
            modal.remove();
            this.createQuickQuiz();
        });

        // Add assignment button
        modal.querySelector('.add-assignment').addEventListener('click', (e) => {
            e.stopPropagation();
            modal.remove();
            const assignmentModal = document.getElementById('create-assignment-modal');
            if (assignmentModal) {
                assignmentModal.classList.remove('hidden');
            }
        });

        // Add file button
        modal.querySelector('.add-file').addEventListener('click', (e) => {
            e.stopPropagation();
            modal.remove();
            const fileModal = document.getElementById('create-file-modal');
            if (fileModal) {
                fileModal.classList.remove('hidden');
            }
        });

        // Add link button
        modal.querySelector('.add-link').addEventListener('click', (e) => {
            e.stopPropagation();
            modal.remove();
            const linkModal = document.getElementById('create-link-modal');
            if (linkModal) {
                linkModal.classList.remove('hidden');
            }
        });

        // Close on overlay click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    },

    createQuickQuiz() {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50';
        modal.innerHTML = `
            <div class="modal-content bg-white rounded-[2.5rem] shadow-2xl w-full max-w-md overflow-hidden animate-slide-up">
                <div class="bg-gradient-to-br from-amber-500 to-amber-700 px-8 py-6 text-white">
                    <h3 class="text-xl font-black">Buat Kuis Baru</h3>
                    <p class="text-amber-100 text-sm mt-1">Buat kuis interaktif untuk siswa</p>
                </div>
                <div class="p-6">
                    <div class="mb-4">
                        <label class="block text-[10px] font-black text-gray-400 uppercase tracking-widest mb-2">Nama Kuis</label>
                        <input type="text" id="quiz-name-input" class="w-full px-6 py-4 bg-gray-50 border-2 border-gray-100 rounded-2xl focus:border-amber-500 outline-none font-bold" placeholder="Contoh: Kuis Bab 1, UTS, ..." autofocus>
                    </div>
                    <div id="quiz-modal-error" class="hidden p-4 bg-red-50 text-red-600 rounded-2xl text-xs font-bold text-center mb-4"></div>
                </div>
                <div class="px-6 pb-6 flex space-x-3">
                    <button class="quiz-cancel-btn flex-1 px-6 py-4 text-gray-500 bg-gray-100 rounded-2xl font-bold hover:bg-gray-200 transition-all">Batal</button>
                    <button class="quiz-create-btn flex-[2] px-6 py-4 bg-amber-600 text-white rounded-2xl font-bold shadow-lg shadow-amber-200 hover:bg-amber-700 active:scale-95">Buat Kuis</button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        const input = modal.querySelector('#quiz-name-input');
        input.focus();

        const createBtn = modal.querySelector('.quiz-create-btn');
        createBtn.addEventListener('click', async () => {
            const name = input.value.trim();
            const errorDiv = modal.querySelector('#quiz-modal-error');

            if (!name) {
                errorDiv.textContent = 'Nama kuis wajib diisi';
                errorDiv.classList.remove('hidden');
                return;
            }

            try {
                const response = await fetch(`/api/courses/${this.courseId}/quizzes`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: name, is_quiz: true })
                });
                const data = await response.json();

                if (data.success && data.quiz && data.quiz.id) {
                    modal.remove();
                    this.showNotification('Kuis berhasil dibuat! Membuka editor...', 'success');
                    setTimeout(() => {
                        window.location.href = `/quiz/${data.quiz.id}`;
                    }, 500);
                } else {
                    errorDiv.textContent = data.message || 'Gagal membuat kuis';
                    errorDiv.classList.remove('hidden');
                }
            } catch (error) {
                errorDiv.textContent = 'Terjadi kesalahan saat membuat kuis';
                errorDiv.classList.remove('hidden');
                console.error('Error creating quiz:', error);
            }
        });

        modal.querySelector('.quiz-cancel-btn').addEventListener('click', () => modal.remove());

        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') createBtn.click();
        });
    },

    showCreateFolderModal() {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50';
        modal.innerHTML = `
            <div class="modal-content bg-white rounded-[2.5rem] shadow-2xl w-full max-w-md overflow-hidden animate-slide-up">
                <div class="bg-gradient-to-br from-purple-500 to-purple-700 px-8 py-6 text-white">
                    <h3 class="text-xl font-black">Buat Folder Baru</h3>
                    <p class="text-purple-100 text-sm mt-1">Organisir materi kelas Anda</p>
                </div>
                <div class="p-6">
                    <div class="mb-4">
                        <label class="block text-[10px] font-black text-gray-400 uppercase tracking-widest mb-2">Nama Folder</label>
                        <input type="text" id="folder-name-input" class="w-full px-6 py-4 bg-gray-50 border-2 border-gray-100 rounded-2xl focus:border-purple-500 outline-none font-bold" placeholder="Contoh: Bab 1, UTS, Materi Ganjil..." autofocus>
                    </div>
                    <div id="folder-modal-error" class="hidden p-4 bg-red-50 text-red-600 rounded-2xl text-xs font-bold text-center mb-4"></div>
                </div>
                <div class="px-6 pb-6 flex space-x-3">
                    <button class="folder-cancel-btn flex-1 px-6 py-4 text-gray-500 bg-gray-100 rounded-2xl font-bold hover:bg-gray-200 transition-all">Batal</button>
                    <button class="folder-create-btn flex-[2] px-6 py-4 bg-purple-600 text-white rounded-2xl font-bold shadow-lg shadow-purple-200 hover:bg-purple-700 active:scale-95">Buat Folder</button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        const input = modal.querySelector('#folder-name-input');
        input.focus();

        const createBtn = modal.querySelector('.folder-create-btn');
        createBtn.addEventListener('click', async () => {
            const name = input.value.trim();
            const errorDiv = modal.querySelector('#folder-modal-error');

            if (!name) {
                errorDiv.textContent = 'Nama folder wajib diisi';
                errorDiv.classList.remove('hidden');
                return;
            }

            try {
                const response = await fetch(`/api/courses/${this.courseId}/folders`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name })
                });
                const data = await response.json();

                if (data.success) {
                    modal.remove();
                    this.loadAllData().then(() => {
                        this.render();
                        this.attachEventListeners();
                    });
                    this.showNotification('Folder berhasil dibuat!', 'success');
                } else {
                    errorDiv.textContent = data.message || 'Gagal membuat folder';
                    errorDiv.classList.remove('hidden');
                }
            } catch (error) {
                errorDiv.textContent = 'Terjadi kesalahan saat membuat folder';
                errorDiv.classList.remove('hidden');
                console.error('Error creating folder:', error);
            }
        });

        modal.querySelector('.folder-cancel-btn').addEventListener('click', () => modal.remove());

        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') createBtn.click();
        });
    },

    showArchiveConfirmation(id, typeName) {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50';
        modal.innerHTML = `
            <div class="modal-content bg-white rounded-[2.5rem] shadow-2xl w-full max-w-md overflow-hidden animate-slide-up">
                <div class="bg-gradient-to-br from-amber-500 to-amber-700 px-8 py-6 text-white">
                    <div class="flex items-center gap-3">
                        <div class="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center">
                            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4"/>
                            </svg>
                        </div>
                        <div>
                            <h3 class="text-xl font-black">Arsipkan ${typeName}</h3>
                            <p class="text-amber-100 text-sm mt-0.5">Pindahkan ke arsip kelas</p>
                        </div>
                    </div>
                </div>
                <div class="p-8">
                    <p class="text-gray-700 font-bold mb-4">
                        Arsipkan ${typeName} ini?
                    </p>
                    <div class="bg-amber-50 border border-amber-200 rounded-2xl p-5 mb-6">
                        <div class="flex items-start gap-3">
                            <svg class="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                            </svg>
                            <div>
                                <p class="text-sm font-bold text-amber-900 mb-2">${typeName} yang diarsipkan:</p>
                                <ul class="text-xs text-amber-700 space-y-1.5">
                                    <li>• Tetap tersimpan di menu <strong>Arsip</strong></li>
                                    <li>• Tidak ditampilkan di daftar materi</li>
                                    <li>• Data <strong>tetap tersimpan</strong></li>
                                    <li>• Dapat dipulihkan kapan saja</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                    <div class="flex gap-3">
                        <button class="cancel-archive flex-1 px-5 py-3.5 bg-gray-100 text-gray-700 rounded-2xl font-bold hover:bg-gray-200 transition-all">
                            Batal
                        </button>
                        <button class="confirm-archive flex-1 px-5 py-3.5 bg-amber-600 text-white rounded-2xl font-bold hover:bg-amber-700 transition-all shadow-lg shadow-amber-200">
                            Arsipkan
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        const item = this.container.querySelector(`[data-material-id="${id}"]`);
        const type = item?.dataset.materialType;

        modal.querySelector('.cancel-archive').addEventListener('click', () => {
            modal.remove();
        });

        modal.querySelector('.confirm-archive').addEventListener('click', async () => {
            if (type === 'quiz') {
                await this.archiveQuiz(id);
            } else if (type === 'assignment') {
                await this.archiveAssignment(id);
            } else if (type === 'file') {
                await this.archiveFile(id);
            } else if (type === 'link') {
                await this.archiveLink(id);
            }
            modal.remove();
        });

        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    },

    async archiveQuiz(quizId) {
        try {
            const response = await fetch(`/api/quiz/${quizId}/archive`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            const data = await response.json();
            
            if (data.success) {
                this.refresh();
                this.showNotification('Kuis berhasil diarsipkan', 'success');
            } else {
                this.showNotification(data.message || 'Gagal mengarsipkan kuis', 'error');
            }
        } catch (error) {
            console.error('Error archiving quiz:', error);
            this.showNotification('Terjadi kesalahan', 'error');
        }
    },

    async archiveAssignment(assignmentId) {
        try {
            const response = await fetch(`/api/assignment/${assignmentId}/archive`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            const data = await response.json();
            
            if (data.success) {
                this.refresh();
                this.showNotification('Tugas berhasil diarsipkan', 'success');
            } else {
                this.showNotification(data.message || 'Gagal mengarsipkan tugas', 'error');
            }
        } catch (error) {
            console.error('Error archiving assignment:', error);
            this.showNotification('Terjadi kesalahan', 'error');
        }
    },

    async archiveFile(fileId) {
        try {
            const response = await fetch(`/api/file/${fileId}/archive`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            const data = await response.json();
            
            if (data.success) {
                this.refresh();
                this.showNotification('Berkas berhasil diarsipkan', 'success');
            } else {
                this.showNotification(data.message || 'Gagal mengarsipkan berkas', 'error');
            }
        } catch (error) {
            console.error('Error archiving file:', error);
            this.showNotification('Terjadi kesalahan', 'error');
        }
    },

    async archiveLink(linkId) {
        try {
            const response = await fetch(`/api/link/${linkId}/archive`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            const data = await response.json();
            
            if (data.success) {
                this.refresh();
                this.showNotification('Link berhasil diarsipkan', 'success');
            } else {
                this.showNotification(data.message || 'Gagal mengarsipkan link', 'error');
            }
        } catch (error) {
            console.error('Error archiving link:', error);
            this.showNotification('Terjadi kesalahan', 'error');
        }
    },

    showEditMaterialModal(type, id) {
        const typeLabel = { file: 'Berkas', link: 'Link', assignment: 'Tugas' }[type];
        const t = (window.topicsData || []).find(x => x.id === id && x.type === typeLabel) || {};
        const isLink = type === 'link';
        const headerTitle = { file: 'Edit Berkas', link: 'Edit Link', assignment: 'Edit Tugas' }[type];

        const modal = document.createElement('div');
        modal.className = 'modal-overlay fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[60] p-4';
        modal.innerHTML = `
            <div class="bg-white dark:bg-gray-900 rounded-[2rem] border-2 border-[#e5e5e5] dark:border-gray-700 shadow-2xl w-full max-w-lg overflow-hidden animate-slide-up">
                <div class="bg-[#1cb0f6] px-8 py-6 text-white">
                    <h3 class="text-xl font-black">${headerTitle}</h3>
                    <p class="text-white/80 text-sm font-bold mt-0.5">Ubah judul &amp; isi materi</p>
                </div>
                <div class="p-8 space-y-5">
                    <div>
                        <label class="block text-[11px] font-black text-[#afafaf] uppercase tracking-widest mb-2">Judul</label>
                        <input id="edit-mat-title" type="text" maxlength="200" class="w-full px-5 py-4 bg-[#f7f7f7] dark:bg-gray-800 border-2 border-[#e5e5e5] dark:border-gray-700 rounded-2xl font-black text-[#4b4b4b] dark:text-white outline-none focus:border-[#1cb0f6]" placeholder="Judul materi">
                    </div>
                    ${isLink ? `
                    <div>
                        <label class="block text-[11px] font-black text-[#afafaf] uppercase tracking-widest mb-2">URL</label>
                        <input id="edit-mat-url" type="text" class="w-full px-5 py-4 bg-[#f7f7f7] dark:bg-gray-800 border-2 border-[#e5e5e5] dark:border-gray-700 rounded-2xl font-bold text-[#4b4b4b] dark:text-white outline-none focus:border-[#1cb0f6]" placeholder="https://...">
                    </div>` : ''}
                    <div>
                        <label class="block text-[11px] font-black text-[#afafaf] uppercase tracking-widest mb-2">Deskripsi <span class="text-[#afafaf] normal-case">(opsional)</span></label>
                        <textarea id="edit-mat-desc" rows="4" class="w-full px-5 py-4 bg-[#f7f7f7] dark:bg-gray-800 border-2 border-[#e5e5e5] dark:border-gray-700 rounded-2xl font-bold text-[#4b4b4b] dark:text-white outline-none focus:border-[#1cb0f6]" placeholder="Deskripsi materi..."></textarea>
                    </div>
                    <div id="edit-mat-error" class="hidden p-3 bg-red-50 text-[#ff4b4b] rounded-xl text-xs font-black text-center"></div>
                </div>
                <div class="px-8 pb-8 flex gap-3">
                    <button class="edit-mat-cancel btn-duo btn-duo-ghost flex-1 h-14 text-sm">BATAL</button>
                    <button class="edit-mat-save btn-duo btn-duo-green flex-[2] h-14 text-sm">SIMPAN</button>
                </div>
            </div>`;
        document.body.appendChild(modal);

        // Set nilai secara programatik (aman dari masalah escaping)
        modal.querySelector('#edit-mat-title').value = t.name || '';
        if (isLink) modal.querySelector('#edit-mat-url').value = t.url || '';
        modal.querySelector('#edit-mat-desc').value = t.description || '';

        const close = () => modal.remove();
        modal.querySelector('.edit-mat-cancel').addEventListener('click', close);
        modal.addEventListener('click', (e) => { if (e.target === modal) close(); });
        modal.querySelector('#edit-mat-title').focus();

        modal.querySelector('.edit-mat-save').addEventListener('click', async () => {
            const err = modal.querySelector('#edit-mat-error');
            const newTitle = modal.querySelector('#edit-mat-title').value.trim();
            const desc = modal.querySelector('#edit-mat-desc').value.trim();
            const linkUrl = isLink ? modal.querySelector('#edit-mat-url').value.trim() : '';
            err.classList.add('hidden');
            if (!newTitle) { err.textContent = 'Judul tidak boleh kosong'; err.classList.remove('hidden'); return; }
            if (isLink && !linkUrl) { err.textContent = 'URL tidak boleh kosong'; err.classList.remove('hidden'); return; }

            const endpoints = { file: `/api/file/${id}`, link: `/api/link/${id}`, assignment: `/api/assignment/${id}` };
            const bodies = {
                file: { name: newTitle, description: desc },
                link: { name: newTitle, url: linkUrl, description: desc },
                assignment: { title: newTitle, description: desc },
            };
            try {
                const res = await fetch(endpoints[type], {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(bodies[type])
                });
                const data = await res.json();
                if (data.success) {
                    close();
                    this.refresh();
                    this.showNotification('Materi berhasil diperbarui', 'success');
                } else {
                    err.textContent = data.message || 'Gagal menyimpan'; err.classList.remove('hidden');
                }
            } catch (e) {
                err.textContent = 'Terjadi kesalahan koneksi'; err.classList.remove('hidden');
            }
        });
    },

    showMoveToFolderModal(materialId, materialType) {
        if (this.folders.length === 0) {
            this.showNotification('Belum ada folder. Buat folder terlebih dahulu.', 'error');
            return;
        }

        const modal = document.createElement('div');
        modal.className = 'modal-overlay fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50';
        
        const folderOptions = this.folders.map(f => 
            `<option value="${f.id}">${f.name}</option>`
        ).join('');

        modal.innerHTML = `
            <div class="modal-content bg-white rounded-[2.5rem] shadow-2xl w-full max-w-md overflow-hidden animate-slide-up">
                <div class="bg-gradient-to-br from-purple-500 to-purple-700 px-8 py-6 text-white">
                    <h3 class="text-xl font-black">Pindah ke Folder</h3>
                    <p class="text-purple-100 text-sm mt-1">Pilih folder tujuan</p>
                </div>
                <div class="p-6">
                    <select id="folder-select" class="w-full px-6 py-4 bg-gray-50 border-2 border-gray-100 rounded-2xl focus:border-purple-500 outline-none font-bold bg-white">
                        <option value="">-- Pilih Folder --</option>
                        ${folderOptions}
                    </select>
                    <div id="move-modal-error" class="hidden p-4 bg-red-50 text-red-600 rounded-2xl text-xs font-bold text-center mt-4"></div>
                </div>
                <div class="px-6 pb-6 flex space-x-3">
                    <button class="move-cancel-btn flex-1 px-6 py-4 text-gray-500 bg-gray-100 rounded-2xl font-bold hover:bg-gray-200 transition-all">Batal</button>
                    <button class="move-confirm-btn flex-[2] px-6 py-4 bg-purple-600 text-white rounded-2xl font-bold shadow-lg shadow-purple-200 hover:bg-purple-700 active:scale-95">Pindah</button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        const confirmBtn = modal.querySelector('.move-confirm-btn');
        confirmBtn.addEventListener('click', async () => {
            const folderId = modal.querySelector('#folder-select').value;
            const errorDiv = modal.querySelector('#move-modal-error');

            if (!folderId) {
                errorDiv.textContent = 'Pilih folder tujuan';
                errorDiv.classList.remove('hidden');
                return;
            }

            await this.moveMaterialToFolder(materialId, parseInt(folderId), materialType);
            modal.remove();
        });

        modal.querySelector('.move-cancel-btn').addEventListener('click', () => modal.remove());
    },

    showRenameFolderModal(folderId, currentName) {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50';
        modal.innerHTML = `
            <div class="modal-content bg-white rounded-[2.5rem] shadow-2xl w-full max-w-md overflow-hidden animate-slide-up">
                <div class="bg-gradient-to-br from-purple-500 to-purple-700 px-8 py-6 text-white">
                    <h3 class="text-xl font-black">Ganti Nama Folder</h3>
                    <p class="text-purple-100 text-sm mt-1">Masukkan nama baru</p>
                </div>
                <div class="p-6">
                    <input type="text" id="folder-rename-input" class="w-full px-6 py-4 bg-gray-50 border-2 border-gray-100 rounded-2xl focus:border-purple-500 outline-none font-bold" value="${currentName}" autofocus>
                    <div id="rename-modal-error" class="hidden p-4 bg-red-50 text-red-600 rounded-2xl text-xs font-bold text-center mt-4"></div>
                </div>
                <div class="px-6 pb-6 flex space-x-3">
                    <button class="rename-cancel-btn flex-1 px-6 py-4 text-gray-500 bg-gray-100 rounded-2xl font-bold hover:bg-gray-200 transition-all">Batal</button>
                    <button class="rename-confirm-btn flex-[2] px-6 py-4 bg-purple-600 text-white rounded-2xl font-bold shadow-lg shadow-purple-200 hover:bg-purple-700 active:scale-95">Simpan</button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        const confirmBtn = modal.querySelector('.rename-confirm-btn');
        confirmBtn.addEventListener('click', async () => {
            const newName = modal.querySelector('#folder-rename-input').value.trim();
            const errorDiv = modal.querySelector('#rename-modal-error');

            if (!newName) {
                errorDiv.textContent = 'Nama folder tidak boleh kosong';
                errorDiv.classList.remove('hidden');
                return;
            }

            try {
                const response = await fetch(`/api/folders/${folderId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: newName })
                });
                const data = await response.json();

                if (data.success) {
                    modal.remove();
                    const folder = this.folders.find(f => f.id === folderId);
                    if (folder) folder.name = newName;
                    this.render();
                    this.attachEventListeners();
                    this.showNotification('Nama folder berhasil diubah', 'success');
                } else {
                    errorDiv.textContent = data.message || 'Gagal mengubah nama folder';
                    errorDiv.classList.remove('hidden');
                }
            } catch (error) {
                errorDiv.textContent = 'Terjadi kesalahan';
                errorDiv.classList.remove('hidden');
                console.error('Error renaming folder:', error);
            }
        });

        modal.querySelector('.rename-cancel-btn').addEventListener('click', () => modal.remove());
    },

    async deleteMaterial(type, id) {
        try {
            // Endpoint yang benar: /api/<type>/<id> (quiz/assignment/file/link)
            const response = await fetch(`/api/${type}/${id}`, { method: 'DELETE' });
            const data = await response.json();

            if (data.success) {
                this.refresh();
                this.showNotification('Materi berhasil dihapus', 'success');
            } else {
                this.showNotification(data.message || 'Gagal menghapus materi', 'error');
            }
        } catch (error) {
            console.error('Error deleting material:', error);
            this.showNotification('Terjadi kesalahan', 'error');
        }
    },

    async deleteFolder(folderId) {
        try {
            const response = await fetch(`/api/folders/${folderId}`, { method: 'DELETE' });
            const data = await response.json();

            if (data.success) {
                this.folders = this.folders.filter(f => f.id !== folderId);
                this.expandedFolders.delete(folderId);
                this.render();
                this.attachEventListeners();
                this.showNotification('Folder berhasil dihapus', 'success');
            } else {
                this.showNotification(data.message || 'Gagal menghapus folder', 'error');
            }
        } catch (error) {
            console.error('Error deleting folder:', error);
            this.showNotification('Terjadi kesalahan', 'error');
        }
    },

    refresh() {
        this.loadAllData().then(() => {
            this.render();
            this.attachEventListeners();
        });
    },
});
