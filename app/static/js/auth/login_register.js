/**
 * Aldudu Academy - Dashboard: Login/Register/Logout
 * Object.assign(Dashboard, {...}) split of dashboard-legacy.js's auth
 * handlers. Loaded after pages/dashboard.js, before
 * dashboard_class_modal.js (which triggers Dashboard.init()).
 */
Object.assign(Dashboard, {
    async handleLogin(e) {
        e.preventDefault();
        const btn = document.getElementById('login-btn');
        const btnText = btn?.querySelector('.btn-text');
        const loader = btn?.querySelector('.loader-container');
        const errorDiv = this.elements.loginError;
        
        if (btn) btn.disabled = true;
        if (btnText) btnText.classList.add('opacity-0', 'translate-y-2');
        if (loader) loader.classList.remove('hidden');
        if (errorDiv) errorDiv.classList.add('hidden');

        try {
            const res = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email: e.target.email.value, password: e.target.password.value })
            });
            const data = await res.json();
            
            if (data.success) {
                if (btn) btn.classList.add('bg-green-600', 'scale-95');
                setTimeout(() => {
                    if (data.redirect) {
                        window.location.href = data.redirect;
                    } else {
                        window.location.reload();
                    }
                }, 600);
            } else {
                // Specific field highlighting
                if (data.field === 'email') {
                    const emailInput = document.getElementById('email');
                    if (emailInput) {
                        emailInput.classList.add('border-red-500', 'ring-4', 'ring-red-100');
                        emailInput.focus();
                        emailInput.addEventListener('input', () => {
                            emailInput.classList.remove('border-red-500', 'ring-4', 'ring-red-100');
                        }, { once: true });
                    }
                } else if (data.field === 'password') {
                    const passwordInput = document.getElementById('password');
                    if (passwordInput) {
                        passwordInput.classList.add('border-red-500', 'ring-4', 'ring-red-100');
                        passwordInput.focus();
                        passwordInput.addEventListener('input', () => {
                            passwordInput.classList.remove('border-red-500', 'ring-4', 'ring-red-100');
                        }, { once: true });
                    }
                }
                throw new Error(data.message || 'Email atau password salah');
            }
        } catch (err) {
            console.error('Login error', err);
            
            if (btn) {
                btn.disabled = false;
                btn.classList.add('animate-bounce', 'border-red-500');
                setTimeout(() => btn.classList.remove('animate-bounce'), 500);
            }
            if (btnText) btnText.classList.remove('opacity-0', 'translate-y-2');
            if (loader) loader.classList.add('hidden');

            if (errorDiv) {
                errorDiv.innerHTML = `
                    <div class="flex items-center space-x-3 animate-slide-up p-1">
                        <div class="flex-shrink-0 w-8 h-8 bg-red-100 text-red-600 rounded-xl flex items-center justify-center shadow-sm">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
                        </div>
                        <div class="flex-1 font-bold text-red-800 text-xs">${err.message}</div>
                    </div>
                `;
                errorDiv.classList.remove('hidden');
                errorDiv.className = "p-4 bg-red-50/80 backdrop-blur-md border border-red-100 rounded-2xl mt-4 shadow-xl shadow-red-200/20 ring-1 ring-red-200";
            }
        }
    },

    async handleLogout() {
        await fetch('/api/logout', { method: 'POST' });
        window.location.reload();
    },

    async handleRegister(e) {
        e.preventDefault();
        const errorDiv = document.getElementById('register-error');
        const submitBtn = e.target.querySelector('button[type="submit"]');

        submitBtn.disabled = true;
        submitBtn.innerText = 'Mendaftar...';
        errorDiv.classList.add('hidden');

        const schoolId = e.target.school_id.value;
        if (!schoolId) {
            errorDiv.textContent = 'Pilih sekolah terlebih dahulu';
            errorDiv.classList.remove('hidden');
            submitBtn.disabled = false;
            submitBtn.innerText = 'Daftar Akun';
            return;
        }

        const payload = {
            name: e.target.name.value,
            email: e.target.email.value,
            password: e.target.password.value,
            role: e.target.role.value,
            school_id: parseInt(schoolId)
        };

        try {
            const res = await fetch('/api/register-user', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            if (data.success) {
                alert('Pendaftaran berhasil! Silakan cek email untuk verifikasi.');
                window.toggleAuthMode(null, 'login');
                e.target.reset();
            } else {
                errorDiv.textContent = data.message;
                errorDiv.classList.remove('hidden');
            }
        } catch (err) {
            errorDiv.textContent = 'Gagal mendaftar. Coba lagi.';
            errorDiv.classList.remove('hidden');
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerText = 'Daftar Akun';
        }
    },
});

window.toggleAuthMode = function(e, mode) {
    if (e) e.preventDefault();
    const loginCard = document.getElementById('login-card');
    const registerCard = document.getElementById('register-card');

    if (mode === 'register') {
        loginCard.classList.add('hidden');
        registerCard.classList.remove('hidden');
    } else {
        registerCard.classList.add('hidden');
        loginCard.classList.remove('hidden');
    }
}
