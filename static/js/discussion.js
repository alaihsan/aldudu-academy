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
            discussionsContainer.innerHTML = '<p>Belum ada diskusi di kelas ini.</p>';
            return;
        }

        discussionsContainer.innerHTML = discussions.map(discussion => `
            <div class="discussion-card" data-discussion-id="${discussion.id}">
                <h3>${discussion.title}</h3>
                <p>Oleh: ${discussion.user.name} pada ${new Date(discussion.created_at).toLocaleString()}</p>
                ${discussion.closed ? 
                    `<p><b>Diskusi ditutup</b></p>
                    <p>Total Respon: ${discussion.posts.length - 1}</p>
                    <p>Total Like: ${discussion.posts.reduce((acc, post) => acc + post.likes.length, 0)}</p>`
                    : ''}
                <div class="posts-container">${renderPosts(discussion.posts)}</div>
                ${!discussion.closed ? `
                    <form class="reply-form">
                        <textarea placeholder="Tulis balasan..."></textarea>
                        <button type="submit">Balas</button>
                    </form>
                ` : ''}
                ${discussion.user.id === currentUserId && !discussion.closed ? `<button class="close-discussion-btn">Tutup Diskusi</button>` : ''}
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
