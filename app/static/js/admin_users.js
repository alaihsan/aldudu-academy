function toggleModal(id, show) {
    const m = document.getElementById(id);
    if (show) m.classList.remove('hidden');
    else m.classList.add('hidden');
}

function openResetModal(id, name) {
    document.getElementById('reset-user-id').value = id;
    document.getElementById('reset-user-name').innerText = `Mengubah password untuk ${name}`;
    toggleModal('reset-modal', true);
}
