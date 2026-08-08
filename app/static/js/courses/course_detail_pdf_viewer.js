/**
 * Aldudu Academy - Course Detail: PDF Viewer (gaya WhatsApp Desktop)
 * Split out of course_detail.js — loaded after it on course_detail.html.
 */

function openPdfViewer(fileId, name) {
    const modal = document.getElementById('pdf-viewer-modal');
    if (!modal) { window.open(`/files/${fileId}`, '_blank'); return; }
    document.getElementById('pdf-viewer-title').textContent = name || 'Dokumen';
    document.getElementById('pdf-viewer-download').setAttribute('href', `/files/${fileId}`);
    document.getElementById('pdf-viewer-frame').setAttribute('src', `/files/${fileId}#view=FitH`);
    modal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
}

function closePdfViewer() {
    const modal = document.getElementById('pdf-viewer-modal');
    if (!modal) return;
    modal.classList.add('hidden');
    document.getElementById('pdf-viewer-frame').setAttribute('src', '');
    document.body.style.overflow = '';
}

// Tutup viewer/roster dengan tombol Escape (closeStudentRoster is defined in
// course_detail_roster.js, loaded alongside this file — same global scope)
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closePdfViewer();
        closeStudentRoster();
    }
});
