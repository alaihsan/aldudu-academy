/**
 * MaterialsList Component v2.0
 * Features:
 * - Drag & Drop reordering
 * - Drag materials into folders
 * - Expandable/collapsible folders
 * - Manual order sorting mode
 * - Visual feedback during drag
 */
class MaterialsList {
    constructor(containerId, courseId, options = {}) {
        this.container = document.getElementById(containerId);
        this.courseId = courseId;
        this.materials = [];
        this.folders = [];
        this.filteredMaterials = [];
        this.filterType = 'all';
        this.searchQuery = '';
        this.isTeacher = options.isTeacher || false;
        this.onMaterialSelect = options.onMaterialSelect || (() => {});
        this.onMaterialDelete = options.onMaterialDelete || (() => {});
        
        // Drag and drop state
        this.draggedItem = null;
        this.draggedType = null; // 'material' or 'folder'
        this.expandedFolders = new Set(); // Set of folder IDs that are expanded
        
        // Sort mode
        this.sortMode = localStorage.getItem(`course_${courseId}_sortMode`) || 'manual';

        this.init();
    }

    async init() {
        await this.loadAllData();
        this.render();
        this.attachEventListeners();
    }

    async loadAllData() {
        await this.loadFolders();
        await this.loadMaterials();
        this.sortMaterials();
    }

    async loadFolders() {
        try {
            const response = await fetch(`/api/courses/${this.courseId}/folders`);
            const data = await response.json();
            
            if (data.success) {
                this.folders = data.folders.map(folder => ({
                    id: folder.id,
                    name: folder.name,
                    parent_id: folder.parent_folder_id,
                    order: folder.order || 0,
                    children: [], // Will be populated
                    isExpanded: this.expandedFolders.has(folder.id)
                }));
                
                // Build folder tree structure
                this.buildFolderTree();
            } else {
                this.folders = [];
            }
        } catch (error) {
            console.error('Error loading folders:', error);
            this.folders = [];
        }
    }

    buildFolderTree() {
        // Reset children
        this.folders.forEach(f => f.children = []);
        
        // Build tree
        const rootFolders = [];
        
        this.folders.forEach(folder => {
            if (folder.parent_id) {
                const parent = this.folders.find(f => f.id === folder.parent_id);
                if (parent) {
                    parent.children.push(folder);
                } else {
                    rootFolders.push(folder);
                }
            } else {
                rootFolders.push(folder);
            }
        });
        
        // Sort children by order
        this.folders.forEach(f => {
            f.children.sort((a, b) => a.order - b.order);
        });
        
        this.rootFolders = rootFolders.sort((a, b) => a.order - b.order);
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
                        folder_id: topic.folder_id || null,
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
        } catch (error) {
            console.error('Error loading materials:', error);
            this.materials = [];
        }
    }

    sortMaterials() {
        if (this.sortMode === 'manual') {
            // Sort by order value
            this.materials.sort((a, b) => a.order - b.order);
        } else if (this.sortMode === 'created_desc') {
            // Sort by created date (newest first)
            this.materials.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
        } else if (this.sortMode === 'name_asc') {
            // Sort by name (A-Z)
            this.materials.sort((a, b) => a.title.localeCompare(b.title));
        }
    }

    getMaterialsForFolder(folderId) {
        return this.materials.filter(m => m.folder_id === folderId);
    }

    getUnfolderedMaterials() {
        return this.materials.filter(m => !m.folder_id);
    }

    applyFilters() {
        if (this.filterType === 'all' && !this.searchQuery) {
            this.filteredMaterials = this.materials;
            return;
        }

        this.filteredMaterials = this.materials.filter(m => {
            // Filter by type
            if (this.filterType !== 'all' && m.type !== this.filterType) {
                return false;
            }

            // Filter by search query
            if (this.searchQuery) {
                const query = this.searchQuery.toLowerCase().trim();
                const title = (m.title || m.name || '').toLowerCase();
                const typeLabel = this.getTypeLabel(m.type).toLowerCase();
                return title.includes(query) || typeLabel.includes(query);
            }

            return true;
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
        this.applyFilters();
        
        const html = `
            <div class="materials-wrapper">
                ${this.renderHeader()}
                ${this.renderControls()}
                ${this.renderContent()}
            </div>
        `;

        this.container.innerHTML = html;
    }

    renderHeader() {
        const totalItems = this.materials.length;
        const totalFolders = this.folders.length;
        
        return `
            <div class="materials-header flex items-center justify-between mb-6">
                <div>
                    <h2 class="text-2xl font-bold text-gray-900">Semua Materi</h2>
                    <p class="text-sm text-gray-500 mt-1">
                        ${totalItems} materi · ${totalFolders} folder
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
        `;
    }

    renderControls() {
        return `
            <div class="materials-controls flex flex-col sm:flex-row gap-4 mb-6">
                <div class="flex-1 relative">
                    <svg class="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                    </svg>
                    <input type="text" id="search-materials" 
                        class="w-full pl-10 pr-10 py-2.5 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-green-500 outline-none transition-all"
                        placeholder="Cari materi..."
                        value="${this.searchQuery}">
                    ${this.searchQuery ? `
                    <button id="clear-search" class="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-full transition-all">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                        </svg>
                    </button>
                    ` : ''}
                </div>
                
                <select id="filter-type" class="px-4 py-2.5 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-green-500 outline-none font-semibold text-sm min-w-[150px]">
                    <option value="all" ${this.filterType === 'all' ? 'selected' : ''}>Semua</option>
                    <option value="quiz" ${this.filterType === 'quiz' ? 'selected' : ''}>📊 Kuis</option>
                    <option value="assignment" ${this.filterType === 'assignment' ? 'selected' : ''}>📝 Tugas</option>
                    <option value="file" ${this.filterType === 'file' ? 'selected' : ''}>📎 Berkas</option>
                    <option value="link" ${this.filterType === 'link' ? 'selected' : ''}>🔗 Link</option>
                </select>
                
                <select id="sort-mode" class="px-4 py-2.5 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-green-500 outline-none font-semibold text-sm min-w-[150px]">
                    <option value="manual" ${this.sortMode === 'manual' ? 'selected' : ''}>📋 Manual</option>
                    <option value="created_desc" ${this.sortMode === 'created_desc' ? 'selected' : ''}>📅 Terbaru</option>
                    <option value="name_asc" ${this.sortMode === 'name_asc' ? 'selected' : ''}>🔤 A-Z</option>
                </select>
            </div>
        `;
    }

    renderContent() {
        if (this.folders.length === 0 && this.filteredMaterials.length === 0) {
            return this.renderEmptyState();
        }

        return `
            <div class="materials-content space-y-4">
                ${this.renderFolders()}
                ${this.renderUnfolderedMaterials()}
            </div>
        `;
    }

    renderFolders() {
        if (this.rootFolders.length === 0) return '';

        return `
            <div class="folders-section">
                <div class="flex items-center gap-2 mb-3">
                    <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/>
                    </svg>
                    <span class="text-sm font-bold text-gray-500 uppercase tracking-wider">Folder</span>
                </div>
                <div class="space-y-2">
                    ${this.rootFolders.map(folder => this.renderFolder(folder, 0)).join('')}
                </div>
            </div>
        `;
    }

    renderFolder(folder, depth = 0) {
        const isExpanded = this.expandedFolders.has(folder.id);
        const materialsInFolder = this.getMaterialsForFolder(folder.id);
        const paddingLeft = depth * 24;

        return `
            <div class="folder-container" data-folder-id="${folder.id}">
                <div class="folder-item group bg-white rounded-2xl border border-gray-200 hover:border-purple-300 hover:bg-purple-50/50 transition-all duration-200 overflow-hidden"
                    style="padding-left: ${paddingLeft}px"
                    draggable="${this.isTeacher && this.sortMode === 'manual'}"
                    data-drag-type="folder"
                    data-folder-id="${folder.id}">
                    <div class="flex items-center gap-3 px-5 py-4">
                        ${this.isTeacher && this.sortMode === 'manual' ? `
                        <svg class="w-5 h-5 text-gray-400 cursor-grab drag-handle" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8h16M4 16h16"/>
                        </svg>
                        ` : ''}
                        
                        <button class="folder-toggle w-6 h-6 flex items-center justify-center text-gray-500 hover:text-purple-600 transition-colors"
                            onclick="materialsList.toggleFolder(${folder.id})">
                            <svg class="w-4 h-4 transition-transform ${isExpanded ? 'rotate-90' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                            </svg>
                        </button>
                        
                        <div class="w-10 h-10 bg-purple-100 text-purple-600 rounded-xl flex items-center justify-center text-xl">
                            📁
                        </div>
                        
                        <div class="flex-1">
                            <h3 class="text-sm font-bold text-gray-900">${folder.name}</h3>
                            <p class="text-xs text-gray-500">${materialsInFolder.length} materi</p>
                        </div>
                        
                        ${this.isTeacher ? `
                        <div class="flex gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
                            <button class="folder-rename-btn p-2 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg" title="Ganti Nama">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                                </svg>
                            </button>
                            <button class="folder-delete-btn p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg" title="Hapus Folder">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                                </svg>
                            </button>
                        </div>
                        ` : ''}
                    </div>
                </div>
                
                ${isExpanded ? `
                <div class="folder-contents ml-8 mt-2 space-y-2" data-folder-id="${folder.id}">
                    ${materialsInFolder.length > 0 ? `
                        ${materialsInFolder.map(material => this.renderMaterialItem(material, true)).join('')}
                    ` : `
                        <div class="text-center py-4 text-sm text-gray-400">Belum ada materi di folder ini</div>
                    `}
                </div>
                ` : ''}
                
                ${folder.children.length > 0 ? `
                    <div class="subfolders ml-8 mt-2 space-y-2">
                        ${folder.children.map(subfolder => this.renderFolder(subfolder, depth + 1)).join('')}
                    </div>
                ` : ''}
            </div>
        `;
    }

    renderUnfolderedMaterials() {
        const unfolderedMaterials = this.getUnfolderedMaterials();
        
        if (unfolderedMaterials.length === 0) return '';

        return `
            <div class="unfoldered-section">
                ${this.folders.length > 0 ? `
                <div class="flex items-center gap-2 mb-3">
                    <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/>
                    </svg>
                    <span class="text-sm font-bold text-gray-500 uppercase tracking-wider">Materi Tanpa Folder</span>
                </div>
                ` : ''}
                <div class="space-y-2">
                    ${unfolderedMaterials.map(material => this.renderMaterialItem(material)).join('')}
                </div>
            </div>
        `;
    }

    renderMaterialItem(material, isInFolder = false) {
        const createdDate = new Date(material.created_at);
        const formattedDate = createdDate.toLocaleDateString('id-ID', {
            day: 'numeric',
            month: 'long',
            year: 'numeric'
        });

        const colorClasses = {
            quiz: 'bg-amber-100 text-amber-600 group-hover:bg-amber-600 group-hover:text-white',
            assignment: 'bg-green-100 text-green-600 group-hover:bg-green-600 group-hover:text-white',
            file: 'bg-blue-100 text-blue-600 group-hover:bg-blue-600 group-hover:text-white',
            link: 'bg-indigo-100 text-indigo-600 group-hover:bg-indigo-600 group-hover:text-white',
            discussion: 'bg-purple-100 text-purple-600 group-hover:bg-purple-600 group-hover:text-white'
        };

        return `
            <div class="group bg-white rounded-2xl border border-gray-200 hover:border-green-300 hover:bg-green-50/50 transition-all duration-200 overflow-hidden material-item"
                data-material-id="${material.id}"
                data-material-type="${material.type}"
                draggable="${this.isTeacher && this.sortMode === 'manual'}"
                data-drag-type="material">
                <div class="flex items-center gap-4 px-5 py-4">
                    ${this.isTeacher && this.sortMode === 'manual' ? `
                    <svg class="w-5 h-5 text-gray-400 cursor-grab drag-handle flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8h16M4 16h16"/>
                    </svg>
                    ` : ''}
                    
                    <div class="w-12 h-12 rounded-xl flex items-center justify-center text-2xl flex-shrink-0 transition-all duration-200 group-hover:scale-105 shadow-sm ${colorClasses[material.type]}">
                        ${material.icon || '📄'}
                    </div>

                    <div class="flex-1 min-w-0">
                        <h3 class="text-sm font-bold text-gray-900 group-hover:text-green-700 transition-colors truncate">
                            ${material.title || material.name || 'Untitled'}
                        </h3>
                        <div class="flex items-center gap-3 mt-1 flex-wrap">
                            <span class="inline-flex items-center px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-[10px] font-bold uppercase tracking-wide">
                                ${this.getTypeLabel(material.type)}
                            </span>
                            <span class="text-xs text-gray-500 flex items-center gap-1">
                                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                                </svg>
                                ${formattedDate}
                            </span>
                        </div>
                    </div>

                    ${this.isTeacher ? `
                    <div class="flex gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button class="move-to-folder-btn p-2 text-gray-500 hover:text-purple-600 hover:bg-purple-50 rounded-lg" title="Pindah ke Folder">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/>
                            </svg>
                        </button>
                        <button class="btn-edit-material p-2 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg" title="Edit">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                            </svg>
                        </button>
                        ${material.type === 'quiz' ? `
                        <button class="btn-archive-material p-2 text-gray-500 hover:text-amber-600 hover:bg-amber-50 rounded-lg" title="Arsipkan">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4"/>
                            </svg>
                        </button>
                        ` : ''}
                        <button class="btn-delete-material p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg" title="Hapus">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                            </svg>
                        </button>
                    </div>
                    ` : ''}
                </div>
            </div>
        `;
    }

    renderEmptyState() {
        return `
            <div class="empty-state text-center py-16 bg-white rounded-3xl border-2 border-dashed border-gray-200">
                <div class="w-20 h-20 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-4">
                    <svg class="w-10 h-10 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                    </svg>
                </div>
                <p class="text-gray-500 font-semibold">Belum ada materi</p>
                <p class="text-sm text-gray-400 mt-1">Klik "Tambah Materi" untuk menambahkan</p>
            </div>
        `;
    }

    toggleFolder(folderId) {
        if (this.expandedFolders.has(folderId)) {
            this.expandedFolders.delete(folderId);
        } else {
            this.expandedFolders.add(folderId);
        }
        
        // Save to localStorage
        localStorage.setItem(`course_${this.courseId}_expandedFolders`, JSON.stringify([...this.expandedFolders]));
        
        this.render();
        this.attachEventListeners();
    }

    attachEventListeners() {
        // Search with debounce
        const searchInput = this.container.querySelector('#search-materials');
        if (searchInput) {
            let searchTimeout;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    this.searchQuery = e.target.value;
                    this.render();
                    this.attachEventListeners();
                }, 300);
            });
        }

        // Clear search
        const clearSearch = this.container.querySelector('#clear-search');
        if (clearSearch) {
            clearSearch.addEventListener('click', () => {
                this.searchQuery = '';
                this.render();
                this.attachEventListeners();
            });
        }

        // Filter type
        const filterType = this.container.querySelector('#filter-type');
        if (filterType) {
            filterType.addEventListener('change', (e) => {
                this.filterType = e.target.value;
                this.render();
                this.attachEventListeners();
            });
        }

        // Sort mode
        const sortMode = this.container.querySelector('#sort-mode');
        if (sortMode) {
            sortMode.addEventListener('change', (e) => {
                this.sortMode = e.target.value;
                localStorage.setItem(`course_${this.courseId}_sortMode`, this.sortMode);
                this.sortMaterials();
                this.render();
                this.attachEventListeners();
            });
        }

        // Add material button
        const addBtn = this.container.querySelector('.btn-add-material');
        if (addBtn) {
            addBtn.addEventListener('click', () => {
                this.showAddMaterialModal();
            });
        }

        // Drag and drop for materials and folders
        if (this.isTeacher && this.sortMode === 'manual') {
            this.attachDragAndDropListeners();
        }

        // Material action buttons
        this.attachMaterialActionListeners();
        
        // Folder action buttons
        this.attachFolderActionListeners();
    }

    attachDragAndDropListeners() {
        // Make materials draggable
        this.container.querySelectorAll('.material-item[draggable="true"]').forEach(item => {
            item.addEventListener('dragstart', (e) => this.handleDragStart(e, 'material'));
            item.addEventListener('dragend', (e) => this.handleDragEnd(e));
        });

        // Make folders draggable
        this.container.querySelectorAll('.folder-item[draggable="true"]').forEach(item => {
            item.addEventListener('dragstart', (e) => this.handleDragStart(e, 'folder'));
            item.addEventListener('dragend', (e) => this.handleDragEnd(e));
        });

        // Drop zones (folders)
        this.container.querySelectorAll('.folder-item').forEach(item => {
            item.addEventListener('dragover', (e) => this.handleDragOver(e));
            item.addEventListener('dragleave', (e) => this.handleDragLeave(e));
            item.addEventListener('drop', (e) => this.handleDropOnFolder(e));
        });

        // Drop zones (between materials for reordering)
        this.container.querySelectorAll('.material-item, .folder-item').forEach(item => {
            item.addEventListener('dragover', (e) => {
                e.preventDefault();
                const rect = item.getBoundingClientRect();
                const midpoint = rect.top + rect.height / 2;
                
                if (e.clientY < midpoint) {
                    item.classList.add('drag-above');
                    item.classList.remove('drag-below');
                } else {
                    item.classList.add('drag-below');
                    item.classList.remove('drag-above');
                }
            });
            
            item.addEventListener('dragleave', () => {
                item.classList.remove('drag-above', 'drag-below');
            });
            
            item.addEventListener('drop', (e) => this.handleDropOnItem(e));
        });
    }

    handleDragStart(e, type) {
        this.draggedItem = e.target.closest('.material-item, .folder-item');
        this.draggedType = type;
        
        if (this.draggedItem) {
            e.dataTransfer.effectAllowed = 'move';
            e.dataTransfer.setData('text/plain', this.draggedItem.dataset.dragType);
            
            // Add dragging class
            this.draggedItem.classList.add('dragging');
        }
    }

    handleDragEnd(e) {
        if (this.draggedItem) {
            this.draggedItem.classList.remove('dragging', 'drag-above', 'drag-below');
        }
        
        // Remove all drag indicators
        this.container.querySelectorAll('.drag-above, .drag-below').forEach(el => {
            el.classList.remove('drag-above', 'drag-below');
        });
        
        this.draggedItem = null;
        this.draggedType = null;
    }

    handleDragOver(e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
    }

    handleDragLeave(e) {
        e.target.closest('.folder-item')?.classList.remove('drag-over');
    }

    handleDropOnFolder(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const folderItem = e.target.closest('.folder-item');
        if (!folderItem || !this.draggedItem) return;
        
        const targetFolderId = parseInt(folderItem.dataset.folderId);
        
        if (this.draggedType === 'material') {
            const materialId = parseInt(this.draggedItem.dataset.materialId);
            this.moveMaterialToFolder(materialId, targetFolderId);
        } else if (this.draggedType === 'folder') {
            const draggedFolderId = parseInt(this.draggedItem.dataset.folderId);
            if (draggedFolderId !== targetFolderId) {
                this.moveFolder(draggedFolderId, targetFolderId);
            }
        }
        
        this.handleDragEnd(e);
    }

    handleDropOnItem(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const targetItem = e.target.closest('.material-item, .folder-item');
        if (!targetItem || !this.draggedItem || this.draggedItem === targetItem) return;
        
        const rect = targetItem.getBoundingClientRect();
        const midpoint = rect.top + rect.height / 2;
        const insertBefore = e.clientY < midpoint;
        
        if (this.draggedType === 'material' && targetItem.classList.contains('material-item')) {
            const draggedId = parseInt(this.draggedItem.dataset.materialId);
            const targetId = parseInt(targetItem.dataset.materialId);
            this.reorderMaterials(draggedId, targetId, insertBefore);
        } else if (this.draggedType === 'folder' && targetItem.classList.contains('folder-item')) {
            const draggedId = parseInt(this.draggedItem.dataset.folderId);
            const targetId = parseInt(targetItem.dataset.folderId);
            this.reorderFolders(draggedId, targetId, insertBefore);
        }
        
        this.handleDragEnd(e);
    }

    async moveMaterialToFolder(materialId, folderId) {
        try {
            const response = await fetch(`/api/materials/${materialId}/move`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ folder_id: folderId })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Update local data
                const material = this.materials.find(m => m.id === materialId);
                if (material) {
                    material.folder_id = folderId;
                }
                
                // Expand the target folder
                this.expandedFolders.add(folderId);
                
                this.render();
                this.attachEventListeners();
                this.showNotification('Materi berhasil dipindahkan ke folder', 'success');
            } else {
                this.showNotification(data.message || 'Gagal memindahkan materi', 'error');
            }
        } catch (error) {
            console.error('Error moving material:', error);
            this.showNotification('Terjadi kesalahan', 'error');
        }
    }

    async moveFolder(folderId, newParentId) {
        try {
            const response = await fetch(`/api/folders/${folderId}/move`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ parent_folder_id: newParentId })
            });
            
            const data = await response.json();
            
            if (data.success) {
                const folder = this.folders.find(f => f.id === folderId);
                if (folder) {
                    folder.parent_id = newParentId;
                }
                
                this.buildFolderTree();
                this.render();
                this.attachEventListeners();
                this.showNotification('Folder berhasil dipindahkan', 'success');
            } else {
                this.showNotification(data.message || 'Gagal memindahkan folder', 'error');
            }
        } catch (error) {
            console.error('Error moving folder:', error);
            this.showNotification('Terjadi kesalahan', 'error');
        }
    }

    async reorderMaterials(draggedId, targetId, insertBefore) {
        // Find indices
        const draggedIndex = this.materials.findIndex(m => m.id === draggedId);
        const targetIndex = this.materials.findIndex(m => m.id === targetId);
        
        if (draggedIndex === -1 || targetIndex === -1) return;
        
        // Reorder array
        const [dragged] = this.materials.splice(draggedIndex, 1);
        const newTargetIndex = insertBefore ? targetIndex : targetIndex + 1;
        this.materials.splice(newTargetIndex > draggedIndex ? newTargetIndex - 1 : newTargetIndex, 0, dragged);
        
        // Update order values
        this.materials.forEach((m, index) => {
            m.order = index;
        });
        
        // Save to server
        try {
            await fetch(`/api/courses/${this.courseId}/materials/reorder`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    order: this.materials.map(m => ({
                        id: m.id,
                        type: m.type,
                        order: m.order
                    }))
                })
            });
            
            this.render();
            this.attachEventListeners();
        } catch (error) {
            console.error('Error reordering:', error);
        }
    }

    async reorderFolders(draggedId, targetId, insertBefore) {
        const draggedIndex = this.folders.findIndex(f => f.id === draggedId);
        const targetIndex = this.folders.findIndex(f => f.id === targetId);
        
        if (draggedIndex === -1 || targetIndex === -1) return;
        
        const [dragged] = this.folders.splice(draggedIndex, 1);
        const newTargetIndex = insertBefore ? targetIndex : targetIndex + 1;
        this.folders.splice(newTargetIndex > draggedIndex ? newTargetIndex - 1 : newTargetIndex, 0, dragged);
        
        this.folders.forEach((f, index) => {
            f.order = index;
        });
        
        try {
            await fetch(`/api/courses/${this.courseId}/folders/reorder`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    order: this.folders.map(f => ({ id: f.id, order: f.order }))
                })
            });
            
            this.buildFolderTree();
            this.render();
            this.attachEventListeners();
        } catch (error) {
            console.error('Error reordering folders:', error);
        }
    }

    attachMaterialActionListeners() {
        // Edit buttons
        this.container.querySelectorAll('.btn-edit-material').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const item = btn.closest('.material-item');
                const type = item.dataset.materialType;
                const id = item.dataset.materialId;
                
                if (type === 'quiz') {
                    window.open(`/quiz/${id}`, '_blank');
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
                this.showArchiveConfirmation(parseInt(id), 'Kuis');
            });
        });

        // Move to folder buttons
        this.container.querySelectorAll('.move-to-folder-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const item = btn.closest('.material-item');
                const id = item.dataset.materialId;
                this.showMoveToFolderModal(parseInt(id));
            });
        });
    }

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

    // Placeholder methods - implement based on your existing code
    showAddMaterialModal() { /* ... */ }
    showArchiveConfirmation(id, type) { /* ... */ }
    showMoveToFolderModal(materialId) { /* ... */ }
    showRenameFolderModal(folderId, currentName) { /* ... */ }
    deleteMaterial(type, id) { /* ... */ }
    deleteFolder(folderId) { /* ... */ }

    refresh() {
        this.loadAllData().then(() => {
            this.render();
            this.attachEventListeners();
        });
    }
}

// Make globally accessible
window.MaterialsList = MaterialsList;
