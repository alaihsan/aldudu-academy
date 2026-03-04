/**
 * Aldudu Academy - Course Detail JavaScript
 * Modern interactions for an elegant learning experience
 */

document.addEventListener('DOMContentLoaded', function() {
    CourseDetail.init();
});

const CourseDetail = {
    init() {
        this.cacheElements();
        this.bindEvents();
        this.loadDiscussions(); // Load discussions initial
        console.log('Course Detail Initialized');
    },

    cacheElements() {
        this.courseId = document.querySelector('main')?.dataset.courseId;
        this.addTopicsBtn = document.getElementById('add-topics-button');
        this.addTopicsMenu = document.getElementById('topics-dropdown-menu');
        this.topicsContainer = document.getElementById('topics-container');
        this.discussionsContainer = document.getElementById('discussions-container');
        this.tabBtns = document.querySelectorAll('.tab-btn');
        
        // Modals
        this.modals = {
            quiz: { el: document.getElementById('create-quiz-modal'), showBtn: document.getElementById('show-create-quiz-modal'), form: document.getElementById('create-quiz-form'), cancelBtn: document.querySelector('.quiz-cancel-btn') },
            file: { el: document.getElementById('create-file-modal'), showBtn: document.getElementById('show-create-file-modal'), form: document.getElementById('create-file-form'), cancelBtn: document.querySelector('.file-cancel-btn') },
            link: { el: document.getElementById('create-link-modal'), showBtn: document.getElementById('show-create-link-modal'), form: document.getElementById('create-link-form'), cancelBtn: document.querySelector('.link-cancel-btn') },
            discussion: { el: document.getElementById('create-discussion-modal'), showBtn: document.getElementById('show-create-discussion-modal'), form: document.getElementById('create-discussion-form'), cancelBtn: document.querySelector('.discussion-cancel-btn') }
        };
    },

    bindEvents() {
        // Dropdown Toggle
        this.addTopicsBtn?.addEventListener('click', (e) => {
            e.stopPropagation();
            this.addTopicsMenu.classList.toggle('hidden');
        });

        window.addEventListener('click', () => this.addTopicsMenu?.classList.add('hidden'));

        // Tab Switching Logic
        this.tabBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const tab = btn.dataset.tab;
                this.switchTab(btn, tab);
            });
        });

        // Initialize all modals
        Object.keys(this.modals).forEach(key => {
            const modal = this.modals[key];
            modal.showBtn?.addEventListener('click', (e) => {
                e.preventDefault();
                this.closeAllModals();
                modal.el.classList.remove('hidden');
                this.addTopicsMenu?.classList.add('hidden');
            });
            modal.cancelBtn?.addEventListener('click', () => modal.el.classList.add('hidden'));
            if (modal.form) modal.form.addEventListener('submit', (e) => this.handleFormSubmit(e, key));
        });
    },

    switchTab(activeBtn, tabType) {
        // Update UI Tabs
        this.tabBtns.forEach(b => {
            b.classList.remove('active', 'bg-primary-600', 'text-white', 'shadow-lg', 'shadow-primary-100');
            b.classList.add('text-gray-500', 'hover:bg-gray-50');
        });
        activeBtn.classList.add('active', 'bg-primary-600', 'text-white', 'shadow-lg', 'shadow-primary-100');
        activeBtn.classList.remove('text-gray-500', 'hover:bg-gray-50');

        // Filter Topics
        const topicCards = this.topicsContainer.querySelectorAll('.group');
        
        if (tabType === 'Diskusi') {
            this.topicsContainer.classList.add('hidden');
            this.discussionsContainer.classList.remove('hidden');
            // Ensure Discussions header is visible if needed
            document.getElementById('diskusi')?.scrollIntoView({ behavior: 'smooth' });
        } else {
            this.topicsContainer.classList.remove('hidden');
            this.discussionsContainer.classList.add('hidden');
            
            topicCards.forEach(card => {
                const typeText = card.querySelector('p.text-gray-500')?.textContent || '';
                if (tabType === 'all' || typeText.includes(tabType)) {
                    card.classList.remove('hidden');
                } else {
                    card.classList.add('hidden');
                }
            });
        }
    },

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

        this.discussionsContainer.innerHTML = discussions.map(d => `
            <div class="group bg-white rounded-[2rem] border border-gray-100 shadow-premium hover:shadow-xl transition-all duration-500 p-8 flex flex-col h-full transform hover:-translate-y-2">
                <div class="flex items-center space-x-3 mb-6">
                    <div class="w-10 h-10 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center font-bold">
                        ${d.user.name[0].toUpperCase()}
                    </div>
                    <div>
                        <p class="text-xs font-black text-gray-400 uppercase tracking-widest leading-none mb-1">${d.user.name}</p>
                        <p class="text-[10px] text-gray-400">${new Date(d.created_at).toLocaleDateString()}</p>
                    </div>
                </div>
                <h3 class="text-lg font-bold text-gray-900 group-hover:text-primary-600 transition-colors mb-4 line-clamp-2">${d.title}</h3>
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
        `).join('');
    },

    closeAllModals() {
        Object.values(this.modals).forEach(m => m.el?.classList.add('hidden'));
    },

    async handleFormSubmit(e, type) {
        e.preventDefault();
        const form = e.target;
        const errorEl = form.querySelector('[id$="-error"]');
        
        let url = `/api/courses/${this.courseId}/`;
        let options = { method: 'POST' };

        if (type === 'quiz') {
            url += 'quizzes';
            options.headers = { 'Content-Type': 'application/json' };
            options.body = JSON.stringify({
                name: document.getElementById('quiz-name-input').value,
                points: document.getElementById('quiz-points').value,
                grade_type: document.getElementById('quiz-grade-type').value
            });
        } else if (type === 'file') {
            url += 'files';
            const formData = new FormData();
            formData.append('name', document.getElementById('file-name-input').value);
            formData.append('file', document.getElementById('file-upload-input').files[0]);
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
                if (type === 'quiz') window.location.href = `/quiz/${data.quiz.id}`;
                else window.location.reload();
            } else {
                errorEl.textContent = data.message || 'Terjadi kesalahan';
                errorEl.classList.remove('hidden');
            }
        } catch (err) {
            console.error('Submit failed', err);
            if (errorEl) { errorEl.textContent = 'Kesalahan koneksi ke server'; errorEl.classList.remove('hidden'); }
        }
    }
};
