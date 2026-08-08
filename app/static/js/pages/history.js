document.addEventListener('DOMContentLoaded', function() {
    let page = 1;
    const perPage = 50;

    loadLogs();

    document.getElementById('load-more-btn')?.addEventListener('click', () => {
        page++;
        loadLogs(true);
    });

    async function loadLogs(append = false) {
        try {
            const res = await fetch(`/api/activity-logs?page=${page}&per_page=${perPage}`);
            const data = await res.json();
            if (data.success) {
                renderLogs(data.logs, append);
                const btn = document.getElementById('load-more-btn');
                if (data.has_more) btn?.classList.remove('hidden');
                else btn?.classList.add('hidden');
            }
        } catch (err) {
            console.error('Failed to load logs', err);
        }
    }

    function renderLogs(logs, append) {
        const tbody = document.getElementById('activity-log-body');
        if (!append) tbody.innerHTML = '';

        if (logs.length === 0 && !append) {
            tbody.innerHTML = '<tr><td colspan="4" class="px-8 py-12 text-center text-gray-400 font-medium">Belum ada aktivitas tercatat.</td></tr>';
            return;
        }

        logs.forEach(log => {
            const row = document.createElement('tr');
            row.className = 'border-t border-gray-50 hover:bg-gray-50 transition-colors';
            row.innerHTML = `
                <td class="px-8 py-4 text-sm text-gray-500 whitespace-nowrap">${log.created_at}</td>
                <td class="px-8 py-4 text-sm font-bold text-gray-900">${log.user_name}</td>
                <td class="px-8 py-4"><span class="px-3 py-1 text-[10px] font-black uppercase tracking-widest rounded-lg ${getRoleBadge(log.user_role)}">${log.user_role}</span></td>
                <td class="px-8 py-4 text-sm text-gray-600">${log.action}</td>
            `;
            tbody.appendChild(row);
        });
    }

    function getRoleBadge(role) {
        switch(role) {
            case 'guru': return 'bg-blue-50 text-blue-700';
            case 'murid': return 'bg-green-50 text-green-700';
            case 'admin': return 'bg-purple-50 text-purple-700';
            default: return 'bg-gray-50 text-gray-700';
        }
    }
});
