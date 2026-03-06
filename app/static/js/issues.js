/**
 * Aldudu Academy - Issue Management Script
 */

const Issues = {
    currentFilter: 'all',
    currentUser: null,

    async init() {
        this.cacheDOM();
        await this.fetchSession();
        this.bindEvents();
        this.loadIssues();
    },

    cacheDOM() {
        this.container = document.getElementById('issues-container');
        this.createModal = document.getElementById('create-issue-modal');
        this.createForm = document.getElementById('create-issue-form');
        this.openModalBtn = document.getElementById('open-create-issue-modal');
        this.closeModalBtn = document.getElementById('close-issue-modal');
        this.filterBtns = document.querySelectorAll('.issue-filter-btn');
        this.errorMsg = document.getElementById('issue-modal-error');
    },

    async fetchSession() {
        try {
            const res = await fetch('/api/session');
            const data = await res.json();
            if (data.isAuthenticated) {
                this.currentUser = data.user;
            }
        } catch (err) {
            console.error('Failed to fetch session', err);
        }
    },

    bindEvents() {
        if (this.openModalBtn) {
            this.openModalBtn.addEventListener('click', () => this.toggleModal(true));
        }
        if (this.closeModalBtn) {
            this.closeModalBtn.addEventListener('click', () => this.toggleModal(false));
        }
        if (this.createForm) {
            this.createForm.addEventListener('submit', (e) => this.handleSubmit(e));
        }
        this.filterBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.filterBtns.forEach(b => b.classList.remove('active', 'bg-primary-600', 'text-white'));
                this.filterBtns.forEach(b => b.classList.add('text-gray-500'));
                
                btn.classList.add('active', 'bg-primary-600', 'text-white');
                btn.classList.remove('text-gray-500');
                
                this.currentFilter = btn.dataset.filter;
                this.loadIssues();
            });
        });
    },

    toggleModal(show) {
        if (show) {
            this.createModal.classList.remove('hidden');
            this.errorMsg.classList.add('hidden');
        } else {
            this.createModal.classList.add('hidden');
            this.createForm.reset();
        }
    },

    async loadIssues() {
        this.container.innerHTML = `
            <div class="space-y-4">
                <div class="bg-white rounded-3xl h-24 animate-pulse border border-gray-100"></div>
                <div class="bg-white rounded-3xl h-24 animate-pulse border border-gray-100"></div>
            </div>
        `;

        try {
            const url = `/api/issues?status=${this.currentFilter}`;
            const res = await fetch(url);
            const data = await res.json();

            if (data.success) {
                this.renderIssues(data.issues);
            }
        } catch (err) {
            console.error('Failed to load issues', err);
            this.container.innerHTML = '<p class="text-center text-red-500 font-bold p-8">Gagal memuat data laporan.</p>';
        }
    },

    renderIssues(issues) {
        if (issues.length === 0) {
            this.container.innerHTML = `
                <div class="bg-white rounded-[2.5rem] p-16 text-center border-2 border-dashed border-gray-200">
                    <div class="w-20 h-20 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-6">
                        <svg class="w-10 h-10 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                        </svg>
                    </div>
                    <h3 class="text-xl font-bold text-gray-900 mb-2">Tidak ada laporan</h3>
                    <p class="text-gray-500">Semua sistem berjalan dengan normal atau filter tidak menemukan hasil.</p>
                </div>
            `;
            return;
        }

        this.container.innerHTML = issues.map(issue => this.createIssueCard(issue)).join('');
    },

    createIssueCard(issue) {
        const statusColors = {
            'Open': 'bg-amber-100 text-amber-700',
            'In Progress': 'bg-blue-100 text-blue-700',
            'Resolved': 'bg-green-100 text-green-700',
            'Closed': 'bg-gray-100 text-gray-700'
        };

        const priorityColors = {
            'Low': 'text-gray-400',
            'Medium': 'text-blue-500',
            'High': 'text-orange-500',
            'Urgent': 'text-red-600'
        };

        const isOwner = this.currentUser && this.currentUser.id === issue.user_id;
        const isPrivileged = this.currentUser && (this.currentUser.role === 'guru' || this.currentUser.role === 'admin');
        const isAdmin = this.currentUser && this.currentUser.role === 'admin';

        return `
            <div class="group bg-white rounded-3xl p-6 border border-gray-100 shadow-sm hover:shadow-md transition-all border-l-4 ${issue.priority === 'Urgent' ? 'border-l-red-500' : 'border-l-indigo-500'}">
                <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div class="flex-1">
                        <div class="flex items-center space-x-3 mb-2">
                            <span class="px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest ${statusColors[issue.status] || 'bg-gray-100 text-gray-600'}">
                                ${issue.status}
                            </span>
                            <span class="text-[10px] font-black uppercase tracking-widest ${priorityColors[issue.priority]}">
                                ${issue.priority} Priority
                            </span>
                            ${!isOwner ? `<span class="text-[10px] font-bold text-gray-400 italic">Oleh: ${issue.user_name}</span>` : ''}
                        </div>
                        <h3 class="text-lg font-bold text-gray-900 mb-1">${issue.title}</h3>
                        <p class="text-sm text-gray-500 line-clamp-2">${issue.description}</p>
                    </div>
                    <div class="flex items-center space-x-4 text-right">
                        <div class="hidden md:block text-right">
                            <p class="text-[10px] font-black text-gray-400 uppercase tracking-widest">Dilaporkan Pada</p>
                            <p class="text-xs font-bold text-gray-700">${issue.created_at}</p>
                        </div>
                        <div class="flex items-center space-x-1">
                            ${(isPrivileged && issue.status !== 'Resolved') ? `
                                <button onclick="Issues.resolveIssue(${issue.id})" class="p-2 text-gray-300 hover:text-green-600 transition-colors" title="Tandai Selesai">
                                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                                    </svg>
                                </button>
                            ` : ''}
                            ${(isOwner || isAdmin) ? `
                                <button onclick="Issues.deleteIssue(${issue.id})" class="p-2 text-gray-300 hover:text-red-600 transition-colors" title="Hapus Laporan">
                                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                                    </svg>
                                </button>
                            ` : ''}
                        </div>
                    </div>
                </div>
            </div>
        `;
    },

    async resolveIssue(id) {
        try {
            const res = await fetch(`/api/issues/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status: 'RESOLVED' })
            });
            const data = await res.json();
            if (data.success) {
                this.loadIssues();
            }
        } catch (err) {
            Swal.fire('Gagal!', 'Gagal memperbarui status laporan.', 'error');
        }
    },

    async handleSubmit(e) {
        e.preventDefault();
        
        const submitBtn = this.createForm.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerText;
        
        submitBtn.disabled = true;
        submitBtn.innerText = 'Mengirim...';
        this.errorMsg.classList.add('hidden');

        const payload = {
            title: document.getElementById('issue-title').value,
            priority: document.getElementById('issue-priority').value,
            description: document.getElementById('issue-description').value
        };

        try {
            const res = await fetch('/api/issues', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();

            if (data.success) {
                this.toggleModal(false);
                this.loadIssues();
                Swal.fire({
                    title: 'Berhasil!',
                    text: 'Laporan Anda telah terkirim.',
                    icon: 'success',
                    timer: 2000,
                    showConfirmButton: false,
                    customClass: { popup: 'rounded-[2.5rem]', title: 'font-black' }
                });
            } else {
                this.errorMsg.innerText = data.message;
                this.errorMsg.classList.remove('hidden');
            }
        } catch (err) {
            this.errorMsg.innerText = 'Terjadi kesalahan koneksi.';
            this.errorMsg.classList.remove('hidden');
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerText = originalText;
        }
    },

    async deleteIssue(id) {
        Swal.fire({
            title: 'Hapus Laporan?',
            text: 'Laporan yang dihapus tidak dapat dikembalikan. Lanjutkan?',
            icon: 'warning',
            showCancelButton: true,
            confirmButtonText: 'Ya, Hapus',
            cancelButtonText: 'Batal',
            confirmButtonColor: '#ef4444',
            cancelButtonColor: '#6b7280',
            reverseButtons: true,
            background: '#ffffff',
            customClass: {
                title: 'font-black text-gray-800',
                popup: 'rounded-[2.5rem] p-8',
                confirmButton: 'rounded-2xl px-6 py-3 font-bold',
                cancelButton: 'rounded-2xl px-6 py-3 font-bold'
            }
        }).then(async (result) => {
            if (result.isConfirmed) {
                try {
                    const res = await fetch(`/api/issues/${id}`, { method: 'DELETE' });
                    const data = await res.json();
                    if (data.success) {
                        this.loadIssues();
                        Swal.fire({
                            title: 'Terhapus!',
                            text: 'Laporan berhasil dihapus.',
                            icon: 'success',
                            timer: 1500,
                            showConfirmButton: false,
                            customClass: {
                                popup: 'rounded-[2.5rem]',
                                title: 'font-black'
                            }
                        });
                    }
                } catch (err) {
                    Swal.fire('Gagal!', 'Gagal menghapus laporan.', 'error');
                }
            }
        });
    }
};

document.addEventListener('DOMContentLoaded', () => Issues.init());
// Re-init for HTMX if needed
document.body.addEventListener('htmx:afterSwap', () => Issues.init());
