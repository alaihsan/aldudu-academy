/**
 * Aldudu Academy - Admin Management Script
 */

var Admin = {
    init() {
        this.cacheDOM();
        this.bindEvents();
    },

    cacheDOM() {
        this.importForm = document.getElementById('bulk-import-form');
        this.classForm = document.getElementById('create-class-form');
        this.resetForm = document.getElementById('reset-password-form');
        this.importControls = document.getElementById('import-controls');
        this.importResults = document.getElementById('import-results');
        this.resultsBody = document.getElementById('results-body');
        this.importFooter = document.getElementById('import-footer');
    },

    bindEvents() {
        if (this.importForm) {
            this.importForm.addEventListener('submit', (e) => this.handleBulkImport(e));
        }
        if (this.classForm) {
            this.classForm.addEventListener('submit', (e) => this.handleCreateClass(e));
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

        if (!rawData.trim()) {
            errorDiv.innerText = 'Data siswa masih kosong.';
            errorDiv.classList.remove('hidden');
            return;
        }

        submitBtn.disabled = true;
        submitBtn.innerText = 'Memproses...';
        errorDiv.classList.add('hidden');

        const targetClass = document.getElementById('import-target-class');
        const payload = { raw_data: rawData };
        if (targetClass && targetClass.value) payload.course_id = parseInt(targetClass.value, 10);

        try {
            const res = await fetch('/admin/api/students/bulk-import', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();

            if (data.success) {
                const classesNote = data.created_classes.length
                    ? ` · ${data.created_classes.length} kelas baru` : '';
                document.getElementById('import-summary').innerText =
                    `${data.created_students} siswa baru · ${data.enrolled} didaftarkan${classesNote} · password: ${data.default_password}`;

                this.resultsBody.innerHTML = data.results.map(u => `
                    <tr class="border-b border-gray-800">
                        <td class="py-2 pr-4">${u.nis}</td>
                        <td class="py-2 pr-4 text-white">${u.name}</td>
                        <td class="py-2 pr-4">${u.kelas}</td>
                        <td class="py-2 font-bold">${u.status}</td>
                    </tr>
                `).join('');

                this.importControls.classList.add('hidden');
                this.importFooter.classList.add('hidden');
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

    async handleCreateClass(e) {
        e.preventDefault();
        const submitBtn = e.target.querySelector('button[type="submit"]');
        const errorDiv = document.getElementById('create-class-error');
        const name = document.getElementById('class-name-input').value.trim();

        if (name.length < 2) {
            errorDiv.innerText = 'Nama kelas minimal 2 karakter.';
            errorDiv.classList.remove('hidden');
            return;
        }

        submitBtn.disabled = true;
        submitBtn.innerText = 'Menyimpan...';
        errorDiv.classList.add('hidden');

        try {
            const res = await fetch('/admin/api/classes', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name })
            });
            const data = await res.json();

            if (data.success) {
                window.location.reload();
            } else {
                errorDiv.innerText = data.message;
                errorDiv.classList.remove('hidden');
                submitBtn.disabled = false;
                submitBtn.innerText = 'Simpan Kelas';
            }
        } catch (err) {
            errorDiv.innerText = 'Gagal membuat kelas.';
            errorDiv.classList.remove('hidden');
            submitBtn.disabled = false;
            submitBtn.innerText = 'Simpan Kelas';
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
    },

    async handleRename(userId, currentName) {
        const { value: newName } = await Swal.fire({
            title: 'Ubah Nama',
            input: 'text',
            inputLabel: 'Nama baru',
            inputValue: currentName,
            inputAttributes: { maxlength: 100 },
            showCancelButton: true,
            confirmButtonText: 'Simpan',
            cancelButtonText: 'Batal',
            confirmButtonColor: '#4f46e5',
            inputValidator: (v) => (!v || v.trim().length < 2) ? 'Nama minimal 2 karakter' : null,
        });
        if (!newName || newName.trim() === currentName) return;

        try {
            const res = await fetch(`/admin/api/users/${userId}/rename`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: newName.trim() }),
            });
            const data = await res.json();
            if (data.success) {
                const nameEl = document.getElementById(`user-name-${userId}`);
                if (nameEl) nameEl.textContent = data.name;
                Swal.fire({ icon: 'success', title: 'Nama diperbarui', timer: 1500, showConfirmButton: false });
            } else {
                Swal.fire({ icon: 'error', title: 'Gagal', text: data.message });
            }
        } catch (err) {
            Swal.fire({ icon: 'error', title: 'Error', text: 'Gagal menghubungi server.' });
        }
    },
};

// init-on-ready: jalan saat full load DAN saat skrip re-eksekusi setelah swap htmx
if (document.readyState !== 'loading') Admin.init();
else document.addEventListener('DOMContentLoaded', () => Admin.init());
window.Admin = Admin;
