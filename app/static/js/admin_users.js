function openResetModal(id, name) {
    document.getElementById('reset-user-id').value = id;
    document.getElementById('reset-user-name').innerText = `Mengubah password untuk ${name}`;
    toggleModal('reset-modal', true);
}
