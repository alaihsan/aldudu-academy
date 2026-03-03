/**
 * Quiz Editor JavaScript
 * Handles quiz question and option management
 */

const QuizEditor = {
  quizId: null,

  init() {
    // Get quiz ID from page
    const titleElement = document.querySelector('.quiz-title');
    if (titleElement) {
      this.quizId = titleElement.dataset.quizId;
    }
    
    this.bindEvents();
  },

  bindEvents() {
    // Title blur handler
    const titleElement = document.querySelector('.quiz-title');
    if (titleElement) {
      titleElement.addEventListener('blur', (e) => this.updateQuizTitle(e.target.textContent));
    }
  },

  // Add new question
  async addQuestion(type) {
    if (!this.quizId) {
      alert('Quiz ID tidak ditemukan');
      return;
    }

    // Convert type to match QuestionType enum values
    const typeMap = {
      'MULTIPLE_CHOICE': 'multiple_choice',
      'TRUE_FALSE': 'true_false',
      'LONG_TEXT': 'long_text'
    };

    try {
      const formData = new FormData();
      formData.append('question_type', typeMap[type] || 'multiple_choice');

      const response = await fetch(`/api/quiz/${this.quizId}/question/add`, {
        method: 'POST',
        body: formData
      });

      if (response.ok) {
        // Reload page to show new question
        window.location.reload();
      } else {
        const errorText = await response.text();
        console.error('Add question error:', errorText);
        alert('Gagal menambahkan pertanyaan');
      }
    } catch (error) {
      console.error('Add question failed:', error);
      alert('Terjadi kesalahan. Silakan coba lagi.');
    }
  },

  // Update question text
  async updateQuestionText(textarea) {
    const questionId = textarea.dataset.questionId;
    const text = textarea.value.trim();

    if (!text) {
      alert('Teks pertanyaan tidak boleh kosong');
      return;
    }

    this.showSaveIndicator();

    try {
      const response = await fetch(`/api/question/${questionId}/update`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ text })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          this.hideSaveIndicator();
        } else {
          alert(data.message || 'Gagal memperbarui pertanyaan');
        }
      } else {
        alert('Gagal memperbarui pertanyaan');
      }
    } catch (error) {
      console.error('Update question failed:', error);
      this.hideSaveIndicator();
    }
  },

  // Delete question
  async deleteQuestion(questionId) {
    if (!confirm('Hapus pertanyaan ini?')) return;

    try {
      const response = await fetch(`/api/question/${questionId}/delete`, {
        method: 'DELETE'
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          // Remove question card from DOM
          const card = document.querySelector(`[data-question-id="${questionId}"]`);
          if (card) {
            card.remove();
          }
          // Check if empty
          const list = document.getElementById('questions-list');
          if (list && list.querySelectorAll('.question-card').length === 0) {
            window.location.reload();
          }
        } else {
          alert(data.message || 'Gagal menghapus pertanyaan');
        }
      } else {
        alert('Gagal menghapus pertanyaan');
      }
    } catch (error) {
      console.error('Delete question failed:', error);
      alert('Terjadi kesalahan. Silakan coba lagi.');
    }
  },

  // Add option to multiple choice question
  async addOption(questionId) {
    try {
      const response = await fetch(`/api/question/${questionId}/option/add`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          option_text: 'Pilihan baru'
        })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          window.location.reload();
        } else {
          alert(data.message || 'Gagal menambahkan pilihan');
        }
      } else {
        alert('Gagal menambahkan pilihan');
      }
    } catch (error) {
      console.error('Add option failed:', error);
      alert('Terjadi kesalahan. Silakan coba lagi.');
    }
  },

  // Update option text
  async updateOptionText(input) {
    const optionId = input.dataset.optionId;
    const text = input.value.trim();

    if (!text) {
      alert('Teks pilihan tidak boleh kosong');
      return;
    }

    this.showSaveIndicator();

    try {
      const response = await fetch(`/api/option/${optionId}/update`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ text })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          this.hideSaveIndicator();
        }
      }
    } catch (error) {
      console.error('Update option failed:', error);
      this.hideSaveIndicator();
    }
  },

  // Delete option
  async deleteOption(optionId) {
    try {
      const response = await fetch(`/api/option/${optionId}/delete`, {
        method: 'DELETE'
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          window.location.reload();
        } else {
          alert(data.message || 'Gagal menghapus pilihan');
        }
      } else {
        alert('Gagal menghapus pilihan');
      }
    } catch (error) {
      console.error('Delete option failed:', error);
      alert('Terjadi kesalahan. Silakan coba lagi.');
    }
  },

  // Set correct option
  async setCorrectOption(optionId) {
    try {
      const response = await fetch(`/api/question/${optionId}/set-correct`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ option_id: optionId })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          window.location.reload();
        }
      }
    } catch (error) {
      console.error('Set correct failed:', error);
    }
  },

  // Update essay description
  async updateEssayDescription(textarea) {
    const questionId = textarea.dataset.questionId;
    const description = textarea.value.trim();

    this.showSaveIndicator();

    try {
      const response = await fetch(`/api/question/${questionId}/update-long-text-description`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ description })
      });

      if (response.ok) {
        this.hideSaveIndicator();
      }
    } catch (error) {
      console.error('Update description failed:', error);
      this.hideSaveIndicator();
    }
  },

  // Update quiz title
  async updateQuizTitle(title) {
    // This would need a new API endpoint
    console.log('Update quiz title:', title);
  },

  // Publish quiz
  async publishQuiz() {
    if (!confirm('Publikasikan kuis ini?')) return;
    
    // Redirect to course page
    window.location.href = document.referrer;
  },

  // Show save indicator
  showSaveIndicator() {
    const indicator = document.getElementById('save-indicator');
    if (indicator) {
      indicator.classList.add('visible');
    }
  },

  // Hide save indicator
  hideSaveIndicator() {
    const indicator = document.getElementById('save-indicator');
    if (indicator) {
      indicator.classList.remove('visible');
      setTimeout(() => {
        indicator.classList.remove('visible');
      }, 1000);
    }
  }
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  QuizEditor.init();
});

// Expose functions globally for inline handlers
window.addQuestion = QuizEditor.addQuestion.bind(QuizEditor);
window.updateQuestionText = QuizEditor.updateQuestionText.bind(QuizEditor);
window.deleteQuestion = QuizEditor.deleteQuestion.bind(QuizEditor);
window.addOption = QuizEditor.addOption.bind(QuizEditor);
window.updateOptionText = QuizEditor.updateOptionText.bind(QuizEditor);
window.deleteOption = QuizEditor.deleteOption.bind(QuizEditor);
window.setCorrectOption = QuizEditor.setCorrectOption.bind(QuizEditor);
window.updateEssayDescription = QuizEditor.updateEssayDescription.bind(QuizEditor);
window.publishQuiz = QuizEditor.publishQuiz.bind(QuizEditor);
