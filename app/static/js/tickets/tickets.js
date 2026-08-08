// Tickets list functionality (tickets.html)

const SLUG = window.location.pathname.split('/')[2];

function showCreateModal() { document.getElementById('create-modal').classList.remove('hidden'); }
function hideCreateModal() { document.getElementById('create-modal').classList.add('hidden'); }

async function loadTickets(status) {
  document.querySelectorAll('[id^="tab-"]').forEach(t => t.className = 'px-4 py-2 rounded-xl text-xs font-black uppercase tracking-widest bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400');
  document.getElementById(`tab-${status}`).className = 'px-4 py-2 rounded-xl text-xs font-black uppercase tracking-widest bg-indigo-600 text-white';

  const res = await fetch(`/s/${SLUG}/api/tickets?status=${status}`);
  const data = await res.json();
  const list = document.getElementById('tickets-list');

  if (!data.tickets.length) {
    list.innerHTML = '<p class="text-sm text-gray-400 dark:text-gray-500 text-center py-8">Tidak ada ticket</p>';
    return;
  }

  list.innerHTML = data.tickets.map(t => `
    <a href="/s/${SLUG}/tickets/${t.id}" class="block bg-white dark:bg-gray-800 rounded-2xl p-5 shadow-sm hover:shadow-md transition-shadow">
      <div class="flex items-start justify-between">
        <div>
          <span class="text-xs font-mono text-indigo-500 dark:text-indigo-400 font-bold">${t.ticket_number}</span>
          <h4 class="font-bold text-gray-900 dark:text-gray-100 mt-1">${t.title}</h4>
          <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">${t.category} | ${t.created_at}</p>
        </div>
        <span class="px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest ${statusBadge(t.status)}">${t.status.replace('_', ' ')}</span>
      </div>
    </a>
  `).join('');
}

function statusBadge(s) {
  const m = { open: 'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400', in_queue: 'bg-yellow-50 dark:bg-yellow-900/30 text-yellow-600 dark:text-yellow-400', in_progress: 'bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400', waiting_user: 'bg-orange-50 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400', resolved: 'bg-green-50 dark:bg-green-900/30 text-green-600 dark:text-green-400', closed: 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400' };
  return m[s] || 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400';
}

document.addEventListener('DOMContentLoaded', function() {
  document.getElementById('create-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const res = await fetch(`/s/${SLUG}/api/tickets`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: document.getElementById('ticket-title').value,
        description: document.getElementById('ticket-desc').value,
        category: document.getElementById('ticket-category').value,
        priority: document.getElementById('ticket-priority').value,
      })
    });
    const data = await res.json();
    if (data.success) {
      hideCreateModal();
      document.getElementById('create-form').reset();
      loadTickets('active');
      Swal.fire('Berhasil', data.message, 'success');
    } else {
      Swal.fire('Error', data.message, 'error');
    }
  });

  loadTickets('active');
});
