// Super Admin tickets list (tickets.html)

let currentFilter = 'active';
let currentPage = 1;

async function loadTickets(status, page) {
  if (status !== undefined) { currentFilter = status; currentPage = 1; }
  if (page) currentPage = page;

  document.querySelectorAll('.sa-tab').forEach(t => t.classList.remove('active'));
  document.getElementById(currentFilter ? `tab-${currentFilter}` : 'tab-all')?.classList.add('active');

  const list = document.getElementById('tickets-list');
  list.innerHTML = `<div class="flex items-center justify-center py-16 text-slate-300 dark:text-gray-600">
    <svg class="w-6 h-6 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/></svg>
  </div>`;

  let url = `/superadmin/api/tickets?page=${currentPage}`;
  if (currentFilter) url += `&status=${currentFilter}`;
  const res = await fetch(url);
  const data = await res.json();

  if (!data.tickets.length) {
    list.innerHTML = `<div class="sa-card flex flex-col items-center py-16 text-center">
      <svg class="w-12 h-12 text-slate-200 dark:text-gray-600 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z"/></svg>
      <p class="text-sm font-bold text-slate-400 dark:text-gray-500">Tidak ada tiket</p>
    </div>`;
    document.getElementById('pagination').innerHTML = '';
    return;
  }

  list.innerHTML = `<div class="space-y-3">${data.tickets.map(t => `
    <a href="/superadmin/tickets/${t.id}" class="sa-card p-5 flex items-start gap-4 hover:shadow-md transition-all group block">
      <!-- Priority bar -->
      <div class="w-1 self-stretch rounded-full flex-shrink-0 ${priorityBar(t.priority)}"></div>
      <!-- Content -->
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2 mb-1 flex-wrap">
          <span class="text-xs font-mono font-bold text-indigo-500 dark:text-indigo-400">${escHtml(t.ticket_number)}</span>
          <span class="sa-badge ${priorityBadgeClass(t.priority)}">${t.priority}</span>
          <span class="sa-badge ${statusBadgeClass(t.status)}">${t.status.replace('_',' ')}</span>
        </div>
        <h4 class="font-bold text-slate-900 dark:text-gray-100 text-sm group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">${escHtml(t.title)}</h4>
        <p class="text-xs text-slate-400 dark:text-gray-500 mt-0.5">${escHtml(t.school_name)} · ${escHtml(t.user_name)} · ${t.created_at}</p>
      </div>
      <svg class="w-4 h-4 text-slate-300 dark:text-gray-600 group-hover:text-indigo-400 transition-colors flex-shrink-0 mt-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
    </a>
  `).join('')}</div>`;

  // Pagination
  const pag = document.getElementById('pagination');
  if (data.pages > 1) {
    let html = '';
    for (let i = 1; i <= data.pages; i++) {
      html += `<button onclick="loadTickets(undefined,${i})" class="w-8 h-8 rounded-lg text-sm font-bold transition-all ${i===currentPage?'bg-indigo-600 text-white shadow-sm':'bg-white dark:bg-gray-700 text-slate-500 dark:text-gray-400 hover:bg-slate-100 dark:hover:bg-gray-600 border border-slate-200 dark:border-gray-600'}">${i}</button>`;
    }
    pag.innerHTML = html;
  } else { pag.innerHTML = ''; }
}

const escHtml = s => String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');

function priorityBar(p) {
  return { urgent:'bg-red-500', high:'bg-orange-400', medium:'bg-yellow-400', low:'bg-slate-300 dark:bg-gray-600' }[p] || 'bg-slate-300 dark:bg-gray-600';
}
function priorityBadgeClass(p) {
  return { urgent:'bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400 border border-red-100 dark:border-red-800', high:'bg-orange-50 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400 border border-orange-100 dark:border-orange-800', medium:'bg-yellow-50 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400 border border-yellow-100 dark:border-yellow-800', low:'bg-slate-100 dark:bg-gray-700 text-slate-500 dark:text-gray-400' }[p] || 'bg-slate-100 dark:bg-gray-700 text-slate-500 dark:text-gray-400';
}
function statusBadgeClass(s) {
  return { open:'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 border border-blue-100 dark:border-blue-800', in_queue:'bg-yellow-50 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400 border border-yellow-100 dark:border-yellow-800', in_progress:'bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 border border-indigo-100 dark:border-indigo-800', waiting_user:'bg-orange-50 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400 border border-orange-100 dark:border-orange-800', resolved:'bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 border border-emerald-100 dark:border-emerald-800', closed:'bg-slate-100 dark:bg-gray-700 text-slate-500 dark:text-gray-400' }[s] || 'bg-slate-100 dark:bg-gray-700 text-slate-500 dark:text-gray-400';
}

document.addEventListener('DOMContentLoaded', () => loadTickets('active'));
