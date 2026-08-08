/**
 * MaterialsList Component v2.0 — DnD
 * Object.assign(MaterialsList.prototype, {...}) split of materials-list-v2.js's
 * drag & drop methods. Loaded right after materials_list.js on course_detail.html.
 */
Object.assign(MaterialsList.prototype, {
    attachDragAndDropListeners() {
        // Baris materi & folder draggable (untuk reorder + drop ke folder).
        // Klik tombol tetap aman karena handleDragStart membatalkan drag bila
        // dimulai dari tombol/kontrol.
        this.container.querySelectorAll('.material-item[draggable="true"]').forEach(item => {
            item.addEventListener('dragstart', (e) => this.handleDragStart(e, 'material'));
            item.addEventListener('dragend', (e) => this.handleDragEnd(e));
        });
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
    },

    handleDragStart(e, type) {
        // Jangan mulai drag bila interaksi berasal dari tombol/kontrol (mis. chevron
        // toggle folder, tombol aksi) — supaya klik tombol tetap berfungsi (terutama Firefox).
        if (e.target.closest('button, a, input, select, textarea')) {
            e.preventDefault();
            return;
        }
        this.draggedItem = e.target.closest('.material-item, .folder-item');
        this.draggedType = type;
        
        if (this.draggedItem) {
            e.dataTransfer.effectAllowed = 'move';
            e.dataTransfer.setData('text/plain', this.draggedItem.dataset.dragType);
            // Gunakan seluruh baris sebagai gambar drag (bukan hanya handle)
            try { e.dataTransfer.setDragImage(this.draggedItem, 20, 20); } catch (err) {}
            // Add dragging class
            this.draggedItem.classList.add('dragging');
        }
    },

    handleDragEnd(e) {
        if (this.draggedItem) {
            this.draggedItem.classList.remove('dragging', 'drag-above', 'drag-below');
        }
        
        // Remove all drag indicators
        this.container.querySelectorAll('.drag-above, .drag-below, .drag-over').forEach(el => {
            el.classList.remove('drag-above', 'drag-below', 'drag-over');
        });

        this.draggedItem = null;
        this.draggedType = null;
    },

    handleDragOver(e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        // Sorot folder sebagai target drop
        const folder = e.currentTarget && e.currentTarget.classList ? e.currentTarget : e.target.closest('.folder-item');
        if (folder && folder.classList.contains('folder-item')) folder.classList.add('drag-over');
    },

    handleDragLeave(e) {
        const folder = e.currentTarget && e.currentTarget.classList ? e.currentTarget : e.target.closest('.folder-item');
        if (folder && folder.classList) folder.classList.remove('drag-over');
    },

    handleDropOnFolder(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const folderItem = e.target.closest('.folder-item');
        if (!folderItem || !this.draggedItem) return;
        
        const targetFolderId = parseInt(folderItem.dataset.folderId);
        
        if (this.draggedType === 'material') {
            const materialId = parseInt(this.draggedItem.dataset.materialId);
            const materialType = this.draggedItem.dataset.materialType;
            this.moveMaterialToFolder(materialId, targetFolderId, materialType);
        } else if (this.draggedType === 'folder') {
            const draggedFolderId = parseInt(this.draggedItem.dataset.folderId);
            if (draggedFolderId !== targetFolderId) {
                this.moveFolder(draggedFolderId, targetFolderId);
            }
        }
        
        this.handleDragEnd(e);
    },

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
    },

    async moveMaterialToFolder(materialId, folderId, materialType) {
        try {
            // Endpoint type-aware: hindari tabrakan id antar tabel (quiz/file/link/tugas)
            const response = await fetch(`/api/materials/${materialType}/${materialId}/move`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ folder_id: folderId })
            });

            const data = await response.json();

            if (data.success) {
                // Update local data (cocokkan id DAN type)
                const material = this.materials.find(m => m.id === materialId && m.type === materialType);
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
    },

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
    },

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
    },

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
    },
});
