/**
 * Aldudu Academy - Admin Management Script
 */

const Admin = {
    init() {
        this.cacheDOM();
        this.bindEvents();
    },

    cacheDOM() {
        this.importForm = document.getElementById('bulk-import-form');
        this.resetForm = document.getElementById('reset-password-form');
        this.importResults = document.getElementById('import-results');
        this.resultsBody = document.getElementById('results-body');
        this.importFooter = document.getElementById('import-footer');
    },

    bindEvents() {
        if (this.importForm) {
            this.importForm.addEventListener('submit', (e) => this.handleBulkImport(e));
        }
        if (this.resetForm) {
            this.resetForm.addEventListener('submit', (e) => this.handleResetPassword(e));
        }
    },

    async handleBulkImport(e) {
        e.preventDefault();
        const submitBtn = e.target.querySelector('button[type="submit"]');
        const errorDiv = document.getElementById('import-error');
        const rawData = document.getElementById('raw-data').value;
        const role = document.getElementById('import-role').value;

        if (!rawData.trim()) return;

        submitBtn.disabled = true;
        submitBtn.innerText = 'Memproses...';
        errorDiv.classList.add('hidden');

        try {
            const res = await fetch('/admin/api/users/bulk-import', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ raw_data: rawData, role: role })
            });
            const data = await res.json();

            if (data.success) {
                // Tampilkan hasil password
                this.importForm.querySelector('textarea').classList.add('hidden');
                this.importForm.querySelector('select').parentElement.classList.add('hidden');
                this.importFooter.classList.add('hidden');
                
                this.resultsBody.innerHTML = data.results.map(u => `
                    <tr class="border-b border-gray-800">
                        <td class="py-2 pr-4">${u.name}</td>
                        <td class="py-2 pr-4">${u.email}</td>
                        <td class="py-2 text-white font-bold">${u.password}</td>
                    </tr>
                `).join('');
                
                this.importResults.classList.remove('hidden');
            } else {
                errorDiv.innerText = data.message;
                errorDiv.classList.remove('hidden');
                submitBtn.disabled = false;
                submitBtn.innerText = 'Proses Impor';
            }
        } catch (err) {
            errorDiv.innerText = 'Terjadi kesalahan koneksi.';
            errorDiv.classList.remove('hidden');
            submitBtn.disabled = false;
            submitBtn.innerText = 'Proses Impor';
        }
    },

    async handleResetPassword(e) {
        e.preventDefault();
        const userId = document.getElementById('reset-user-id').value;
        const password = document.getElementById('new-password').value;
        const errorDiv = document.getElementById('reset-error');
        const submitBtn = e.target.querySelector('button[type="submit"]');

        if (password.length < 6) {
            errorDiv.innerText = 'Password minimal 6 digit';
            errorDiv.classList.remove('hidden');
            return;
        }

        submitBtn.disabled = true;
        submitBtn.innerText = 'Menyimpan...';

        try {
            const res = await fetch(`/admin/api/users/${userId}/reset-password`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ password: password })
            });
            const data = await res.json();

            if (data.success) {
                window.location.reload();
            } else {
                errorDiv.innerText = data.message;
                errorDiv.classList.remove('hidden');
                submitBtn.disabled = false;
                submitBtn.innerText = 'Simpan Password';
            }
        } catch (err) {
            errorDiv.innerText = 'Gagal mereset password.';
            errorDiv.classList.remove('hidden');
            submitBtn.disabled = false;
            submitBtn.innerText = 'Simpan Password';
        }
    },

    async toggleStatus(userId) {
        try {
            const res = await fetch(`/admin/api/users/${userId}/toggle-status`, {
                method: 'POST'
            });
            const data = await res.json();
            if (data.success) {
                window.location.reload();
            } else {
                alert(data.message);
            }
        } catch (err) {
            alert('Gagal memperbarui status user.');
        }
    }
};

document.addEventListener('DOMContentLoaded', () => Admin.init());
