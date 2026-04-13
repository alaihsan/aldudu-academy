/**
 * Aldudu Academy - Course Detail JavaScript
 * Modern interactions for an elegant learning experience
 * Features: Drag & Drop, Sorting, Folders
 */

document.addEventListener('DOMContentLoaded', function() {
    CourseDetail.init();
});

const CourseDetail = {
    currentSort: 'newest',
    draggedEl: null,

    init() {
        this.initFileSizeSlider();
        this.cacheElements();
        this.bindEvents();
        this.loadDiscussions();
        this.initSorting();
        this.initDragAndDrop();
        this.initFolders();
        this.updateFolderCounts();
    },

    initFileSizeSlider() {
        const sizeSlider = document.getElementById('file-max-size-slider');
        const sizeValue = document.getElementById('file-max-size-value');
        
        if (sizeSlider && sizeValue) {
            sizeSlider.addEventListener('input', () => {
                sizeValue.textContent = `${sizeSlider.value} MB`;
            });
        }
    },

    cacheElements() {
        this.courseId = document.querySelector('main')?.dataset.courseId;
        this.addTopicsBtn = document.getElementById('add-topics-button');
        this.addTopicsMenu = document.getElementById('topics-dropdown-menu');
        this.topicsContainer = document.getElementById('topics-container');
        this.discussionsContainer = document.getElementById('discussions-container');
        this.tabBtns = document.querySelectorAll('.tab-btn');
        this.directCreateQuizBtn = document.getElementById('direct-create-quiz');
        this.sortBtn = document.getElementById('sort-button');
        this.sortMenu = document.getElementById('sort-dropdown-menu');

        this.modals = {
            assignment: { el: document.getElementById('create-assignment-modal'), showBtn: document.getElementById('show-create-assignment-modal'), form: document.getElementById('create-assignment-form'), cancelBtn: document.querySelector('.assignment-cancel-btn') },
            file: { el: document.getElementById('create-file-modal'), showBtn: document.getElementById('show-create-file-modal'), form: document.getElementById('create-file-form'), cancelBtn: document.querySelector('.file-cancel-btn') },
            link: { el: document.getElementById('create-link-modal'), showBtn: document.getElementById('show-create-link-modal'), form: document.getElementById('create-link-form'), cancelBtn: document.querySelector('.link-cancel-btn') },
            discussion: { el: document.getElementById('create-discussion-modal'), showBtn: document.getElementById('show-create-discussion-modal'), form: document.getElementById('create-discussion-form'), cancelBtn: document.querySelector('.discussion-cancel-btn') },
            folder: { el: document.getElementById('create-folder-modal'), showBtn: document.getElementById('show-create-folder-modal'), form: document.getElementById('create-folder-form'), cancelBtn: document.querySelector('.folder-cancel-btn') }
        };
    },

    bindEvents() {
        this.addTopicsBtn?.addEventListener('click', (e) => {
            e.stopPropagation();
            this.addTopicsMenu.classList.toggle('hidden');
        });

        window.addEventListener('click', (e) => {
            if (!e.target.closest('#add-topics-dropdown')) {
                this.addTopicsMenu?.classList.add('hidden');
            }
            if (!e.target.closest('#sort-dropdown')) {
                this.sortMenu?.classList.add('hidden');
            }
        });

        this.directCreateQuizBtn?.addEventListener('click', (e) => {
            e.preventDefault();
            this.addTopicsMenu?.classList.add('hidden');
            this.createQuizDirectly();
        });

        this.tabBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const tab = btn.dataset.tab;
                this.switchTab(btn, tab);
            });
        });

        // Initialize all modals
        Object.keys(this.modals).forEach(key => {
            const modal = this.modals[key];
            if (!modal.el) return;
            modal.showBtn?.addEventListener('click', (e) => {
                e.preventDefault();
                this.closeAllModals();
                modal.el.classList.remove('hidden');
                this.addTopicsMenu?.classList.add('hidden');
            });
            modal.cancelBtn?.addEventListener('click', () => modal.el.classList.add('hidden'));
            if (modal.form) {
                modal.form.addEventListener('submit', (e) => {
                    if (key === 'folder') {
                        this.handleFolderCreate(e);
                    } else {
                        this.handleFormSubmit(e, key);
                    }
                });
            }
        });
    },

    // ─── Sorting ────────────────────────────────────────────────

    initSorting() {
        this.sortBtn?.addEventListener('click', (e) => {
            e.stopPropagation();
            this.sortMenu?.classList.toggle('hidden');
        });

        document.querySelectorAll('.sort-option').forEach(btn => {
            btn.addEventListener('click', () => {
                const sort = btn.dataset.sort;
                this.currentSort = sort;
                document.getElementById('sort-label').textContent = btn.querySelector('span').textContent;
                this.sortMenu?.classList.add('hidden');
                this.applySorting(sort);
            });
        });
    },

    applySorting(sort) {
        const container = this.topicsContainer;
        const items = Array.from(container.querySelectorAll('.draggable-item'));

        if (sort === 'newest') {
            items.sort((a, b) => {
                const dateA = new Date(a.dataset.created || 0);
                const dateB = new Date(b.dataset.created || 0);
                return dateB - dateA;
            });
        } else if (sort === 'oldest') {
            items.sort((a, b) => {
                const dateA = new Date(a.dataset.created || 0);
                const dateB = new Date(b.dataset.created || 0);
                return dateA - dateB;
            });
        } else if (sort === 'manual') {
            items.sort((a, b) => {
                return (parseInt(a.dataset.order) || 0) - (parseInt(b.dataset.order) || 0);
            });
        }

        // Re-append in sorted order (preserves non-draggable items like empty state)
        items.forEach(item => container.appendChild(item));
    },

    // ─── Drag & Drop ────────────────────────────────────────────

    initDragAndDrop() {
        this.setupDraggables();
        this.setupDropZones();
    },

    setupDraggables() {
        const items = document.querySelectorAll('.draggable-item');
        items.forEach(item => {
            item.setAttribute('draggable', 'true');

            item.addEventListener('dragstart', (e) => {
                this.draggedEl = item;
                item.classList.add('dragging');
                
                // Set drag image and data
                e.dataTransfer.effectAllowed = 'move';
                e.dataTransfer.setData('text/plain', JSON.stringify({
                    id: item.dataset.itemId,
                    type: item.dataset.itemType,
                    folderId: item.dataset.folderId || ''
                }));
                
                // Add visual feedback
                setTimeout(() => {
                    item.style.opacity = '0.5';
                    item.style.transform = 'scale(1.02)';
                }, 0);
            });

            item.addEventListener('dragend', () => {
                item.classList.remove('dragging');
                item.style.opacity = '1';
                item.style.transform = 'scale(1)';
                this.draggedEl = null;
                
                // Remove all drag-over states
                document.querySelectorAll('.drag-over, .folder-drop-highlight').forEach(el => {
                    el.classList.remove('drag-over', 'folder-drop-highlight');
                });
            });
        });
    },

    setupDropZones() {
        const container = this.topicsContainer;

        // Main grid as drop zone for reordering
        container.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';

            const afterElement = this.getDragAfterElement(container, e.clientY, e.clientX);
            if (this.draggedEl && !this.draggedEl.classList.contains('folder-card')) {
                if (afterElement == null) {
                    container.appendChild(this.draggedEl);
                } else {
                    container.insertBefore(this.draggedEl, afterElement);
                }
            }
        });

        container.addEventListener('drop', (e) => {
            e.preventDefault();
            if (!this.draggedEl || this.draggedEl.classList.contains('folder-card')) return;

            // If dropped on the main container (not in a folder), remove from folder
            if (this.draggedEl.dataset.folderId) {
                this.draggedEl.dataset.folderId = '';
            }

            this.saveOrder();
        });

        // Folder drop zones
        document.querySelectorAll('.folder-drop-zone').forEach(zone => {
            zone.addEventListener('dragover', (e) => {
                e.preventDefault();
                e.stopPropagation();
                e.dataTransfer.dropEffect = 'move';
                zone.classList.add('folder-drop-highlight');
            });

            zone.addEventListener('dragleave', (e) => {
                if (!zone.contains(e.relatedTarget)) {
                    zone.classList.remove('folder-drop-highlight');
                }
            });

            zone.addEventListener('drop', (e) => {
                e.preventDefault();
                e.stopPropagation();
                zone.classList.remove('folder-drop-highlight');

                if (!this.draggedEl || this.draggedEl.classList.contains('folder-card')) return;

                const folderId = zone.dataset.folderId;
                this.moveToFolder(this.draggedEl, folderId);
            });
        });

        // Folder cards as drop targets
        document.querySelectorAll('.folder-card').forEach(folderCard => {
            folderCard.addEventListener('dragover', (e) => {
                e.preventDefault();
                if (this.draggedEl && !this.draggedEl.classList.contains('folder-card')) {
                    folderCard.classList.add('drag-over');
                    e.dataTransfer.dropEffect = 'move';
                }
            });

            folderCard.addEventListener('dragleave', (e) => {
                if (!folderCard.contains(e.relatedTarget)) {
                    folderCard.classList.remove('drag-over');
                }
            });

            folderCard.addEventListener('drop', (e) => {
                e.preventDefault();
                e.stopPropagation();
                folderCard.classList.remove('drag-over');

                if (!this.draggedEl || this.draggedEl.classList.contains('folder-card')) return;

                const folderId = folderCard.dataset.itemId;
                this.moveToFolder(this.draggedEl, folderId);
            });
        });
    },

    getDragAfterElement(container, y, x) {
        const draggableElements = [...container.querySelectorAll('.draggable-item:not(.dragging)')];

        return draggableElements.reduce((closest, child) => {
            const box = child.getBoundingClientRect();
            const offsetY = y - box.top - box.height / 2;
            const offsetX = x - box.left - box.width / 2;
            const offset = Math.sqrt(offsetY * offsetY + offsetX * offsetX);

            if (offsetY < 0 && offset < (closest.offset || Infinity)) {
                return { offset: offset, element: child };
            }
            return closest;
        }, {}).element;
    },

    async moveToFolder(itemEl, folderId) {
        const itemId = itemEl.dataset.itemId;
        const itemType = itemEl.dataset.itemType;
        const originalFolderId = itemEl.dataset.folderId;

        // Visual feedback - show moving state
        itemEl.style.transition = 'all 0.3s ease';
        itemEl.style.transform = 'scale(0.95)';
        itemEl.style.opacity = '0.7';

        try {
            const res = await fetch(`/api/courses/${this.courseId}/content/move-to-folder`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    item_id: itemId, 
                    item_type: itemType, 
                    folder_id: folderId 
                })
            });
            
            if (!res.ok) {
                throw new Error('Failed to move item');
            }
            
            const data = await res.json();
            
            if (data.success) {
                // Update data attribute
                itemEl.dataset.folderId = folderId;
                
                // Visual success feedback
                itemEl.style.transform = 'scale(1)';
                itemEl.style.opacity = '1';
                itemEl.style.backgroundColor = '#dcfce7'; // green-100
                setTimeout(() => {
                    itemEl.style.backgroundColor = '';
                }, 1000);
                
                // Move item visually into the folder's drop zone
                const folderCard = document.querySelector(`.folder-card[data-item-id="${folderId}"]`);
                if (folderCard) {
                    const dropZone = folderCard.querySelector('.folder-drop-zone');
                    const emptyMsg = dropZone.querySelector('.folder-empty-msg');
                    if (emptyMsg) emptyMsg.style.display = 'none';

                    // Create a compact version of the item inside the folder
                    const miniItem = this.createMiniItem(itemEl, folderId);
                    dropZone.appendChild(miniItem);

                    // Remove from main grid if it was there
                    if (itemEl.parentElement === this.topicsContainer) {
                        itemEl.remove();
                    }

                    // Expand folder to show the item
                    const contents = folderCard.querySelector('.folder-contents');
                    if (contents.classList.contains('hidden')) {
                        contents.classList.remove('hidden');
                        const arrow = folderCard.querySelector('.folder-arrow');
                        if (arrow) arrow.style.transform = 'rotate(180deg)';
                    }

                    this.updateFolderCounts();
                    
                    // Show success notification
                    this.showNotification('✅ Materi berhasil dipindahkan ke folder', 'success');
                }
            } else {
                throw new Error(data.message || 'Gagal memindahkan materi');
            }
        } catch (err) {
            console.error('Failed to move item:', err);
            
            // Revert visual state on error
            itemEl.style.transform = 'scale(1)';
            itemEl.style.opacity = '1';
            itemEl.style.backgroundColor = '#fee2e2'; // red-100
            setTimeout(() => {
                itemEl.style.backgroundColor = '';
            }, 1000);
            
            // Show error notification
            this.showNotification('❌ Gagal memindahkan materi. Silakan coba lagi.', 'error');
            
            // Revert folderId if move failed
            if (originalFolderId) {
                itemEl.dataset.folderId = originalFolderId;
            }
        }
    },

    createMiniItem(originalItem, folderId) {
        const type = originalItem.dataset.itemType;
        const id = originalItem.dataset.itemId;
        const link = originalItem.querySelector('a');
        const name = originalItem.querySelector('h3')?.textContent || 'Untitled';
        const href = link?.getAttribute('href') || '#';
        const typeLabel = originalItem.querySelector('p.text-gray-500')?.textContent || '';

        const colorMap = {
            quiz: { bg: 'bg-amber-100', text: 'text-amber-600' },
            assignment: { bg: 'bg-green-100', text: 'text-green-600' },
            file: { bg: 'bg-blue-100', text: 'text-blue-600' },
            link: { bg: 'bg-indigo-100', text: 'text-indigo-600' }
        };
        const color = colorMap[type] || colorMap.file;

        const div = document.createElement('div');
        div.className = 'folder-mini-item flex items-center space-x-3 bg-white rounded-xl p-3 border border-gray-100 hover:shadow-md transition-all cursor-grab';
        div.setAttribute('draggable', 'true');
        div.dataset.itemId = id;
        div.dataset.itemType = type;
        div.dataset.folderId = folderId;

        div.innerHTML = `
            <div class="w-8 h-8 rounded-lg ${color.bg} ${color.text} flex items-center justify-center flex-shrink-0">
                ${this.getTypeIcon(type)}
            </div>
            <a href="${href}" class="flex-1 min-w-0 text-sm font-bold text-gray-700 truncate hover:text-primary-600">${name}</a>
            ${typeof IS_TEACHER !== 'undefined' && IS_TEACHER ? `<button class="remove-from-folder-btn p-1 text-gray-300 hover:text-red-500 transition-colors flex-shrink-0" data-item-id="${id}" data-item-type="${type}" title="Keluarkan dari folder">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
            </button>` : ''}
        `;

        // Drag events for mini items
        div.addEventListener('dragstart', (e) => {
            this.draggedEl = div;
            div.classList.add('dragging');
            e.dataTransfer.effectAllowed = 'move';
            e.dataTransfer.setData('text/plain', JSON.stringify({ id, type }));
        });

        div.addEventListener('dragend', () => {
            div.classList.remove('dragging');
            this.draggedEl = null;
            document.querySelectorAll('.drag-over, .folder-drop-highlight').forEach(el => {
                el.classList.remove('drag-over', 'folder-drop-highlight');
            });
        });

        // Remove from folder button
        const removeBtn = div.querySelector('.remove-from-folder-btn');
        removeBtn?.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.removeFromFolder(id, type, div);
        });

        return div;
    },

    getTypeIcon(type) {
        const icons = {
            quiz: '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25"/></svg>',
            assignment: '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"/></svg>',
            file: '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"/></svg>',
            link: '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"/></svg>'
        };
        return icons[type] || icons.file;
    },

    async removeFromFolder(itemId, itemType, miniItemEl) {
        try {
            const res = await fetch(`/api/courses/${this.courseId}/content/move-to-folder`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ item_id: itemId, item_type: itemType, folder_id: null })
            });
            const data = await res.json();
            if (data.success) {
                miniItemEl.remove();
                this.updateFolderCounts();
                // Reload to get full card back in main grid
                window.location.reload();
            }
        } catch (err) {
            console.error('Failed to remove from folder', err);
        }
    },

    async saveOrder() {
        const items = [];
        const allItems = this.topicsContainer.querySelectorAll('.draggable-item');
        allItems.forEach((item, index) => {
            items.push({
                id: parseInt(item.dataset.itemId),
                type: item.dataset.itemType,
                order: index,
                folder_id: item.dataset.folderId || null
            });
        });

        try {
            await fetch(`/api/courses/${this.courseId}/content/reorder`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ items })
            });
            // Update data attributes
            allItems.forEach((item, index) => {
                item.dataset.order = index;
            });
        } catch (err) {
            console.error('Failed to save order', err);
        }
    },

    // ─── Folders ────────────────────────────────────────────────

    initFolders() {
        // Folder toggle (expand/collapse)
        document.querySelectorAll('.folder-toggle-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const folderCard = btn.closest('.folder-card');
                const contents = folderCard.querySelector('.folder-contents');
                const arrow = folderCard.querySelector('.folder-arrow');
                const label = btn.querySelector('span');

                contents.classList.toggle('hidden');
                if (contents.classList.contains('hidden')) {
                    arrow.style.transform = 'rotate(0deg)';
                    label.textContent = 'Buka Folder';
                } else {
                    arrow.style.transform = 'rotate(180deg)';
                    label.textContent = 'Tutup Folder';
                }
            });
        });

        // Rename folder
        document.querySelectorAll('.rename-folder-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const folderCard = btn.closest('.folder-card');
                const folderId = folderCard.dataset.itemId;
                const currentName = folderCard.querySelector('.folder-name').textContent.trim();
                const newName = prompt('Nama folder baru:', currentName);
                if (newName && newName.trim() !== currentName) {
                    this.renameFolder(folderId, newName.trim(), folderCard);
                }
            });
        });

        // Delete folder
        document.querySelectorAll('.delete-folder-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const folderCard = btn.closest('.folder-card');
                const folderId = folderCard.dataset.itemId;
                const folderName = folderCard.querySelector('.folder-name').textContent.trim();
                if (confirm(`Hapus folder "${folderName}"? Konten di dalamnya akan dipindah ke level atas.`)) {
                    this.deleteFolder(folderId, folderCard);
                }
            });
        });

        // Populate folder contents from server data
        this.populateFolderContents();
    },

    populateFolderContents() {
        // Find items that are inside folders (rendered by server with folder_id)
        // These are in the topics data passed via template
        if (typeof FOLDERS_DATA === 'undefined') return;

        // Items with folder_id are not rendered in main grid (template filters them)
        // But we need to show them inside their folders
        // We'll load them via API
        this.loadFolderContents();
    },

    loadFolderContents() {
        if (typeof TOPICS_DATA === 'undefined') return;

        TOPICS_DATA.forEach(topic => {
            if (topic.folder_id) {
                const folderCard = document.querySelector(`.folder-card[data-item-id="${topic.folder_id}"]`);
                if (folderCard) {
                    const dropZone = folderCard.querySelector('.folder-drop-zone');
                    const emptyMsg = dropZone.querySelector('.folder-empty-msg');
                    if (emptyMsg) emptyMsg.remove();

                    // Create a pseudo-element for createMiniItem
                    const pseudoItem = {
                        dataset: {
                            itemId: topic.id,
                            itemType: topic.type.toLowerCase().replace('kuis', 'quiz').replace('tugas', 'assignment').replace('berkas', 'file'),
                        },
                        querySelector: (selector) => {
                            if (selector === 'a') return { getAttribute: () => topic.url };
                            if (selector === 'h3') return { textContent: topic.name };
                            if (selector === 'p.text-gray-500') return { textContent: topic.type };
                            return null;
                        }
                    };

                    const miniItem = this.createMiniItem(pseudoItem, topic.folder_id);
                    dropZone.appendChild(miniItem);
                }
            }
        });
        this.updateFolderCounts();
    },

    async renameFolder(folderId, newName, folderCard) {
        try {
            const res = await fetch(`/api/folders/${folderId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: newName })
            });
            const data = await res.json();
            if (data.success) {
                folderCard.querySelector('.folder-name').textContent = newName;
            }
        } catch (err) {
            console.error('Failed to rename folder', err);
        }
    },

    async deleteFolder(folderId, folderCard) {
        try {
            const res = await fetch(`/api/folders/${folderId}`, { method: 'DELETE' });
            const data = await res.json();
            if (data.success) {
                folderCard.remove();
                window.location.reload();
            }
        } catch (err) {
            console.error('Failed to delete folder', err);
        }
    },

    async handleFolderCreate(e) {
        e.preventDefault();
        const nameInput = document.getElementById('folder-name-input');
        const errorEl = document.getElementById('folder-modal-error');
        const name = nameInput.value.trim();

        if (!name) {
            errorEl.textContent = 'Nama folder wajib diisi';
            errorEl.classList.remove('hidden');
            return;
        }

        try {
            const res = await fetch(`/api/courses/${this.courseId}/folders`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name })
            });
            const data = await res.json();
            if (data.success) {
                window.location.reload();
            } else {
                errorEl.textContent = data.message || 'Gagal membuat folder';
                errorEl.classList.remove('hidden');
            }
        } catch (err) {
            errorEl.textContent = 'Kesalahan koneksi ke server';
            errorEl.classList.remove('hidden');
        }
    },

    updateFolderCounts() {
        document.querySelectorAll('.folder-card').forEach(folderCard => {
            const dropZone = folderCard.querySelector('.folder-drop-zone');
            const items = dropZone.querySelectorAll('.folder-mini-item');
            const countEl = folderCard.querySelector('.folder-item-count');
            const emptyMsg = dropZone.querySelector('.folder-empty-msg');

            if (countEl) {
                countEl.textContent = `${items.length} item`;
            }

            if (items.length === 0 && !emptyMsg) {
                const msg = document.createElement('p');
                msg.className = 'folder-empty-msg col-span-full text-center text-xs text-gray-400 py-4';
                msg.textContent = 'Seret konten ke sini';
                dropZone.appendChild(msg);
            } else if (items.length > 0 && emptyMsg) {
                emptyMsg.remove();
            }
        });
    },

    // ─── Quiz Creation ──────────────────────────────────────────

    async createQuizDirectly() {
        try {
            const res = await fetch(`/api/courses/${this.courseId}/quizzes`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: 'Kuis Tanpa Judul', points: 100, grade_type: 'numeric' })
            });
            const data = await res.json();
            if (data.success) {
                window.location.href = `/quiz/${data.quiz.id}`;
            } else {
                alert(data.message || 'Gagal membuat kuis');
            }
        } catch (err) {
            console.error('Failed to create quiz', err);
            alert('Kesalahan koneksi ke server');
        }
    },

    // ─── Tab Switching ──────────────────────────────────────────

    switchTab(activeBtn, tabType) {
        this.tabBtns.forEach(b => {
            b.classList.remove('active', 'bg-primary-600', 'text-white', 'shadow-lg', 'shadow-primary-100');
            b.classList.add('text-gray-500', 'hover:bg-gray-50');
        });
        activeBtn.classList.add('active', 'bg-primary-600', 'text-white', 'shadow-lg', 'shadow-primary-100');
        activeBtn.classList.remove('text-gray-500', 'hover:bg-gray-50');

        const topicCards = this.topicsContainer.querySelectorAll('.draggable-item');

        if (tabType === 'Diskusi' || tabType === 'diskusi') {
            this.topicsContainer.classList.add('hidden');
            this.discussionsContainer.classList.remove('hidden');
            document.getElementById('diskusi-section')?.scrollIntoView({ behavior: 'smooth' });
        } else {
            this.topicsContainer.classList.remove('hidden');
            this.discussionsContainer.classList.add('hidden');

            topicCards.forEach(card => {
                const typeText = card.querySelector('p.text-gray-500')?.textContent || '';
                if (tabType === 'all') {
                    card.classList.remove('hidden');
                } else if (card.classList.contains('folder-card')) {
                    // Show folders in all tabs
                    card.classList.remove('hidden');
                } else if (typeText.includes(tabType)) {
                    card.classList.remove('hidden');
                } else {
                    card.classList.add('hidden');
                }
            });
        }
    },

    // ─── Discussions ────────────────────────────────────────────

    async loadDiscussions() {
        if (!this.courseId) return;
        try {
            const res = await fetch(`/api/courses/${this.courseId}/discussions`);
            const data = await res.json();
            if (data.success) {
                this.renderDiscussions(data.discussions);
            }
        } catch (err) { console.error('Failed to load discussions', err); }
    },

    renderDiscussions(discussions) {
        if (!this.discussionsContainer) return;
        if (discussions.length === 0) {
            this.discussionsContainer.innerHTML = '<div class="col-span-full py-10 text-center text-gray-400 font-medium">Belum ada diskusi di kelas ini.</div>';
            return;
        }

        this.discussionsContainer.innerHTML = DOMPurify.sanitize(discussions.map(d => `
            <div class="group bg-white rounded-[2rem] border border-gray-100 shadow-premium hover:shadow-xl transition-all duration-500 p-8 flex flex-col h-full transform hover:-translate-y-2">
                <div class="flex items-center space-x-3 mb-6">
                    <div class="w-10 h-10 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center font-bold">
                        ${d.user.name[0].toUpperCase()}
                    </div>
                    <div>
                        <p class="text-xs font-black text-gray-400 uppercase tracking-widest leading-none mb-1">${DOMPurify.sanitize(d.user.name)}</p>
                        <p class="text-[10px] text-gray-400">${new Date(d.created_at).toLocaleDateString()}</p>
                    </div>
                </div>
                <h3 class="text-lg font-bold text-gray-900 group-hover:text-primary-600 transition-colors mb-4 line-clamp-2">${DOMPurify.sanitize(d.title)}</h3>
                <div class="mt-auto pt-6 border-t border-gray-50 flex items-center justify-between text-gray-400">
                    <div class="flex items-center space-x-4">
                        <div class="flex items-center space-x-1.5">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/></svg>
                            <span class="text-xs font-bold">${d.posts.length} Balasan</span>
                        </div>
                    </div>
                    <a href="/kelas/${this.courseId}/diskusi/${d.id}" class="text-xs font-black text-primary-600 uppercase tracking-widest hover:underline">Buka Diskusi</a>
                </div>
            </div>
        `).join(''));
    },

    // ─── Modals & Forms ─────────────────────────────────────────

    closeAllModals() {
        Object.values(this.modals).forEach(m => m.el?.classList.add('hidden'));
    },

    async handleFormSubmit(e, type) {
        e.preventDefault();
        const form = e.target;
        const errorEl = form.querySelector('[id$="-error"]');

        let url = `/api/courses/${this.courseId}/`;
        let options = { method: 'POST' };

        if (type === 'file') {
            url += 'files';
            
            // Validate file upload
            const fileInput = document.getElementById('file-upload-input');
            const file = fileInput.files[0];
            const maxSizeSlider = document.getElementById('file-max-size-slider');
            const maxSizeMB = parseInt(maxSizeSlider.value) || 10;
            const maxSizeBytes = maxSizeMB * 1024 * 1024;
            
            if (!file) {
                errorEl.textContent = 'Pilih file yang akan diunggah';
                errorEl.classList.remove('hidden');
                return;
            }
            
            // Validate file type
            const allowedExtensions = ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'png', 'jpg', 'jpeg', 'gif', 'webp', 'txt', 'rtf', 'zip', 'rar', '7z'];
            const fileExtension = file.name.split('.').pop().toLowerCase();
            if (!allowedExtensions.includes(fileExtension)) {
                errorEl.textContent = `Tipe file .${fileExtension} tidak diizinkan. Format yang diterima: ${allowedExtensions.join(', ')}`;
                errorEl.classList.remove('hidden');
                return;
            }
            
            // Validate file size
            if (file.size > maxSizeBytes) {
                errorEl.textContent = `Ukuran file (${(file.size / (1024 * 1024)).toFixed(2)} MB) melebihi batas maksimal ${maxSizeMB} MB`;
                errorEl.classList.remove('hidden');
                return;
            }
            
            const formData = new FormData();
            formData.append('name', document.getElementById('file-name-input').value);
            formData.append('file', file);
            options.body = formData;
        } else if (type === 'assignment') {
            url = `/assignment/course/${this.courseId}/create`;
            const formData = new FormData(form);
            options.body = formData;
        } else if (type === 'link') {
            url += 'links';
            options.headers = { 'Content-Type': 'application/json' };
            options.body = JSON.stringify({
                name: document.getElementById('link-name-input').value,
                url: document.getElementById('link-url-input').value
            });
        } else if (type === 'discussion') {
            url = `/api/courses/${this.courseId}/discussions`;
            options.headers = { 'Content-Type': 'application/json' };
            options.body = JSON.stringify({
                title: document.getElementById('discussion-title-input').value,
                content: document.getElementById('discussion-content-input').value
            });
        }

        try {
            const res = await fetch(url, options);
            const data = await res.json();
            if (data.success) {
                window.location.reload();
            } else {
                errorEl.textContent = data.message || 'Terjadi kesalahan';
                errorEl.classList.remove('hidden');
            }
        } catch (err) {
            console.error('Submit failed', err);
            if (errorEl) { errorEl.textContent = 'Kesalahan koneksi ke server'; errorEl.classList.remove('hidden'); }
        }
    },

    // ─── Notifications ────────────────────────────────────────────

    showNotification(message, type = 'info') {
        // Remove existing notification
        const existing = document.querySelector('.drag-notification');
        if (existing) existing.remove();

        const colors = {
            success: { bg: 'bg-green-50', border: 'border-green-200', text: 'text-green-700', icon: '✅' },
            error: { bg: 'bg-red-50', border: 'border-red-200', text: 'text-red-700', icon: '❌' },
            info: { bg: 'bg-blue-50', border: 'border-blue-200', text: 'text-blue-700', icon: 'ℹ️' }
        };

        const color = colors[type] || colors.info;

        const notification = document.createElement('div');
        notification.className = `drag-notification fixed bottom-6 right-6 ${color.bg} ${color.border} border-2 rounded-2xl px-6 py-4 shadow-2xl z-[9999] animate-slide-up flex items-center gap-3`;
        notification.innerHTML = `
            <span class="text-xl">${color.icon}</span>
            <span class="font-bold ${color.text}">${message}</span>
        `;

        document.body.appendChild(notification);

        // Auto-remove after 3 seconds
        setTimeout(() => {
            notification.style.transition = 'all 0.3s ease';
            notification.style.opacity = '0';
            notification.style.transform = 'translateY(20px)';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
};

/**
 * KBM Tab Activation - Called from sidebar
 */
function activateKbmTab() {
    const kbmSection = document.getElementById('kbm-section');
    const diskusiSection = document.getElementById('diskusi-section');
    const topicsContainer = document.getElementById('topics-container');

    // Hide other sections
    if (diskusiSection) diskusiSection.classList.add('hidden');
    if (topicsContainer) topicsContainer.classList.add('hidden');

    // Show KBM section
    if (kbmSection) {
        kbmSection.classList.remove('hidden');
        kbmSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    // Update tab state
    updateTabState('kbm');

    // Load KBM data
    if (typeof loadKbmNotes === 'function') {
        loadKbmNotes();
    }
}

function updateTabState(tabName) {
    document.querySelectorAll('[data-tab]').forEach(btn => {
        btn.classList.remove('active', 'bg-theme', 'text-white');
        btn.classList.add('text-gray-500');
    });

    const activeBtn = document.querySelector(`[data-tab="${tabName}"]`);
    if (activeBtn) {
        activeBtn.classList.add('active', 'bg-theme', 'text-white');
        activeBtn.classList.remove('text-gray-500');
    }
}

function toggleKbmForm() {
    const form = document.getElementById('kbm-add-form');
    form.classList.toggle('hidden');
}

async function loadKbmNotes() {
    try {
        const courseId = window.courseId;
        const res = await fetch(`/api/courses/${courseId}/kbm-notes`);
        const data = await res.json();
        currentKbmNotes = data.kbm_notes || [];
        renderKbmNotes();
    } catch (err) {
        console.error('Failed to load KBM notes:', err);
    }
}

function renderKbmNotes() {
    const container = document.getElementById('kbm-timeline-content');
    if (!container) return;

    container.innerHTML = '';

    if (currentKbmNotes.length === 0) {
        container.innerHTML = '<p class="text-center py-8 text-gray-500 dark:text-gray-400">Belum ada catatan KBM.</p>';
        return;
    }

    const sortedNotes = currentKbmNotes.sort((a, b) => new Date(b.activity_date) - new Date(a.activity_date));
    const typeIcons = {
        'teori': '📖',
        'praktikum': '🧪',
        'ujian': '📝',
        'tugas': '📋',
        'review': '🔁',
        'lainnya': '📌'
    };

    sortedNotes.forEach(note => {
        const date = new Date(note.activity_date);
        const dateStr = date.toLocaleDateString('id-ID', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });

        const div = document.createElement('div');
        div.className = 'relative pl-16 group';
        div.innerHTML = `
            <!-- Dot on timeline -->
            <div class="absolute left-0 top-0 w-12 h-12 rounded-full bg-white border-4 border-theme shadow-lg flex items-center justify-center text-xl group-hover:scale-110 transition-transform">
                ${typeIcons[note.activity_type] || '📌'}
            </div>

            <!-- Content card -->
            <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-800 rounded-2xl p-5 hover:shadow-lg transition-all cursor-pointer" onclick="openKbmEditModal(${note.id})">
                <div class="flex items-start justify-between mb-2">
                    <div class="flex-1">
                        <h4 class="font-bold text-gray-900 dark:text-gray-100 text-lg">${note.topic}</h4>
                        <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">${dateStr}${note.start_time ? ' • ' + note.start_time + '-' + note.end_time : ''}</p>
                    </div>
                    <div class="flex items-center space-x-2">
                        <span class="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded text-xs font-bold uppercase">${note.activity_type}</span>
                        <span class="text-gray-400 dark:text-gray-500 group-hover:text-theme transition-colors">✏️</span>
                    </div>
                </div>
                ${note.description ? `<p class="text-sm text-gray-700 dark:text-gray-300 mt-2 line-clamp-2">${note.description}</p>` : ''}
                ${note.notes ? `<div class="mt-3 pt-3 border-t border-gray-100 dark:border-gray-700"><p class="text-xs text-gray-500 dark:text-gray-400 italic">📝 ${note.notes}</p></div>` : ''}
            </div>
        `;
        container.appendChild(div);
    });
}

async function saveKbmNote() {
    const date = document.getElementById('kbm-date').value;
    const topic = document.getElementById('kbm-topic').value.trim();

    if (!date || !topic) {
        alert('Tanggal dan materi/topik wajib diisi');
        return;
    }

    const data = {
        activity_date: date,
        start_time: document.getElementById('kbm-start-time').value || null,
        end_time: document.getElementById('kbm-end-time').value || null,
        activity_type: document.getElementById('kbm-type').value,
        topic: topic,
        description: document.getElementById('kbm-description').value.trim(),
        notes: document.getElementById('kbm-notes').value.trim(),
    };

    try {
        const courseId = window.courseId;
        const res = await fetch(`/api/courses/${courseId}/kbm-notes`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        const result = await res.json();

        if (result.success) {
            toggleKbmForm();
            loadKbmNotes();
            // Reset form
            document.getElementById('kbm-topic').value = '';
            document.getElementById('kbm-description').value = '';
            document.getElementById('kbm-notes').value = '';
        } else {
            alert('Gagal: ' + result.message);
        }
    } catch (err) {
        alert('Gagal menyimpan catatan');
    }
}

function openKbmEditModal(noteId) {
    const note = currentKbmNotes.find(n => n.id === noteId);
    if (!note) return;

    document.getElementById('kbm-edit-id').value = note.id;
    document.getElementById('kbm-edit-date').value = note.activity_date;
    document.getElementById('kbm-edit-start-time').value = note.start_time || '';
    document.getElementById('kbm-edit-end-time').value = note.end_time || '';
    document.getElementById('kbm-edit-type').value = note.activity_type;
    document.getElementById('kbm-edit-topic').value = note.topic;
    document.getElementById('kbm-edit-description').value = note.description || '';
    document.getElementById('kbm-edit-notes').value = note.notes || '';

    document.getElementById('kbm-edit-modal').classList.remove('hidden');
}

function closeKbmEditModal() {
    document.getElementById('kbm-edit-modal').classList.add('hidden');
}

async function updateKbmNote() {
    const noteId = document.getElementById('kbm-edit-id').value;
    const date = document.getElementById('kbm-edit-date').value;
    const topic = document.getElementById('kbm-edit-topic').value.trim();

    if (!date || !topic) {
        alert('Tanggal dan materi/topik wajib diisi');
        return;
    }

    const data = {
        activity_date: date,
        start_time: document.getElementById('kbm-edit-start-time').value || null,
        end_time: document.getElementById('kbm-edit-end-time').value || null,
        activity_type: document.getElementById('kbm-edit-type').value,
        topic: topic,
        description: document.getElementById('kbm-edit-description').value.trim(),
        notes: document.getElementById('kbm-edit-notes').value.trim(),
    };

    try {
        const courseId = window.courseId;
        const res = await fetch(`/api/courses/${courseId}/kbm-notes/${noteId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        const result = await res.json();

        if (result.success) {
            closeKbmEditModal();
            loadKbmNotes();
        } else {
            const errorEl = document.getElementById('kbm-edit-error');
            errorEl.textContent = result.message;
            errorEl.classList.remove('hidden');
        }
    } catch (err) {
        console.error('Update failed', err);
        const errorEl = document.getElementById('kbm-edit-error');
        errorEl.textContent = 'Kesalahan koneksi ke server';
        errorEl.classList.remove('hidden');
    }
}

async function deleteKbmNote() {
    const noteId = document.getElementById('kbm-edit-id').value;
    if (!confirm('Yakin ingin menghapus catatan ini?')) return;

    try {
        const courseId = window.courseId;
        const res = await fetch(`/api/courses/${courseId}/kbm-notes/${noteId}`, {
            method: 'DELETE',
        });
        const result = await res.json();

        if (result.success) {
            closeKbmEditModal();
            loadKbmNotes();
        } else {
            alert('Gagal menghapus catatan');
        }
    } catch (err) {
        alert('Gagal menghapus catatan');
    }
}

// Color Picker Functions
function openColorPicker() {
    document.getElementById('color-picker-modal').classList.remove('hidden');
}

function closeColorPicker() {
    document.getElementById('color-picker-modal').classList.add('hidden');
}

function selectColor(color) {
    const courseId = window.courseId;

    // Update CSS variables immediately for preview
    document.documentElement.style.setProperty('--course-theme', color);
    document.documentElement.style.setProperty('--course-theme-light', color + '15');
    document.documentElement.style.setProperty('--course-theme-dark', color + 'cc');
    document.documentElement.style.setProperty('--course-theme-gradient', `linear-gradient(135deg, ${color}, ${color}cc)`);

    // Update hero section background
    const heroSection = document.querySelector('.hero-section');
    if (heroSection) {
        heroSection.style.backgroundColor = color;
    }

    // Save to database
    fetch(`/api/course/${courseId}/theme`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ color: color })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            // Show success notification
            const notification = document.createElement('div');
            notification.className = 'fixed bottom-6 right-6 px-6 py-4 bg-green-600 text-white rounded-2xl shadow-2xl z-[100] animate-slide-up flex items-center gap-3';
            notification.innerHTML = `
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                </svg>
                <span class="font-bold text-sm">Warna tema berhasil diubah!</span>
            `;
            document.body.appendChild(notification);
            setTimeout(() => {
                notification.style.opacity = '0';
                notification.style.transition = 'opacity 0.3s';
                setTimeout(() => notification.remove(), 300);
            }, 3000);

            closeColorPicker();
        } else {
            alert('Gagal mengubah warna tema');
        }
    })
    .catch(err => {
        console.error(err);
        alert('Terjadi kesalahan');
    });
}

// Materials List Initialization
document.addEventListener('DOMContentLoaded', function() {
    const courseId = window.courseId;
    const isTeacher = window.isTeacher;

    // Initialize Materials List (Full Width - No Folder Tree)
    window.materialsList = new MaterialsList('materials-list-container', courseId, {
        isTeacher: isTeacher,
        onMaterialSelect: (type, id) => {
            // Handle material selection (open/view)
            // For teachers, quiz opens in editor mode by default; students see preview
            const urls = {
                'quiz': `/quiz/${id}`,
                'assignment': `/assignment/${id}`,
                'file': `/files/${id}`,
                'link': null
            };
            if (urls[type]) {
                window.open(urls[type], '_blank');
            }
        },
        onMaterialDelete: () => {
            window.materialsList.refresh();
        }
    });
});
