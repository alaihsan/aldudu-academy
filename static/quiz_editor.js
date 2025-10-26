document.addEventListener('DOMContentLoaded', () => {
    const quizContainer = document.getElementById('quiz-container');
    const addQuestionBtn = document.getElementById('add-question-btn');
    const container = document.querySelector('.container');
    const quizId = container.dataset.quizId;
    const courseId = container.dataset.courseId;

    let quizData = [];

    // --- Debounce function for autosaving ---
    const debounce = (func, delay) => {
        let timeout;
        return (...args) => {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), delay);
        };
    };

    // --- Autosave function ---
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
        } catch (error) {
            console.error('Error saving quiz:', error);
            // Optionally, show a non-blocking notification to the user
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
        
        // --- Question Number ---
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
                debouncedAutosave();
            });
            optionsContainer.appendChild(answerInput);
        }

        questionWrapper.appendChild(questionHeader);
        questionWrapper.appendChild(optionsContainer);
        
        // For animation
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
        debouncedAutosave();
    });

    // Initial render
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
});
