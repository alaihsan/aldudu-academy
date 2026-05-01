let currentGradeItem = null;
let currentGradeItemData = null;
let students = [];
let gradeItems = [];
let entriesByItem = {};

document.addEventListener('DOMContentLoaded', function() {
    loadGradebook();
});

async function loadGradebook() {
    setSaveStatus('Memuat data...');
    await loadStudents();
    await loadGradeItems();
    await loadEntriesForItems();
    await loadStats();
    renderGradebook();
    setSaveStatus('');
}

async function loadStudents() {
    try {
        const res = await fetch(`/api/courses/${window.courseId}/students`);
        const data = await res.json();
        students = data.students || [];
        document.getElementById('stat-students').textContent = students.length;
    } catch (err) {
        console.error('Failed to load students:', err);
        students = [];
    }
}

async function loadGradeItems() {
    try {
        const res = await fetch(`/gradebook/api/items?course_id=${window.courseId}`);
        const data = await res.json();
        gradeItems = data.success ? (data.items || []) : [];
        document.getElementById('stat-items').textContent = gradeItems.length;
    } catch (err) {
        console.error('Failed to load grade items:', err);
        gradeItems = [];
    }
}

async function loadEntriesForItems() {
    const pairs = await Promise.all(gradeItems.map(async item => {
        try {
            const res = await fetch(`/gradebook/api/entries?grade_item_id=${item.id}`);
            const data = await res.json();
            const map = {};
            if (data.success) {
                (data.entries || []).forEach(entry => {
                    map[entry.student_id] = entry;
                });
            }
            return [item.id, map];
        } catch (err) {
            console.error('Failed to load entries:', err);
            return [item.id, {}];
        }
    }));

    entriesByItem = Object.fromEntries(pairs);
    const gradedCount = pairs.reduce((total, pair) => total + Object.keys(pair[1]).length, 0);
    document.getElementById('stat-graded').textContent = gradedCount;
}

async function loadStats() {
    try {
        const res = await fetch(`/gradebook/api/stats/${window.courseId}`);
        const data = await res.json();
        document.getElementById('stat-average').textContent = data.success && data.stats.average_grade
            ? data.stats.average_grade.toFixed(1)
            : '-';
    } catch (err) {
        document.getElementById('stat-average').textContent = '-';
    }
}

function renderGradebook() {
    const wrap = document.getElementById('gradebook-table-wrap');
    const filter = document.getElementById('filter-type').value;
    const visibleItems = gradeItems.filter(item => !filter || getItemType(item) === filter);

    if (students.length === 0) {
        wrap.innerHTML = '<div class="text-center py-12 text-gray-500 dark:text-gray-400">Belum ada siswa di kelas ini.</div>';
        return;
    }

    if (visibleItems.length === 0) {
        wrap.innerHTML = '<div class="text-center py-12 text-gray-500 dark:text-gray-400">Belum ada kolom nilai untuk filter ini.</div>';
        return;
    }

    const headers = visibleItems.map(item => `
        <th class="grade-col px-3 py-3 text-left align-top">
            <button type="button" onclick="openGradeEntryModal(${item.id})" class="grade-col-title">
                <span class="grade-type ${getItemType(item)}">${getItemTypeLabel(item)}</span>
                <span class="grade-name">${escapeHtml(cleanItemName(item.name))}</span>
                <span class="grade-max">Max ${formatNumber(item.max_score)}</span>
            </button>
        </th>
    `).join('');

    const rows = students.map((student, index) => {
        const cells = visibleItems.map(item => {
            const entry = (entriesByItem[item.id] || {})[student.id];
            const score = entry && entry.score !== null && entry.score !== undefined ? formatNumber(entry.score) : '';
            const feedback = entry && entry.feedback ? entry.feedback : '';
            const emptyClass = score === '' ? 'empty' : '';

            return `
                <td class="grade-cell px-3 py-3 align-top" onclick="openGradeEntryModal(${item.id})">
                    <div class="score-pill ${emptyClass}">${score || '-'}</div>
                    <div class="feedback-text" title="${escapeHtml(feedback)}">${feedback ? escapeHtml(feedback) : '<span class="muted">Komentar</span>'}</div>
                </td>
            `;
        }).join('');

        return `
            <tr class="border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/40">
                <td class="sticky-col number px-4 py-3 text-sm text-gray-500 dark:text-gray-400">${index + 1}</td>
                <td class="sticky-col student px-4 py-3">
                    <div class="font-semibold text-gray-900 dark:text-gray-100">${escapeHtml(student.name)}</div>
                    <div class="text-xs text-gray-500 dark:text-gray-400">${student.email ? escapeHtml(student.email) : ''}</div>
                </td>
                ${cells}
            </tr>
        `;
    }).join('');

    wrap.innerHTML = `
        <table class="gradebook-table">
            <thead>
                <tr>
                    <th class="sticky-col number px-4 py-3 text-left">No</th>
                    <th class="sticky-col student px-4 py-3 text-left">Siswa</th>
                    ${headers}
                </tr>
            </thead>
            <tbody>${rows}</tbody>
        </table>
    `;
}

function getItemType(item) {
    if (item.quiz_id) return 'quiz';
    if (item.is_assignment || item.assignment_id) return 'assignment';
    return 'manual';
}

function getItemTypeLabel(item) {
    const type = getItemType(item);
    if (type === 'quiz') return 'Quiz';
    if (type === 'assignment') return 'Tugas';
    return 'Lainnya';
}

function cleanItemName(name) {
    return (name || '').replace(/^Quiz:\s*/i, '').replace(/^Kuis:\s*/i, '').replace(/^Tugas:\s*/i, '');
}

function openAddItemModal() {
    document.getElementById('add-item-modal').classList.remove('hidden');
    setTimeout(() => document.getElementById('item-name').focus(), 0);
}

function closeAddItemModal() {
    document.getElementById('add-item-modal').classList.add('hidden');
    document.getElementById('add-item-form').reset();
    document.getElementById('add-item-error').classList.add('hidden');
}

async function saveGradeItem() {
    const errorDiv = document.getElementById('add-item-error');
    errorDiv.classList.add('hidden');

    const name = document.getElementById('item-name').value.trim();
    const maxScore = document.getElementById('item-max-score').value || 100;

    if (!name) {
        errorDiv.textContent = 'Nama kolom wajib diisi';
        errorDiv.classList.remove('hidden');
        return;
    }

    try {
        const res = await fetch('/gradebook/api/items', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                course_id: window.courseId,
                name,
                max_score: maxScore,
                weight: 0,
                description: document.getElementById('item-description').value
            }),
        });
        const result = await res.json();

        if (!result.success) {
            errorDiv.textContent = result.message || 'Gagal menyimpan kolom';
            errorDiv.classList.remove('hidden');
            return;
        }

        closeAddItemModal();
        await loadGradebook();
        openGradeEntryModal(result.item.id);
    } catch (err) {
        errorDiv.textContent = 'Gagal menyimpan kolom';
        errorDiv.classList.remove('hidden');
    }
}

async function openGradeEntryModal(itemId) {
    currentGradeItem = itemId;
    currentGradeItemData = gradeItems.find(item => item.id === itemId) || null;

    if (!currentGradeItemData) {
        const res = await fetch(`/gradebook/api/items/${itemId}`);
        const data = await res.json();
        currentGradeItemData = data.item;
    }

    document.getElementById('entry-modal-title').textContent = cleanItemName(currentGradeItemData.name);
    document.getElementById('entry-modal-desc').textContent = `${getItemTypeLabel(currentGradeItemData)} | Nilai maksimal ${formatNumber(currentGradeItemData.max_score)}`;

    const entriesMap = entriesByItem[itemId] || {};
    const tbody = document.getElementById('grade-entry-body');
    tbody.innerHTML = students.map((student, idx) => {
        const entry = entriesMap[student.id] || {};
        return `
            <tr data-student-id="${student.id}">
                <td class="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">${idx + 1}</td>
                <td class="px-4 py-3">
                    <div class="font-semibold text-gray-900 dark:text-gray-100">${escapeHtml(student.name)}</div>
                    <div class="text-xs text-gray-500 dark:text-gray-400">${student.email ? escapeHtml(student.email) : ''}</div>
                </td>
                <td class="px-4 py-3">
                    <input type="number" step="0.1" min="0" max="${currentGradeItemData.max_score}" data-score
                        class="grade-input"
                        value="${entry.score !== undefined && entry.score !== null ? entry.score : ''}">
                </td>
                <td class="px-4 py-3">
                    <textarea data-feedback rows="2" class="feedback-input" placeholder="Komentar nilai">${entry.feedback ? escapeHtml(entry.feedback) : ''}</textarea>
                </td>
            </tr>
        `;
    }).join('');

    document.getElementById('grade-entry-modal').classList.remove('hidden');
}

function closeGradeEntryModal() {
    document.getElementById('grade-entry-modal').classList.add('hidden');
    currentGradeItem = null;
    currentGradeItemData = null;
}

function autoFillGrades() {
    if (!currentGradeItemData) return;
    document.querySelectorAll('input[data-score]').forEach(input => {
        input.value = currentGradeItemData.max_score;
    });
}

async function saveAllGrades() {
    const rows = document.querySelectorAll('#grade-entry-body tr');
    const entries = [];

    rows.forEach(row => {
        const score = row.querySelector('input[data-score]').value;
        const feedback = row.querySelector('textarea[data-feedback]').value;

        if (score !== '' || feedback.trim() !== '') {
            entries.push({
                grade_item_id: currentGradeItem,
                student_id: parseInt(row.dataset.studentId, 10),
                score: score === '' ? null : parseFloat(score),
                feedback: feedback
            });
        }
    });

    if (entries.length === 0) {
        alert('Minimal satu nilai atau komentar harus diisi');
        return;
    }

    try {
        setSaveStatus('Menyimpan...');
        const res = await fetch('/gradebook/api/entries/bulk', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ entries }),
        });
        const result = await res.json();

        if (!result.success) {
            alert('Gagal menyimpan: ' + (result.message || 'Terjadi kesalahan'));
            setSaveStatus('');
            return;
        }

        closeGradeEntryModal();
        await loadGradebook();
        setSaveStatus(`${result.saved_count} nilai disimpan`);
        setTimeout(() => setSaveStatus(''), 2500);
    } catch (err) {
        alert('Gagal menyimpan nilai');
        setSaveStatus('');
    }
}

async function syncQuizGrades() {
    const btn = document.getElementById('sync-quiz-btn');
    try {
        if (btn) {
            btn.disabled = true;
            btn.setAttribute('aria-busy', 'true');
            btn.querySelector('.gradebook-action-title').textContent = 'Menyinkronkan...';
            btn.querySelector('.gradebook-action-subtitle').textContent = 'Mohon tunggu sebentar';
        }
        setSaveStatus('Menyinkronkan quiz...');
        const res = await fetch(`/gradebook/api/course/${window.courseId}/sync-quizzes`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const result = await res.json();

        if (!result.success) {
            alert(result.message || 'Gagal menyinkronkan quiz');
            setSaveStatus('');
            return;
        }

        await loadGradebook();
        const created = result.created_items || 0;
        const updated = result.updated_entries || 0;
        setSaveStatus(`${created} kolom baru, ${updated} nilai quiz disinkronkan`);
        setTimeout(() => setSaveStatus(''), 3000);
    } catch (err) {
        alert('Gagal menyinkronkan quiz');
        setSaveStatus('');
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.removeAttribute('aria-busy');
            btn.querySelector('.gradebook-action-title').textContent = 'Sinkronkan Quiz';
            btn.querySelector('.gradebook-action-subtitle').textContent = 'Tarik nilai terbaru ke Buku Nilai';
        }
    }
}

function setSaveStatus(message) {
    document.getElementById('save-status').textContent = message;
}

function formatNumber(value) {
    const number = Number(value);
    if (!Number.isFinite(number)) return '-';
    return Number.isInteger(number) ? String(number) : number.toFixed(1);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text == null ? '' : String(text);
    return div.innerHTML;
}
