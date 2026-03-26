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

        this.container.innerHTML = DOMPurify.sanitize(html);
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
            <div class="group bg-white rounded-2xl border border-gray-200 hover:border-green-300 hover:bg-green-50/50 transition-all duration-200 overflow-hidden material-item cursor-pointer"
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
                        ${['quiz', 'assignment', 'file', 'link'].includes(material.type) ? `
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
                this.showMoveToFolderModal(parseInt(id));
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
                    <button class="btn btn-secondary w-full px-5 py-3.5 bg-gray-100 text-gray-700 rounded-2xl font-bold hover:bg-gray-200 transition-all cancel-add-material">Batal</button>
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
    }

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
    }

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
    }

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
    }

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
    }

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
    }

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
    }

    showMoveToFolderModal(materialId) {
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

            await this.moveMaterialToFolder(materialId, parseInt(folderId));
            modal.remove();
        });

        modal.querySelector('.move-cancel-btn').addEventListener('click', () => modal.remove());
    }

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
    }

    async deleteMaterial(type, id) {
        try {
            const response = await fetch(`/${type}s/${id}`, { method: 'DELETE' });
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
    }

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
    }

    refresh() {
        this.loadAllData().then(() => {
            this.render();
            this.attachEventListeners();
        });
    }
}

// Make globally accessible
window.MaterialsList = MaterialsList;
