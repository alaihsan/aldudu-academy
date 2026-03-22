/**
 * MaterialsList Component
 * Displays materials (quizzes, assignments, files, links) with List view
 * macOS Finder-style list with detailed time and file type information
 * Full-width layout with integrated folder management
 */
class MaterialsList {
    constructor(containerId, courseId, options = {}) {
        this.container = document.getElementById(containerId);
        this.courseId = courseId;
        this.materials = [];
        this.filteredMaterials = [];
        this.filterType = 'all';
        this.searchQuery = '';
        this.isTeacher = options.isTeacher || false;
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
            if (window.topicsData && Array.isArray(window.topicsData)) {
                this.materials = window.topicsData.map(topic => {
                    const typeMap = {
                        'Kuis': 'quiz',
                        'Tugas': 'assignment',
                        'Berkas': 'file',
                        'Link': 'link',
                        'Diskusi': 'discussion'
                    };

                    const colorMap = {
                        'quiz': 'amber',
                        'assignment': 'green',
                        'file': 'blue',
                        'link': 'indigo',
                        'discussion': 'purple'
                    };

                    const iconMap = {
                        'quiz': '📊',
                        'assignment': '📝',
                        'file': '📎',
                        'link': '🔗',
                        'discussion': '💬'
                    };

                    const type = typeMap[topic.type] || 'file';
                    return {
                        id: topic.id,
                        type: type,
                        title: topic.name || 'Untitled',
                        name: topic.name || 'Untitled',
                        created_at: topic.created_at || new Date().toISOString(),
                        order: topic.order || 0,
                        icon: iconMap[type],
                        color: colorMap[type],
                        due_date: topic.due_date,
                        filename: topic.filename,
                        url: topic.url,
                        description: topic.description
                    };
                });
            } else {
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
            // Filter by type
            if (this.filterType !== 'all' && m.type !== this.filterType) {
                return false;
            }

            // Filter by search query
            if (this.searchQuery) {
                const query = this.searchQuery.toLowerCase().trim();
                
                // Search in title/name
                const title = (m.title || m.name || '').toLowerCase();
                
                // Search in description
                const description = (m.description || '').toLowerCase();
                
                // Search in type label
                const typeLabel = this.getTypeLabel(m.type).toLowerCase();
                
                // Search in file extension (for files)
                const fileExt = (m.filename || '').split('.').pop().toLowerCase();
                
                // Check if query matches any field
                const matchesTitle = title.includes(query);
                const matchesDescription = description.includes(query);
                const matchesType = typeLabel.includes(query);
                const matchesFileExt = fileExt.includes(query);
                
                if (!matchesTitle && !matchesDescription && !matchesType && !matchesFileExt) {
                    return false;
                }
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

    getTypeLabel(type) {
        const labels = {
            quiz: 'Kuis',
            assignment: 'Tugas',
            file: 'Berkas',
            link: 'Link',
            discussion: 'Diskusi'
        };
        return labels[type] || type;
    }

    render() {
        const typeFilterOptions = [
            { value: 'all', label: 'Semua' },
            { value: 'quiz', label: 'Kuis' },
            { value: 'assignment', label: 'Tugas' },
            { value: 'file', label: 'Berkas' },
            { value: 'link', label: 'Link' },
            { value: 'discussion', label: 'Diskusi' }
        ];

        const html = `
            <div class="materials-wrapper">
                <!-- Header -->
                <div class="materials-header flex items-center justify-between mb-6">
                    <div>
                        <h2 class="text-2xl font-bold text-gray-900">Semua Materi</h2>
                        <p class="text-sm text-gray-500 mt-1">
                            ${this.filteredMaterials.length} ${this.filteredMaterials.length === 1 ? 'materi' : 'materi'}${this.searchQuery ? ` (menampilkan hasil untuk "${this.searchQuery}")` : ''}
                        </p>
                    </div>

                    ${this.isTeacher ? `
                    <button class="btn btn-primary btn-add-material inline-flex items-center px-4 py-2.5 bg-green-600 text-white rounded-xl font-bold text-sm shadow-lg shadow-green-200 hover:bg-green-700 transition-all active:scale-95">
                        <svg class="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 4v16m8-8H4"/>
                        </svg>
                        Tambah Materi
                    </button>
                    ` : ''}
                </div>

                <!-- Search and Filter -->
                <div class="materials-filters flex flex-col sm:flex-row gap-4 mb-6">
                    <div class="flex-1 relative">
                        <svg class="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                        </svg>
                        <input type="text" id="search-materials" class="w-full pl-10 pr-10 py-2.5 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-green-500 outline-none transition-all"
                               placeholder="Cari materi, tugas, kuis, diskusi...">
                        ${this.searchQuery ? `
                        <button id="clear-search" class="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-full transition-all" title="Hapus pencarian">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                            </svg>
                        </button>
                        ` : ''}
                    </div>
                    <select id="filter-type" class="form-control px-4 py-2.5 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-green-500 outline-none transition-all font-semibold text-sm min-w-[150px]">
                        ${typeFilterOptions.map(opt => `
                            <option value="${opt.value}" ${opt.value === this.filterType ? 'selected' : ''}>${opt.label}</option>
                        `).join('')}
                    </select>
                </div>

                <!-- Materials List -->
                <div class="materials-items materials-list-view">
                    ${this.filteredMaterials.length > 0 ? this.renderListView() : `
                        <div class="empty-state text-center py-16 bg-white rounded-3xl border-2 border-dashed border-gray-200">
                            <div class="w-20 h-20 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-4">
                                <svg class="w-10 h-10 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                                </svg>
                            </div>
                            <p class="text-gray-500 font-semibold">Belum ada materi</p>
                            <p class="text-sm text-gray-400 mt-1">Klik "Tambah Materi" untuk menambahkan materi</p>
                        </div>
                    `}
                </div>
            </div>
        `;

        this.container.innerHTML = html;
    }

    renderMaterials() {
        return this.renderListView();
    }

    renderListView() {
        return `<div class="space-y-2">` + this.filteredMaterials.map(material => {
            const createdDate = new Date(material.created_at);
            const formattedDate = createdDate.toLocaleDateString('id-ID', {
                day: 'numeric',
                month: 'long',
                year: 'numeric'
            });
            const formattedTime = createdDate.toLocaleTimeString('id-ID', {
                hour: '2-digit',
                minute: '2-digit'
            });

            const typeLabels = {
                quiz: 'Kuis',
                assignment: 'Tugas',
                file: 'Berkas',
                link: 'Link',
                discussion: 'Diskusi'
            };

            const colorClasses = {
                quiz: 'amber',
                assignment: 'green',
                file: 'blue',
                link: 'indigo',
                discussion: 'purple'
            };

            const color = colorClasses[material.type];
            const isAssignment = material.type === 'assignment';
            const isFile = material.type === 'file';
            const isDiscussion = material.type === 'discussion';

            // Get file extension
            let fileExtension = '';
            if (isFile && material.filename) {
                fileExtension = material.filename.split('.').pop().toUpperCase();
            }

            return `
                <div class="group bg-white rounded-2xl border border-gray-200 hover:border-green-300 hover:bg-green-50/50 transition-all duration-200 overflow-hidden material-list-item"
                     data-material-id="${material.id}"
                     data-material-type="${material.type}">
                    <div class="flex items-center gap-4 px-5 py-4">
                        <!-- Icon -->
                        <div class="flex-shrink-0 w-12 h-12 rounded-xl flex items-center justify-center transition-all duration-200 group-hover:scale-105 shadow-sm
                            ${color === 'amber' ? 'bg-amber-100 text-amber-600 group-hover:bg-amber-600 group-hover:text-white' : ''}
                            ${color === 'green' ? 'bg-green-100 text-green-600 group-hover:bg-green-600 group-hover:text-white' : ''}
                            ${color === 'blue' ? 'bg-blue-100 text-blue-600 group-hover:bg-blue-600 group-hover:text-white' : ''}
                            ${color === 'indigo' ? 'bg-indigo-100 text-indigo-600 group-hover:bg-indigo-600 group-hover:text-white' : ''}
                            ${color === 'purple' ? 'bg-purple-100 text-purple-600 group-hover:bg-purple-600 group-hover:text-white' : ''}">
                            <span class="text-xl">${material.icon || '📄'}</span>
                        </div>

                        <!-- Content -->
                        <div class="flex-1 min-w-0">
                            <h3 class="text-sm font-bold text-gray-900 group-hover:text-green-700 transition-colors truncate">
                                ${material.title || material.name || 'Untitled'}
                            </h3>
                            <div class="flex items-center gap-3 mt-1">
                                <span class="inline-flex items-center px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-[10px] font-bold uppercase tracking-wide">
                                    ${typeLabels[material.type]}
                                </span>
                                <span class="text-xs text-gray-500 flex items-center gap-1">
                                    <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                                    </svg>
                                    ${formattedDate} · ${formattedTime}
                                </span>
                            </div>
                        </div>

                        <!-- Additional Info -->
                        ${isAssignment && material.due_date ? `
                            <div class="flex-shrink-0 flex items-center gap-2 px-3 py-1.5 bg-orange-50 text-orange-700 rounded-lg">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                                </svg>
                                <span class="text-xs font-bold">Tenggat: ${new Date(material.due_date).toLocaleDateString('id-ID', { day: 'numeric', month: 'short', year: 'numeric' })}</span>
                            </div>
                        ` : isFile && fileExtension ? `
                            <div class="flex-shrink-0 flex items-center gap-2 px-3 py-1.5 bg-blue-50 text-blue-700 rounded-lg">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                                </svg>
                                <span class="text-xs font-bold">${fileExtension}</span>
                            </div>
                        ` : isFile ? `
                            <div class="flex-shrink-0 flex items-center gap-2 px-3 py-1.5 bg-blue-50 text-blue-700 rounded-lg">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                                </svg>
                                <span class="text-xs font-bold">Dokumen</span>
                            </div>
                        ` : ''}

                        <!-- Actions (Teacher Only) -->
                        ${this.isTeacher && material.type === 'quiz' ? `
                        <div class="flex-shrink-0 flex gap-1.5">
                            <button class="btn-edit-material p-2 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-all" title="Edit Kuis">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                                </svg>
                            </button>
                            <button class="btn-preview-material p-2 text-gray-500 hover:text-green-600 hover:bg-green-50 rounded-lg transition-all" title="Pratinjau Kuis">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                                </svg>
                            </button>
                            <button class="btn-archive-material p-2 text-gray-500 hover:text-amber-600 hover:bg-amber-50 rounded-lg transition-all" title="Arsipkan Kuis">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4"/>
                                </svg>
                            </button>
                            <button class="btn-delete-material p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-all" title="Hapus Permanen">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                                </svg>
                            </button>
                        </div>
                        ` : this.isTeacher && (material.type === 'assignment' || material.type === 'file') ? `
                        <div class="flex-shrink-0 flex gap-1.5">
                            <button class="btn-edit-material p-2 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-all" title="Edit">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                                </svg>
                            </button>
                            <button class="btn-archive-material p-2 text-gray-500 hover:text-amber-600 hover:bg-amber-50 rounded-lg transition-all" title="Arsipkan">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4"/>
                                </svg>
                            </button>
                            <button class="btn-delete-material p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-all" title="Hapus Permanen">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                                </svg>
                            </button>
                        </div>
                        ` : this.isTeacher ? `
                        <div class="flex-shrink-0 flex gap-1.5">
                            <button class="btn-delete-material p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-all" title="Hapus">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                                </svg>
                            </button>
                        </div>
                        ` : ''}
                    </div>
                </div>
            `;
        }).join('') + `</div>`;
    }

    attachEventListeners() {
        // Search input with debounce for better performance
        const searchInput = this.container.querySelector('#search-materials');
        if (searchInput) {
            let searchTimeout;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    this.searchQuery = e.target.value;
                    this.applyFilters();
                    this.render();
                    this.attachEventListeners();
                }, 300); // 300ms debounce
            });
            
            // Clear search on Escape key
            searchInput.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    this.searchQuery = '';
                    searchInput.value = '';
                    this.applyFilters();
                    this.render();
                    this.attachEventListeners();
                    searchInput.blur();
                }
            });
        }
        
        // Clear search button
        const clearSearchBtn = this.container.querySelector('#clear-search');
        if (clearSearchBtn) {
            clearSearchBtn.addEventListener('click', () => {
                this.searchQuery = '';
                const searchInput = this.container.querySelector('#search-materials');
                if (searchInput) {
                    searchInput.value = '';
                }
                this.applyFilters();
                this.render();
                this.attachEventListeners();
                searchInput?.focus();
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

        // Material card/item click
        this.container.querySelectorAll('.material-card, .material-list-item').forEach(item => {
            item.addEventListener('click', (e) => {
                if (e.target.closest('button')) return;
                const materialType = item.dataset.materialType;
                const materialId = item.dataset.materialId;
                this.onMaterialSelect(materialType, parseInt(materialId));
            });
        });

        // Delete material (Teacher Only) - with themed confirmation modal for quizzes
        this.container.querySelectorAll('.btn-delete-material').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                const item = btn.closest('.material-card, .material-list-item');
                const materialType = item.dataset.materialType;
                const materialId = item.dataset.materialId;
                const materialTitle = item.querySelector('h3')?.textContent || 'materi ini';

                if (materialType === 'quiz') {
                    this.showDeleteQuizConfirmation(parseInt(materialId), materialTitle);
                } else {
                    if (confirm('Hapus materi ini?')) {
                        this.deleteMaterial(materialType, parseInt(materialId));
                    }
                }
            });
        });

        // Edit quiz (Teacher Only)
        this.container.querySelectorAll('.btn-edit-material').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                const item = btn.closest('.material-card, .material-list-item');
                const materialId = item.dataset.materialId;
                window.open(`/quiz/${materialId}`, '_blank');
            });
        });

        // Preview quiz
        this.container.querySelectorAll('.btn-preview-material').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                const item = btn.closest('.material-card, .material-list-item');
                const materialId = item.dataset.materialId;
                window.open(`/quiz/${materialId}?preview=true`, '_blank');
            });
        });

        // Archive quiz (Teacher Only)
        this.container.querySelectorAll('.btn-archive-material').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                const item = btn.closest('.material-list-item');
                const materialType = item.dataset.materialType;
                const materialId = item.dataset.materialId;
                const materialTitle = item.querySelector('h3')?.textContent || 'item ini';
                
                if (materialType === 'quiz') {
                    this.showArchiveQuizConfirmation(parseInt(materialId), materialTitle);
                } else if (materialType === 'assignment') {
                    this.showArchiveConfirmation(parseInt(materialId), materialTitle, 'Tugas');
                } else if (materialType === 'file') {
                    this.showArchiveConfirmation(parseInt(materialId), materialTitle, 'File');
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

    showDeleteQuizConfirmation(quizId, quizTitle) {
        // First, check if quiz has submissions/grades
        this.checkQuizHasSubmissions(quizId).then(hasSubmissions => {
            this.renderDeleteModal(quizId, quizTitle, hasSubmissions);
        });
    }

    async checkQuizHasSubmissions(quizId) {
        try {
            const response = await fetch(`/api/quiz/${quizId}/stats`);
            const data = await response.json();
            return data.success && data.total_submissions > 0;
        } catch (error) {
            console.error('Error checking quiz submissions:', error);
            return false;
        }
    }

    renderDeleteModal(quizId, quizTitle, hasSubmissions) {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 animate-fade-in';
        
        const hasSubmissionsContent = hasSubmissions ? `
            <div class="bg-amber-50 border border-amber-200 rounded-2xl p-5 mb-6">
                <div class="flex items-start gap-3">
                    <svg class="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
                    </svg>
                    <div>
                        <p class="text-sm font-bold text-amber-900 mb-3">💡 Saran: Kuis ini memiliki nilai siswa!</p>
                        <p class="text-xs text-amber-700 mb-3">
                            Kuis ini sudah dikerjakan oleh siswa. Daripada menghapus permanen, lebih baik 
                            <strong>arsipkan saja</strong> untuk menjaga nilai tetap tersimpan.
                        </p>
                        <button class="btn-archive-instead w-full px-4 py-3 bg-amber-600 text-white rounded-xl font-bold text-sm hover:bg-amber-700 transition-all flex items-center justify-center gap-2 shadow-lg shadow-amber-200">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4"/>
                            </svg>
                            Arsipkan Saja (Nilai Tersimpan)
                        </button>
                    </div>
                </div>
            </div>
        ` : '';

        modal.innerHTML = `
            <div class="modal-content bg-white rounded-[2.5rem] shadow-2xl w-full max-w-md overflow-hidden animate-slide-up">
                <div class="bg-gradient-to-br from-red-500 to-red-700 px-8 py-6 text-white">
                    <div class="flex items-center gap-3">
                        <div class="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center">
                            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
                            </svg>
                        </div>
                        <div>
                            <h3 class="text-xl font-black">Hapus Kuis Permanen</h3>
                            <p class="text-red-100 text-sm mt-0.5">Tindakan ini tidak dapat dibatalkan</p>
                        </div>
                    </div>
                </div>
                <div class="p-8">
                    <p class="text-gray-700 font-bold mb-4">
                        Apakah Anda yakin ingin menghapus <span class="text-red-600">${quizTitle}</span>?
                    </p>
                    ${hasSubmissionsContent}
                    <div class="bg-red-50 border border-red-200 rounded-2xl p-5 mb-6">
                        <div class="flex items-start gap-3">
                            <svg class="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                            </svg>
                            <div>
                                <p class="text-sm font-bold text-red-900 mb-2">Peringatan Penting:</p>
                                <ul class="text-xs text-red-700 space-y-1.5">
                                    <li>• Semua nilai siswa untuk kuis ini akan <strong>dihapus permanen</strong></li>
                                    <li>• Semua soal dan jawaban akan <strong>dihapus</strong></li>
                                    <li>• Data yang telah dihapus <strong>tidak dapat dipulihkan</strong></li>
                                </ul>
                            </div>
                        </div>
                    </div>
                    <div class="flex gap-3">
                        <button class="cancel-delete flex-1 px-5 py-3.5 bg-gray-100 text-gray-700 rounded-2xl font-bold hover:bg-gray-200 transition-all">
                            Batal
                        </button>
                        <button class="confirm-delete flex-1 px-5 py-3.5 bg-red-600 text-white rounded-2xl font-bold hover:bg-red-700 transition-all shadow-lg shadow-red-200">
                            Ya, Hapus Kuis
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        modal.querySelector('.cancel-delete').addEventListener('click', () => {
            modal.remove();
        });

        modal.querySelector('.confirm-delete').addEventListener('click', async () => {
            await this.deleteMaterial('quiz', quizId);
            modal.remove();
        });

        // Archive instead button
        const archiveInsteadBtn = modal.querySelector('.btn-archive-instead');
        if (archiveInsteadBtn) {
            archiveInsteadBtn.addEventListener('click', async () => {
                await this.archiveQuiz(quizId);
                modal.remove();
            });
        }

        // Close on overlay click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }

    showArchiveQuizConfirmation(quizId, quizTitle) {
        this.showArchiveConfirmation(quizId, quizTitle, 'Kuis');
    }

    showArchiveConfirmation(id, title, typeName) {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 animate-fade-in';
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
                        Arsipkan <span class="text-amber-600">${title}</span>?
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
                            Arsipkan ${typeName}
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        modal.querySelector('.cancel-archive').addEventListener('click', () => {
            modal.remove();
        });

        modal.querySelector('.confirm-archive').addEventListener('click', async () => {
            if (typeName === 'Kuis') {
                await this.archiveQuiz(id);
            } else if (typeName === 'Tugas') {
                await this.archiveAssignment(id);
            } else if (typeName === 'File') {
                await this.archiveFile(id);
            }
            modal.remove();
        });

        // Close on overlay click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }

    async archiveQuiz(quizId) {
        try {
            const response = await fetch(`/api/quiz/${quizId}/archive`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            const data = await response.json();
            if (data.success) {
                await this.loadMaterials();
                this.render();
                this.attachEventListeners();
                // Show success notification
                this.showNotification('Kuis berhasil diarsipkan', 'success');
            } else {
                this.showNotification(data.message || 'Gagal mengarsipkan kuis', 'error');
            }
        } catch (error) {
            console.error('Error archiving quiz:', error);
            this.showNotification('Terjadi kesalahan saat mengarsipkan kuis', 'error');
        }
    }

    async archiveAssignment(assignmentId) {
        try {
            const response = await fetch(`/api/assignment/${assignmentId}/archive`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            const data = await response.json();
            if (data.success) {
                await this.loadMaterials();
                this.render();
                this.attachEventListeners();
                this.showNotification('Tugas berhasil diarsipkan', 'success');
            } else {
                this.showNotification(data.message || 'Gagal mengarsipkan tugas', 'error');
            }
        } catch (error) {
            console.error('Error archiving assignment:', error);
            this.showNotification('Terjadi kesalahan saat mengarsipkan tugas', 'error');
        }
    }

    async archiveFile(fileId) {
        try {
            const response = await fetch(`/api/file/${fileId}/archive`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            const data = await response.json();
            if (data.success) {
                await this.loadMaterials();
                this.render();
                this.attachEventListeners();
                this.showNotification('File berhasil diarsipkan', 'success');
            } else {
                this.showNotification(data.message || 'Gagal mengarsipkan file', 'error');
            }
        } catch (error) {
            console.error('Error archiving file:', error);
            this.showNotification('Terjadi kesalahan saat mengarsipkan file', 'error');
        }
    }

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
        modal.className = 'modal-overlay fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50';
        modal.innerHTML = `
            <div class="modal-content bg-white rounded-[2.5rem] shadow-2xl w-full max-w-lg overflow-hidden animate-slide-up">
                <div class="bg-gradient-to-br from-green-500 to-green-700 px-8 py-6 text-white">
                    <h3 class="text-xl font-black">Tambah Konten Baru</h3>
                    <p class="text-green-100 text-sm mt-1">Pilih jenis konten atau buat folder</p>
                </div>
                <div class="p-6">
                    <!-- Folder Section -->
                    <div class="mb-4">
                        <p class="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-3 px-2">Organisasi</p>
                        <button class="add-folder w-full text-left px-5 py-4 rounded-2xl hover:bg-purple-50 border border-gray-100 transition-all group flex items-center gap-4">
                            <div class="w-12 h-12 rounded-xl bg-purple-100 text-purple-600 flex items-center justify-center text-xl group-hover:bg-purple-600 group-hover:text-white transition-all">
                                📁
                            </div>
                            <div>
                                <div class="font-bold text-gray-900 group-hover:text-purple-600 transition-colors">Buat Folder</div>
                                <div class="text-xs text-gray-500">Organisir materi dalam folder</div>
                            </div>
                        </button>
                    </div>
                    
                    <!-- Materials Section -->
                    <div>
                        <p class="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-3 px-2">Materi & Tugas</p>
                        <div class="space-y-3">
                            <button class="add-quiz w-full text-left px-5 py-4 rounded-2xl hover:bg-amber-50 border border-gray-100 transition-all group flex items-center gap-4">
                                <div class="w-12 h-12 rounded-xl bg-amber-100 text-amber-600 flex items-center justify-center text-xl group-hover:bg-amber-600 group-hover:text-white transition-all">
                                    📊
                                </div>
                                <div>
                                    <div class="font-bold text-gray-900 group-hover:text-amber-600 transition-colors">Kuis</div>
                                    <div class="text-xs text-gray-500">Buat kuis interaktif</div>
                                </div>
                            </button>
                            <button class="add-assignment w-full text-left px-5 py-4 rounded-2xl hover:bg-green-50 border border-gray-100 transition-all group flex items-center gap-4">
                                <div class="w-12 h-12 rounded-xl bg-green-100 text-green-600 flex items-center justify-center text-xl group-hover:bg-green-600 group-hover:text-white transition-all">
                                    📝
                                </div>
                                <div>
                                    <div class="font-bold text-gray-900 group-hover:text-green-600 transition-colors">Tugas</div>
                                    <div class="text-xs text-gray-500">Berikan tugas kepada siswa</div>
                                </div>
                            </button>
                            <button class="add-file w-full text-left px-5 py-4 rounded-2xl hover:bg-blue-50 border border-gray-100 transition-all group flex items-center gap-4">
                                <div class="w-12 h-12 rounded-xl bg-blue-100 text-blue-600 flex items-center justify-center text-xl group-hover:bg-blue-600 group-hover:text-white transition-all">
                                    📎
                                </div>
                                <div>
                                    <div class="font-bold text-gray-900 group-hover:text-blue-600 transition-colors">Berkas</div>
                                    <div class="text-xs text-gray-500">Upload file materi</div>
                                </div>
                            </button>
                            <button class="add-link w-full text-left px-5 py-4 rounded-2xl hover:bg-indigo-50 border border-gray-100 transition-all group flex items-center gap-4">
                                <div class="w-12 h-12 rounded-xl bg-indigo-100 text-indigo-600 flex items-center justify-center text-xl group-hover:bg-indigo-600 group-hover:text-white transition-all">
                                    🔗
                                </div>
                                <div>
                                    <div class="font-bold text-gray-900 group-hover:text-indigo-600 transition-colors">Link</div>
                                    <div class="text-xs text-gray-500">Tambahkan link eksternal</div>
                                </div>
                            </button>
                        </div>
                    </div>
                </div>
                <div class="px-6 pb-6">
                    <button class="btn btn-secondary w-full px-5 py-3.5 bg-gray-100 text-gray-700 rounded-2xl font-bold hover:bg-gray-200 transition-all">Batal</button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Add folder button
        modal.querySelector('.add-folder').addEventListener('click', (e) => {
            e.preventDefault();
            modal.remove();
            this.showCreateFolderModal();
        });

        modal.querySelector('.add-quiz').addEventListener('click', (e) => {
            e.preventDefault();
            modal.remove();
            document.getElementById('show-create-quiz-modal')?.click();
        });

        modal.querySelector('.add-assignment').addEventListener('click', (e) => {
            e.preventDefault();
            modal.remove();
            document.getElementById('show-create-assignment-modal')?.click();
        });

        modal.querySelector('.add-file').addEventListener('click', (e) => {
            e.preventDefault();
            modal.remove();
            document.getElementById('show-create-file-modal')?.click();
        });

        modal.querySelector('.add-link').addEventListener('click', (e) => {
            e.preventDefault();
            modal.remove();
            document.getElementById('show-create-link-modal')?.click();
        });

        modal.querySelector('.btn-secondary').addEventListener('click', () => modal.remove());
    }

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
                const response = await fetch(`/courses/${this.courseId}/folders`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name })
                });
                const data = await response.json();
                
                if (data.success) {
                    modal.remove();
                    // Show success feedback
                    alert('Folder berhasil dibuat!');
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
    }

    refresh() {
        this.loadMaterials().then(() => {
            this.render();
            this.attachEventListeners();
        });
    }
}
