// Quiz detail functionality (quiz_detail.html)

// Initialize theme RGB for CSS patterns
(function() {
  const hex = window.quizThemeColor || "#673ab7";
  const r = parseInt(hex.slice(1,3), 16);
  const g = parseInt(hex.slice(3,5), 16);
  const b = parseInt(hex.slice(5,7), 16);
  document.documentElement.style.setProperty('--quiz-theme-rgb', `${r}, ${g}, ${b}`);
})();

let timeRemaining = window.quizDuration ? window.quizDuration * 60 : 0;
let timerInterval = null;
let isQuizActive = false;

// Browser Close Protection (Default UI)
window.addEventListener('beforeunload', function (e) {
  if (isQuizActive) {
    const message = 'Soal yang kamu kerjakan akan hilang, harap submit dahulu.';
    e.preventDefault();
    e.returnValue = message;
    return message;
  }
});

// Internal Exit Protection (Beautiful UI)
function handleExit() {
  if (!isQuizActive) {
    window.location.href = window.quizExitUrl;
    return;
  }

  Swal.fire({
    title: 'Tinggalkan Kuis?',
    text: 'Progres pengerjaan Anda akan hilang. Apakah Anda yakin ingin keluar?',
    icon: 'warning',
    showCancelButton: true,
    confirmButtonText: 'Ya, Keluar',
    cancelButtonText: 'Tetap Mengerjakan',
    confirmButtonColor: '#ef4444',
    cancelButtonColor: '#6b7280',
    reverseButtons: true,
    background: '#ffffff',
    customClass: {
      title: 'font-black text-gray-800',
      popup: 'rounded-3xl'
    }
  }).then((result) => {
    if (result.isConfirmed) {
      isQuizActive = false;
      window.location.href = window.quizExitUrl;
    }
  });
}

function confirmStart() {
  const passwordInput = document.getElementById('quiz-password-input');
  if (passwordInput) {
    const entered = passwordInput.value.trim();
    const errorEl = document.getElementById('password-error');
    if (!entered) {
      errorEl.textContent = 'Password wajib diisi.';
      errorEl.classList.remove('hidden');
      passwordInput.focus();
      return;
    }

    // Show loading state for password verification
    Swal.fire({
      title: 'Memverifikasi...',
      allowOutsideClick: false,
      didOpen: () => Swal.showLoading()
    });

    fetch(`/api/quiz/${window.quizId}/verify-password`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password: entered })
    })
    .then(res => res.json())
    .then(data => {
      Swal.close();
      if (!data.success) {
        errorEl.textContent = 'Password salah, coba lagi.';
        errorEl.classList.remove('hidden');
        passwordInput.value = '';
        passwordInput.focus();
        return;
      }
      errorEl.classList.add('hidden');

      // If password correct, show the start confirmation
      showStartConfirmation();
    })
    .catch(e => {
      Swal.close();
      errorEl.textContent = 'Terjadi kesalahan, coba lagi.';
      errorEl.classList.remove('hidden');
    });
  } else {
    showStartConfirmation();
  }
}

function showStartConfirmation() {
  Swal.fire({
    title: 'Mulai Kuis?',
    text: 'Waktu akan mulai berjalan setelah Anda menekan tombol mulai.',
    icon: 'question',
    showCancelButton: true,
    confirmButtonText: 'Ya, Mulai!',
    cancelButtonText: 'Batal',
    confirmButtonColor: 'var(--quiz-theme)',
    customClass: { popup: 'rounded-3xl', title: 'font-black' }
  }).then((result) => {
    if (result.isConfirmed) {
      startQuiz();
    }
  });
}

function startQuiz() {
  isQuizActive = true;
  document.getElementById('start-screen').classList.add('hidden');
  document.getElementById('quiz-main-container').classList.remove('hidden');

  if (timeRemaining > 0) {
    document.getElementById('timer-display').classList.remove('hidden');
    startTimer();
  }
}

function startTimer() {
  timerInterval = setInterval(() => {
    timeRemaining--;
    updateTimerDisplay();

    if (timeRemaining <= 0) {
      clearInterval(timerInterval);
      isQuizActive = false; // Turn off protection before auto-submit
      Swal.fire({
        title: 'Waktu Habis!',
        text: 'Waktu pengerjaan telah selesai. Jawaban Anda akan dikirim otomatis.',
        icon: 'warning',
        allowOutsideClick: false,
        confirmButtonText: 'Oke',
        customClass: { popup: 'rounded-3xl' }
      }).then(() => {
        submitQuiz(true);
      });
    }
  }, 1000);
}

function updateTimerDisplay() {
  const minutes = Math.floor(timeRemaining / 60);
  const seconds = timeRemaining % 60;
  document.getElementById('time-left').textContent =
    `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
}

document.addEventListener('DOMContentLoaded', function () {
  const submitBtn = document.getElementById('submit-quiz-btn');
  if (submitBtn) {
    submitBtn.addEventListener('click', function () {
      submitQuiz();
    });
  }
});

function submitQuiz(autoSubmit = false) {
  const answers = [];
  const questionCards = document.querySelectorAll('.question-card-student');
  const formData = new FormData();
  let missingRequired = [];

  questionCards.forEach((card, index) => {
    const questionId = card.dataset.questionId;
    const type = card.dataset.questionType;
    const isRequired = card.dataset.required === 'true';
    let hasAnswer = false;

    if (type === 'MULTIPLE_CHOICE' || type === 'TRUE_FALSE') {
      const selected = card.querySelector(`input[name="question_${questionId}"]:checked`);
      if (selected) {
        answers.push({ question_id: parseInt(questionId), selected_option_id: parseInt(selected.value) });
        hasAnswer = true;
      }
    } else if (type === 'CHECKBOX') {
      const selected = Array.from(card.querySelectorAll(`input[name="question_${questionId}"]:checked`)).map(el => parseInt(el.value));
      if (selected.length > 0) {
        answers.push({ question_id: parseInt(questionId), selected_option_ids: selected });
        hasAnswer = true;
      }
    } else if (type === 'DROPDOWN') {
      const selected = card.querySelector(`select[name="question_${questionId}"]`).value;
      if (selected) {
        answers.push({ question_id: parseInt(questionId), selected_option_id: parseInt(selected) });
        hasAnswer = true;
      }
    } else if (type === 'LONG_TEXT') {
      const text = card.querySelector(`textarea[name="question_${questionId}"]`).value.trim();
      if (text) {
        answers.push({ question_id: parseInt(questionId), answer_text: text });
        hasAnswer = true;
      }
    } else if (type === 'UPLOAD') {
      const fileInput = card.querySelector(`input[name="question_${questionId}"]`);
      if (fileInput.files.length > 0) {
        const file = fileInput.files[0];
        const maxSize = parseInt(fileInput.dataset.maxSize) * 1024 * 1024;
        if (file.size > maxSize) {
          Swal.fire('File Terlalu Besar', `Maksimal ukuran file untuk pertanyaan ${index+1} adalah ${fileInput.dataset.maxSize}MB`, 'error');
          return;
        }
        formData.append(`file_${questionId}`, file);
        answers.push({ question_id: parseInt(questionId), type: 'UPLOAD' });
        hasAnswer = true;
      }
    }

    if (isRequired && !hasAnswer) {
      missingRequired.push(index + 1);
      card.classList.add('border-red-500');
    } else {
      card.classList.remove('border-red-500');
    }
  });

  if (!autoSubmit && missingRequired.length > 0) {
    Swal.fire({
      title: 'Wajib Diisi',
      text: `Pertanyaan nomor ${missingRequired.join(', ')} wajib dijawab sebelum dikirim.`,
      icon: 'error',
      customClass: { popup: 'rounded-3xl' }
    });
    return;
  }

  formData.append('answers', JSON.stringify(answers));

  if (autoSubmit) {
    sendAnswers(formData);
    return;
  }

  Swal.fire({
    title: 'Kirim Jawaban?',
    text: 'Apakah Anda yakin ingin mengirim semua jawaban sekarang?',
    icon: 'warning',
    showCancelButton: true,
    confirmButtonText: 'Ya, Kirim',
    cancelButtonText: 'Periksa Kembali',
    confirmButtonColor: 'var(--quiz-theme)',
    customClass: { popup: 'rounded-3xl', title: 'font-black' }
  }).then((result) => {
    if (result.isConfirmed) {
      sendAnswers(formData);
    }
  });
}

async function sendAnswers(formData) {
  isQuizActive = false;
  if (timerInterval) clearInterval(timerInterval);

  if (window.isPreview) {
    Swal.fire({
      icon: 'success',
      title: 'Terkirim (Mode Pratinjau)!',
      text: 'Ini adalah mode pratinjau, jawaban Anda tidak disimpan. Skor simulasi: 100%',
      confirmButtonText: 'Kembali ke Editor',
      customClass: { popup: 'rounded-3xl' }
    }).then(() => window.location.href = window.quizEditorUrl);
    return;
  }

  Swal.fire({ title: 'Mengirim...', allowOutsideClick: false, didOpen: () => Swal.showLoading() });
  try {
    const res = await fetch(`/api/quiz/${window.quizId}/submit`, {
      method: 'POST',
      body: formData
    });
    const data = await res.json();
    if (data.success) {
      Swal.fire({
        icon: 'success',
        title: 'Terkirim!',
        html: `<p class="mb-2">${window.quizConfirmationMessage || 'Jawaban Anda telah direkam.'}</p><p class="font-bold text-lg">Skor Anda: ${data.score.toFixed(1)}%</p>`,
        confirmButtonText: 'Kembali ke Kelas',
        customClass: { popup: 'rounded-3xl' }
      }).then(() => window.location.href = window.quizReturnUrl);
    } else { Swal.fire('Error', data.message, 'error'); }
  } catch (err) { Swal.fire('Error', 'Gagal terhubung ke server', 'error'); }
}
