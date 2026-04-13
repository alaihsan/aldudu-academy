// Tab switching
function switchTab(type) {
    const items = document.querySelectorAll('.archive-item');
    const tabs = document.querySelectorAll('.archive-tab');

    tabs.forEach(tab => {
        if (tab.dataset.tab === type) {
            tab.classList.add('active', 'border-amber-600', 'text-amber-600');
            tab.classList.remove('border-transparent', 'text-gray-500');
        } else {
            tab.classList.remove('active', 'border-amber-600', 'text-amber-600');
            tab.classList.add('border-transparent', 'text-gray-500');
        }
    });

    items.forEach(item => {
        if (type === 'all' || item.dataset.type === type) {
            item.style.display = 'block';
        } else {
            item.style.display = 'none';
        }
    });
}

function viewQuiz(quizId) {
    window.open(`/quiz/${quizId}`, '_blank');
}

function viewAssignment(assignmentId) {
    window.open(`/assignment/${assignmentId}`, '_blank');
}

function viewFile(fileId) {
    window.open(`/files/${fileId}`, '_blank');
}

function restoreQuiz(quizId, quizName) {
    showRestoreModal(quizId, quizName, 'quiz');
}

function restoreAssignment(assignmentId, assignmentName) {
    showRestoreModal(assignmentId, assignmentName, 'assignment');
}

function restoreFile(fileId, fileName) {
    showRestoreModal(fileId, fileName, 'file');
}

function restoreLink(linkId, linkName) {
    showRestoreModal(linkId, linkName, 'link');
}

let itemToRestore = null;

function showRestoreModal(id, name, type) {
    itemToRestore = { id, name, type };

    Swal.fire({
        title: 'Pulihkan ' + getTypeName(type) + '?',
        html: `
            <div class="text-left text-sm">
                <p class="mb-3"><strong>${name}</strong> akan:</p>
                <ul class="space-y-2 text-gray-600 dark:text-gray-400">
                    <li>✅ Muncul kembali di daftar materi kelas</li>
                    <li>✅ Dapat diakses siswa (jika dipublikasikan)</li>
                    <li>✅ Semua data tetap tersimpan</li>
                </ul>
            </div>
        `,
        icon: 'question',
        showCancelButton: true,
        confirmButtonText: 'Ya, Pulihkan',
        cancelButtonText: 'Batal',
        confirmButtonColor: '#22c55e',
        cancelButtonColor: '#6b7280',
        reverseButtons: true,
        customClass: { popup: 'rounded-3xl' }
    }).then((result) => {
        if (result.isConfirmed) {
            performRestore();
        }
    });
}

function performRestore() {
    if (!itemToRestore) return;

    let url;
    if (itemToRestore.type === 'link') {
        url = `/api/link/${itemToRestore.id}/restore`;
    } else {
        url = `/api/${itemToRestore.type}/${itemToRestore.id}/restore`;
    }

    fetch(url, { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                Swal.fire({
                    icon: 'success',
                    title: 'Berhasil!',
                    text: itemToRestore.type === 'quiz' ? 'Kuis berhasil dipulihkan.' :
                          itemToRestore.type === 'assignment' ? 'Tugas berhasil dipulihkan.' :
                          itemToRestore.type === 'file' ? 'Berkas berhasil dipulihkan.' : 'Link berhasil dipulihkan.',
                    confirmButtonColor: '#22c55e',
                    customClass: { popup: 'rounded-3xl' }
                }).then(() => {
                    location.reload();
                });
            } else {
                Swal.fire({
                    icon: 'error',
                    title: 'Gagal',
                    text: data.message || 'Gagal memulihkan.',
                    confirmButtonColor: '#ef4444',
                    customClass: { popup: 'rounded-3xl' }
                });
            }
        })
        .catch(err => {
            console.error(err);
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: 'Terjadi kesalahan.',
                confirmButtonColor: '#ef4444',
                customClass: { popup: 'rounded-3xl' }
            });
        });
}

function deleteArchivedQuiz(quizId, quizName) {
    showDeleteModal(quizId, quizName, 'quiz');
}

function deleteArchivedAssignment(assignmentId, assignmentName) {
    showDeleteModal(assignmentId, assignmentName, 'assignment');
}

function deleteArchivedFile(fileId, fileName) {
    showDeleteModal(fileId, fileName, 'file');
}

function deleteArchivedLink(linkId, linkName) {
    showDeleteModal(linkId, linkName, 'link');
}

let itemToDelete = null;

function showDeleteModal(id, name, type) {
    itemToDelete = { id, name, type };

    Swal.fire({
        title: 'Hapus Permanen?',
        html: `
            <div class="text-left text-sm">
                <p class="mb-3 text-red-600 font-bold">⚠️ ${getTypeName(type)}: <strong>${name}</strong></p>
                <div class="bg-red-50 p-4 rounded-xl mb-3">
                    <p class="text-xs text-red-700"><strong>Peringatan:</strong></p>
                    <ul class="space-y-1 text-xs text-red-600 mt-2">
                        <li>• Semua data akan dihapus permanen</li>
                        <li>• Tidak dapat dipulihkan</li>
                    </ul>
                </div>
            </div>
        `,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'Ya, Hapus Permanen',
        cancelButtonText: 'Batal',
        confirmButtonColor: '#ef4444',
        cancelButtonColor: '#6b7280',
        reverseButtons: true,
        customClass: { popup: 'rounded-3xl' }
    }).then((result) => {
        if (result.isConfirmed) {
            performDelete();
        }
    });
}

function performDelete() {
    if (!itemToDelete) return;

    let url;
    if (itemToDelete.type === 'quiz') {
        url = `/api/quiz/${itemToDelete.id}`;
    } else if (itemToDelete.type === 'assignment') {
        url = `/api/assignment/${itemToDelete.id}`;
    } else if (itemToDelete.type === 'file') {
        url = `/api/file/${itemToDelete.id}`;
    } else if (itemToDelete.type === 'link') {
        url = `/api/link/${itemToDelete.id}`;
    }

    fetch(url, { method: 'DELETE' })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                Swal.fire({
                    icon: 'success',
                    title: 'Berhasil!',
                    text: 'Item berhasil dihapus permanen.',
                    confirmButtonColor: '#22c55e',
                    customClass: { popup: 'rounded-3xl' }
                }).then(() => {
                    location.reload();
                });
            } else {
                Swal.fire({
                    icon: 'error',
                    title: 'Gagal',
                    text: data.message || 'Gagal menghapus.',
                    confirmButtonColor: '#ef4444',
                    customClass: { popup: 'rounded-3xl' }
                });
            }
        })
        .catch(err => {
            console.error(err);
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: 'Terjadi kesalahan.',
                confirmButtonColor: '#ef4444',
                customClass: { popup: 'rounded-3xl' }
            });
        });
}

function getTypeName(type) {
    const names = {
        quiz: 'Kuis',
        assignment: 'Tugas',
        file: 'File'
    };
    return names[type] || type;
}
