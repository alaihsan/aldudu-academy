/**
 * Aldudu Academy - Shared DOM Utilities
 * escapeHtml() and showNotification() were each reimplemented independently
 * across several files (dashboard.js, course_detail.js as escapeHtmlRoster,
 * gradebook/teacher_gradebook.js, materials_list_modals.js) — consolidated
 * here. Loaded in base.html before global-utils.js, so available site-wide
 * (every page extends base.html, including gradebook's).
 */

function escapeHtml(str) {
    const d = document.createElement('div');
    d.textContent = str == null ? '' : String(str);
    return d.innerHTML;
}

function showNotification(message, type = 'info') {
    // Remove existing notification
    const existing = document.querySelector('.drag-notification');
    if (existing) existing.remove();

    const colors = {
        success: { bg: 'bg-green-50', border: 'border-green-200', text: 'text-green-700', icon: '✅' },
        error: { bg: 'bg-red-50', border: 'border-red-200', text: 'text-red-700', icon: '❌' },
        info: { bg: 'bg-blue-50', border: 'border-blue-200', text: 'text-blue-700', icon: 'ℹ️' }
    };

    const color = colors[type] || colors.info;

    const notification = document.createElement('div');
    notification.className = `drag-notification fixed bottom-6 right-6 ${color.bg} ${color.border} border-2 rounded-2xl px-6 py-4 shadow-2xl z-[9999] animate-slide-up flex items-center gap-3`;
    notification.innerHTML = `
        <span class="text-xl">${color.icon}</span>
        <span class="font-bold ${color.text}">${message}</span>
    `;

    document.body.appendChild(notification);

    // Auto-remove after 3 seconds
    setTimeout(() => {
        notification.style.transition = 'all 0.3s ease';
        notification.style.opacity = '0';
        notification.style.transform = 'translateY(20px)';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}
