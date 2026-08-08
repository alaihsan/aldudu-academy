// Ticket detail reply functionality (ticket_detail.html - school view)

document.addEventListener('DOMContentLoaded', function() {
  const SLUG = window.location.pathname.split('/')[2];
  const ticketId = window.ticketId;

  const replyForm = document.getElementById('reply-form');
  if (!replyForm) return;

  replyForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const content = document.getElementById('reply-content').value;
    const res = await fetch(`/s/${SLUG}/api/tickets/${ticketId}/message`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content })
    });
    const data = await res.json();
    if (data.success) location.reload();
  });
});
