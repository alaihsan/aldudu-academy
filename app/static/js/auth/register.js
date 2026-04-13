// School registration functionality (register.html)

document.addEventListener('DOMContentLoaded', function() {
  const registerForm = document.getElementById('register-form');
  if (!registerForm) return;

  registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('register-btn');
    const errorEl = document.getElementById('register-error');
    const original = btn.innerText;

    btn.disabled = true;
    btn.innerText = 'MENDAFTARKAN...';
    errorEl.classList.add('hidden');

    try {
      const res = await fetch('/api/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          school_name: document.getElementById('school-name').value,
          slug: document.getElementById('school-slug').value,
          school_email: document.getElementById('school-email').value,
          admin_name: document.getElementById('admin-name').value,
          admin_email: document.getElementById('admin-email').value,
          password: document.getElementById('admin-password').value,
        })
      });
      const data = await res.json();

      if (data.success) {
        document.querySelector('.bg-white').innerHTML = `
          <div class="text-center py-8">
            <div class="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg class="w-8 h-8 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
              </svg>
            </div>
            <h3 class="text-xl font-black text-gray-900 mb-2">Registrasi Berhasil!</h3>
            <p class="text-sm text-gray-500 mb-6">Silakan cek email Anda untuk verifikasi akun.</p>
            <a href="/login" class="text-indigo-600 font-bold text-sm hover:underline">Ke halaman login</a>
          </div>
        `;
      } else {
        errorEl.textContent = data.message;
        errorEl.classList.remove('hidden');
      }
    } catch (err) {
      errorEl.textContent = 'Terjadi kesalahan koneksi.';
      errorEl.classList.remove('hidden');
    } finally {
      btn.disabled = false;
      btn.innerText = original;
    }
  });

  // Auto-generate slug from school name
  document.getElementById('school-name').addEventListener('input', (e) => {
    const slug = e.target.value.toLowerCase()
      .replace(/[^a-z0-9\s-]/g, '')
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-')
      .substring(0, 100);
    document.getElementById('school-slug').value = slug;
  });
});
