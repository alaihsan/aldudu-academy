/**
 * FolderTree Component
 * Manages hierarchical folder display with expand/collapse, drag&drop targets
 */
class FolderTree {
    constructor(containerId, courseId, options = {}) {
        this.container = document.getElementById(containerId);
        this.courseId = courseId;
        this.folders = [];
        this.activeFolderId = null;
        this.expandedFolders = new Set();
        this.onFolderSelect = options.onFolderSelect || (() => {});
        this.onFolderCreate = options.onFolderCreate || (() => {});
        this.onFolderDelete = options.onFolderDelete || (() => {});

        this.init();
    }

    async init() {
        await this.loadFolders();
        this.render();
        this.attachEventListeners();
    }

    async loadFolders() {
        try {
            const response = await fetch(`/api/courses/${this.courseId}/folders`);
            const data = await response.json();
            if (data.success) {
                this.folders = data.folders;
            }
        } catch (error) {
            console.error('Error loading folders:', error);
        }
    }

    render() {
        const html = `
            <div class="folder-tree">
                <div class="folder-tree-header">
                    <h3 class="text-sm font-bold text-gray-700 mb-4">📁 Materi Kelas</h3>
                    <button class="btn-add-folder btn btn-sm btn-outline" title="Tambah Folder">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
                        </svg>
                        Folder
                    </button>
                </div>

                <div class="folder-tree-items space-y-1">
                    ${this.renderFolders(this.folders)}
                </div>

                <div class="folder-tree-all-materials mt-4 pt-4 border-t border-gray-200">
                    <button class="folder-item folder-item-all flex items-center w-full px-3 py-2 rounded-lg hover:bg-gray-100 transition-colors" data-folder-id="all">
                        <svg class="w-4 h-4 mr-2 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                        </svg>
                        <span class="text-sm font-medium text-gray-700">Semua Materi</span>
                    </button>
                </div>
            </div>
        `;

        this.container.innerHTML = html;
    }

    renderFolders(folders, level = 0) {
        return folders.map(folder => {
            const hasChildren = folder.children && folder.children.length > 0;
            const isExpanded = this.expandedFolders.has(folder.id);
            const indent = `${level * 1.5}rem`;
            const itemCount = folder.total_items || 0;

            return `
                <div class="folder-item-group" data-folder-id="${folder.id}">
                    <div class="folder-item flex items-center w-full px-3 py-2 rounded-lg hover:bg-gray-100 transition-colors"
                         style="padding-left: calc(${indent} + 0.75rem)"
                         data-folder-id="${folder.id}">
                        ${hasChildren ? `
                            <button class="toggle-folder mr-2 text-gray-500 hover:text-gray-700 transition-transform ${isExpanded ? 'rotate-90' : ''}"
                                    data-folder-id="${folder.id}" title="Toggle">
                                <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                    <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"/>
                                </svg>
                            </button>
                        ` : '<div class="w-6"></div>'}

                        <svg class="w-4 h-4 mr-2 text-amber-500 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M2 6a2 2 0 012-2h12a2 2 0 012 2v8a2 2 0 01-2 2H4a2 2 0 01-2-2V6z"/>
                        </svg>

                        <span class="text-sm font-medium text-gray-700 flex-1 truncate">${folder.name}</span>
                        <span class="text-xs text-gray-400 ml-2">${itemCount}</span>

                        <button class="folder-menu-btn text-gray-400 hover:text-gray-600 transition-colors"
                                data-folder-id="${folder.id}" title="Menu">
                            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z"/>
                            </svg>
                        </button>
                    </div>

                    ${hasChildren && isExpanded ? `
                        <div class="folder-children">
                            ${this.renderFolders(folder.children, level + 1)}
                        </div>
                    ` : ''}
                </div>
            `;
        }).join('');
    }

    attachEventListeners() {
        // Folder selection
        this.container.querySelectorAll('.folder-item').forEach(el => {
            el.addEventListener('click', (e) => {
                if (e.target.closest('.toggle-folder') || e.target.closest('.folder-menu-btn')) {
                    return;
                }
                const folderId = el.dataset.folderId === 'all' ? null : parseInt(el.dataset.folderId);
                this.selectFolder(folderId);
            });
        });

        // Toggle expand/collapse
        this.container.querySelectorAll('.toggle-folder').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const folderId = parseInt(btn.dataset.folderId);
                this.toggleFolder(folderId);
            });
        });

        // Folder menu
        this.container.querySelectorAll('.folder-menu-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const folderId = parseInt(btn.dataset.folderId);
                this.showFolderMenu(folderId, e);
            });
        });

        // Add folder button
        const addBtn = this.container.querySelector('.btn-add-folder');
        if (addBtn) {
            addBtn.addEventListener('click', () => this.showCreateFolderModal());
        }

        // Make folders droppable for drag&drop
        this.container.querySelectorAll('.folder-item').forEach(el => {
            el.addEventListener('dragover', (e) => {
                e.preventDefault();
                el.classList.add('drag-over');
            });
            el.addEventListener('dragleave', () => {
                el.classList.remove('drag-over');
            });
            el.addEventListener('drop', (e) => {
                e.preventDefault();
                el.classList.remove('drag-over');
                const folderId = el.dataset.folderId === 'all' ? null : parseInt(el.dataset.folderId);
                this.onDrop(folderId, e);
            });
        });
    }

    selectFolder(folderId) {
        this.activeFolderId = folderId;

        // Update UI
        this.container.querySelectorAll('.folder-item').forEach(el => {
            el.classList.remove('active');
        });

        const activeEl = this.container.querySelector(`.folder-item[data-folder-id="${folderId === null ? 'all' : folderId}"]`);
        if (activeEl) {
            activeEl.classList.add('active');
        }

        this.onFolderSelect(folderId);
    }

    toggleFolder(folderId) {
        if (this.expandedFolders.has(folderId)) {
            this.expandedFolders.delete(folderId);
        } else {
            this.expandedFolders.add(folderId);
        }
        this.render();
        this.attachEventListeners();
    }

    showFolderMenu(folderId, event) {
        // Show context menu for folder operations
        const menu = document.createElement('div');
        menu.className = 'context-menu absolute bg-white rounded-lg shadow-lg border border-gray-200 z-50';
        menu.innerHTML = `
            <button class="menu-item w-full text-left px-4 py-2 hover:bg-gray-50 text-sm text-gray-700">
                <svg class="w-4 h-4 inline mr-2"/>Rename
            </button>
            <button class="menu-item w-full text-left px-4 py-2 hover:bg-gray-50 text-sm text-red-600">
                <svg class="w-4 h-4 inline mr-2"/>Delete
            </button>
        `;
        menu.style.left = event.pageX + 'px';
        menu.style.top = event.pageY + 'px';

        document.body.appendChild(menu);

        menu.addEventListener('click', (e) => {
            const btn = e.target.closest('button');
            if (btn) {
                if (btn.textContent.includes('Rename')) {
                    this.showRenameFolderModal(folderId);
                } else if (btn.textContent.includes('Delete')) {
                    this.deleteFolder(folderId);
                }
            }
            menu.remove();
        });

        document.addEventListener('click', () => menu.remove(), { once: true });
    }

    showCreateFolderModal(parentFolderId = null) {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay fixed inset-0 bg-black/50 flex items-center justify-center z-50';
        modal.innerHTML = `
            <div class="modal-content bg-white rounded-2xl shadow-2xl p-6 w-96">
                <h3 class="text-lg font-bold mb-4">Buat Folder Baru</h3>
                <input type="text" id="folder-name" class="form-control w-full px-4 py-2 border border-gray-300 rounded-lg mb-4" placeholder="Nama folder...">
                <div class="flex gap-3">
                    <button class="btn btn-primary flex-1">Buat</button>
                    <button class="btn btn-secondary flex-1">Batal</button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        const input = modal.querySelector('#folder-name');
        input.focus();

        const createBtn = modal.querySelector('.btn-primary');
        createBtn.addEventListener('click', async () => {
            const name = input.value.trim();
            if (name) {
                await this.createFolder(name, parentFolderId);
                modal.remove();
            }
        });

        modal.querySelector('.btn-secondary').addEventListener('click', () => modal.remove());
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') createBtn.click();
        });
    }

    showRenameFolderModal(folderId) {
        const folder = this.findFolder(folderId);
        if (!folder) return;

        const modal = document.createElement('div');
        modal.className = 'modal-overlay fixed inset-0 bg-black/50 flex items-center justify-center z-50';
        modal.innerHTML = `
            <div class="modal-content bg-white rounded-2xl shadow-2xl p-6 w-96">
                <h3 class="text-lg font-bold mb-4">Rename Folder</h3>
                <input type="text" id="folder-name" class="form-control w-full px-4 py-2 border border-gray-300 rounded-lg mb-4" value="${folder.name}">
                <div class="flex gap-3">
                    <button class="btn btn-primary flex-1">Simpan</button>
                    <button class="btn btn-secondary flex-1">Batal</button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        const input = modal.querySelector('#folder-name');
        input.focus();
        input.select();

        const saveBtn = modal.querySelector('.btn-primary');
        saveBtn.addEventListener('click', async () => {
            const name = input.value.trim();
            if (name) {
                await this.updateFolder(folderId, { name });
                modal.remove();
            }
        });

        modal.querySelector('.btn-secondary').addEventListener('click', () => modal.remove());
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') saveBtn.click();
        });
    }

    async createFolder(name, parentFolderId = null) {
        try {
            const response = await fetch(`/api/courses/${this.courseId}/folders`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, parent_folder_id: parentFolderId })
            });
            const data = await response.json();
            if (data.success) {
                await this.loadFolders();
                this.render();
                this.attachEventListeners();
                this.onFolderCreate(data.folder);
            }
        } catch (error) {
            console.error('Error creating folder:', error);
        }
    }

    async updateFolder(folderId, updates) {
        try {
            const response = await fetch(`/folders/${folderId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updates)
            });
            const data = await response.json();
            if (data.success) {
                await this.loadFolders();
                this.render();
                this.attachEventListeners();
            }
        } catch (error) {
            console.error('Error updating folder:', error);
        }
    }

    async deleteFolder(folderId) {
        if (!confirm('Hapus folder ini? Isi folder akan dipindahkan ke parent folder.')) return;

        try {
            const response = await fetch(`/folders/${folderId}`, { method: 'DELETE' });
            const data = await response.json();
            if (data.success) {
                await this.loadFolders();
                this.render();
                this.attachEventListeners();
                this.onFolderDelete(folderId);
            }
        } catch (error) {
            console.error('Error deleting folder:', error);
        }
    }

    findFolder(folderId) {
        const search = (folders) => {
            for (let folder of folders) {
                if (folder.id === folderId) return folder;
                if (folder.children) {
                    const found = search(folder.children);
                    if (found) return found;
                }
            }
            return null;
        };
        return search(this.folders);
    }

    onDrop(folderId, event) {
        const dragData = event.dataTransfer.getData('application/json');
        if (dragData) {
            try {
                const data = JSON.parse(dragData);
                // Handle drop by emitting event
                this.onFolderSelect(folderId, data);
            } catch (error) {
                console.error('Error parsing drop data:', error);
            }
        }
    }

    refresh() {
        this.loadFolders().then(() => {
            this.render();
            this.attachEventListeners();
        });
    }
}
