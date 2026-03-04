document.addEventListener('DOMContentLoaded', function () {
    const courseId = document.querySelector('.container').dataset.courseId;
    const currentUserId = document.body.dataset.userId;

    const showCreateDiscussionModal = document.getElementById('show-create-discussion-modal');
    const createDiscussionModal = document.getElementById('create-discussion-modal');
    const discussionCancelButton = document.getElementById('discussion-cancel-button');
    const createDiscussionForm = document.getElementById('create-discussion-form');
    const discussionsContainer = document.getElementById('discussions-container');

    if (showCreateDiscussionModal) {
        showCreateDiscussionModal.addEventListener('click', () => {
            createDiscussionModal.classList.remove('hidden');
        });
    }

    if (discussionCancelButton) {
        discussionCancelButton.addEventListener('click', () => {
            createDiscussionModal.classList.add('hidden');
        });
    }

    if (createDiscussionForm) {
        createDiscussionForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const title = document.getElementById('discussion-title-input').value;
            const content = document.getElementById('discussion-content-input').value;
            const errorDiv = document.getElementById('discussion-modal-error');

            try {
                const response = await fetch(`/api/courses/${courseId}/discussions`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ title, content })
                });

                const data = await response.json();

                if (data.success) {
                    createDiscussionModal.classList.add('hidden');
                    createDiscussionForm.reset();
                    fetchDiscussions();
                } else {
                    errorDiv.textContent = data.message;
                    errorDiv.classList.remove('hidden');
                }
            } catch (error) {
                errorDiv.textContent = 'Terjadi kesalahan saat membuat diskusi.';
                errorDiv.classList.remove('hidden');
            }
        });
    }

    async function fetchDiscussions() {
        try {
            const response = await fetch(`/api/courses/${courseId}/discussions`);
            const data = await response.json();

            if (data.success) {
                renderDiscussions(data.discussions);
            } else {
                discussionsContainer.innerHTML = '<p>Gagal memuat diskusi.</p>';
            }
        } catch (error) {
            discussionsContainer.innerHTML = '<p>Terjadi kesalahan saat memuat diskusi.</p>';
        }
    }

    function renderDiscussions(discussions) {
        if (discussions.length === 0) {
            discussionsContainer.innerHTML = '<p class="no-content-message">Belum ada diskusi di kelas ini.</p>';
            return;
        }

        discussionsContainer.innerHTML = discussions.map(discussion => `
            <div class="topic-card">
                <a href="/kelas/${courseId}/diskusi/${discussion.id}" class="topic-link">
                    <div class="topic-icon">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="dropdown-item-icon">
                          <path stroke-linecap="round" stroke-linejoin="round" d="M20.25 8.511c.884.284 1.5 1.128 1.5 2.097v4.286c0 1.136-.847 2.1-1.98 2.193l-3.722.06c-.247.007-.48.057-.7.144a4.5 4.5 0 01-2.586 0c-.22-.087-.453-.137-.7-.144l-3.722-.06c-1.133-.093-1.98-1.057-1.98-2.193V10.608c0-.97.616-1.813 1.5-2.097m14.25-6.118c-.228.06-.447.11-.66.162a4.5 4.5 0 00-2.586 0c-.213-.051-.432-.102-.66-.162m14.25 6.118A4.491 4.491 0 0018 10.5c-1.052 0-2.062.18-3 .512a4.5 4.5 0 00-2.586 0c-.938-.333-1.948-.512-3-.512-1.052 0-2.062.18-3 .512a4.5 4.5 0 00-2.586 0c-.938-.333-1.948-.512-3-.512A4.491 4.491 0 001.5 10.5c0 .97.616 1.813 1.5 2.097m14.25-6.118c-.228.06-.447.11-.66.162a4.5 4.5 0 00-2.586 0c-.213-.051-.432-.102-.66-.162" />
                        </svg>
                    </div>
                    <div class="topic-info">
                        <div class="topic-name">${discussion.title}</div>
                        <div class="topic-details">
                            <span>Diskusi</span>
                        </div>
                    </div>
                </a>
            </div>
        `).join('');
    }

    function renderPosts(posts, parentId = null) {
        return posts
            .filter(post => post.parent_id === parentId)
            .map(post => `
                <div class="post" data-post-id="${post.id}">
                    <p><b>${post.user.name}</b>: ${post.content}</p>
                    <div class="post-actions">
                        <button class="like-btn">❤️</button>
                        <span class="like-count">${post.likes.length}</span>
                        <button class="reply-btn">Balas</button>
                    </div>
                    <div class="replies">${renderPosts(posts, post.id)}</div>
                </div>
            `).join('');
    }

    fetchDiscussions();

    discussionsContainer.addEventListener('click', async (e) => {
        const target = e.target;

        if (target.classList.contains('like-btn')) {
            const postId = target.closest('.post').dataset.postId;
            const response = await fetch(`/api/posts/${postId}/like`, { method: 'POST' });
            const data = await response.json();
            if (data.success) {
                fetchDiscussions();
            }
        }

        if (target.classList.contains('reply-btn')) {
            const post = target.closest('.post');
            const replyForm = post.querySelector('.reply-form');
            if (replyForm) {
                replyForm.classList.toggle('hidden');
            } else {
                const newReplyForm = document.createElement('form');
                newReplyForm.classList.add('reply-form');
                newReplyForm.innerHTML = `
                    <textarea placeholder="Tulis balasan..."></textarea>
                    <button type="submit">Balas</button>
                `;
                post.querySelector('.replies').appendChild(newReplyForm);
            }
        }

        if (target.classList.contains('close-discussion-btn')) {
            const discussionId = target.closest('.discussion-card').dataset.discussionId;
            const response = await fetch(`/api/discussions/${discussionId}/close`, { method: 'POST' });
            const data = await response.json();
            if (data.success) {
                fetchDiscussions();
            }
        }
    });

    discussionsContainer.addEventListener('submit', async (e) => {
        e.preventDefault();
        const target = e.target;

        if (target.classList.contains('reply-form')) {
            const discussionId = target.closest('.discussion-card').dataset.discussionId;
            const parentId = target.closest('.post')?.dataset.postId;
            const content = target.querySelector('textarea').value;

            const response = await fetch(`/api/discussions/${discussionId}/posts`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ content, parent_id: parentId })
            });

            const data = await response.json();
            if (data.success) {
                fetchDiscussions();
            }
        }
    });
});
