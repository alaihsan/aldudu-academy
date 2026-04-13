// Forgot password functionality (forgot_password.html)

document.addEventListener('DOMContentLoaded', function() {
  const forgotForm = document.getElementById('forgot-form');
  if (!forgotForm) return;

  forgotForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('forgot-btn');
    const btnText = document.getElementById('forgot-btn-text');
    const msgEl = document.getElementById('forgot-msg');
    const msgText = document.getElementById('forgot-msg-text');
    const msgIcon = document.getElementById('forgot-msg-icon');

    btn.disabled = true;
    btnText.textContent = 'Mengirim...';
    btn.classList.add('opacity-75');
    msgEl.classList.add('hidden');

    try {
      await fetch('/api/forgot-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: document.getElementById('forgot-email').value.trim() })
      });
      // Always show success - don't reveal if email exists (security)
      msgEl.className = 'rounded-2xl px-4 py-3.5 text-sm font-semibold flex items-start gap-3 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400';
      msgIcon.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>';
      msgText.textContent = 'Jika email Anda terdaftar, link reset telah dikirim. Periksa inbox dan folder spam Anda.';
      msgEl.classList.remove('hidden');
      document.getElementById('forgot-email').value = '';
    } catch {
      msgEl.className = 'rounded-2xl px-4 py-3.5 text-sm font-semibold flex items-start gap-3 bg-red-500/10 border border-red-500/20 text-red-400';
      msgIcon.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>';
      msgText.textContent = 'Gagal terhubung ke server. Coba lagi.';
      msgEl.classList.remove('hidden');
    } finally {
      btn.disabled = false;
      btnText.textContent = 'Kirim Link Reset Password';
      btn.classList.remove('opacity-75');
    }
  });
});
