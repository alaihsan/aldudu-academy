document.addEventListener('DOMContentLoaded', () => {
    const quizContainer = document.getElementById('quiz-container');
    const addQuestionBtn = document.getElementById('add-question-btn');
    const saveQuizBtn = document.getElementById('save-quiz-btn');
    const container = document.querySelector('.container');
    const quizId = container.dataset.quizId;
    const courseId = container.dataset.courseId;

    const recoveryBanner = document.getElementById('recovery-banner');
    const restoreBtn = document.getElementById('restore-btn');
    const discardBtn = document.getElementById('discard-btn');

    const localStorageKey = `quiz-draft-${quizId}`;

    let quizData = [];

    const saveToLocalStorage = () => {
        localStorage.setItem(localStorageKey, JSON.stringify(quizData));
    };

    const loadFromLocalStorage = () => {
        const savedData = localStorage.getItem(localStorageKey);
        if (savedData) {
            quizData = JSON.parse(savedData);
            // Ensure image_path is present for older saved data
            quizData.forEach(q => {
                if (!q.hasOwnProperty('image_path')) {
                    q.image_path = null;
                }
            });
            renderQuiz();
        }
    };

    const clearLocalStorage = () => {
        localStorage.removeItem(localStorageKey);
    };

    const debounce = (func, delay) => {
        let timeout;
        return (...args) => {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), delay);
        };
    };

    const autosave = async () => {
        try {
            const response = await fetch(`/api/quiz/${quizId}/save-questions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(quizData),
            });

            if (!response.ok) {
                throw new Error('Failed to save the quiz.');
            }
            console.log('Quiz saved automatically.');
            clearLocalStorage(); // Clear local storage on successful save
        } catch (error) {
            console.error('Error saving quiz:', error);
        }
    };

    const debouncedAutosave = debounce(autosave, 500);

    const questionTypes = {
        'multiple_choice': {
            text: 'Pilihan Ganda',
            defaultOptions: [{ text: 'Opsi 1' }],
            defaultAnswer: []
        },
        'true_false': {
            text: 'Benar/Salah',
            defaultOptions: [{ text: 'Benar' }, { text: 'Salah' }],
            defaultAnswer: ''
        },
        'long_text': {
            text: 'Jawaban Panjang',
            defaultOptions: [],
            defaultAnswer: ''
        }
    };

    const uploadImage = async (questionId, file, imagePreviewElement, uploadProgressElement) => {
        const formData = new FormData();
        formData.append('file', file);

        try {
            uploadProgressElement.style.width = '0%';
            uploadProgressElement.style.display = 'block';

            const xhr = new XMLHttpRequest();
            xhr.open('POST', `/api/question/${questionId}/image`);
            xhr.upload.addEventListener('progress', (event) => {
                if (event.lengthComputable) {
                    const percent = (event.loaded / event.total) * 100;
                    uploadProgressElement.style.width = `${percent}%`;
                }
            });
            xhr.addEventListener('load', () => {
                uploadProgressElement.style.display = 'none';
                if (xhr.status === 200) {
                    const response = JSON.parse(xhr.responseText);
                    if (response.success) {
                        imagePreviewElement.innerHTML = `<img src="${response.image_path}" alt="Question Image" class="question-image">`;
                        const questionIndex = quizData.findIndex(q => q.id === questionId);
                        if (questionIndex !== -1) {
                            quizData[questionIndex].image_path = response.image_path.split('/').slice(2).join('/'); // Store relative path
                            saveToLocalStorage();
                            debouncedAutosave();
                        }
                    } else {
                        alert(`Error uploading image: ${response.message}`);
                    }
                } else {
                    alert(`Error uploading image: ${xhr.statusText}`);
                }
            });
            xhr.addEventListener('error', () => {
                uploadProgressElement.style.display = 'none';
                alert('Error uploading image.');
            });
            xhr.send(formData);

        } catch (error) {
            console.error('Error uploading image:', error);
            alert('Error uploading image.');
        }
    };

    const createQuestionElement = (question, index) => {
        const questionWrapper = document.createElement('div');
        questionWrapper.className = 'question-wrapper';
        questionWrapper.dataset.index = index;

        const questionHeader = document.createElement('div');
        questionHeader.className = 'question-header';
        
        const questionNumber = document.createElement('div');
        questionNumber.className = 'question-number';
        questionNumber.textContent = `${index + 1}.`;

        const questionText = document.createElement('input');
        questionText.type = 'text';
        questionText.className = 'question-text';
        questionText.placeholder = 'Question';
        questionText.value = question.text || '';
        questionText.addEventListener('input', (e) => {
            quizData[index].text = e.target.value;
            saveToLocalStorage();
            debouncedAutosave();
        });

        const addImageBtn = document.createElement('button');
        addImageBtn.className = 'btn-icon';
        addImageBtn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-image"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>';
        addImageBtn.addEventListener('click', () => {
            fileInput.click();
        });

        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.style.display = 'none';
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                uploadImage(question.id, e.target.files[0], imagePreview, uploadProgress);
            }
        });

        const questionTypeSelector = document.createElement('select');
        questionTypeSelector.className = 'question-type-selector';
        for (const type in questionTypes) {
            const option = document.createElement('option');
            option.value = type;
            option.textContent = questionTypes[type].text;
            if (question.type === type) {
                option.selected = true;
            }
            questionTypeSelector.appendChild(option);
        }

        questionTypeSelector.addEventListener('change', (e) => {
            const newType = e.target.value;
            quizData[index].type = newType;
            quizData[index].options = JSON.parse(JSON.stringify(questionTypes[newType].defaultOptions));
            quizData[index].answer = JSON.parse(JSON.stringify(questionTypes[newType].defaultAnswer));
            renderQuiz();
            saveToLocalStorage();
            debouncedAutosave();
        });

        const deleteQuestionBtn = document.createElement('button');
        deleteQuestionBtn.className = 'delete-question-btn';
        deleteQuestionBtn.textContent = 'Hapus';
        deleteQuestionBtn.addEventListener('click', () => {
            questionWrapper.classList.add('deleting');
            questionWrapper.addEventListener('animationend', () => {
                quizData.splice(index, 1);
                renderQuiz();
                saveToLocalStorage();
                debouncedAutosave();
            });
        });

        questionHeader.appendChild(questionNumber);
        questionHeader.appendChild(questionText);
        questionHeader.appendChild(addImageBtn);
        questionHeader.appendChild(fileInput);
        questionHeader.appendChild(questionTypeSelector);
        questionHeader.appendChild(deleteQuestionBtn);

        const imagePreview = document.createElement('div');
        imagePreview.className = 'image-preview-container';
        if (question.image_path) {
            const img = document.createElement('img');
            img.src = `/uploads/${question.image_path}`;
            img.alt = 'Question Image';
            img.className = 'question-image';
            imagePreview.appendChild(img);
        }

        const uploadProgress = document.createElement('div');
        uploadProgress.className = 'upload-progress';

        const optionsContainer = document.createElement('div');
        optionsContainer.className = 'options-container';

        if (question.type === 'multiple_choice' || question.type === 'true_false') {
            question.options.forEach((option, optionIndex) => {
                const optionWrapper = document.createElement('div');
                optionWrapper.className = 'option-wrapper';

                const optionInput = document.createElement('input');
                optionInput.type = 'text';
                optionInput.className = 'option-text';
                optionInput.value = option.text;
                optionInput.addEventListener('input', (e) => {
                    quizData[index].options[optionIndex].text = e.target.value;
                    saveToLocalStorage();
                    debouncedAutosave();
                });

                const answerCheckbox = document.createElement('input');
                if (question.type === 'multiple_choice') {
                    answerCheckbox.type = 'checkbox';
                    if (quizData[index].answer.includes(optionIndex)) {
                        answerCheckbox.checked = true;
                    }
                    answerCheckbox.addEventListener('change', (e) => {
                        if (e.target.checked) {
                            quizData[index].answer.push(optionIndex);
                        } else {
                            quizData[index].answer = quizData[index].answer.filter(i => i !== optionIndex);
                        }
                        saveToLocalStorage();
                        debouncedAutosave();
                    });
                } else { // true_false
                    answerCheckbox.type = 'radio';
                    answerCheckbox.name = `answer-${index}`;
                    if (quizData[index].answer === optionIndex) {
                        answerCheckbox.checked = true;
                    }
                    answerCheckbox.addEventListener('change', (e) => {
                        if (e.target.checked) {
                            quizData[index].answer = optionIndex;
                        }
                        saveToLocalStorage();
                        debouncedAutosave();
                    });
                }

                optionWrapper.appendChild(answerCheckbox);
                optionWrapper.appendChild(optionInput);

                if (question.type === 'multiple_choice') {
                    const deleteOptionBtn = document.createElement('button');
                    deleteOptionBtn.className = 'delete-option-btn';
                    deleteOptionBtn.textContent = 'x';
                    deleteOptionBtn.addEventListener('click', () => {
                        quizData[index].options.splice(optionIndex, 1);
                        renderQuiz();
                        saveToLocalStorage();
                        debouncedAutosave();
                    });
                    optionWrapper.appendChild(deleteOptionBtn);
                }

                optionsContainer.appendChild(optionWrapper);
            });

            if (question.type === 'multiple_choice') {
                const addOptionBtn = document.createElement('button');
                addOptionBtn.className = 'add-option-btn';
                addOptionBtn.textContent = 'Tambah Opsi';
                addOptionBtn.addEventListener('click', () => {
                    quizData[index].options.push({ text: `Opsi ${quizData[index].options.length + 1}` });
                    renderQuiz();
                    saveToLocalStorage();
                    debouncedAutosave();
                });
                optionsContainer.appendChild(addOptionBtn);
            }
        } else if (question.type === 'long_text') {
            const descriptionTextarea = document.createElement('textarea');
            descriptionTextarea.className = 'long-text-description';
            descriptionTextarea.placeholder = 'Masukkan deskripsi untuk pertanyaan jawaban panjang...';
            descriptionTextarea.value = question.description || '';
            descriptionTextarea.rows = 4;
            descriptionTextarea.maxLength = 1000;
            descriptionTextarea.addEventListener('input', (e) => {
                quizData[index].description = e.target.value;
                saveToLocalStorage();
                debouncedAutosave();
            });
            optionsContainer.appendChild(descriptionTextarea);
        }

        questionWrapper.appendChild(questionHeader);
        questionWrapper.appendChild(imagePreview);
        questionWrapper.appendChild(uploadProgress);
        questionWrapper.appendChild(optionsContainer);
        
        setTimeout(() => {
            questionWrapper.classList.add('visible');
        }, 10);

        return questionWrapper;
    };

    const renderQuiz = () => {
        quizContainer.innerHTML = '';
        quizData.forEach((question, index) => {
            const questionElement = createQuestionElement(question, index);
            quizContainer.appendChild(questionElement);
        });
    };

    addQuestionBtn.addEventListener('click', async () => {
        try {
            const response = await fetch(`/api/quiz/${quizId}/question/add-json`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                throw new Error('Failed to add a new question.');
            }

            const newQuestion = await response.json();
            quizData.push({
                id: newQuestion.id,
                type: newQuestion.type,
                text: newQuestion.text,
                options: newQuestion.options,
                answer: newQuestion.answer,
                image_path: newQuestion.image_path || null
            });
            renderQuiz();
            saveToLocalStorage();
            debouncedAutosave();
        } catch (error) {
            console.error('Error adding question:', error);
            alert('Gagal menambahkan pertanyaan baru.');
        }
    });

    saveQuizBtn.addEventListener('click', async () => {
        try {
            await autosave();
            alert('Kuis berhasil disimpan!');
        } catch (error) {
            alert('Gagal menyimpan kuis.');
        }
    });

    // Initial Load
    const savedData = localStorage.getItem(localStorageKey);
    if (savedData) {
        recoveryBanner.style.display = 'block';
    } else {
        // In a real app, you would fetch the initial quiz data here
        // For now, we start with one empty question
        if (quizData.length === 0) {
            quizData.push({
                type: 'multiple_choice',
                text: '',
                options: [{ text: 'Opsi 1' }],
                answer: [],
                image_path: null
            });
        }
        renderQuiz();
    }

    restoreBtn.addEventListener('click', () => {
        loadFromLocalStorage();
        recoveryBanner.style.display = 'none';
    });

    discardBtn.addEventListener('click', () => {
        clearLocalStorage();
        recoveryBanner.style.display = 'none';
        // Optionally, reload the page to get the original server data
        window.location.reload();
    });
});
