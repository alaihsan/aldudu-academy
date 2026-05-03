const shell = document.querySelector(".editor-shell");
const quizId = shell.dataset.quizId;
const questionsEl = document.getElementById("questions");
const saveState = document.getElementById("save-state");

let state = null;
let activeQuestionId = null;
let settingsTimer = null;
let questionTimer = null;
const LIKERT_DEFAULT_LABELS = ["Sangat tidak setuju", "Tidak setuju", "Netral", "Setuju", "Sangat setuju"];
const UPLOAD_TYPE_LABELS = {
  document: "Dokumen",
  image: "Gambar",
  video: "Video",
};

async function api(path, options = {}) {
  const response = await fetch(path, options);
  const data = await response.json();
  if (!response.ok || data.success === false) {
    throw new Error(data.message || "Request gagal");
  }
  return data;
}

function escapeHtml(value) {
  return String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function questionTypes() {
  return [
    ["MULTIPLE_CHOICE", "Pilihan Ganda", "○", "Satu jawaban benar"],
    ["CHECKBOX", "Kotak Centang", "☑", "Bisa lebih dari satu jawaban"],
    ["DROPDOWN", "Dropdown", "▾", "Pilih dari daftar"],
    ["TRUE_FALSE", "Benar / Salah", "✓", "Dua pilihan tetap"],
    ["MATCHING", "Menjodohkan", "↔", "Pasangkan pertanyaan dan jawaban"],
    ["LIKERT_SCALE", "Skala Likert", "★", "Rating 5 bintang"],
    ["LONG_TEXT", "Jawaban Singkat", "≡", "Jawaban teks/manual"],
    ["UPLOAD", "Upload File", "⇧", "Jawaban berupa file"],
  ];
}

function questionTypeMeta(type) {
  const found = questionTypes().find(([value]) => value === type);
  return found || questionTypes()[0];
}

function defaultOptionsForType(type) {
  if (type === "TRUE_FALSE") {
    return [
      { text: "Benar", is_correct: false, order: 1 },
      { text: "Salah", is_correct: false, order: 2 },
    ];
  }
  if (type === "MATCHING") {
    return [{ text: "Istilah = Pasangan", is_correct: true, order: 1 }];
  }
  if (type === "LIKERT_SCALE") {
    return LIKERT_DEFAULT_LABELS.map((label, index) => ({
      text: label,
      is_correct: false,
      order: index + 1,
    }));
  }
  if (["MULTIPLE_CHOICE", "CHECKBOX", "DROPDOWN"].includes(type)) {
    return [{ text: "Opsi 1", is_correct: false, order: 1 }];
  }
  return [];
}

function setSaveState(text) {
  if (saveState) saveState.textContent = text;
}

function setTheme(color) {
  shell.style.setProperty("--forms-theme", color || "#673ab7");
}

function getThemePayload() {
  return {
    theme_color: document.getElementById("theme-color").value,
    theme_font: document.getElementById("theme-font").value,
    theme_text_size: document.getElementById("theme-text-size").value,
    theme_background: document.getElementById("theme-background").value,
    theme_background_intensity: parseInt(document.getElementById("theme-background-intensity").value || "20", 10),
    theme_form_width: document.getElementById("theme-form-width").value,
    theme_card_radius: document.getElementById("theme-card-radius").value,
    theme_density: document.getElementById("theme-density").value,
  };
}

function applyTheme(theme) {
  setTheme(theme.theme_color);
  shell.dataset.themeFont = theme.theme_font;
  shell.dataset.themeTextSize = theme.theme_text_size;
  shell.dataset.themeBackground = theme.theme_background;
  shell.dataset.themeBackgroundIntensity = theme.theme_background_intensity;
  shell.dataset.themeFormWidth = theme.theme_form_width;
  shell.dataset.themeCardRadius = theme.theme_card_radius;
  shell.dataset.themeDensity = theme.theme_density;
  shell.style.setProperty("--theme-bg-opacity", String((theme.theme_background_intensity || 0) / 100));
}

function fillThemeControls(theme) {
  document.getElementById("theme-color").value = theme.theme_color || "#2563eb";
  document.getElementById("theme-font").value = theme.theme_font || "Inter";
  document.getElementById("theme-text-size").value = theme.theme_text_size || "normal";
  document.getElementById("theme-background").value = theme.theme_background || "plain";
  document.getElementById("theme-background-intensity").value = theme.theme_background_intensity ?? 20;
  document.getElementById("theme-form-width").value = theme.theme_form_width || "standard";
  document.getElementById("theme-card-radius").value = theme.theme_card_radius || "google";
  document.getElementById("theme-density").value = theme.theme_density || "normal";
}

function typeNeedsOptions(type) {
  return ["MULTIPLE_CHOICE", "CHECKBOX", "DROPDOWN", "TRUE_FALSE", "MATCHING", "LIKERT_SCALE"].includes(type);
}

function correctInputType(type) {
  return ["MULTIPLE_CHOICE", "DROPDOWN", "TRUE_FALSE"].includes(type) ? "radio" : "checkbox";
}

function preservesChoiceOptions(type) {
  return ["MULTIPLE_CHOICE", "CHECKBOX", "DROPDOWN"].includes(type);
}

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

function uploadMaxFiles(value) {
  const found = String(value || "")
    .split(/[;,]/)
    .map((item) => item.trim().toLowerCase())
    .find((item) => item.startsWith("max_files=") || item.startsWith("jumlah_file="));
  const amount = parseInt((found || "").split("=")[1] || "1", 10);
  return Math.min(10, Math.max(1, Number.isNaN(amount) ? 1 : amount));
}

function uploadConfigValue(card) {
  const categories = Array.from(card.querySelectorAll(".question-file-type-check:checked")).map((input) => input.value);
  const maxFiles = parseInt(card.querySelector(".question-max-files")?.value || "1", 10);
  return `${(categories.length ? categories : uploadCategories(card.querySelector(".question-file-types").value)).join(",")};max_files=${Math.min(10, Math.max(1, Number.isNaN(maxFiles) ? 1 : maxFiles))}`;
}

function uploadChecklistHtml(value) {
  const selected = uploadCategories(value);
  return Object.entries(UPLOAD_TYPE_LABELS).map(([category, label]) => `
    <label class="upload-type-check">
      <input class="question-file-type-check" type="checkbox" value="${category}" ${selected.includes(category) ? "checked" : ""}>
      <span>${label}</span>
    </label>
  `).join("");
}

function optionRowHtml(questionId, type, option = {}, index = 0) {
  const optionInputType = correctInputType(type);
  const isStandby = Boolean(option.standby);
  const pair = parseMatchingText(option.text || "");
  const placeholder = isStandby
    ? "Tambahkan opsi"
    : (type === "MATCHING" ? "Istilah = Pasangan" : "Opsi jawaban");
  if (type === "MATCHING") {
    return `
      <div class="option-row matching-option-row${isStandby ? " standby-option" : ""}" data-option-id="${option.id || ""}" ${isStandby ? 'data-standby="true"' : ""}>
        <input class="option-match-left" value="${escapeHtml(pair.left)}" placeholder="${isStandby ? "Tambahkan pertanyaan" : "Pertanyaan"}">
        <span class="match-separator">=</span>
        <input class="option-match-right" value="${escapeHtml(pair.right)}" placeholder="${isStandby ? "Tambahkan jawaban" : "Jawaban"}">
        <input class="option-text" type="hidden" value="${escapeHtml(option.text || "")}">
        <input class="option-correct" type="hidden" value="true" checked>
        <button class="remove-option ghost-icon" type="button" aria-label="Hapus opsi" ${isStandby ? "disabled" : ""}>x</button>
        <input class="option-order" type="hidden" value="${option.order || index + 1}">
      </div>
    `;
  }
  if (type === "LIKERT_SCALE") {
    return `
      <div class="option-row likert-option-row" data-option-id="${option.id || ""}">
        <span class="likert-star" aria-hidden="true">★</span>
        <input class="option-text" value="${escapeHtml(option.text || LIKERT_DEFAULT_LABELS[index] || "")}" placeholder="Nama pilihan">
        <input class="option-correct" type="hidden" value="false">
        <input class="option-order" type="hidden" value="${option.order || index + 1}">
      </div>
    `;
  }
  return `
    <div class="option-row${isStandby ? " standby-option" : ""}" data-option-id="${option.id || ""}" ${isStandby ? 'data-standby="true"' : ""}>
      <label class="correct-choice" title="Jawaban benar">
        <input type="${optionInputType}" name="correct_${questionId}" class="option-correct" ${option.is_correct ? "checked" : ""}>
      </label>
      <input class="option-text" value="${escapeHtml(option.text || "")}" placeholder="${placeholder}" data-empty-placeholder="${placeholder}">
      <button class="remove-option ghost-icon" type="button" aria-label="Hapus opsi" ${isStandby ? "disabled" : ""}>x</button>
      <input class="option-order" type="hidden" value="${option.order || index + 1}">
    </div>
  `;
}

function questionMediaHtml(question) {
  if (!question.image) return "";
  if (question.media_type === "video") {
    return `<video class="question-image question-video" src="${question.image_url}" controls preload="metadata"></video>`;
  }
  return `<img class="question-image" src="${question.image_url}" alt="Gambar soal">`;
}

function parseMatchingText(value) {
  const text = String(value || "");
  for (const separator of ["::", "=>", "->", "=", "|"]) {
    if (text.includes(separator)) {
      const [left, ...rightParts] = text.split(separator);
      return { left: left.trim(), right: rightParts.join(separator).trim() };
    }
  }
  return { left: text.trim(), right: "" };
}

function scheduleSettingsSave() {
  setSaveState("Menyimpan...");
  clearTimeout(settingsTimer);
  settingsTimer = setTimeout(() => {
    saveSettings().catch((error) => setSaveState(error.message));
  }, 700);
}

function scheduleQuestionSave(card, rerender = false) {
  setSaveState("Menyimpan...");
  clearTimeout(questionTimer);
  questionTimer = setTimeout(() => {
    saveQuestionCard(card, rerender).catch((error) => setSaveState(error.message));
  }, 700);
}

function renderQuestion(question, index) {
  const typeOptions = questionTypes().map(([value, label]) =>
    `<option value="${value}" ${question.type === value ? "selected" : ""}>${label}</option>`
  ).join("");
  const [, currentLabel, currentIcon] = questionTypeMeta(question.type);
  const typeMenu = questionTypes().map(([value, label, icon, description]) => `
    <button class="question-type-option" type="button" data-type="${value}">
      <span class="material-symbol">${icon}</span>
      <span>
        <strong>${label}</strong>
        <small>${description}</small>
      </span>
    </button>
  `).join("");
  const visibleOptions = question.type === "LIKERT_SCALE" ? (question.options || []).slice(0, 5) : (question.options || []);
  const options = visibleOptions.map((option, optionIndex) =>
    optionRowHtml(question.id, question.type, option, optionIndex)
  ).join("");
  const standbyOption = typeNeedsOptions(question.type) && question.type !== "LIKERT_SCALE"
    ? optionRowHtml(question.id, question.type, { standby: true }, (question.options || []).length)
    : "";
  const likertControls = question.type === "LIKERT_SCALE" ? `
    <div class="likert-config" aria-label="Rentang Skala Likert">
      <span>Default 5 bintang</span>
    </div>
  ` : "";
  const activeClass = activeQuestionId === question.id ? " active" : "";
  const help = question.type === "MATCHING"
    ? "Gunakan format kiri = kanan untuk setiap pasangan."
    : question.type === "LIKERT_SCALE"
      ? "Ubah nama setiap pilihan sesuai kebutuhan."
    : question.type === "LONG_TEXT"
      ? "Jawaban panjang disimpan untuk penilaian manual."
      : question.type === "UPLOAD"
        ? "Siswa akan mengunggah file sesuai batas ukuran."
        : "Centang pilihan yang menjadi jawaban benar.";

  return `
    <article class="question-editor${activeClass}" data-question-id="${question.id}" data-question-type="${question.type}" tabindex="0">
      <div class="question-editor-header">
        <textarea class="question-text" placeholder="Pertanyaan">${escapeHtml(question.text)}</textarea>
        <div class="type-select-wrap">
          <select class="question-type hidden-native-select" aria-label="Tipe pertanyaan">${typeOptions}</select>
          <button class="question-type-trigger" type="button" aria-haspopup="menu" aria-expanded="false">
            <span class="material-symbol">${currentIcon}</span>
            <span>${currentLabel}</span>
          </button>
          <div class="question-type-menu hidden" role="menu">${typeMenu}</div>
        </div>
      </div>
      <textarea class="question-description" rows="2" placeholder="Deskripsi atau petunjuk jawaban">${escapeHtml(question.description)}</textarea>
      ${questionMediaHtml(question)}
      <div class="question-meta-row ${question.type === "UPLOAD" ? "" : "hidden"}">
        <label>Maks file MB <input class="question-max-file" type="number" min="1" value="${question.max_file_size || 10}"></label>
        <label>Jumlah file <input class="question-max-files" type="number" min="1" max="10" value="${uploadMaxFiles(question.allowed_file_types)}"></label>
        <fieldset class="upload-types-field">
          <legend>Jenis file</legend>
          <div class="upload-types-list">${uploadChecklistHtml(question.allowed_file_types)}</div>
          <input class="question-file-types" type="hidden" value="${escapeHtml(uploadCategories(question.allowed_file_types).join(","))};max_files=${uploadMaxFiles(question.allowed_file_types)}">
        </fieldset>
      </div>
      <input class="question-max-file ${question.type === "UPLOAD" ? "hidden" : ""}" type="hidden" value="${question.max_file_size || 10}">
      <input class="question-file-types ${question.type === "UPLOAD" ? "hidden" : ""}" type="hidden" value="${escapeHtml(question.allowed_file_types || "")}">
      <div class="options-block ${typeNeedsOptions(question.type) ? "" : "hidden"}">
        ${likertControls}
        <div class="options">${options}${standbyOption}</div>
      </div>
      <p class="question-help muted">${help}</p>
      <div class="question-footer">
        <label class="check-row"><input class="question-required" type="checkbox" ${question.is_required ? "checked" : ""}> Wajib diisi</label>
        <label class="points-chip">Poin <input class="question-points" type="number" min="0" value="${question.points || 0}"></label>
      </div>
    </article>
  `;
}

function render() {
  if (!activeQuestionId && state.questions.length) {
    activeQuestionId = state.questions[0].id;
  }
  questionsEl.innerHTML = state.questions.map(renderQuestion).join("");
}

function readQuestion(card) {
  const type = card.querySelector(".question-type").value;
  return {
    text: card.querySelector(".question-text").value,
    type,
    description: card.querySelector(".question-description").value,
    points: parseInt(card.querySelector(".question-points").value || "0", 10),
    is_required: card.querySelector(".question-required").checked,
    max_file_size: parseInt(card.querySelector(".question-max-file").value || "10", 10),
    allowed_file_types: type === "UPLOAD" ? uploadConfigValue(card) : card.querySelector(".question-file-types").value,
    options: typeNeedsOptions(type) ? Array.from(card.querySelectorAll(".option-row")).map((row, index) => {
      const isMatching = row.classList.contains("matching-option-row");
      const left = isMatching ? row.querySelector(".option-match-left").value.trim() : "";
      const right = isMatching ? row.querySelector(".option-match-right").value.trim() : "";
      return {
        id: row.dataset.optionId ? parseInt(row.dataset.optionId, 10) : null,
        text: isMatching ? `${left} = ${right}` : row.querySelector(".option-text").value,
        is_correct: isMatching ? true : row.querySelector(".option-correct").checked,
        order: parseInt(row.querySelector(".option-order").value || String(index + 1), 10),
        has_content: isMatching ? Boolean(left || right) : Boolean(row.querySelector(".option-text").value.trim()),
      };
    }).filter((option) => option.id || option.has_content).map(({ has_content, ...option }) => option) : [],
  };
}

async function loadQuiz() {
  state = await api(`/api/quizzes/${quizId}`);
  fillThemeControls(state);
  applyTheme(state);
  document.getElementById("quiz-title-top").value = state.title;
  document.getElementById("confirmation-message").value = state.confirmation_message || "Terima kasih telah mengerjakan, jawaban kamu sudah direkam.";
  render();
  loadResponses().catch(() => {});
}

async function saveSettings() {
  const title = document.getElementById("quiz-title").value || document.getElementById("quiz-title-top").value;
  await api(`/api/quizzes/${quizId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      title,
      description: document.getElementById("quiz-description").value,
      duration_minutes: parseInt(document.getElementById("duration").value || "0", 10),
      max_attempts: parseInt(document.getElementById("max-attempts").value || "1", 10),
      quiz_password: document.getElementById("quiz-password").value,
      confirmation_message: document.getElementById("confirmation-message").value,
      ...getThemePayload(),
      shuffle_questions: document.getElementById("shuffle").checked,
    }),
  });
  await api(`/api/quizzes/${quizId}/status`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status: document.getElementById("quiz-status").value }),
  });
  document.getElementById("quiz-title-top").value = title;
  document.getElementById("quiz-title").value = title;
  applyTheme(getThemePayload());
  setSaveState("Perubahan tersimpan");
}

async function saveQuestionCard(card, rerender = false) {
  const questionId = card.dataset.questionId;
  const result = await api(`/api/questions/${questionId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(readQuestion(card)),
  });
  const index = state.questions.findIndex((item) => item.id === result.question.id);
  state.questions[index] = result.question;
  activeQuestionId = result.question.id;
  if (rerender) render();
  setSaveState("Perubahan tersimpan");
}

function setActiveCard(card) {
  if (!card) return;
  activeQuestionId = parseInt(card.dataset.questionId, 10);
  document.querySelectorAll(".question-editor").forEach((item) => item.classList.toggle("active", item === card));
}

function insertDescriptionMarkup(format) {
  const editor = document.getElementById("quiz-description-editor");
  editor.focus();
  const commands = {
    bold: ["bold"],
    italic: ["italic"],
    underline: ["underline"],
    numbered: ["insertOrderedList"],
    bullet: ["insertUnorderedList"],
    checklist: ["insertHTML", "<ul><li>☐ Tugas pertama</li></ul>"],
  };
  const [command, value = null] = commands[format] || commands.bold;
  document.execCommand(command, false, value);
  syncDescriptionValue();
  scheduleSettingsSave();
}

document.querySelectorAll(".description-toolbar button").forEach((button) => {
  button.addEventListener("click", () => insertDescriptionMarkup(button.dataset.format));
});

function syncDescriptionValue() {
  const editor = document.getElementById("quiz-description-editor");
  const textarea = document.getElementById("quiz-description");
  textarea.value = editor.innerHTML.trim();
}

document.getElementById("quiz-description-editor").addEventListener("input", () => {
  syncDescriptionValue();
  scheduleSettingsSave();
});

document.getElementById("quiz-title-top").addEventListener("input", (event) => {
  document.getElementById("quiz-title").value = event.target.value;
  scheduleSettingsSave();
});

document.getElementById("quiz-title").addEventListener("input", (event) => {
  document.getElementById("quiz-title-top").value = event.target.value;
  scheduleSettingsSave();
});

document.getElementById("theme-color").addEventListener("input", (event) => {
  applyTheme(getThemePayload());
  scheduleSettingsSave();
});

document.getElementById("theme-panel-toggle").addEventListener("click", () => {
  document.getElementById("theme-panel").classList.toggle("hidden");
});

document.getElementById("theme-panel-close").addEventListener("click", () => {
  document.getElementById("theme-panel").classList.add("hidden");
});

document.querySelectorAll(".color-presets button").forEach((button) => {
  button.addEventListener("click", () => {
    const color = button.dataset.color;
    document.getElementById("theme-color").value = color;
    applyTheme(getThemePayload());
    scheduleSettingsSave();
  });
});

[
  "theme-font",
  "theme-text-size",
  "theme-background",
  "theme-background-intensity",
  "theme-form-width",
  "theme-card-radius",
  "theme-density",
].forEach((id) => {
  const element = document.getElementById(id);
  element.addEventListener("input", () => {
    applyTheme(getThemePayload());
    scheduleSettingsSave();
  });
  element.addEventListener("change", () => {
    applyTheme(getThemePayload());
    scheduleSettingsSave();
  });
});

["quiz-status", "duration", "max-attempts", "quiz-password", "confirmation-message", "shuffle"].forEach((id) => {
  const element = document.getElementById(id);
  element.addEventListener("input", scheduleSettingsSave);
  element.addEventListener("change", scheduleSettingsSave);
});

document.querySelectorAll(".forms-tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".forms-tab").forEach((item) => item.classList.toggle("active", item === tab));
    for (const name of ["questions", "responses", "settings"]) {
      document.getElementById(`${name}-panel`).classList.toggle("hidden", tab.dataset.tab !== name);
    }
    document.querySelector(".forms-floating-toolbar").classList.toggle("hidden", tab.dataset.tab !== "questions");
    if (tab.dataset.tab === "responses") {
      loadResponses().catch((error) => setSaveState(error.message));
    }
  });
});

document.getElementById("add-question").addEventListener("click", async () => {
  const result = await api(`/api/quizzes/${quizId}/questions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ type: "MULTIPLE_CHOICE" }),
  });
  state.questions.push(result.question);
  activeQuestionId = result.question.id;
  render();
  document.querySelector(`[data-question-id="${activeQuestionId}"]`)?.scrollIntoView({ behavior: "smooth", block: "center" });
});

questionsEl.addEventListener("click", (event) => {
  const card = event.target.closest(".question-editor");
  if (!card) return;
  setActiveCard(card);

  if (event.target.classList.contains("remove-option")) {
    if (event.target.disabled) return;
    event.target.closest(".option-row").remove();
    scheduleQuestionSave(card, true);
  }

  const trigger = event.target.closest(".question-type-trigger");
  if (trigger) {
    const menu = trigger.parentElement.querySelector(".question-type-menu");
    document.querySelectorAll(".question-type-menu").forEach((item) => {
      if (item !== menu) item.classList.add("hidden");
    });
    menu.classList.toggle("hidden");
    trigger.setAttribute("aria-expanded", String(!menu.classList.contains("hidden")));
  }

  const typeOption = event.target.closest(".question-type-option");
  if (typeOption) {
    const select = card.querySelector(".question-type");
    select.value = typeOption.dataset.type;
    typeOption.closest(".question-type-menu").classList.add("hidden");
    select.dispatchEvent(new Event("change", { bubbles: true }));
  }
});

document.addEventListener("click", (event) => {
  if (event.target.closest(".type-select-wrap")) return;
  document.querySelectorAll(".question-type-menu").forEach((item) => item.classList.add("hidden"));
});

questionsEl.addEventListener("focusin", (event) => {
  setActiveCard(event.target.closest(".question-editor"));
  if (event.target.classList.contains("option-text") && !event.target.value.trim()) {
    event.target.dataset.emptyPlaceholder = event.target.placeholder;
    event.target.placeholder = "";
  }
});

questionsEl.addEventListener("focusout", (event) => {
  if (event.target.classList.contains("option-text") && !event.target.value.trim()) {
    event.target.placeholder = event.target.dataset.emptyPlaceholder || "Opsi jawaban";
  }
});

questionsEl.addEventListener("input", (event) => {
  const card = event.target.closest(".question-editor");
  if (!card) return;

  if (event.target.classList.contains("option-text") || event.target.classList.contains("option-match-left") || event.target.classList.contains("option-match-right")) {
    const row = event.target.closest(".option-row");
    const hasValue = row?.classList.contains("matching-option-row")
      ? row.querySelector(".option-match-left").value.trim() || row.querySelector(".option-match-right").value.trim()
      : event.target.value.trim();
    if (row?.dataset.standby === "true" && hasValue) {
      const type = card.querySelector(".question-type").value;
      delete row.dataset.standby;
      row.classList.remove("standby-option");
      row.querySelector(".remove-option").disabled = false;
      card.querySelector(".options").insertAdjacentHTML(
        "beforeend",
        optionRowHtml(card.dataset.questionId, type, { standby: true }, card.querySelectorAll(".option-row").length)
      );
    }
  }

  scheduleQuestionSave(card);
});

questionsEl.addEventListener("change", (event) => {
  const card = event.target.closest(".question-editor");
  if (!card) return;
  setActiveCard(card);

  if (event.target.classList.contains("question-type")) {
    const qtype = event.target.value;
    const oldType = card.dataset.questionType || "";
    const existingOptions = Array.from(card.querySelectorAll(".option-row:not(.standby-option)"));
    const shouldResetOptions =
      qtype === "MATCHING" ||
      oldType === "MATCHING" ||
      qtype === "TRUE_FALSE" ||
      qtype === "LIKERT_SCALE" ||
      oldType === "LIKERT_SCALE" ||
      !preservesChoiceOptions(oldType) ||
      !preservesChoiceOptions(qtype);

    if (typeNeedsOptions(qtype) && (shouldResetOptions || existingOptions.length === 0)) {
      card.querySelector(".options").innerHTML = defaultOptionsForType(qtype)
        .map((option, index) => optionRowHtml(card.dataset.questionId, qtype, option, index))
        .join("");
    }
    if (typeNeedsOptions(qtype) && qtype !== "LIKERT_SCALE" && !card.querySelector(".standby-option")) {
      card.querySelector(".options").insertAdjacentHTML(
        "beforeend",
        optionRowHtml(card.dataset.questionId, qtype, { standby: true }, card.querySelectorAll(".option-row").length)
      );
    }
    card.querySelector(".options-block").classList.toggle("hidden", !typeNeedsOptions(qtype));
    card.querySelector(".question-meta-row").classList.toggle("hidden", qtype !== "UPLOAD");
    card.dataset.questionType = qtype;
    scheduleQuestionSave(card, true);
    return;
  }

  scheduleQuestionSave(card);
});

async function duplicateActiveQuestion() {
  if (!activeQuestionId) return;
  const result = await api(`/api/questions/${activeQuestionId}/duplicate`, { method: "POST" });
  state.questions.push(result.question);
  activeQuestionId = result.question.id;
  render();
  document.querySelector(`[data-question-id="${activeQuestionId}"]`)?.scrollIntoView({ behavior: "smooth", block: "center" });
  setSaveState("Perubahan tersimpan");
}

async function deleteActiveQuestion() {
  if (!activeQuestionId || !confirm("Hapus soal aktif?")) return;
  await api(`/api/questions/${activeQuestionId}`, { method: "DELETE" });
  state.questions = state.questions.filter((item) => item.id !== activeQuestionId);
  activeQuestionId = state.questions[0]?.id || null;
  render();
  setSaveState("Perubahan tersimpan");
}

document.getElementById("duplicate-active").addEventListener("click", () => duplicateActiveQuestion().catch((error) => setSaveState(error.message)));
document.getElementById("delete-active").addEventListener("click", () => deleteActiveQuestion().catch((error) => setSaveState(error.message)));
document.getElementById("active-image-input").addEventListener("change", async (event) => {
  const file = event.target.files[0];
  if (!activeQuestionId || !file) return;
  const formData = new FormData();
  formData.append("image", file);
  const response = await fetch(`/api/questions/${activeQuestionId}/upload-image`, { method: "POST", body: formData });
  const result = await response.json();
  const index = state.questions.findIndex((item) => item.id === result.question.id);
  state.questions[index] = result.question;
  activeQuestionId = result.question.id;
  render();
  event.target.value = "";
  setSaveState("Perubahan tersimpan");
});

document.getElementById("active-video-input").addEventListener("change", async (event) => {
  const file = event.target.files[0];
  if (!activeQuestionId || !file) return;
  const formData = new FormData();
  formData.append("video", file);
  const response = await fetch(`/api/questions/${activeQuestionId}/upload-video`, { method: "POST", body: formData });
  const result = await response.json();
  if (!response.ok || result.success === false) {
    setSaveState(result.message || "Gagal mengunggah video");
    event.target.value = "";
    return;
  }
  const index = state.questions.findIndex((item) => item.id === result.question.id);
  state.questions[index] = result.question;
  activeQuestionId = result.question.id;
  render();
  event.target.value = "";
  setSaveState("Perubahan tersimpan");
});

async function loadResponses() {
  const stats = await api(`/api/quizzes/${quizId}/stats`);
  document.getElementById("responses-count").textContent = stats.total_submissions;
  document.getElementById("stats").innerHTML = `
    <div class="responses-summary">
      <article><span>Total Respons</span><strong>${stats.total_submissions}</strong></article>
      <article><span>Rata-rata</span><strong>${stats.average_score}%</strong></article>
      <article><span>Tertinggi</span><strong>${stats.max_score}%</strong></article>
      <article><span>Terendah</span><strong>${stats.min_score}%</strong></article>
    </div>
    <div class="responses-actions">
      <a class="button" href="${stats.download_url}">Download XLSX</a>
    </div>
    <section class="responses-block">
      <h3>Ringkasan Pertanyaan</h3>
      <div class="question-response-list">
        ${stats.questions.map((question, index) => `
          <article>
            <span>${index + 1}</span>
            <strong>${escapeHtml(question.text)}</strong>
            <small>${question.answered} jawaban</small>
          </article>
        `).join("") || `<p class="muted">Belum ada pertanyaan.</p>`}
      </div>
    </section>
    <section class="responses-block">
      <h3>Respons Murid</h3>
      <div class="submission-list">
        ${stats.submissions.map((item) => `
          <details class="submission-response-card">
            <summary>
              <span>
                <strong>${escapeHtml(item.student_name)}</strong>
                <small>${escapeHtml(item.student_email)} · ${item.submitted_at}</small>
              </span>
              <b>${item.score}%</b>
            </summary>
            <div class="submission-answers">
              ${item.answers.map((answer) => `
                <article>
                  <strong>${escapeHtml(answer.question)}</strong>
                  <p>${escapeHtml(answer.answer || "-")}</p>
                  ${(answer.attachments || []).length ? `
                    <div class="response-file-list">
                      ${answer.attachments.map((file) => `
                        <span>
                          <strong>${escapeHtml(file.name)}</strong>
                          <a href="${file.url}" target="_blank">Lihat</a>
                          <a href="${file.download_url}">Download</a>
                        </span>
                      `).join("")}
                    </div>
                  ` : ""}
                </article>
              `).join("")}
              <a href="/quiz/${quizId}/submissions/${item.id}">Buka detail</a>
            </div>
          </details>
        `).join("") || `<p class="muted">Belum ada jawaban murid.</p>`}
      </div>
    </section>
    <section class="responses-block">
      <div class="section-head sheet-head">
        <div>
          <h3>Preview Sheets</h3>
          <p class="muted">Tabel ini mengikuti format file XLSX yang bisa diunduh.</p>
        </div>
      </div>
      <div class="sheet-preview">
        <table>
          <thead><tr>${stats.sheet.headers.map((header) => `<th>${escapeHtml(header)}</th>`).join("")}</tr></thead>
          <tbody>
            ${stats.sheet.rows.map((row) => `<tr>${row.map((cell) => `<td>${escapeHtml(cell)}</td>`).join("")}</tr>`).join("") || `<tr><td colspan="${stats.sheet.headers.length}">Belum ada data.</td></tr>`}
          </tbody>
        </table>
      </div>
    </section>
  `;
}

document.getElementById("load-stats").addEventListener("click", () => loadResponses().catch((error) => setSaveState(error.message)));

document.getElementById("docx-import-button").addEventListener("click", async () => {
  const input = document.getElementById("docx-import-input");
  const resultEl = document.getElementById("docx-import-result");
  const file = input.files[0];
  if (!file) {
    resultEl.textContent = "Pilih file .docx terlebih dahulu.";
    return;
  }
  const formData = new FormData();
  formData.append("file", file);
  resultEl.textContent = "Mengimpor soal...";
  try {
    const result = await api(`/api/quizzes/${quizId}/import-docx`, { method: "POST", body: formData });
    resultEl.textContent = `${result.imported_count} soal berhasil diimpor.${(result.warnings || []).length ? ` Catatan: ${result.warnings.join(" ")}` : ""}`;
    input.value = "";
    await loadQuiz();
    document.querySelector('[data-tab="questions"]').click();
  } catch (error) {
    resultEl.textContent = error.message;
  }
});

loadQuiz().catch((error) => alert(error.message));
