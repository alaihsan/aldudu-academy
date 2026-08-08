/**
 * Aldudu Academy - Course Detail: KBM (Teaching Journal) Notes
 * Split out of course_detail.js — loaded after it on course_detail.html.
 */

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
