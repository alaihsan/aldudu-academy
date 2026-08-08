/**
 * Aldudu Academy - Dashboard: Class Create/Edit Modal + Manual Reorder
 * Object.assign(Dashboard, {...}) split of dashboard-legacy.js. Loaded
 * last of the 3 dashboard files — triggers Dashboard.init() once
 * everything is merged onto the Dashboard object.
 */
Object.assign(Dashboard, {
    async handleCreateClass(e) {
        e.preventDefault();
        try {
            const res = await fetch('/api/courses', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    name: e.target['course-name'].value, 
                    academic_year_id: this.state.selectedYearId,
                    color: this.elements.addColorInput.value
                })
            });
            const data = await res.json();
            if (data.success) {
                this.elements.addClassModal.classList.add('hidden');
                e.target.reset();
                this.elements.generatedCode.textContent = data.course.classCode;
                this.elements.showCodeModal.classList.remove('hidden');
                await this.loadInitialData();
            }
        } catch (err) { console.error('Create error', err); }
    },

    openEditClass(id) {
        const course = this.state.courses.find(c => c.id === id);
        if (!course) return;
        this.state.editingCourseId = id;
        this.elements.editCourseName.value = course.name;
        
        // Handle color dots
        const color = course.color || '#58cc02';
        this.elements.editColorInput.value = color;
        
        const dots = this.elements.editClassModal.querySelectorAll('.color-dot');
        dots.forEach(dot => {
            const isMatch = dot.getAttribute('data-color') === color;
            dot.classList.toggle('ring-2', isMatch);
            dot.classList.toggle('ring-[#1cb0f6]', isMatch);
            dot.classList.toggle('shadow-md', isMatch);
            dot.classList.toggle('shadow-sm', !isMatch);
        });
        
        this.elements.editClassModal.classList.remove('hidden');
    },

    selectColor(btn, color) {
        // Update hidden input
        const container = btn.parentElement;
        const input = container.querySelector('input[type="hidden"]');
        if (input) input.value = color;

        // Update visual selection
        container.querySelectorAll('.color-dot').forEach(dot => {
            dot.classList.remove('ring-2', 'ring-[#1cb0f6]', 'shadow-md');
            dot.classList.add('shadow-sm');
        });
        btn.classList.add('ring-2', 'ring-[#1cb0f6]', 'shadow-md');
        btn.classList.remove('shadow-sm');
    },

    async handleUpdateClass(e) {
        e.preventDefault();
        try {
            const res = await fetch(`/api/courses/${this.state.editingCourseId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: this.elements.editCourseName.value, color: this.elements.editColorInput.value })
            });
            if (res.ok) { this.elements.editClassModal.classList.add('hidden'); await this.loadInitialData(); }
        } catch (err) { console.error('Update error', err); }
    },

    async handleEnroll(e) {
        e.preventDefault();
        try {
            const res = await fetch('/api/enroll', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ class_code: e.target['class-code-input'].value })
            });
            const data = await res.json();
            if (data.success) { e.target.reset(); await this.loadInitialData(); alert('Berhasil bergabung!'); }
            else { alert(data.message); }
        } catch (err) { console.error('Enroll error', err); }
    },

    setSortMode(mode) {
        if (mode === 'manual') {
            // Toggle editing state if already in manual mode, or enter manual mode
            if (this.state.sortMode === 'manual') {
                this.state.isEditingOrder = !this.state.isEditingOrder;
            } else {
                this.state.sortMode = 'manual';
                this.state.isEditingOrder = true;
            }
            localStorage.setItem('courseSortMode', 'manual');
        } else {
            this.state.sortMode = mode;
            this.state.isEditingOrder = false;
            localStorage.setItem('courseSortMode', mode);
        }
        this.updateSortButtons();
        this.renderCourses();
    },

    finishSorting() {
        if (this.state.isEditingOrder) {
            this.state.isEditingOrder = false;
            this.updateSortButtons();
            this.renderCourses();
            
            // Subtle status hint
            this.showStatusHint('Urutan manual disimpan');
        }
    },

    showStatusHint(message) {
        const hint = document.createElement('div');
        hint.className = 'fixed bottom-12 left-1/2 -translate-x-1/2 bg-gray-900/90 backdrop-blur-xl text-white px-6 py-3.5 rounded-2xl text-[11px] font-black uppercase tracking-[0.2em] shadow-2xl animate-premium-entrance z-[100] border border-white/10 flex items-center space-x-3 pointer-events-none';
        hint.innerHTML = `
            <div class="w-5 h-5 bg-green-500 rounded-lg flex items-center justify-center">
                <svg class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="4" d="M5 13l4 4L19 7"/></svg>
            </div>
            <span>${message}</span>
        `;
        document.body.appendChild(hint);
        setTimeout(() => {
            hint.classList.add('opacity-0', 'translate-y-4');
            hint.style.transition = 'all 0.6s cubic-bezier(0.16, 1, 0.3, 1)';
            setTimeout(() => hint.remove(), 600);
        }, 2500);
    },

    updateSortButtons() {
        const buttons = document.querySelectorAll('.sort-btn');
        buttons.forEach(btn => {
            const mode = btn.id.replace('sort-', '');
            const manualIcon = `<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M4 6h16M4 12h16M4 18h16"/></svg>`;
            const checkIcon = `<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"/></svg>`;

            if (mode === this.state.sortMode) {
                btn.classList.add('bg-primary-600', 'text-white', 'shadow-lg', 'shadow-primary-100');
                btn.classList.remove('text-gray-400', 'hover:text-gray-600');
                
                if (mode === 'manual') {
                    if (this.state.isEditingOrder) {
                        btn.innerHTML = `${checkIcon}<span class="hidden md:inline">Selesai</span>`;
                        btn.classList.add('animate-pulse');
                        btn.title = "Selesai Mengurutkan";
                    } else {
                        btn.innerHTML = `${manualIcon}<span class="hidden md:inline">Manual</span>`;
                        btn.classList.remove('animate-pulse');
                        btn.title = "Urutan Manual (Drag & Drop)";
                    }
                }
            } else {
                btn.classList.remove('bg-primary-600', 'text-white', 'shadow-lg', 'shadow-primary-100', 'animate-pulse');
                btn.classList.add('text-gray-400', 'hover:text-gray-600');
                
                if (mode === 'manual') {
                    btn.innerHTML = `${manualIcon}<span class="hidden md:inline">Manual</span>`;
                    btn.title = "Urutan Manual (Drag & Drop)";
                }
            }
        });
    },

    // Copy class code yang robust: pakai Clipboard API bila tersedia
    // (HTTPS/localhost), fallback ke execCommand untuk HTTP non-secure (LAN IP).
    copyCode(evt, code) {
        // Kompat: pemanggil lama (`copyCode('AB12')`) — geser argumen
        if (typeof evt === 'string' && code === undefined) {
            code = evt;
            evt = window.event;
        }
        const btn = (evt && (evt.currentTarget || evt.target && evt.target.closest('button'))) || null;
        const fallbackCopy = (text) => {
            const ta = document.createElement('textarea');
            ta.value = text;
            ta.setAttribute('readonly', '');
            ta.style.position = 'fixed';
            ta.style.left = '-9999px';
            document.body.appendChild(ta);
            ta.select();
            let ok = false;
            try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
            document.body.removeChild(ta);
            return ok;
        };
        const showFeedback = (success, message) => {
            if (btn && success) {
                const originalHTML = btn.innerHTML;
                btn.innerHTML = `
                    <svg class="w-5 h-5 text-green-600 animate-success-pop" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                    </svg>`;
                btn.classList.add('bg-green-50', 'ring-2', 'ring-green-500');
                setTimeout(() => {
                    btn.innerHTML = originalHTML;
                    btn.classList.remove('bg-green-50', 'ring-2', 'ring-green-500');
                }, 1600);
            }
            const toast = document.createElement('div');
            toast.className = 'fixed z-[100] left-1/2 -translate-x-1/2 px-6 py-3 rounded-2xl font-bold text-sm shadow-2xl animate-toast-float flex items-center gap-3 ' +
                (success ? 'bg-gray-900 text-white' : 'bg-red-600 text-white');
            toast.style.top = '20px';
            toast.innerHTML = success
                ? `<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"/></svg><span>${message}</span>`
                : `<span>${message}</span>`;
            document.body.appendChild(toast);
            setTimeout(() => toast.remove(), 2000);
        };

        const doFallback = () => {
            const ok = fallbackCopy(code);
            showFeedback(ok, ok ? `Kode kelas disalin: ${code}` : `Gagal menyalin. Salin manual: ${code}`);
        };

        if (navigator.clipboard && window.isSecureContext) {
            navigator.clipboard.writeText(code)
                .then(() => showFeedback(true, `Kode kelas disalin: ${code}`))
                .catch(() => doFallback());
        } else {
            doFallback();
        }
    }
});

// Initial run
if (document.readyState !== 'loading') Dashboard.init();
else document.addEventListener('DOMContentLoaded', () => Dashboard.init());
