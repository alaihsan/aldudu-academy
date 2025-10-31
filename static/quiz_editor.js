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
            text: 'Multiple Choice',
            defaultOptions: [{ text: 'Option 1' }],
            defaultAnswer: []
        },
        'true_false': {
            text: 'True/False',
            defaultOptions: [{ text: 'True' }, { text: 'False' }],
            defaultAnswer: ''
        },
        'short_answer': {
            text: 'Short Answer',
            defaultOptions: [],
            defaultAnswer: ''
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
        deleteQuestionBtn.textContent = 'Delete';
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
        questionHeader.appendChild(questionTypeSelector);
        questionHeader.appendChild(deleteQuestionBtn);

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
                addOptionBtn.textContent = 'Add Option';
                addOptionBtn.addEventListener('click', () => {
                    quizData[index].options.push({ text: `Option ${quizData[index].options.length + 1}` });
                    renderQuiz();
                    saveToLocalStorage();
                    debouncedAutosave();
                });
                optionsContainer.appendChild(addOptionBtn);
            }
        } else if (question.type === 'short_answer') {
            const answerInput = document.createElement('input');
            answerInput.type = 'text';
            answerInput.className = 'short-answer-input';
            answerInput.placeholder = 'Correct Answer';
            answerInput.value = question.answer || '';
            answerInput.addEventListener('input', (e) => {
                quizData[index].answer = e.target.value;
                saveToLocalStorage();
                debouncedAutosave();
            });
            optionsContainer.appendChild(answerInput);
        }

        questionWrapper.appendChild(questionHeader);
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

    addQuestionBtn.addEventListener('click', () => {
        quizData.push({
            type: 'multiple_choice',
            text: '',
            options: [{ text: 'Option 1' }],
            answer: []
        });
        renderQuiz();
        saveToLocalStorage();
        debouncedAutosave();
    });

    saveQuizBtn.addEventListener('click', async () => {
        try {
            await autosave();
            alert('Quiz saved successfully!');
        } catch (error) {
            alert('Failed to save quiz.');
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
                options: [{ text: 'Option 1' }],
                answer: []
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
