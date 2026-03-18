/**
 * Aldudu Academy - Admin Management Script
 * Note: Modal handling now uses Alpine.js (see admin_users.html)
 */

const Admin = {
    init() {
        this.bindEvents();
    },

    bindEvents() {
        // Form handlers removed - now handled by Alpine.js
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

document.addEventListener('DOMContentLoaded', () => Admin.init());
