// Super Admin core functionality (base.html)
// Includes: sidebar toggle, logout, test email, global confirm helper

// Sidebar toggle (mobile)
function toggleSidebar() {
  const sidebar = document.getElementById('sa-sidebar');
  const overlay = document.getElementById('sa-overlay');
  sidebar.classList.toggle('open');
  overlay.classList.toggle('hidden');
}

// Logout
async function handleSALogout() {
  const result = await Swal.fire({
    title: 'Logout?',
    text: 'Sesi kamu akan berakhir.',
    icon: 'question',
    showCancelButton: true,
    confirmButtonText: 'Ya, Logout',
    cancelButtonText: 'Batal',
    confirmButtonColor: '#ef4444',
    reverseButtons: true,
  });
  if (result.isConfirmed) {
    await fetch('/api/logout', { method: 'POST' });
    window.location.href = '/login';
  }
}

// Test email
async function testEmail() {
  const { value: email } = await Swal.fire({
    title: 'Test Kirim Email',
    input: 'email',
    inputLabel: 'Alamat email tujuan',
    inputPlaceholder: 'contoh@email.com',
    inputValue: window.saCurrentUserEmail || '',
    showCancelButton: true,
    confirmButtonText: 'Kirim',
    cancelButtonText: 'Batal',
    confirmButtonColor: '#4f46e5',
  });
  if (!email) return;

  const btn = Swal.showLoading();
  const res = await fetch('/superadmin/api/test-email', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email }),
  });
  const data = await res.json();
  if (data.success) {
    Swal.fire({ icon: 'success', title: 'Terkirim!', text: data.message, confirmButtonColor: '#4f46e5' });
  } else {
    Swal.fire({ icon: 'error', title: 'Gagal', text: data.message });
  }
}

// Global confirm helper
window.ask = (title, text, icon = 'question') => Swal.fire({
  title, text, icon,
  showCancelButton: true,
  confirmButtonText: 'Ya',
  cancelButtonText: 'Batal',
  confirmButtonColor: '#4f46e5',
  reverseButtons: true,
}).then(r => r.isConfirmed);
