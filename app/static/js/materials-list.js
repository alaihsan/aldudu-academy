/**
 * MaterialsList Component
 * Displays materials (quizzes, assignments, files, links) in list view
 */
class MaterialsList {
    constructor(containerId, courseId, options = {}) {
        this.container = document.getElementById(containerId);
        this.courseId = courseId;
        this.materials = [];
        this.filteredMaterials = [];
        this.currentFolderId = null;
        this.filterType = 'all';
        this.searchQuery = '';
        this.onMaterialSelect = options.onMaterialSelect || (() => {});
        this.onMaterialDelete = options.onMaterialDelete || (() => {});

        this.init();
    }

    async init() {
        await this.loadMaterials();
        this.render();
        this.attachEventListeners();
    }

    async loadMaterials() {
        try {
            // Load materials from window.topicsData if available (from template)
            if (window.topicsData && Array.isArray(window.topicsData)) {
                // Transform topics from template to standardized format
                this.materials = window.topicsData.map(topic => {
                    const typeMap = {
                        'Kuis': 'quiz',
                        'Tugas': 'assignment',
                        'Berkas': 'file',
                        'Link': 'link'
                    };

                    const colorMap = {
                        'quiz': 'purple',
                        'assignment': 'blue',
                        'file': 'gray',
                        'link': 'green'
                    };

                    const iconMap = {
                        'quiz': '📊',
                        'assignment': '📝',
                        'file': '📎',
                        'link': '🔗'
                    };

                    const type = typeMap[topic.type] || 'file';
                    return {
                        id: topic.id,
                        type: type,
                        title: topic.name || 'Untitled',
                        name: topic.name || 'Untitled',
                        created_at: topic.created_at || new Date().toISOString(),
                        folder_id: topic.folder_id || null,
                        order: topic.order || 0,
                        icon: iconMap[type],
                        color: colorMap[type],
                        due_date: topic.due_date,
                        filename: topic.filename,
                        url: topic.url
                    };
                });
            } else {
                // Fallback: Initialize empty
                this.materials = [];
            }

            this.applyFilters();
        } catch (error) {
            console.error('Error loading materials:', error);
            this.materials = [];
        }
    }

    applyFilters() {
        this.filteredMaterials = this.materials.filter(m => {
            // Filter by folder
            if (this.currentFolderId !== null) {
                const folderMatch = m.folder_id === this.currentFolderId;
                if (!folderMatch) return false;
            } else {
                // Show all materials not in any folder (root level)
                const noFolder = !m.folder_id;
                if (!noFolder) return false;
            }

            // Filter by type
            if (this.filterType !== 'all' && m.type !== this.filterType) {
                return false;
            }

            // Filter by search
            if (this.searchQuery) {
                const query = this.searchQuery.toLowerCase();
                const title = (m.title || m.name || '').toLowerCase();
                return title.includes(query);
            }

            return true;
        });

        // Sort by creation date (newest first)
        this.filteredMaterials.sort((a, b) => {
            const dateA = new Date(a.created_at);
            const dateB = new Date(b.created_at);
            return dateB - dateA;
        });
    }

    render() {
        const typeFilterOptions = [
            { value: 'all', label: 'Semua' },
            { value: 'quiz', label: 'Quiz' },
            { value: 'assignment', label: 'Tugas' },
            { value: 'file', label: 'File' },
            { value: 'link', label: 'Link' }
        ];

        const html = `
            <div class="materials-list">
                <!-- Header -->
                <div class="materials-list-header flex items-center justify-between mb-6">
                    <div>
                        <h2 class="text-2xl font-bold text-gray-900" id="folder-title">Semua Materi</h2>
                        <p class="text-sm text-gray-500 mt-1">
                            ${this.filteredMaterials.length} materi
                        </p>
                    </div>
                    <button class="btn btn-primary btn-add-material" title="Tambah Material">
                        <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
                        </svg>
                        Tambah Materi
                    </button>
                </div>

                <!-- Search and Filter -->
                <div class="materials-filters flex gap-4 mb-6">
                    <div class="flex-1">
                        <input type="text" id="search-materials" class="form-control w-full px-4 py-2 border border-gray-300 rounded-lg"
                               placeholder="Cari materi...">
                    </div>
                    <select id="filter-type" class="form-control px-4 py-2 border border-gray-300 rounded-lg">
                        ${typeFilterOptions.map(opt => `
                            <option value="${opt.value}" ${opt.value === this.filterType ? 'selected' : ''}>${opt.label}</option>
                        `).join('')}
                    </select>
                </div>

                <!-- Breadcrumb -->
                <div class="materials-breadcrumb text-sm text-gray-600 mb-4" id="breadcrumb">
                    Materi Kelas
                </div>

                <!-- Materials List -->
                <div class="materials-items space-y-3">
                    ${this.filteredMaterials.length > 0 ? this.renderMaterials() : `
                        <div class="text-center py-12">
                            <svg class="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                            </svg>
                            <p class="text-gray-500">Belum ada materi</p>
                        </div>
                    `}
                </div>
            </div>
        `;

        this.container.innerHTML = html;
    }

    renderMaterials() {
        return this.filteredMaterials.map(material => {
            const createdDate = new Date(material.created_at);
            const formattedDate = createdDate.toLocaleDateString('id-ID', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });

            const typeLabels = {
                quiz: 'Quiz',
                assignment: 'Tugas',
                file: 'File',
                link: 'Link'
            };

            const typeColors = {
                quiz: 'purple',
                assignment: 'blue',
                file: 'gray',
                link: 'green'
            };

            return `
                <div class="material-item flex items-center gap-4 p-4 rounded-lg border border-gray-200 hover:border-primary-300 hover:bg-primary-50 transition-all group cursor-move"
                     draggable="true"
                     data-material-id="${material.id}"
                     data-material-type="${material.type}">

                    <!-- Icon -->
                    <div class="flex-shrink-0 w-12 h-12 rounded-lg bg-${typeColors[material.type]}-100 flex items-center justify-center text-xl">
                        ${material.icon || '📄'}
                    </div>

                    <!-- Content -->
                    <div class="flex-1 min-w-0">
                        <h3 class="text-sm font-semibold text-gray-900 truncate">
                            ${material.title || material.name || 'Untitled'}
                        </h3>
                        <p class="text-xs text-gray-500 mt-1">
                            <span class="badge badge-${typeColors[material.type]}">${typeLabels[material.type]}</span>
                            <span class="ml-2">Dibuat ${formattedDate}</span>
                        </p>
                    </div>

                    <!-- Additional Info -->
                    ${material.type === 'assignment' && material.due_date ? `
                        <div class="flex-shrink-0 text-right">
                            <p class="text-xs text-gray-600">
                                Deadline: ${new Date(material.due_date).toLocaleDateString('id-ID')}
                            </p>
                        </div>
                    ` : material.type === 'file' && material.filename ? `
                        <div class="flex-shrink-0 text-right">
                            <p class="text-xs text-gray-600">
                                ${material.filename.split('.').pop().toUpperCase()}
                            </p>
                        </div>
                    ` : ''}

                    <!-- Actions -->
                    <div class="flex-shrink-0 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button class="btn-view-material p-2 text-gray-500 hover:text-primary-600 transition-colors"
                                title="Lihat">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                            </svg>
                        </button>
                        <button class="btn-delete-material p-2 text-gray-500 hover:text-red-600 transition-colors"
                                title="Hapus">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                            </svg>
                        </button>
                    </div>
                </div>
            `;
        }).join('');
    }

    attachEventListeners() {
        // Search input
        const searchInput = this.container.querySelector('#search-materials');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.searchQuery = e.target.value;
                this.applyFilters();
                this.render();
                this.attachEventListeners();
            });
        }

        // Filter type
        const filterType = this.container.querySelector('#filter-type');
        if (filterType) {
            filterType.addEventListener('change', (e) => {
                this.filterType = e.target.value;
                this.applyFilters();
                this.render();
                this.attachEventListeners();
            });
        }

        // Drag and drop
        this.container.querySelectorAll('.material-item').forEach(item => {
            item.addEventListener('dragstart', (e) => {
                const materialId = item.dataset.materialId;
                const materialType = item.dataset.materialType;
                e.dataTransfer.effectAllowed = 'move';
                e.dataTransfer.setData('application/json', JSON.stringify({
                    type: 'material',
                    materialId: parseInt(materialId),
                    materialType: materialType
                }));
            });
        });

        // View material
        this.container.querySelectorAll('.btn-view-material').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const item = btn.closest('.material-item');
                const materialType = item.dataset.materialType;
                const materialId = item.dataset.materialId;
                this.onMaterialSelect(materialType, parseInt(materialId));
            });
        });

        // Delete material
        this.container.querySelectorAll('.btn-delete-material').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const item = btn.closest('.material-item');
                const materialType = item.dataset.materialType;
                const materialId = item.dataset.materialId;
                if (confirm('Hapus materi ini?')) {
                    this.deleteMaterial(materialType, parseInt(materialId));
                }
            });
        });

        // Add material
        const addBtn = this.container.querySelector('.btn-add-material');
        if (addBtn) {
            addBtn.addEventListener('click', () => {
                this.showAddMaterialModal();
            });
        }
    }

    setFolder(folderId) {
        this.currentFolderId = folderId;
        this.applyFilters();
        this.render();
        this.attachEventListeners();

        // Update title
        const title = this.container.querySelector('#folder-title');
        if (title) {
            title.textContent = folderId === null ? 'Semua Materi' : 'Materi di Folder';
        }
    }

    async deleteMaterial(type, id) {
        try {
            const url = `/${type}s/${id}`;
            const response = await fetch(url, { method: 'DELETE' });
            const data = await response.json();
            if (data.success) {
                await this.loadMaterials();
                this.render();
                this.attachEventListeners();
                this.onMaterialDelete(type, id);
            }
        } catch (error) {
            console.error('Error deleting material:', error);
        }
    }

    showAddMaterialModal() {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay fixed inset-0 bg-black/50 flex items-center justify-center z-50';
        modal.innerHTML = `
            <div class="modal-content bg-white rounded-2xl shadow-2xl p-6 w-96">
                <h3 class="text-lg font-bold mb-6">Tambah Materi</h3>
                <div class="space-y-2">
                    <button class="add-quiz w-full text-left px-4 py-3 rounded-lg hover:bg-purple-50 border border-gray-200 transition-colors">
                        <div class="font-semibold text-purple-600">📊 Quiz</div>
                        <div class="text-xs text-gray-600">Buat kuis interaktif</div>
                    </button>
                    <button class="add-assignment w-full text-left px-4 py-3 rounded-lg hover:bg-blue-50 border border-gray-200 transition-colors">
                        <div class="font-semibold text-blue-600">📝 Tugas</div>
                        <div class="text-xs text-gray-600">Berikan tugas kepada siswa</div>
                    </button>
                    <button class="add-file w-full text-left px-4 py-3 rounded-lg hover:bg-gray-50 border border-gray-200 transition-colors">
                        <div class="font-semibold text-gray-600">📎 File</div>
                        <div class="text-xs text-gray-600">Upload file materi</div>
                    </button>
                    <button class="add-link w-full text-left px-4 py-3 rounded-lg hover:bg-green-50 border border-gray-200 transition-colors">
                        <div class="font-semibold text-green-600">🔗 Link</div>
                        <div class="text-xs text-gray-600">Tambahkan link eksternal</div>
                    </button>
                </div>
                <button class="btn btn-secondary w-full mt-4">Batal</button>
            </div>
        `;

        document.body.appendChild(modal);

        modal.querySelector('.add-quiz').addEventListener('click', () => {
            modal.remove();
            window.location.href = `/courses/${this.courseId}/quiz/new`;
        });

        modal.querySelector('.add-assignment').addEventListener('click', () => {
            modal.remove();
            window.location.href = `/courses/${this.courseId}/assignment/new`;
        });

        modal.querySelector('.add-file').addEventListener('click', () => {
            modal.remove();
            // Trigger file upload modal or navigate
        });

        modal.querySelector('.add-link').addEventListener('click', () => {
            modal.remove();
            // Trigger link creation modal or navigate
        });

        modal.querySelector('.btn-secondary').addEventListener('click', () => modal.remove());
    }

    refresh() {
        this.loadMaterials().then(() => {
            this.render();
            this.attachEventListeners();
        });
    }
}
