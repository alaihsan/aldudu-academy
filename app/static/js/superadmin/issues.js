// Super Admin issues management (issues.html)

let currentFilter = 'active';
let allIssues = [];

async function loadIssues(status) {
  if (status !== undefined) currentFilter = status;

  document.querySelectorAll('.sa-tab').forEach(t => t.classList.remove('active'));
  document.getElementById(currentFilter ? `tab-${currentFilter}` : 'tab-all')?.classList.add('active');

  const list = document.getElementById('issues-list');
  list.innerHTML = `<div class="flex items-center justify-center py-16 text-slate-300 dark:text-gray-600">
    <svg class="w-6 h-6 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/></svg>
  </div>`;

  let url = '/superadmin/api/issues';
  if (currentFilter) url += `?status=${currentFilter}`;
  const res = await fetch(url);
  const data = await res.json();
  allIssues = data.issues || [];

  if (!allIssues.length) {
    list.innerHTML = `<div class="sa-card flex flex-col items-center py-16 text-center">
      <svg class="w-12 h-12 text-slate-200 dark:text-gray-600 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
      <p class="text-sm font-bold text-slate-400 dark:text-gray-500">Tidak ada laporan masalah</p>
    </div>`;
    return;
  }

  list.innerHTML = `<div class="space-y-3">${allIssues.map(i => `
    <div onclick="showIssue(${i.id})" class="sa-card p-5 flex items-start gap-4 hover:shadow-md transition-all cursor-pointer group">
      <div class="w-1 self-stretch rounded-full flex-shrink-0 ${priorityBar(i.priority)}"></div>
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2 mb-1 flex-wrap">
          <span class="sa-badge ${priorityBadge(i.priority)}">${esc(i.priority)}</span>
          <span class="sa-badge ${statusBadge(i.status)}">${esc(i.status)}</span>
        </div>
        <h4 class="font-bold text-slate-900 dark:text-gray-100 text-sm group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">${esc(i.title)}</h4>
        <p class="text-xs text-slate-400 dark:text-gray-500 mt-0.5">${esc(i.school_name)} · ${esc(i.user_name)} · ${i.created_at}</p>
      </div>
      <svg class="w-4 h-4 text-slate-300 dark:text-gray-600 group-hover:text-indigo-400 transition-colors flex-shrink-0 mt-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
    </div>
  `).join('')}</div>`;
}

function showIssue(id) {
  const i = allIssues.find(x => x.id === id);
  if (!i) return;
  document.getElementById('modal-title').textContent = i.title;
  document.getElementById('modal-badges').innerHTML = `
    <span class="sa-badge ${priorityBadge(i.priority)}">${esc(i.priority)}</span>
    <span class="sa-badge ${statusBadge(i.status)}">${esc(i.status)}</span>`;
  document.getElementById('modal-meta').textContent = `${i.school_name} · ${i.user_name} · ${i.created_at}`;
  document.getElementById('modal-desc').textContent = i.description;

  const statuses = ['OPEN','IN_PROGRESS','RESOLVED','CLOSED'];
  const labels = { OPEN:'Open', IN_PROGRESS:'In Progress', RESOLVED:'Resolved', CLOSED:'Closed' };
  const currentKey = i.status.toUpperCase().replace(/ /g,'_');
  document.getElementById('modal-actions').innerHTML = statuses
    .filter(s => s !== currentKey)
    .map(s => `<button onclick="updateStatus(${i.id},'${s}')" class="px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${statusBtn(s)}">${labels[s]}</button>`)
    .join('');

  const modal = document.getElementById('issue-modal');
  modal.classList.remove('hidden');
  modal.classList.add('flex');
}

function closeModal() {
  const modal = document.getElementById('issue-modal');
  modal.classList.add('hidden');
  modal.classList.remove('flex');
}

async function updateStatus(id, status) {
  const res = await fetch(`/superadmin/api/issues/${id}/status`, {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ status })
  });
  const data = await res.json();
  if (data.success) {
    closeModal();
    loadIssues(undefined);
  } else {
    alert(data.message || 'Gagal mengubah status');
  }
}

const esc = s => String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');

function priorityBar(p) {
  return { Urgent:'bg-red-500', High:'bg-orange-400', Medium:'bg-yellow-400', Low:'bg-slate-300 dark:bg-gray-600' }[p] || 'bg-slate-300 dark:bg-gray-600';
}
function priorityBadge(p) {
  return { Urgent:'bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400 border border-red-100 dark:border-red-800', High:'bg-orange-50 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400 border border-orange-100 dark:border-orange-800', Medium:'bg-yellow-50 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400 border border-yellow-100 dark:border-yellow-800', Low:'bg-slate-100 dark:bg-gray-700 text-slate-500 dark:text-gray-400' }[p] || 'bg-slate-100 dark:bg-gray-700 text-slate-500 dark:text-gray-400';
}
function statusBadge(s) {
  return { Open:'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 border border-blue-100 dark:border-blue-800', 'In Progress':'bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 border border-indigo-100 dark:border-indigo-800', Resolved:'bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 border border-emerald-100 dark:border-emerald-800', Closed:'bg-slate-100 dark:bg-gray-700 text-slate-500 dark:text-gray-400' }[s] || 'bg-slate-100 dark:bg-gray-700 text-slate-500 dark:text-gray-400';
}
function statusBtn(s) {
  return { OPEN:'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 hover:bg-blue-100 dark:hover:bg-blue-900/50', IN_PROGRESS:'bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 hover:bg-indigo-100 dark:hover:bg-indigo-900/50', RESOLVED:'bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 hover:bg-emerald-100 dark:hover:bg-emerald-900/50', CLOSED:'bg-slate-100 dark:bg-gray-700 text-slate-500 dark:text-gray-400 hover:bg-slate-200 dark:hover:bg-gray-600' }[s] || 'bg-slate-100 dark:bg-gray-700 text-slate-500 dark:text-gray-400';
}

document.addEventListener('DOMContentLoaded', function() {
  document.getElementById('issue-modal').addEventListener('click', e => { if (e.target === e.currentTarget) closeModal(); });
  loadIssues('active');
});
