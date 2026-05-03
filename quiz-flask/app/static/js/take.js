const config = window.quizConfig;
let timer = config.durationSeconds || 0;
let interval = null;

function show(element) { element.classList.remove("hidden"); }
function hide(element) { element.classList.add("hidden"); }

document.getElementById("start-btn").addEventListener("click", async () => {
  const passwordInput = document.getElementById("quiz-password-input");
  if (passwordInput) {
    const response = await fetch(config.verifyUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password: passwordInput.value }),
    });
    const data = await response.json();
    if (!data.success) {
      show(document.getElementById("password-error"));
      return;
    }
  }

  hide(document.getElementById("start-screen"));
  show(document.getElementById("quiz-area"));
  if (timer > 0) {
    show(document.getElementById("timer"));
    tick();
    interval = setInterval(() => {
      timer -= 1;
      tick();
      if (timer <= 0) {
        clearInterval(interval);
        submitQuiz(true);
      }
    }, 1000);
  }
});

function tick() {
  const minutes = Math.floor(timer / 60);
  const seconds = timer % 60;
  document.getElementById("timer").textContent = `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

function collectAnswers() {
  const answers = [];
  const missing = [];
  document.querySelectorAll(".question-card").forEach((card, index) => {
    const id = parseInt(card.dataset.questionId, 10);
    const type = card.dataset.questionType;
    const required = card.dataset.required === "true";
    let answered = false;
    const item = { question_id: id };

    if (["MULTIPLE_CHOICE", "TRUE_FALSE"].includes(type)) {
      const selected = card.querySelector(`input[name="question_${id}"]:checked`);
      if (selected) {
        item.selected_option_id = parseInt(selected.value, 10);
        answered = true;
      }
    } else if (type === "CHECKBOX") {
      const selected = Array.from(card.querySelectorAll(`input[name="question_${id}"]:checked`)).map((input) => parseInt(input.value, 10));
      if (selected.length) {
        item.selected_option_ids = selected;
        answered = true;
      }
    } else if (type === "DROPDOWN") {
      const selected = card.querySelector(`select[name="question_${id}"]`).value;
      if (selected) {
        item.selected_option_id = parseInt(selected, 10);
        answered = true;
      }
    } else if (type === "MATCHING") {
      const pairs = {};
      card.querySelectorAll(".matching-select").forEach((select) => {
        if (select.value) pairs[select.dataset.left] = select.value;
      });
      if (Object.keys(pairs).length) {
        item.matching_answers = pairs;
        answered = true;
      }
    } else if (type === "LONG_TEXT") {
      const text = card.querySelector(`textarea[name="question_${id}"]`).value.trim();
      if (text) {
        item.answer_text = text;
        answered = true;
      }
    } else if (type === "UPLOAD") {
      const input = card.querySelector(`input[name="question_${id}"]`);
      if (input.files.length) {
        answered = true;
      }
    }

    if (answered) answers.push(item);
    if (required && !answered) missing.push(index + 1);
  });
  return { answers, missing };
}

async function submitQuiz(auto = false) {
  const { answers, missing } = collectAnswers();
  if (!auto && missing.length) {
    alert(`Pertanyaan wajib belum dijawab: ${missing.join(", ")}`);
    return;
  }
  if (!auto && !confirm("Kirim jawaban sekarang?")) return;
  if (config.isPreview) {
    alert("Mode pratinjau: jawaban tidak disimpan.");
    window.location.href = config.returnUrl;
    return;
  }

  const formData = new FormData();
  document.querySelectorAll(".question-card").forEach((card) => {
    const id = parseInt(card.dataset.questionId, 10);
    const input = card.querySelector(`input[type="file"][name="question_${id}"]`);
    if (input && input.files.length) formData.append(`file_${id}`, input.files[0]);
  });
  formData.append("answers", JSON.stringify(answers));

  const response = await fetch(config.submitUrl, { method: "POST", body: formData });
  const data = await response.json();
  if (!data.success) {
    alert(data.message || "Gagal mengirim jawaban.");
    return;
  }
  alert(`${config.message}\nSkor Anda: ${data.score.toFixed(1)}%`);
  window.location.href = config.returnUrl;
}

document.getElementById("submit-quiz").addEventListener("click", () => submitQuiz(false));
