// Quiz submission detail - edit score functionality (quiz_submission_detail.html)

async function editScore() {
  const { value: newScore } = await Swal.fire({
    title: 'Ubah Nilai Murid',
    input: 'number',
    inputLabel: 'Masukkan skor baru (0-100)',
    inputValue: window.submissionScore || 0,
    showCancelButton: true,
    inputAttributes: { min: 0, max: 100, step: 0.1 },
    confirmButtonText: 'Simpan',
    cancelButtonText: 'Batal'
  });

  if (newScore !== undefined && newScore !== null && newScore !== "") {
    try {
      const res = await fetch(`/api/submission/${window.submissionId}/update-score`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ score: parseFloat(newScore) })
      });
      const data = await res.json();
      if (data.success) {
        document.getElementById('submission-score').textContent = parseFloat(newScore).toFixed(1) + '%';
        Swal.fire('Berhasil!', 'Nilai telah diperbarui.', 'success');
      } else {
        Swal.fire('Gagal!', data.message, 'error');
      }
    } catch (err) {
      Swal.fire('Error', 'Gagal menghubungi server', 'error');
    }
  }
}
