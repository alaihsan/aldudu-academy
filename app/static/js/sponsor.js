// Sponsor/donation page functionality (sponsor.html)

let selectedAmount = 0;

function selectAmount(amount) {
  selectedAmount = amount;
  document.getElementById('custom-amount').value = '';
  updateDisplay();
  // Highlight selected button
  document.querySelectorAll('.donation-amount-btn').forEach(btn => {
    btn.classList.remove('border-amber-400', 'bg-amber-50');
    btn.classList.add('border-gray-100', 'dark:border-gray-700');
  });
  event.currentTarget.classList.add('border-amber-400', 'bg-amber-50', 'dark:bg-amber-900/30');
  event.currentTarget.classList.remove('border-gray-100', 'dark:border-gray-700');
}

document.addEventListener('DOMContentLoaded', function() {
  document.getElementById('custom-amount')?.addEventListener('input', function() {
    selectedAmount = parseInt(this.value) || 0;
    document.querySelectorAll('.donation-amount-btn').forEach(btn => {
      btn.classList.remove('border-amber-400', 'bg-amber-50', 'dark:bg-gray-700');
      btn.classList.add('border-gray-100', 'dark:border-gray-700');
    });
    updateDisplay();
  });

  document.getElementById('donate-btn')?.addEventListener('click', function() {
    if (selectedAmount < 10000) {
      Swal.fire({
        title: 'Nominal Terlalu Kecil',
        text: 'Minimal donasi adalah Rp 10.000',
        icon: 'warning',
        confirmButtonText: 'OKE'
      });
      return;
    }
    Swal.fire({
      title: 'Segera Hadir!',
      text: 'Fitur pembayaran melalui Stripe sedang dalam pengembangan. Terima kasih atas niat baik Anda!',
      icon: 'info',
      confirmButtonText: 'Mengerti',
      confirmButtonColor: '#f59e0b'
    });
  });
});

function updateDisplay() {
  const display = document.getElementById('selected-amount-display');
  const amountEl = document.getElementById('display-amount');
  if (selectedAmount > 0) {
    display.classList.remove('hidden');
    amountEl.textContent = 'Rp ' + selectedAmount.toLocaleString('id-ID');
  } else {
    display.classList.add('hidden');
  }
}
