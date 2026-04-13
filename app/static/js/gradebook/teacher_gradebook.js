let currentGradeItem = null;
let students = [];

function switchTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
    document.querySelectorAll('.tab-btn').forEach(el => {
        el.classList.remove('active');
        el.classList.add('text-gray-600', 'dark:text-gray-400', 'hover:bg-gray-100', 'dark:hover:bg-gray-700');
    });

    document.getElementById('content-' + tabName).classList.remove('hidden');
    document.getElementById('tab-' + tabName).classList.add('active');
    document.getElementById('tab-' + tabName).classList.remove('text-gray-600', 'hover:bg-gray-100');

    if (tabName === 'input') loadGradeItems();
    if (tabName === 'recap') loadRecap();
    if (tabName === 'quiz') loadAvailableQuizzes();
    if (tabName === 'analytics') loadAnalytics();
}

document.addEventListener('DOMContentLoaded', function() {
    loadCategories();
    loadLearningObjectives();
    loadStudents();
    loadGradeItems();
});

async function loadStudents() {
    try {
        const courseId = window.courseId;
        const res = await fetch(`/api/courses/${courseId}/students`);
        const data = await res.json();
        students = data.students || [];
    } catch (err) {
        console.error('Failed to load students:', err);
    }
}

async function loadCategories() {
    try {
        const courseId = window.courseId;
        const res = await fetch(`/gradebook/api/categories?course_id=${courseId}`);
        const data = await res.json();
        if (data.success) {
            const selects = ['filter-category', 'item-category', 'import-category'];
            selects.forEach(id => {
                const select = document.getElementById(id);
                if (select) {
                    data.categories.forEach(cat => {
                        const opt = document.createElement('option');
                        opt.value = cat.id;
                        opt.textContent = `${cat.name} (${cat.category_type})`;
                        select.appendChild(opt);
                    });
                }
            });
        }
    } catch (err) {
        console.error('Failed to load categories:', err);
    }
}

async function loadLearningObjectives() {
    try {
        const courseId = window.courseId;
        const res = await fetch(`/gradebook/api/learning-objectives?course_id=${courseId}`);
        const data = await res.json();
        if (data.success) {
            const select = document.getElementById('filter-cp');
            const itemCpSelect = document.getElementById('item-cp');
            data.learning_objectives.forEach(cp => {
                const opt = document.createElement('option');
                opt.value = cp.id;
                opt.textContent = `${cp.code}: ${cp.description.substring(0, 50)}...`;
                if (select) select.appendChild(opt.cloneNode(true));
                if (itemCpSelect) itemCpSelect.appendChild(opt.cloneNode(true));
            });
        }
    } catch (err) {
        console.error('Failed to load learning objectives:', err);
    }
}

async function loadGradeItems() {
    const courseId = window.courseId;
    const container = document.getElementById('grade-items-container');
    container.innerHTML = '<div class="col-span-full text-center py-12"><div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-theme"></div></div>';

    try {
        let url = `/gradebook/api/items?course_id=${courseId}`;
        const categoryId = document.getElementById('filter-category').value;
        if (categoryId) url += `&category_id=${categoryId}`;

        const res = await fetch(url);
        const data = await res.json();

        if (data.success) {
            let items = data.items;
            if (items.length === 0) {
                container.innerHTML = '<div class="col-span-full text-center py-12 text-gray-500">Belum ada item penilaian. Klik "Tambah Item" untuk membuat.</div>';
                return;
            }

            container.innerHTML = '';
            items.forEach(item => {
                container.appendChild(createGradeItemCard(item));
            });
        }
    } catch (err) {
        container.innerHTML = '<div class="col-span-full text-center py-12 text-red-500">Gagal memuat item penilaian</div>';
    }
}

function createGradeItemCard(item) {
    const div = document.createElement('div');
    div.className = 'bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 hover:shadow-lg transition-all';

    const isAssignment = item.is_assignment && item.assignment_id;
    const previewButton = isAssignment
        ? `<button onclick="openAssignmentPreview(${item.assignment_id}, '${escapeHtml(item.name)}')" class="px-4 py-2.5 bg-indigo-50 text-indigo-700 rounded-lg font-semibold hover:bg-indigo-100 transition-all">
            📎 Lampiran
        </button>`
        : '';

    div.innerHTML = `
        <div class="flex items-start justify-between mb-4">
            <div class="flex-1">
                <div class="flex items-center space-x-2 mb-2">
                    <span class="px-2 py-1 bg-theme-light text-theme rounded text-xs font-bold">${item.quiz_id ? '🎯' : isAssignment ? '📝' : '📊'}</span>
                    <h4 class="font-bold text-gray-900 dark:text-gray-100">${item.name}</h4>
                </div>
                <p class="text-sm text-gray-500 dark:text-gray-400">Max: ${item.max_score} | Bobot: ${item.weight}%</p>
            </div>
        </div>
        <div class="flex items-center justify-between text-sm mb-4">
            <span class="text-gray-500 dark:text-gray-400">${item.entries_count || 0} / ${students.length} siswa dinilai</span>
        </div>
        <div class="flex gap-2">
            <button onclick="openGradeEntryModal(${item.id})" class="flex-1 px-4 py-2.5 bg-theme text-white rounded-lg font-semibold hover:opacity-90 transition-all">
                ✏️ Input Nilai
            </button>
            <button onclick="editGradeItem(${item.id})" class="px-4 py-2.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg font-semibold hover:bg-gray-200 dark:hover:bg-gray-600 transition-all">
                Edit
            </button>
            ${previewButton}
        </div>
    `;
    return div;
}

async function loadRecap() {
    const courseId = window.courseId;
    const tbody = document.getElementById('recap-body');
    tbody.innerHTML = '<tr><td colspan="6" class="text-center py-8"><div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-theme"></div></td></tr>';

    try {
        const res = await fetch(`/gradebook/api/stats/${courseId}`);
        const data = await res.json();

        if (data.success && data.stats.grades) {
            tbody.innerHTML = '';
            data.stats.grades.forEach((grade, idx) => {
                const predikat = getPredikat(grade.final_grade);
                tbody.innerHTML += `
                    <tr class="hover:bg-gray-50 dark:hover:bg-gray-700">
                        <td class="px-6 py-4 text-sm text-gray-900 dark:text-gray-100">${idx + 1}</td>
                        <td class="px-6 py-4 text-sm font-semibold text-gray-900 dark:text-gray-100">${grade.student_name}</td>
                        <td class="px-6 py-4 text-sm text-center text-gray-600 dark:text-gray-400">-</td>
                        <td class="px-6 py-4 text-sm text-center text-gray-600 dark:text-gray-400">-</td>
                        <td class="px-6 py-4 text-sm text-center font-bold text-theme">${grade.final_grade.toFixed(1)}</td>
                        <td class="px-6 py-4 text-sm text-center"><span class="px-3 py-1 rounded-full text-xs font-bold ${getPredikatClass(predikat)}">${predikat.split(' ')[0]}</span></td>
                    </tr>
                `;
            });
        }
    } catch (err) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center py-8 text-red-500">Gagal memuat rekap</td></tr>';
    }
}

function getPredikat(grade) {
    if (grade >= 90) return 'A (Sangat Baik)';
    if (grade >= 80) return 'B (Baik)';
    if (grade >= 70) return 'C (Cukup)';
    if (grade >= 60) return 'D (Kurang)';
    return 'E (Sangat Kurang)';
}

function getPredikatClass(predikat) {
    if (predikat.startsWith('A')) return 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400';
    if (predikat.startsWith('B')) return 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400';
    if (predikat.startsWith('C')) return 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400';
    if (predikat.startsWith('D')) return 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400';
    return 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

async function loadAvailableQuizzes() {
    const courseId = window.courseId;
    const container = document.getElementById('quiz-list');
    container.innerHTML = '<div class="text-center py-8"><div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-theme"></div></div>';

    try {
        const res = await fetch(`/gradebook/api/quizzes/available?course_id=${courseId}`);
        const data = await res.json();

        if (data.success) {
            if (data.quizzes.length === 0) {
                container.innerHTML = '<div class="text-center py-8 text-gray-500">Semua quiz sudah diimpor atau belum ada quiz</div>';
                return;
            }

            container.innerHTML = '';
            data.quizzes.forEach(quiz => {
                const div = document.createElement('div');
                div.className = 'bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 flex items-center justify-between hover:shadow-md transition-all';
                div.innerHTML = `
                    <div>
                        <h4 class="font-bold text-gray-900 dark:text-gray-100">${quiz.name}</h4>
                        <p class="text-sm text-gray-500 dark:text-gray-400">Max Points: ${quiz.points} | Submissions: ${quiz.submissions_count}</p>
                    </div>
                    <button onclick="openImportQuizModal(${quiz.id})" class="px-4 py-2 bg-theme text-white rounded-lg text-sm font-semibold hover:opacity-90 transition-all">
                        Import
                    </button>
                `;
                container.appendChild(div);
            });
        }
    } catch (err) {
        container.innerHTML = '<div class="text-center py-8 text-red-500">Gagal memuat quiz</div>';
    }
}

async function loadAnalytics() {
    const courseId = window.courseId;
    try {
        const res = await fetch(`/gradebook/api/stats/${courseId}`);
        const data = await res.json();

        if (data.success) {
            document.getElementById('stat-average').textContent = data.stats.average_grade ? data.stats.average_grade.toFixed(1) : '-';
            document.getElementById('stat-highest').textContent = data.stats.highest_grade ? data.stats.highest_grade.toFixed(1) : '-';
            document.getElementById('stat-lowest').textContent = data.stats.lowest_grade ? data.stats.lowest_grade.toFixed(1) : '-';

            const grades = data.stats.grades.map(g => g.final_grade);
            const distribution = {
                '90-100 (A)': grades.filter(g => g >= 90).length,
                '80-89 (B)': grades.filter(g => g >= 80 && g < 90).length,
                '70-79 (C)': grades.filter(g => g >= 70 && g < 80).length,
                '60-69 (D)': grades.filter(g => g >= 60 && g < 70).length,
                '< 60 (E)': grades.filter(g => g < 60).length,
            };

            const maxCount = Math.max(...Object.values(distribution), 1);
            const distContainer = document.getElementById('grade-distribution');
            distContainer.innerHTML = '';

            for (const [range, count] of Object.entries(distribution)) {
                const width = (count / maxCount * 100);
                distContainer.innerHTML += `
                    <div class="flex items-center space-x-4">
                        <span class="text-sm font-semibold text-gray-600 w-28">${range}</span>
                        <div class="flex-1 bg-gray-200 rounded-full h-8">
                            <div class="bg-theme h-8 rounded-full transition-all font-bold text-white text-sm flex items-center px-3" style="width: ${width}%"></div>
                        </div>
                        <span class="text-sm font-bold text-gray-700 w-12 text-right">${count}</span>
                    </div>
                `;
            }
        }
    } catch (err) {
        console.error('Failed to load analytics:', err);
    }
}

// Modal functions
function openAddItemModal() {
    document.getElementById('add-item-modal').classList.remove('hidden');
}

function closeAddItemModal() {
    document.getElementById('add-item-modal').classList.add('hidden');
    document.getElementById('add-item-form').reset();
}

async function saveGradeItem() {
    const errorDiv = document.getElementById('add-item-error');
    errorDiv.classList.add('hidden');

    const data = {
        course_id: document.getElementById('item-course-id').value,
        name: document.getElementById('item-name').value,
        category_id: document.getElementById('item-category').value,
        max_score: document.getElementById('item-max-score').value,
        weight: document.getElementById('item-weight').value,
        description: document.getElementById('item-description').value,
        learning_objective_id: document.getElementById('item-cp').value || null,
        learning_goal_id: document.getElementById('item-tp').value || null,
    };

    if (!data.name || !data.category_id) {
        errorDiv.textContent = 'Nama dan kategori wajib diisi';
        errorDiv.classList.remove('hidden');
        return;
    }

    try {
        const res = await fetch('/gradebook/api/items', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        const result = await res.json();

        if (result.success) {
            closeAddItemModal();
            loadGradeItems();
        } else {
            errorDiv.textContent = result.message;
            errorDiv.classList.remove('hidden');
        }
    } catch (err) {
        errorDiv.textContent = 'Gagal menyimpan item';
        errorDiv.classList.remove('hidden');
    }
}

async function loadTPForItem() {
    const courseId = window.courseId;
    const cpId = document.getElementById('item-cp').value;
    const tpSelect = document.getElementById('item-tp');
    tpSelect.innerHTML = '<option value="">Tidak ada</option>';

    if (!cpId) return;

    try {
        const res = await fetch(`/gradebook/api/learning-objectives?course_id=${courseId}`);
        const data = await res.json();

        if (data.success) {
            const cp = data.learning_objectives.find(c => c.id == cpId);
            if (cp && cp.goals) {
                cp.goals.forEach(goal => {
                    const opt = document.createElement('option');
                    opt.value = goal.id;
                    opt.textContent = `${goal.code}: ${goal.description}`;
                    tpSelect.appendChild(opt);
                });
            }
        }
    } catch (err) {
        console.error('Failed to load TP:', err);
    }
}

async function openGradeEntryModal(itemId) {
    currentGradeItem = itemId;

    try {
        const res = await fetch(`/gradebook/api/items/${itemId}`);
        const data = await res.json();

        if (data.success) {
            const item = data.item;
            document.getElementById('entry-modal-title').textContent = `Input Nilai - ${item.name}`;
            document.getElementById('entry-modal-desc').textContent = `Max Score: ${item.max_score} | Bobot: ${item.weight}%`;

            const entriesRes = await fetch(`/gradebook/api/entries?grade_item_id=${itemId}`);
            const entriesData = await entriesRes.json();

            const tbody = document.getElementById('grade-entry-body');
            tbody.innerHTML = '';

            if (entriesData.success) {
                const entriesMap = {};
                entriesData.entries.forEach(e => entriesMap[e.student_id] = e);

                students.forEach((student, idx) => {
                    const entry = entriesMap[student.id];
                    tbody.innerHTML += `
                        <tr data-student-id="${student.id}">
                            <td class="px-4 py-3 text-sm text-gray-900 dark:text-gray-100">${idx + 1}</td>
                            <td class="px-4 py-3 text-sm font-semibold text-gray-900 dark:text-gray-100">${student.name}</td>
                            <td class="px-4 py-3 text-center">
                                <input type="number" step="0.1" data-score
                                    class="w-24 px-3 py-2 border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-lg text-center focus:ring-2 focus-theme focus:border-theme outline-none"
                                    value="${entry ? entry.score : ''}"
                                    max="${item.max_score}">
                            </td>
                            <td class="px-4 py-3 text-center">
                                <input type="text" data-feedback
                                    class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-lg text-center focus:ring-2 focus-theme focus:border-theme outline-none"
                                    value="${entry ? entry.feedback || '' : ''}"
                                    placeholder="Feedback...">
                            </td>
                        </tr>
                    `;
                });
            }

            document.getElementById('grade-entry-modal').classList.remove('hidden');
        }
    } catch (err) {
        alert('Gagal memuat data');
    }
}

function closeGradeEntryModal() {
    document.getElementById('grade-entry-modal').classList.add('hidden');
    currentGradeItem = null;
}

function autoFillGrades() {
    const inputs = document.querySelectorAll('input[data-score]');
    inputs.forEach(input => input.value = 100);
}

async function saveAllGrades() {
    const rows = document.querySelectorAll('#grade-entry-body tr');
    const entries = [];

    rows.forEach(row => {
        const studentId = row.dataset.studentId;
        const score = row.querySelector('input[data-score]').value;
        const feedback = row.querySelector('input[data-feedback]').value;

        if (score !== '') {
            entries.push({
                grade_item_id: currentGradeItem,
                student_id: parseInt(studentId),
                score: parseFloat(score),
                feedback: feedback,
            });
        }
    });

    if (entries.length === 0) {
        alert('Minimal satu nilai harus diisi');
        return;
    }

    try {
        const res = await fetch('/gradebook/api/entries/bulk', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ entries }),
        });
        const result = await res.json();

        if (result.success) {
            alert(`Berhasil menyimpan ${result.saved_count} nilai`);
            closeGradeEntryModal();
            loadGradeItems();
        } else {
            alert('Gagal menyimpan: ' + result.message);
        }
    } catch (err) {
        alert('Gagal menyimpan nilai');
    }
}

function openImportQuizModal(quizId) {
    document.getElementById('import-quiz-id').value = quizId;
    document.getElementById('import-quiz-modal').classList.remove('hidden');
}

function closeImportQuizModal() {
    document.getElementById('import-quiz-modal').classList.add('hidden');
}

async function confirmImportQuiz() {
    const quizId = document.getElementById('import-quiz-id').value;
    const categoryId = document.getElementById('import-category').value;
    const tpId = document.getElementById('import-tp').value;

    if (!categoryId) {
        alert('Pilih kategori terlebih dahulu');
        return;
    }

    try {
        const res = await fetch(`/gradebook/api/quizzes/${quizId}/import`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                category_id: categoryId,
                learning_goal_id: tpId || null,
            }),
        });
        const result = await res.json();

        if (result.success) {
            alert('Quiz berhasil diimpor!');
            closeImportQuizModal();
            loadGradeItems();
        } else {
            alert('Gagal mengimpor: ' + result.message);
        }
    } catch (err) {
        alert('Gagal mengimpor quiz');
    }
}

// CTT Item Analysis Functions
async function loadCTTQuizList() {
    const courseId = window.courseId;
    const select = document.getElementById('ctt-quiz-select');

    try {
        const res = await fetch(`/gradebook/api/course/${courseId}/quizzes-with-analysis`);
        const data = await res.json();

        if (data.success && data.quizzes) {
            select.innerHTML = '<option value="">Pilih Quiz/Tugas</option>';
            data.quizzes.forEach(quiz => {
                const option = document.createElement('option');
                option.value = quiz.id;
                option.textContent = `${quiz.name} (${quiz.submission_count} submissions)`;
                select.appendChild(option);
            });
        }
    } catch (err) {
        console.error('Failed to load quiz list:', err);
    }
}

async function loadCTTAnalysis() {
    const quizId = document.getElementById('ctt-quiz-select').value;
    const content = document.getElementById('ctt-analysis-content');

    if (!quizId) {
        content.innerHTML = `
            <div class="text-center py-12 text-gray-400">
                <p class="text-sm">Pilih quiz atau tugas untuk melihat analisis butir soal</p>
            </div>
        `;
        return;
    }

    try {
        const res = await fetch(`/gradebook/api/quiz/${quizId}/ctt-analysis`);
        const data = await res.json();

        if (!data.success || !data.items || data.items.length === 0) {
            content.innerHTML = `
                <div class="text-center py-12 text-gray-400">
                    <p class="text-sm">Tidak ada data untuk dianalisis</p>
                </div>
            `;
            return;
        }

        const items = data.items;

        let html = `
            <div class="overflow-x-auto">
                <table class="w-full text-sm">
                    <thead>
                        <tr class="border-b border-gray-200 dark:border-gray-700">
                            <th class="text-left py-3 px-4 font-bold text-gray-700 dark:text-gray-300">Soal</th>
                            <th class="text-center py-3 px-4 font-bold text-gray-700 dark:text-gray-300">p-value<br><span class="text-xs font-normal">(Kesukaran)</span></th>
                            <th class="text-center py-3 px-4 font-bold text-gray-700 dark:text-gray-300">Daya Beda</th>
                            <th class="text-center py-3 px-4 font-bold text-gray-700 dark:text-gray-300">Status</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

        items.forEach((item, index) => {
            const pValue = item.p_value || 0;
            const pointBiserial = item.point_biserial || 0;

            // Interpret p-value
            let difficulty = 'Sedang';
            let difficultyColor = 'text-blue-600 dark:text-blue-400';
            if (pValue < 0.3) {
                difficulty = 'Sukar';
                difficultyColor = 'text-red-600 dark:text-red-400';
            } else if (pValue > 0.7) {
                difficulty = 'Mudah';
                difficultyColor = 'text-green-600 dark:text-green-400';
            }

            // Interpret point-biserial
            let discrimination = 'Cukup';
            let discriminationColor = 'text-yellow-600 dark:text-yellow-400';
            let status = '⚠️ Perlu Review';
            let statusBg = 'bg-yellow-50 dark:bg-yellow-900/30';

            if (pointBiserial >= 0.4) {
                discrimination = 'Baik';
                discriminationColor = 'text-green-600 dark:text-green-400';
                status = '✅ Baik';
                statusBg = 'bg-green-50 dark:bg-green-900/30';
            } else if (pointBiserial >= 0.2) {
                discrimination = 'Cukup';
                discriminationColor = 'text-blue-600 dark:text-blue-400';
                status = '👍 Cukup';
                statusBg = 'bg-blue-50 dark:bg-blue-900/30';
            } else if (pointBiserial < 0) {
                discrimination = 'Buruk';
                discriminationColor = 'text-red-600 dark:text-red-400';
                status = '❌ Buruk';
                statusBg = 'bg-red-50 dark:bg-red-900/30';
            }

            html += `
                <tr class="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700">
                    <td class="py-3 px-4">
                        <p class="font-semibold text-gray-900 dark:text-gray-100">Soal ${index + 1}</p>
                        <p class="text-xs text-gray-500 dark:text-gray-400">Benar: ${item.correct_count}/${item.total_students}</p>
                    </td>
                    <td class="text-center py-3 px-4">
                        <span class="text-lg font-bold ${difficultyColor}">${pValue.toFixed(2)}</span>
                        <p class="text-xs text-gray-500 dark:text-gray-400">${difficulty}</p>
                    </td>
                    <td class="text-center py-3 px-4">
                        <span class="text-lg font-bold ${discriminationColor}">${pointBiserial.toFixed(2)}</span>
                    </td>
                    <td class="text-center py-3 px-4">
                        <span class="px-3 py-1 rounded-full text-xs font-bold ${statusBg}">${status}</span>
                    </td>
                </tr>
            `;
        });

        html += `
                    </tbody>
                </table>
            </div>

            <!-- Summary Stats -->
            <div class="grid grid-cols-3 gap-4 mt-6">
                <div class="bg-blue-50 rounded-lg p-4 text-center">
                    <p class="text-xs text-blue-600 font-bold uppercase">Rata-rata p-value</p>
                    <p class="text-2xl font-bold text-blue-700 mt-1">${data.summary.avg_p_value.toFixed(2)}</p>
                    <p class="text-xs text-blue-600 mt-1">${data.summary.difficulty_level}</p>
                </div>
                <div class="bg-green-50 rounded-lg p-4 text-center">
                    <p class="text-xs text-green-600 font-bold uppercase">Rata-rata Daya Beda</p>
                    <p class="text-2xl font-bold text-green-700 mt-1">${data.summary.avg_point_biserial.toFixed(2)}</p>
                    <p class="text-xs text-green-600 mt-1">${data.summary.discrimination_level}</p>
                </div>
                <div class="bg-purple-50 rounded-lg p-4 text-center">
                    <p class="text-xs text-purple-600 font-bold uppercase">Reliabilitas</p>
                    <p class="text-2xl font-bold text-purple-700 mt-1">${(data.summary.reliability_kr20 || 0).toFixed(2)}</p>
                    <p class="text-xs text-purple-600 mt-1">${data.summary.reliability_label || '-'}</p>
                </div>
            </div>
        `;

        content.innerHTML = html;

    } catch (err) {
        console.error('Failed to load CTT analysis:', err);
        content.innerHTML = `
            <div class="text-center py-12 text-red-400">
                <p class="text-sm">Gagal memuat analisis</p>
            </div>
        `;
    }
}

// Load quiz list on page load
document.addEventListener('DOMContentLoaded', function() {
    loadCTTQuizList();
});

// Assignment Attachments Preview
async function openAssignmentPreview(assignmentId, assignmentName) {
    const modal = document.getElementById('assignment-preview-modal');
    const title = document.getElementById('assignment-preview-title');
    const content = document.getElementById('assignment-preview-content');

    title.textContent = assignmentName;
    modal.classList.remove('hidden');
    content.innerHTML = '<div class="text-center py-12"><div class="animate-spin rounded-full h-12 w-12 border-b-2 border-theme mx-auto"></div><p class="text-gray-500 mt-4">Memuat submissions...</p></div>';

    try {
        const res = await fetch(`/gradebook/api/assignments/${assignmentId}/submissions`);
        const data = await res.json();

        if (!data.success || data.submissions.length === 0) {
            content.innerHTML = '<div class="text-center py-12 text-gray-400"><p>Belum ada submissions</p></div>';
            return;
        }

        let html = '<div class="grid grid-cols-1 md:grid-cols-2 gap-4">';

        data.submissions.forEach(sub => {
            const hasAttachment = sub.file_path && sub.file_path.trim() !== '';
            const statusColor = sub.status === 'graded' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700';
            const statusLabel = sub.status === 'graded' ? 'Dinilai' : 'Disubmit';

            html += `
                <div class="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                    <div class="flex items-start justify-between mb-2">
                        <div>
                            <p class="font-bold text-gray-900">${sub.student_name}</p>
                            <p class="text-xs text-gray-500">${sub.submitted_at || '-'}</p>
                        </div>
                        <span class="px-2 py-1 rounded-full text-xs font-bold ${statusColor}">${statusLabel}</span>
                    </div>

                    ${sub.content ? `<p class="text-sm text-gray-700 mb-2 line-clamp-2">${sub.content}</p>` : ''}

                    ${hasAttachment ? `
                        <a href="/uploads/${sub.file_path}" target="_blank" class="inline-flex items-center gap-2 px-3 py-2 bg-indigo-50 text-indigo-700 rounded-lg text-sm font-semibold hover:bg-indigo-100 transition-colors">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                            </svg>
                            Lihat Lampiran
                        </a>
                    ` : '<p class="text-sm text-gray-400 italic">Tidak ada lampiran</p>'}
                </div>
            `;
        });

        html += '</div>';
        content.innerHTML = html;

    } catch (err) {
        console.error('Failed to load submissions:', err);
        content.innerHTML = '<div class="text-center py-12 text-red-400"><p>Gagal memuat submissions</p></div>';
    }
}

function closeAssignmentPreview() {
    document.getElementById('assignment-preview-modal').classList.add('hidden');
}
