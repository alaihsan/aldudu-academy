/**
 * Aldudu Academy - Course Detail: Edit Class Modal (name + color picker)
 * Split out of course_detail.js — loaded after it on course_detail.html.
 */

function openEditClass() {
    const modal = document.getElementById('color-picker-modal');
    if (!modal) return;
    const nameInput = document.getElementById('edit-class-name');
    if (nameInput) nameInput.value = window.courseName || '';
    window._selectedColor = window.courseColor || '#1cb0f6';
    _markSelectedColor(window._selectedColor);
    const err = document.getElementById('edit-class-error');
    if (err) err.classList.add('hidden');
    modal.classList.remove('hidden');
    if (nameInput) nameInput.focus();
}

// Alias kompat (pemanggil lama)
function openColorPicker() { openEditClass(); }

function closeColorPicker() {
    document.getElementById('color-picker-modal').classList.add('hidden');
}

function _markSelectedColor(color) {
    document.querySelectorAll('#color-picker-modal .color-swatch').forEach((b) => {
        const on = (b.dataset.color || '').toLowerCase() === (color || '').toLowerCase();
        b.style.outline = on ? '3px solid #4b4b4b' : '';
        b.style.outlineOffset = on ? '2px' : '';
    });
}

function selectColor(color) {
    window._selectedColor = color;
    _markSelectedColor(color);
}

function saveClassEdit() {
    const courseId = window.courseId;
    const nameInput = document.getElementById('edit-class-name');
    const err = document.getElementById('edit-class-error');
    const name = (nameInput ? nameInput.value : '').trim();
    const color = window._selectedColor || window.courseColor || '#1cb0f6';
    if (err) err.classList.add('hidden');
    if (name.length < 2) {
        if (err) { err.textContent = 'Nama kelas minimal 2 karakter'; err.classList.remove('hidden'); }
        return;
    }
    fetch(`/api/courses/${courseId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name, color: color })
    })
    .then((res) => res.json())
    .then((data) => {
        if (data.success) {
            window.location.reload();   // muat ulang agar hero, judul, dan warna ter-update
        } else if (err) {
            err.textContent = data.message || 'Gagal menyimpan perubahan';
            err.classList.remove('hidden');
        }
    })
    .catch(() => {
        if (err) { err.textContent = 'Terjadi kesalahan koneksi'; err.classList.remove('hidden'); }
    });
}
