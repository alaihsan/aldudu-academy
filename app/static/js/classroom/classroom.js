(function () {
    const loadingEl = document.getElementById('classroom-loading');
    const itemsEl = document.getElementById('classroom-items');
    const emptyEl = document.getElementById('classroom-empty-state');
    const filterEl = document.getElementById('classroom-filter');
    const sortEl = document.getElementById('classroom-sort');

    if (!loadingEl || !itemsEl || !emptyEl || !filterEl || !sortEl) {
        return;
    }

    const ICONS = {
        assignment: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>',
        quiz: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>',
    };

    function escapeHtml(text) {
        if (window.escapeHtml) {
            return window.escapeHtml(text);
        }
        const div = document.createElement('div');
        div.textContent = text == null ? '' : String(text);
        return div.innerHTML;
    }

    function formatDueDate(isoString) {
        if (!isoString) return null;
        const date = new Date(isoString);
        if (Number.isNaN(date.getTime())) return null;
        return date.toLocaleDateString('id-ID', { day: 'numeric', month: 'short', year: 'numeric' });
    }

    function renderItem(item) {
        const isAssignment = item.type === 'assignment';
        const dueDate = formatDueDate(item.due_date);
        const badgeHtml = item.pending_count
            ? `<span class="px-2.5 py-1 bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 text-[10px] font-black rounded-full uppercase tracking-wide">${item.pending_count} menunggu</span>`
            : '';
        const dueBadgeHtml = dueDate
            ? `<span class="px-2.5 py-1 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-[10px] font-black rounded-full uppercase tracking-wide">Tenggat: ${dueDate}</span>`
            : '';

        return `
        <a href="${item.url}" class="block bg-white dark:bg-gray-900 rounded-2xl p-5 border border-gray-100 dark:border-gray-800 hover:border-primary-300 dark:hover:border-primary-700 hover:shadow-md transition-all">
            <div class="flex items-start gap-4">
                <div class="w-11 h-11 shrink-0 rounded-xl flex items-center justify-center ${isAssignment ? 'bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400' : 'bg-emerald-50 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400'}">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">${ICONS[item.type] || ''}</svg>
                </div>
                <div class="min-w-0 flex-1">
                    <h4 class="font-bold text-gray-900 dark:text-gray-100 truncate">${escapeHtml(item.title)}</h4>
                    <p class="text-xs text-gray-500 dark:text-gray-400 font-medium mt-0.5 truncate">${escapeHtml(item.course_name)}</p>
                    <div class="flex flex-wrap items-center gap-2 mt-3">
                        ${dueBadgeHtml}
                        ${badgeHtml}
                    </div>
                </div>
            </div>
        </a>`;
    }

    function setLoading(isLoading) {
        loadingEl.classList.toggle('hidden', !isLoading);
        if (isLoading) {
            itemsEl.classList.add('hidden');
            emptyEl.classList.add('hidden');
        }
    }

    async function loadItems() {
        setLoading(true);
        const params = new URLSearchParams({
            filter: filterEl.value,
            sort: sortEl.value,
        });

        try {
            const response = await fetch(`/api/classroom/items?${params.toString()}`);
            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(data.message || 'Gagal memuat data');
            }

            renderItems(data.items || []);
        } catch (err) {
            itemsEl.innerHTML = `<div class="text-center py-12 text-red-500 font-medium">Gagal memuat data. Coba lagi nanti.</div>`;
            itemsEl.classList.remove('hidden');
            emptyEl.classList.add('hidden');
        } finally {
            setLoading(false);
        }
    }

    function renderItems(items) {
        if (items.length === 0) {
            itemsEl.classList.add('hidden');
            emptyEl.classList.remove('hidden');
            return;
        }

        itemsEl.innerHTML = items.map(renderItem).join('');
        itemsEl.classList.remove('hidden');
        emptyEl.classList.add('hidden');
    }

    filterEl.addEventListener('change', loadItems);
    sortEl.addEventListener('change', loadItems);

    loadItems();
})();
