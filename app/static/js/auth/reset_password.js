// Password reset functionality (reset_password.html)
// Requires window.resetToken to be set via Jinja2 config

// Show/hide password toggle
function togglePw(id, btn) {
  const input = document.getElementById(id);
  const isText = input.type === 'text';
  input.type = isText ? 'password' : 'text';
  btn.querySelector('svg').style.opacity = isText ? '1' : '0.5';
}

// Password strength meter
function checkStrength(pw) {
  const bars = ['s1','s2','s3','s4'];
  const label = document.getElementById('strength-label');
  let score = 0;
  if (pw.length >= 6) score++;
  if (pw.length >= 10) score++;
  if (/[A-Z]/.test(pw) && /[a-z]/.test(pw)) score++;
  if (/[0-9]/.test(pw) && /[^A-Za-z0-9]/.test(pw)) score++;

  const colors = ['bg-red-500','bg-orange-500','bg-yellow-500','bg-emerald-500'];
  const labels = ['','Lemah','Cukup','Kuat','Sangat Kuat'];
  const labelColors = ['','text-red-400','text-orange-400','text-yellow-400','text-emerald-400'];

  bars.forEach((id, i) => {
    const el = document.getElementById(id);
    el.className = `h-1 flex-1 rounded-full transition-all duration-300 ${i < score ? colors[score-1] : 'bg-white/10'}`;
  });
  label.textContent = labels[score] || '';
  label.className = `text-xs mt-1 ${labelColors[score] || 'text-slate-600'}`;
}

// Form submit
document.addEventListener('DOMContentLoaded', function() {
  const resetForm = document.getElementById('reset-form');
  if (!resetForm) return;

  resetForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const pw = document.getElementById('new-password').value;
    const confirm = document.getElementById('confirm-password').value;
    const errorEl = document.getElementById('reset-error');
    const errorText = document.getElementById('reset-error-text');
    const btn = document.getElementById('reset-btn');
    const btnText = document.getElementById('reset-btn-text');

    errorEl.classList.add('hidden');

    if (pw !== confirm) {
      errorText.textContent = 'Password tidak cocok. Periksa kembali.';
      errorEl.classList.remove('hidden');
      return;
    }
    if (pw.length < 6) {
      errorText.textContent = 'Password minimal 6 karakter.';
      errorEl.classList.remove('hidden');
      return;
    }

    btn.disabled = true;
    btnText.textContent = 'Menyimpan...';
    btn.classList.add('opacity-75');

    try {
      const res = await fetch(`/api/reset-password/${window.resetToken}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password: pw })
      });
      const data = await res.json();

      if (data.success) {
        // Replace card content with success state
        document.querySelector('.rounded-3xl').innerHTML = `
          <div class="p-10 text-center">
            <div class="w-20 h-20 bg-emerald-500/15 rounded-3xl flex items-center justify-center mx-auto mb-5 border border-emerald-500/25">
              <svg class="w-10 h-10 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
              </svg>
            </div>
            <h2 class="text-2xl font-black text-white mb-2">Password Berhasil Diubah!</h2>
            <p class="text-sm text-slate-400 mb-8 leading-relaxed">Gunakan password baru Anda untuk masuk ke akun Aldudu Academy.</p>
            <a href="/login" class="inline-flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-500 hover:to-emerald-400 text-white rounded-2xl font-bold text-sm shadow-lg shadow-emerald-500/25 transition-all active:scale-95">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1"/>
              </svg>
              Login Sekarang
            </a>
          </div>`;
      } else {
        errorText.textContent = data.message || 'Gagal menyimpan password.';
        errorEl.classList.remove('hidden');
      }
    } catch {
      errorText.textContent = 'Gagal terhubung ke server. Coba lagi.';
      errorEl.classList.remove('hidden');
    } finally {
      btn.disabled = false;
      btnText.textContent = 'Simpan Password Baru';
      btn.classList.remove('opacity-75');
    }
  });
});
