// ===== Utility =====
function hexToRgb(hex) {
    const r = parseInt(hex.slice(1,3), 16);
    const g = parseInt(hex.slice(3,5), 16);
    const b = parseInt(hex.slice(5,7), 16);
    return `${r}, ${g}, ${b}`;
}

// Initialize theme RGB on load
(function() {
    const quizThemeColor = window.quizThemeColor || '#673ab7';
    document.documentElement.style.setProperty('--quiz-theme-rgb', hexToRgb(quizThemeColor));
})();

// ===== Publish Dropdown =====
function togglePublishDropdown() {
    document.getElementById('publish-dropdown').classList.toggle('show');
}

function syncQuizName(value, targetId) {
    if (targetId === 'main') {
        document.querySelector('.quiz-title-input').value = value;
    } else {
        document.getElementById('navbar-quiz-name-input').value = value;
    }
}

window.addEventListener('click', (e) => {
    if (!e.target.closest('#publish-main-btn')) {
        document.getElementById('publish-dropdown')?.classList.remove('show');
    }
});

async function setQuizStatus(newStatus) {
    const quizId = window.quizId;
    const res = await fetch(`/api/quiz/${quizId}/status`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus })
    });
    const data = await res.json();
    if (data.success) {
        const badge = document.getElementById('status-badge');
        let label = 'Draft';
        let classes = 'px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest ';

        if (newStatus === 'published') {
            label = 'Publikasikan';
            classes += 'bg-green-100 text-green-600';
        } else if (newStatus === 'unpublished') {
            label = 'Tidak Diterbitkan';
            classes += 'bg-red-100 text-red-600';
        } else {
            label = 'Draft';
            classes += 'bg-amber-100 text-amber-600';
        }

        badge.textContent = label;
        badge.className = classes;
        togglePublishDropdown();
        showSaveIndicator();
    }
}

// ===== Settings Handlers =====
async function updateDuration(value) {
    const quizId = window.quizId;
    const res = await fetch(`/api/quiz/${quizId}/update-duration`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ duration: parseInt(value || 0) })
    });
    if (res.ok) showSaveIndicator();
}

async function updateMaxAttempts(value) {
    const quizId = window.quizId;
    const res = await fetch(`/api/quiz/${quizId}/update-max-attempts`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ max_attempts: parseInt(value || 1) })
    });
    if (res.ok) showSaveIndicator();
}

async function updateSetting(field, value) {
    const quizId = window.quizId;
    const res = await fetch(`/api/quiz/${quizId}/update-settings`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ field, value })
    });
    if (res.ok) showSaveIndicator();
}

// ===== Theme Panel =====
function toggleThemePanel() {
    document.getElementById('theme-panel').classList.toggle('open');
}

async function updateQuizTheme() {
    const quizId = window.quizId;
    const activeBtn = document.querySelector('.bg-pattern-btn.active-pattern');
    const selectedPattern = activeBtn ? activeBtn.dataset.pattern : 'none';
    const data = {
        theme_color: document.getElementById('theme-color-input').value,
        font_question: document.getElementById('font-q-select').value,
        bg_pattern: selectedPattern,
        bg_opacity: parseInt(document.getElementById('bg-opacity-slider')?.value || 60)
    };
    document.documentElement.style.setProperty('--quiz-theme', data.theme_color);
    document.documentElement.style.setProperty('--quiz-theme-rgb', hexToRgb(data.theme_color));
    document.documentElement.style.setProperty('--font-q', `'${data.font_question}', sans-serif`);
    await fetch(`/api/quiz/${quizId}/update-theme`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    showSaveIndicator();
}

function selectBgPattern(pattern) {
    const overlay = document.getElementById('bg-pattern-overlay');
    // Remove all bg- classes then add new one
    overlay.className = 'bg-pattern-overlay' + (pattern !== 'none' ? ' bg-' + pattern : '');

    // Update active state
    document.querySelectorAll('.bg-pattern-btn').forEach(btn => {
        if (btn.dataset.pattern === pattern) {
            btn.classList.add('active-pattern', 'border-primary-500');
            btn.classList.remove('border-gray-100');
        } else {
            btn.classList.remove('active-pattern', 'border-primary-500');
            btn.classList.add('border-gray-100');
        }
    });

    // Show/hide opacity slider
    document.getElementById('opacity-slider-section').classList.toggle('hidden', pattern === 'none');

    updateQuizTheme();
}

function updateBgOpacity(value) {
    document.getElementById('bg-pattern-overlay').style.opacity = value / 100;
    document.getElementById('opacity-value').textContent = value + '%';
    clearTimeout(window._opacityTimer);
    window._opacityTimer = setTimeout(() => updateQuizTheme(), 500);
}

// ===== Description - Contenteditable + Rich Text Toolbar =====
function execCmd(command) {
    document.execCommand(command, false, null);
    updateToolbarState();
}

function updateToolbarState() {
    const toolbar = document.getElementById('rich-text-toolbar');
    if (!toolbar) return;
    const cmds = { 'bold': 0, 'italic': 1, 'underline': 2, 'insertOrderedList': 4, 'insertUnorderedList': 5 };
    const buttons = toolbar.querySelectorAll('button');
    Object.entries(cmds).forEach(([cmd, idx]) => {
        if (buttons[idx]) {
            const isActive = (cmd === 'insertOrderedList' || cmd === 'insertUnorderedList')
                ? document.queryCommandState(cmd)
                : document.queryCommandState(cmd);
            buttons[idx].classList.toggle('active', isActive);
        }
    });
}

function checkSelection(event) {
    setTimeout(() => {
        const sel = window.getSelection();
        const toolbar = document.getElementById('rich-text-toolbar');
        if (!sel || sel.isCollapsed || !sel.rangeCount) {
            toolbar.style.display = 'none';
            return;
        }

        const range = sel.getRangeAt(0);
        const container = range.commonAncestorContainer.nodeType === 3
            ? range.commonAncestorContainer.parentNode
            : range.commonAncestorContainer;

        const editable = container.closest('[contenteditable="true"]');
        if (!editable || (!editable.classList.contains('quiz-desc-input') && !editable.classList.contains('question-title-input'))) {
            toolbar.style.display = 'none';
            return;
        }

        const rect = range.getBoundingClientRect();
        toolbar.style.display = 'flex';
        toolbar.style.left = (rect.left + rect.width / 2) + 'px';
        toolbar.style.top = (rect.top - 48 + window.scrollY) + 'px';
        toolbar.style.position = 'absolute';
        updateToolbarState();
    }, 10);
}

document.addEventListener('mousedown', (e) => {
    const toolbar = document.getElementById('rich-text-toolbar');
    if (!toolbar) return;
    if (!e.target.closest('#rich-text-toolbar') && !e.target.closest('[contenteditable="true"]')) {
        toolbar.style.display = 'none';
    }
});

// HTMX extension to submit contenteditable content
htmx.defineExtension('editable-submit', {
    onEvent: function(name, evt) {
        if (name === 'htmx:configRequest') {
            const elt = evt.detail.elt;
            if (elt.getAttribute('contenteditable') === 'true') {
                const nameAttr = elt.getAttribute('name');
                if (nameAttr) {
                    evt.detail.parameters[nameAttr] = elt.innerHTML;
                }
            }
        }
    }
});

function saveDescription() {
    const quizId = window.quizId;
    const descEl = document.getElementById('quiz-description');
    const hiddenInput = document.getElementById('description-hidden');
    hiddenInput.value = descEl.innerHTML;

    const nameInput = document.querySelector('.quiz-title-input');
    const formData = new FormData();
    formData.append('name', nameInput.value);
    formData.append('description', descEl.innerHTML);

    fetch(`/api/quiz/${quizId}/update-meta`, {
        method: 'PUT',
        body: formData
    }).then(res => {
        if (res.ok) showSaveIndicator();
    });
}

// ===== Tab Switching =====
function switchMode(mode) {
    const qSection = document.getElementById('questions-section');
    const rSection = document.getElementById('results-section');
    const sSection = document.getElementById('settings-section');
    const qTab = document.getElementById('tab-questions');
    const rTab = document.getElementById('tab-results');
    const sTab = document.getElementById('tab-settings');
    const toolbar = document.getElementById('side-toolbar');

    if (mode !== 'questions' && toolbar) toolbar.style.display = 'none';

    if (mode === 'results') {
        qSection.classList.add('hidden'); rSection.classList.remove('hidden'); sSection.classList.add('hidden');
        qTab.classList.remove('active'); rTab.classList.add('active'); sTab.classList.remove('active');
        loadResults();
    } else if (mode === 'settings') {
        qSection.classList.add('hidden'); rSection.classList.add('hidden'); sSection.classList.remove('hidden');
        qTab.classList.remove('active'); rTab.classList.remove('active'); sTab.classList.add('active');
    } else {
        qSection.classList.remove('hidden'); rSection.classList.add('hidden'); sSection.classList.add('hidden');
        qTab.classList.add('active'); rTab.classList.remove('active'); sTab.classList.remove('active');
    }
}

// ===== Side Toolbar + Sortable =====
document.addEventListener('DOMContentLoaded', () => {
    const toolbar = document.getElementById('side-toolbar');
    const duplicateBtn = document.getElementById('duplicate-btn');
    const addQuestionBtn = document.querySelector('[hx-post*="/question/add"]');
    let activeQuestionId = null;
    let activeCard = null;

    // Fix: Handle HTMX completion for add question button
    if (addQuestionBtn) {
        addQuestionBtn.addEventListener('htmx:afterSwap', function(event) {
            // Scroll to new question
            const newQuestion = event.target.querySelector('[data-question-id]') || event.detail.target;
            if (newQuestion) {
                newQuestion.scrollIntoView({ behavior: 'smooth', block: 'center' });
                newQuestion.classList.add('animate-pulse');
                setTimeout(() => newQuestion.classList.remove('animate-pulse'), 2000);
            }
        });

        addQuestionBtn.addEventListener('htmx:beforeRequest', function() {
            // Show loading state
            this.disabled = true;
            this.classList.add('opacity-50');
        });

        addQuestionBtn.addEventListener('htmx:afterRequest', function() {
            // Re-enable button
            this.disabled = false;
            this.classList.remove('opacity-50');
        });
    }

    // Fix: Handle HTMX errors
    document.body.addEventListener('htmx:responseError', function(event) {
        console.error('HTMX Error:', event.detail);
        alert('Terjadi kesalahan saat menyimpan. Silakan coba lagi.');
    });

    function updateToolbar(card) {
        if (card && toolbar && !document.getElementById('questions-section').classList.contains('hidden')) {
            const isHeader = card.querySelector('.form-header-strip') !== null;
            activeCard = card;
            activeQuestionId = card.dataset.questionId;

            toolbar.style.display = 'flex';
            toolbar.style.top = card.offsetTop + 'px';

            if (isHeader) {
                duplicateBtn.style.display = 'none';
            } else {
                duplicateBtn.style.display = 'flex';
                duplicateBtn.setAttribute('hx-post', `/api/question/${activeQuestionId}/duplicate`);
                duplicateBtn.setAttribute('hx-target', `#question-${activeQuestionId}`);
                duplicateBtn.setAttribute('hx-swap', 'afterend');
                htmx.process(duplicateBtn);
            }
        }
    }

    document.body.addEventListener('click', (e) => {
        const card = e.target.closest('.form-card');
        if (card) updateToolbar(card);
    });

    const el = document.getElementById('questions-list');
    if (el) {
        Sortable.create(el, {
            animation: 150,
            handle: '.drag-handle',
            ghostClass: 'opacity-50',
            onEnd: async function() {
                const quizId = window.quizId;
                const order = Array.from(el.querySelectorAll('.form-card')).map((card, index) => ({
                    id: parseInt(card.dataset.questionId),
                    order: index + 1
                }));

                try {
                    const res = await fetch(`/api/quiz/${quizId}/questions/reorder`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ order })
                    });
                    if (res.ok) showSaveIndicator();
                } catch (e) { console.error('Failed to reorder', e); }
            }
        });
    }
});

// ===== Results Loading =====
async function loadResults() {
    const quizId = window.quizId;
    const res = await fetch(`/api/quiz/${quizId}/stats`);
    const data = await res.json();
    if (data.total_submissions > 0) {
        document.getElementById('no-responses-view').classList.add('hidden');
        document.getElementById('total-responses').textContent = data.total_submissions;
        document.getElementById('avg-score').textContent = `${data.average_score}%`;
        document.getElementById('max-score').textContent = `${data.max_score}%`;
        document.getElementById('min-score').textContent = `${data.min_score}%`;
        const breakdown = document.getElementById('question-breakdown');
        breakdown.innerHTML = '';
        data.questions_stats.forEach((stat, index) => {
            const card = document.createElement('div');
            card.className = 'form-card p-8';
            card.innerHTML = `<h3 class="font-bold text-gray-800 mb-6">${index + 1}. ${stat.question_text || 'Tanpa Judul'}</h3><div class="flex flex-col md:flex-row items-center gap-10"><div class="chart-container"><canvas id="chart-${index}"></canvas></div><div class="flex-1 space-y-3 w-full"><div class="flex items-center justify-between text-sm"><span class="text-green-600 font-bold">Benar</span><span class="font-black">${stat.correct}</span></div><div class="w-full bg-gray-100 h-2 rounded-full overflow-hidden"><div class="bg-green-500 h-full" style="width: ${(stat.correct/stat.total)*100}%"></div></div><div class="flex items-center justify-between text-sm"><span class="text-red-600 font-bold">Salah</span><span class="font-black">${stat.incorrect}</span></div><div class="w-full bg-gray-100 h-2 rounded-full overflow-hidden"><div class="bg-red-500 h-full" style="width: ${(stat.incorrect/stat.total)*100}%"></div></div></div></div>`;
            breakdown.appendChild(card);
            new Chart(document.getElementById(`chart-${index}`), {
                type: 'pie',
                data: { labels: ['Benar', 'Salah'], datasets: [{ data: [stat.correct, stat.incorrect], backgroundColor: ['#10b981', '#ef4444'], borderWidth: 0 }] },
                options: { plugins: { legend: { position: 'bottom' } } }
            });
        });
        const studentRows = document.getElementById('student-rows');
        document.getElementById('student-results-list').classList.remove('hidden');
        studentRows.innerHTML = data.submissions.map(s => `
            <div class="flex items-center justify-between p-4 px-6 hover:bg-gray-50 transition-colors">
                <div class="flex items-center space-x-4">
                    <div class="w-10 h-10 rounded-full bg-primary-50 text-primary-600 flex items-center justify-center font-black">
                        ${s.student_name.charAt(0).toUpperCase()}
                    </div>
                    <div>
                        <p class="font-bold text-gray-800">${s.student_name}</p>
                        <p class="text-[10px] text-gray-400 uppercase tracking-widest">${s.submitted_at}</p>
                    </div>
                </div>
                <div class="flex items-center space-x-6">
                    <span class="font-black text-primary-600 text-lg">${s.score}%</span>
                    <a href="/api/submission/${s.id}" target="_blank" class="p-2 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded-xl transition-all" title="Lihat Detail Jawaban">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>
                    </a>
                </div>
            </div>
        `).join('');
    }
}
