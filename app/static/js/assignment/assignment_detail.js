function openGradeModal(submissionId, studentName, content, filePath) {
    document.getElementById('grade-submission-id').value = submissionId;
    document.getElementById('grade-student-name').textContent = studentName;
    document.getElementById('grade-content').textContent = content || '(Tidak ada keterangan teks)';

    const fileLinkDiv = document.getElementById('grade-file-link');
    if (filePath && filePath !== 'None') {
        fileLinkDiv.innerHTML = `<a href="/assignment/{{ assignment.id }}/download/${submissionId}" class="inline-flex items-center space-x-2 text-theme hover:underline font-bold text-sm"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/></svg><span>Unduh File Lampiran</span></a>`;
    } else {
        fileLinkDiv.innerHTML = '';
    }

    document.getElementById('grade-modal').classList.remove('hidden');
}

function closeGradeModal() {
    document.getElementById('grade-modal').classList.add('hidden');
}

document.getElementById('grade-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    const submissionId = document.getElementById('grade-submission-id').value;
    const score = document.getElementById('grade-score').value;
    const feedback = document.getElementById('grade-feedback').value;

    try {
        const formData = new FormData();
        formData.append('score', score);
        formData.append('feedback', feedback);

        const res = await fetch(`/assignment/{{ assignment.id }}/grade/${submissionId}`, {
            method: 'POST',
            body: formData
        });
        const data = await res.json();

        if (data.success) {
            window.location.reload();
        } else {
            alert(data.message || 'Gagal menyimpan nilai');
        }
    } catch (err) {
        console.error(err);
        alert('Kesalahan koneksi');
    }
});
