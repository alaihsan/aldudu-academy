// Quiz Student JavaScript for enhanced UX

document.addEventListener('DOMContentLoaded', function() {
    // Character counter for long text questions
    const textareas = document.querySelectorAll('.form-textarea');
    textareas.forEach(textarea => {
        const counter = textarea.parentElement.querySelector('.character-count');
        if (counter) {
            textarea.addEventListener('input', function() {
                const count = this.value.length;
                const max = this.getAttribute('maxlength') || 5000;
                counter.textContent = `${count}/${max} karakter`;

                // Change color when approaching limit
                if (count > max * 0.9) {
                    counter.style.color = '#ef4444'; // red
                } else if (count > max * 0.8) {
                    counter.style.color = '#f59e0b'; // yellow
                } else {
                    counter.style.color = 'var(--text-secondary-color)';
                }
            });

            // Initialize counter
            textarea.dispatchEvent(new Event('input'));
        }
    });

    // Enhanced radio button interactions
    const optionItems = document.querySelectorAll('.option-item');
    optionItems.forEach(item => {
        item.addEventListener('click', function(e) {
            // Don't trigger if clicking on the radio input itself
            if (e.target.type === 'radio') return;

            const radio = this.querySelector('input[type="radio"]');
            if (radio) {
                radio.checked = true;

                // Add visual feedback
                this.style.transform = 'scale(0.98)';
                setTimeout(() => {
                    this.style.transform = '';
                }, 150);
            }
        });
    });

    // Smooth scrolling for question navigation
    const questionCards = document.querySelectorAll('.question-card');
    if (questionCards.length > 0) {
        // Add subtle entrance animation
        questionCards.forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';

            setTimeout(() => {
                card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, index * 100);
        });
    }

    // Quiz submission validation
    const submitBtn = document.getElementById('submit-quiz-btn');
    if (submitBtn) {
        submitBtn.addEventListener('click', function(e) {
            // Basic validation - check if at least one question is answered
            const totalQuestions = document.querySelectorAll('.question-card').length;
            const answeredQuestions = document.querySelectorAll('input[type="radio"]:checked, textarea:not(:placeholder-shown)').length;

            if (answeredQuestions === 0) {
                e.preventDefault();
                showNotification('Silakan jawab setidaknya satu pertanyaan sebelum mengirim.', 'warning');
                return false;
            }

            // Show loading state
            this.disabled = true;
            this.innerHTML = '<svg class="animate-spin" style="width: 20px; height: 20px; margin-right: 8px;" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>Mengirim...';
        });
    }

    // Notification system
    function showNotification(message, type = 'info') {
        // Remove existing notifications
        const existingNotifications = document.querySelectorAll('.quiz-notification');
        existingNotifications.forEach(notif => notif.remove());

        // Create notification element
        const notification = document.createElement('div');
        notification.className = `quiz-notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <div class="notification-icon">
                    ${type === 'warning' ? '⚠️' : type === 'success' ? '✅' : 'ℹ️'}
                </div>
                <p>${message}</p>
                <button class="notification-close">&times;</button>
            </div>
        `;

        // Add to page
        document.body.appendChild(notification);

        // Show with animation
        setTimeout(() => notification.classList.add('show'), 10);

        // Auto hide after 5 seconds
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 5000);

        // Close button
        notification.querySelector('.notification-close').addEventListener('click', () => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        });
    }
});

// Image preview functionality for quiz questions
document.addEventListener('DOMContentLoaded', function() {
    // Handle image upload preview
    const fileInputs = document.querySelectorAll('input[type="file"][name="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function(e) {
            const file = e.target.files[0];
            const questionId = this.id.replace('file-upload-', '');
            const previewContainer = document.getElementById(`image-preview-${questionId}`);

            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    // Show preview immediately
                    previewContainer.innerHTML = `
                        <img src="${e.target.result}" alt="Preview" class="question-image" style="max-width: 100%; max-height: 400px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    `;
                };
                reader.readAsDataURL(file);
            } else {
                // Reset to placeholder if no file selected
                previewContainer.innerHTML = `
                    <div class="image-placeholder">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 15.75l5.159-5.159a2.25 2.25 0 0 1 3.182 0l5.159 5.159m-1.5-1.5 1.409-1.409a2.25 2.25 0 0 1 3.182 0l2.909 2.909m-18 3.75h16.5a1.5 1.5 0 0 0 1.5-1.5V6a1.5 1.5 0 0 0-1.5-1.5H3.75A1.5 1.5 0 0 0 2.25 6v12a1.5 1.5 0 0 0 1.5 1.5Zm10.5-11.25h.008v.008h-.008V8.25Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Z" />
                        </svg>
                        <p>Klik tombol gambar di atas untuk menambah gambar</p>
                    </div>
                `;
            }
        });
    });
});

// Add notification styles dynamically
const notificationStyles = `
<style>
.quiz-notification {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 1000;
    max-width: 400px;
    opacity: 0;
    transform: translateX(100%);
    transition: all 0.3s ease;
}

.quiz-notification.show {
    opacity: 1;
    transform: translateX(0);
}

.notification-content {
    background: white;
    border-radius: 12px;
    padding: 1rem;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
    border-left: 4px solid var(--primary-color);
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.notification-warning .notification-content {
    border-left-color: #f59e0b;
}

.notification-success .notification-content {
    border-left-color: var(--success-color);
}

.notification-icon {
    font-size: 1.25rem;
    flex-shrink: 0;
}

.notification-content p {
    margin: 0;
    flex: 1;
    font-weight: 500;
}

.notification-close {
    background: none;
    border: none;
    font-size: 1.5rem;
    cursor: pointer;
    color: var(--text-secondary-color);
    padding: 0;
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    transition: all 0.2s ease;
}

.notification-close:hover {
    background: rgba(0, 0, 0, 0.1);
    color: var(--text-primary-color);
}

.animate-spin {
    animation: spin 1s linear infinite;
}

@keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

@media (max-width: 768px) {
    .quiz-notification {
        left: 20px;
        right: 20px;
        max-width: none;
    }
}
</style>
`;

// Inject styles
document.head.insertAdjacentHTML('beforeend', notificationStyles);
