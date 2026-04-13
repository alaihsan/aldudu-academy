// Super Admin ticket detail (ticket_detail.html)

document.addEventListener('DOMContentLoaded', function() {
  const ticketId = window.saTicketId;

  document.getElementById('reply-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const content = document.getElementById('reply-content').value.trim();
    if (!content) return;
    const isInternal = document.getElementById('reply-internal').checked;
    const btn = document.getElementById('reply-btn');
    btn.disabled = true;
    btn.textContent = 'Mengirim...';

    const res = await fetch(`/superadmin/api/tickets/${ticketId}/reply`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content, is_internal: isInternal })
    });
    const data = await res.json();
    if (data.success) {
      location.reload();
    } else {
      Swal.fire({ icon: 'error', title: 'Gagal', text: data.message });
      btn.disabled = false;
      btn.textContent = 'Kirim Balasan';
    }
  });

  window.updateTicketStatus = async function() {
    const status = document.getElementById('status-select').value;
    const res = await fetch(`/superadmin/api/tickets/${ticketId}/status`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status })
    });
    const data = await res.json();
    if (data.success) {
      Swal.fire({ icon: 'success', title: 'Status diperbarui', timer: 1500, showConfirmButton: false });
    } else {
      Swal.fire({ icon: 'error', title: 'Gagal', text: data.message });
      location.reload();
    }
  };
});
