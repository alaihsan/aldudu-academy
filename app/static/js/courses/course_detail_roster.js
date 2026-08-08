/**
 * Aldudu Academy - Course Detail: Student Roster Modal
 * Split out of course_detail.js — loaded after it on course_detail.html.
 */

async function openStudentRoster() {
    const modal = document.getElementById('student-roster-modal');
    const body = document.getElementById('roster-body');
    const countEl = document.getElementById('roster-count');
    if (!modal) return;
    modal.classList.remove('hidden');
    body.innerHTML = '<tr><td colspan="4" class="py-6 text-center text-[#afafaf] font-bold">Memuat…</td></tr>';
    countEl.textContent = 'Memuat…';
    try {
        const res = await fetch(`/api/courses/${window.courseId}/students`);
        const data = await res.json();
        if (!data.success) {
            body.innerHTML = `<tr><td colspan="4" class="py-6 text-center text-[#ff4b4b] font-bold">${data.message || 'Gagal memuat'}</td></tr>`;
            countEl.textContent = '';
            return;
        }
        const genderLabel = (g) => g === 'L' ? 'Laki-laki' : (g === 'P' ? 'Perempuan' : '-');
        countEl.textContent = `${data.students.length} siswa terdaftar`;
        if (data.students.length === 0) {
            body.innerHTML = '<tr><td colspan="4" class="py-6 text-center text-[#afafaf] font-bold">Belum ada siswa di kelas ini.</td></tr>';
            return;
        }
        body.innerHTML = data.students.map((s, i) => `
            <tr>
                <td class="py-3 pr-4 font-bold text-[#afafaf]">${i + 1}</td>
                <td class="py-3 pr-4 font-mono font-bold">${s.nis || '-'}</td>
                <td class="py-3 pr-4 font-black">${escapeHtmlRoster(s.name)}</td>
                <td class="py-3 font-bold text-[#afafaf]">${genderLabel(s.gender)}</td>
            </tr>`).join('');
    } catch (e) {
        body.innerHTML = '<tr><td colspan="4" class="py-6 text-center text-[#ff4b4b] font-bold">Terjadi kesalahan koneksi.</td></tr>';
        countEl.textContent = '';
    }
}

function closeStudentRoster() {
    document.getElementById('student-roster-modal')?.classList.add('hidden');
}

function escapeHtmlRoster(str) {
    const d = document.createElement('div');
    d.textContent = str == null ? '' : String(str);
    return d.innerHTML;
}
