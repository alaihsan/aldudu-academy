const config = window.quizConfig;
let timer = config.durationSeconds || 0;
let interval = null;

const UPLOAD_RULES = {
  document: {
    label: "Dokumen",
    extensions: ["pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt"],
    accept: [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt"],
  },
  image: {
    label: "Gambar",
    extensions: ["jpg", "jpeg", "png", "heic", "heif"],
    accept: [".jpg", ".jpeg", ".png", ".heic", ".heif", "image/jpeg", "image/png", "image/heic", "image/heif"],
  },
  video: {
    label: "Video",
    extensions: ["mp4", "avi", "mov", "hevc", "h265"],
    accept: [".mp4", ".avi", ".mov", ".hevc", ".h265", "video/mp4", "video/x-msvideo", "video/quicktime"],
  },
};

function show(element) { element.classList.remove("hidden"); }
function hide(element) { element.classList.add("hidden"); }

function uploadCategories(value) {
  const aliases = {
    dokumen: "document",
    document: "document",
    documents: "document",
    pdf: "document",
    doc: "document",
    xls: "document",
    ppt: "document",
    txt: "document",
    gambar: "image",
    image: "image",
    images: "image",
    jpg: "image",
    jpeg: "image",
    png: "image",
    heic: "image",
    heif: "image",
    video: "video",
    videos: "video",
    mp4: "video",
    avi: "video",
    mov: "video",
    hevc: "video",
    "h.265": "video",
    h265: "video",
  };
  const categories = String(value || "document")
    .split(/[;,]/)
    .map((item) => aliases[item.trim().toLowerCase()])
    .filter(Boolean);
  return [...new Set(categories)].length ? [...new Set(categories)] : ["document"];
}

function uploadExtensions(input) {
  return uploadCategories(input.dataset.fileTypes).flatMap((category) => UPLOAD_RULES[category].extensions);
}

function uploadLabels(input) {
  return uploadCategories(input.dataset.fileTypes).map((category) => UPLOAD_RULES[category].label);
}

function uploadMaxFiles(input) {
  const found = String(input.dataset.fileTypes || "")
    .split(/[;,]/)
    .map((item) => item.trim().toLowerCase())
    .find((item) => item.startsWith("max_files=") || item.startsWith("jumlah_file="));
  const amount = parseInt((found || "").split("=")[1] || "1", 10);
  return Math.min(10, Math.max(1, Number.isNaN(amount) ? 1 : amount));
}

function escapeHtml(value) {
  return String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function fileExtension(file) {
  const name = file?.name || "";
  if (name.toLowerCase().endsWith(".h.265")) return "h265";
  return name.includes(".") ? name.split(".").pop().toLowerCase().replace("h.265", "h265") : "";
}

function formatFileSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(bytes < 100 * 1024 ? 1 : 0)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
}

function uploadPreviewKind(extension) {
  if (UPLOAD_RULES.image.extensions.includes(extension)) return "image";
  if (UPLOAD_RULES.video.extensions.includes(extension)) return "video";
  return "document";
}

function renderUploadPreview(input) {
  const box = input.closest("[data-upload-box]");
  const preview = box?.querySelector("[data-upload-preview]");
  const files = Array.from(input.files || []);
  if (!box || !preview) return;
  if (!files.length) {
    preview.innerHTML = "";
    preview.classList.add("hidden");
    return;
  }

  preview.classList.remove("hidden");
  preview.innerHTML = files.map((file, index) => {
    const extension = fileExtension(file);
    const kind = uploadPreviewKind(extension);
    const label = UPLOAD_RULES[kind]?.label || "File";
    return `
      <article class="file-preview-card ${kind}">
        <span class="file-preview-type">${label} · ${escapeHtml(extension.toUpperCase() || "FILE")}</span>
        <strong>${escapeHtml(file.name)}</strong>
        <span>${formatFileSize(file.size)}</span>
        <button class="remove-upload-file" type="button" data-file-index="${index}">Hapus file</button>
      </article>
    `;
  }).join("");
}

function validateUploadInput(input) {
  const files = Array.from(input.files || []);
  if (!files.length) return "";
  const maxFiles = uploadMaxFiles(input);
  if (files.length > maxFiles) {
    return `Maksimal ${maxFiles} file.`;
  }
  const maxMb = parseInt(input.dataset.maxSize || "10", 10);
  for (const file of files) {
    if (file.size > maxMb * 1024 * 1024) {
      return `${file.name} melebihi batas ${maxMb} MB.`;
    }
    const extension = fileExtension(file);
    if (!uploadExtensions(input).includes(extension)) {
      return `${file.name} tidak sesuai. Gunakan: ${uploadLabels(input).join(", ")}.`;
    }
  }
  return "";
}

function prepareUploadInputs() {
  document.querySelectorAll(".upload-input").forEach((input) => {
    const categories = uploadCategories(input.dataset.fileTypes);
    input.accept = categories.flatMap((category) => UPLOAD_RULES[category].accept).join(",");
    const rule = input.closest("[data-upload-box]")?.querySelector("[data-upload-rule]");
    if (rule) {
      rule.textContent = `Maksimal ${uploadMaxFiles(input)} file. Diterima: ${uploadLabels(input).join(", ")}. Format: ${uploadExtensions(input).map((item) => item.toUpperCase()).join(", ")}.`;
    }
  });
}

function setUploadState(input) {
  const box = input.closest("[data-upload-box]");
  const name = box?.querySelector("[data-upload-name]");
  const error = box?.querySelector("[data-upload-error]");
  const files = Array.from(input.files || []);
  const message = validateUploadInput(input);
  box?.classList.remove("uploading", "invalid", "ready");
  if (error) {
    error.textContent = message;
    error.classList.toggle("hidden", !message);
  }
  if (!files.length) {
    if (name) name.textContent = "Belum ada file dipilih";
    renderUploadPreview(input);
    return;
  }
  if (name) name.textContent = `${files.length} file dipilih`;
  if (message) {
    box?.classList.add("invalid");
    input.value = "";
    renderUploadPreview(input);
    return;
  }
  renderUploadPreview(input);
  box?.classList.add("uploading");
  window.setTimeout(() => {
    box?.classList.remove("uploading");
    box?.classList.add("ready");
  }, 650);
}

function removeUploadFile(input, index) {
  const nextFiles = new DataTransfer();
  Array.from(input.files || []).forEach((file, fileIndex) => {
    if (fileIndex !== index) nextFiles.items.add(file);
  });
  input.files = nextFiles.files;
  setUploadState(input);
}

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

function isQuestionAnswered(card) {
  const id = parseInt(card.dataset.questionId, 10);
  const type = card.dataset.questionType;
  if (["MULTIPLE_CHOICE", "TRUE_FALSE", "LIKERT_SCALE"].includes(type)) {
    return Boolean(card.querySelector(`input[name="question_${id}"]:checked`));
  }
  if (type === "CHECKBOX") {
    return Boolean(card.querySelector(`input[name="question_${id}"]:checked`));
  }
  if (type === "DROPDOWN") {
    return Boolean(card.querySelector(`select[name="question_${id}"]`)?.value);
  }
  if (type === "MATCHING") {
    return Array.from(card.querySelectorAll(".matching-select")).some((select) => Boolean(select.value));
  }
  if (type === "LONG_TEXT") {
    return Boolean(card.querySelector(`textarea[name="question_${id}"]`)?.value.trim());
  }
  if (type === "UPLOAD") {
    return Boolean(card.querySelector(`input[name="question_${id}"]`)?.files.length);
  }
  return false;
}

function updateQuestionMap() {
  document.querySelectorAll(".question-card").forEach((card) => {
    const id = card.dataset.questionId;
    const mapButton = document.querySelector(`.question-map-button[data-target-question="${id}"]`);
    const doubtButton = card.querySelector(".doubt-toggle");
    const isDoubt = card.dataset.doubt === "true";
    const answered = isQuestionAnswered(card);
    mapButton?.classList.toggle("answered", answered && !isDoubt);
    mapButton?.classList.toggle("doubt", isDoubt);
    doubtButton?.classList.toggle("active", isDoubt);
  });
}

function responseSummary() {
  const cards = Array.from(document.querySelectorAll(".question-card"));
  return {
    answered: cards.filter(isQuestionAnswered).length,
    doubt: cards.filter((card) => card.dataset.doubt === "true").length,
  };
}

function showSubmitModal() {
  const modal = document.getElementById("submit-modal");
  const summary = responseSummary();
  document.getElementById("modal-answered-count").textContent = summary.answered;
  document.getElementById("modal-doubt-count").textContent = summary.doubt;
  modal.classList.remove("hidden");
  return new Promise((resolve) => {
    const cleanup = (value) => {
      modal.classList.add("hidden");
      document.getElementById("confirm-submit").removeEventListener("click", confirm);
      document.getElementById("cancel-submit").removeEventListener("click", cancel);
      modal.removeEventListener("click", backdrop);
      resolve(value);
    };
    const confirm = () => cleanup(true);
    const cancel = () => cleanup(false);
    const backdrop = (event) => {
      if (event.target === modal) cleanup(false);
    };
    document.getElementById("confirm-submit").addEventListener("click", confirm);
    document.getElementById("cancel-submit").addEventListener("click", cancel);
    modal.addEventListener("click", backdrop);
  });
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

    if (["MULTIPLE_CHOICE", "TRUE_FALSE", "LIKERT_SCALE"].includes(type)) {
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
      const message = validateUploadInput(input);
      if (message) {
        missing.push(`${index + 1} (${message})`);
        return;
      }
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
  if (!auto && !(await showSubmitModal())) return;
  if (config.isPreview) {
    window.location.href = config.returnUrl;
    return;
  }

  const formData = new FormData();
  document.querySelectorAll(".question-card").forEach((card) => {
    const id = parseInt(card.dataset.questionId, 10);
    const input = card.querySelector(`input[type="file"][name="question_${id}"]`);
    if (input && input.files.length) {
      Array.from(input.files).forEach((file) => formData.append(`file_${id}`, file));
    }
  });
  formData.append("answers", JSON.stringify(answers));

  const response = await fetch(config.submitUrl, { method: "POST", body: formData });
  const data = await response.json();
  if (!data.success) {
    alert(data.message || "Gagal mengirim jawaban.");
    return;
  }
  window.location.href = data.completion_url || config.returnUrl;
}

document.getElementById("submit-quiz").addEventListener("click", () => submitQuiz(false));
document.querySelectorAll(".question-map-button").forEach((button) => {
  button.addEventListener("click", () => {
    const card = document.querySelector(`.question-card[data-question-id="${button.dataset.targetQuestion}"]`);
    if (!card) return;
    const questionMap = document.querySelector(".question-map");
    const mapTop = questionMap ? questionMap.getBoundingClientRect().top : 18;
    const targetTop = card.getBoundingClientRect().top + window.scrollY - Math.max(12, mapTop);
    window.scrollTo({ top: Math.max(0, targetTop), behavior: "smooth" });
  });
});
document.querySelectorAll(".doubt-toggle").forEach((button) => {
  button.addEventListener("click", () => {
    const card = button.closest(".question-card");
    card.dataset.doubt = card.dataset.doubt === "true" ? "false" : "true";
    updateQuestionMap();
  });
});
document.getElementById("quiz-form").addEventListener("input", updateQuestionMap);
document.getElementById("quiz-form").addEventListener("change", updateQuestionMap);
prepareUploadInputs();
document.querySelectorAll(".upload-input").forEach((input) => {
  input.addEventListener("change", () => {
    setUploadState(input);
    updateQuestionMap();
  });
});
document.querySelectorAll("[data-upload-box]").forEach((box) => {
  box.addEventListener("click", (event) => {
    const button = event.target.closest(".remove-upload-file");
    if (!button) return;
    const input = box.querySelector(".upload-input");
    removeUploadFile(input, parseInt(button.dataset.fileIndex, 10));
    updateQuestionMap();
  });
});
updateQuestionMap();
