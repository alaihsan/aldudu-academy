document.addEventListener('DOMContentLoaded', function() {
    const courseId = new URLSearchParams(window.location.search).get('course_id') || window.location.pathname.split('/')[2];
    const discussionId = window.location.pathname.split('/')[4];
    const currentUserId = document.body.dataset.userId;
    const isDiscussionClosed = document.querySelector('.discussion-details p:last-child span').textContent.includes('Ditutup');

    const postsContainer = document.getElementById('posts-container');
    const replyForm = document.getElementById('reply-form');
    const closeDiscussionBtn = document.getElementById('close-discussion-btn');

    // Fetch and render posts
    async function fetchPosts() {
        try {
            const response = await fetch(`/api/discussions/${discussionId}/posts`);
            const data = await response.json();

            if (data.success) {
                renderPosts(data.posts);
            } else {
                postsContainer.innerHTML = '<p>Gagal memuat postingan.</p>';
            }
        } catch (error) {
            postsContainer.innerHTML = '<p>Terjadi kesalahan saat memuat postingan.</p>';
        }
    }

    function renderPosts(posts) {
        if (posts.length === 0) {
            postsContainer.innerHTML = '<p>Belum ada postingan di diskusi ini.</p>';
            return;
        }

        postsContainer.innerHTML = posts.map(post => `
            <div class="post-card" data-post-id="${post.id}" style="border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 1rem; margin-bottom: 1rem; background-color: var(--surface-color);">
                <div class="post-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <div class="post-author">
                        <strong>${post.user.name}</strong>
                        <span style="color: var(--text-secondary-color); font-size: 0.875rem;">${new Date(post.created_at).toLocaleString()}</span>
                    </div>
                    <div class="post-actions">
                        <button class="like-btn btn-link" style="color: ${post.likes.some(like => like.user.id == currentUserId) ? 'var(--danger-color)' : 'var(--text-secondary-color)'};">
                            ❤️ ${post.likes.length}
                        </button>
                        ${!isDiscussionClosed ? '<button class="reply-btn btn-link" style="margin-left: 1rem;">Balas</button>' : ''}
                    </div>
                </div>
                <div class="post-content" style="margin-bottom: 0.5rem;">
                    ${post.content.replace(/\n/g, '<br>')}
                </div>
                <div class="replies" style="margin-left: 2rem;">
                    ${renderReplies(posts, post.id)}
                </div>
            </div>
        `).join('');
    }

    function renderReplies(allPosts, parentId) {
        const replies = allPosts.filter(post => post.parent_id == parentId);
        return replies.map(reply => `
            <div class="reply-card" data-post-id="${reply.id}" style="border-left: 2px solid var(--border-light-color); padding-left: 1rem; margin-top: 0.5rem;">
                <div class="post-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <div class="post-author">
                        <strong>${reply.user.name}</strong>
                        <span style="color: var(--text-secondary-color); font-size: 0.875rem;">${new Date(reply.created_at).toLocaleString()}</span>
                    </div>
                    <div class="post-actions">
                        <button class="like-btn btn-link" style="color: ${reply.likes.some(like => like.user.id == currentUserId) ? 'var(--danger-color)' : 'var(--text-secondary-color)'};">
                            ❤️ ${reply.likes.length}
                        </button>
                    </div>
                </div>
                <div class="post-content">
                    ${reply.content.replace(/\n/g, '<br>')}
                </div>
            </div>
        `).join('');
    }

    // Handle reply form submission
    if (replyForm) {
        replyForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const content = document.getElementById('reply-content').value;

            try {
                const response = await fetch(`/api/discussions/${discussionId}/posts`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ content })
                });

                const data = await response.json();

                if (data.success) {
                    document.getElementById('reply-content').value = '';
                    fetchPosts();
                } else {
                    alert(data.message || 'Gagal mengirim balasan.');
                }
            } catch (error) {
                alert('Terjadi kesalahan saat mengirim balasan.');
            }
        });
    }

    // Handle close discussion
    if (closeDiscussionBtn) {
        closeDiscussionBtn.addEventListener('click', async () => {
            if (confirm('Apakah Anda yakin ingin menutup diskusi ini?')) {
                try {
                    const response = await fetch(`/api/discussions/${discussionId}/close`, {
                        method: 'POST'
                    });

                    const data = await response.json();

                    if (data.success) {
                        window.location.reload();
                    } else {
                        alert(data.message || 'Gagal menutup diskusi.');
                    }
                } catch (error) {
                    alert('Terjadi kesalahan saat menutup diskusi.');
                }
            }
        });
    }

    // Handle likes and replies
    postsContainer.addEventListener('click', async (e) => {
        const target = e.target;

        if (target.classList.contains('like-btn')) {
            const postCard = target.closest('[data-post-id]');
            const postId = postCard.dataset.postId;
            const likeBtn = target;
            const isLiked = likeBtn.style.color === 'var(--danger-color)';
            const currentCount = parseInt(likeBtn.textContent.replace('❤️ ', ''));

            // Optimistic update
            if (isLiked) {
                likeBtn.style.color = 'var(--text-secondary-color)';
                likeBtn.textContent = `❤️ ${currentCount - 1}`;
            } else {
                likeBtn.style.color = 'var(--danger-color)';
                likeBtn.textContent = `❤️ ${currentCount + 1}`;
            }

            try {
                const response = await fetch(`/api/posts/${postId}/like`, {
                    method: 'POST'
                });

                const data = await response.json();

                if (!data.success) {
                    // Revert optimistic update on failure
                    if (isLiked) {
                        likeBtn.style.color = 'var(--danger-color)';
                        likeBtn.textContent = `❤️ ${currentCount}`;
                    } else {
                        likeBtn.style.color = 'var(--text-secondary-color)';
                        likeBtn.textContent = `❤️ ${currentCount}`;
                    }
                    alert(data.message || 'Gagal memberikan like.');
                }
            } catch (error) {
                // Revert optimistic update on error
                if (isLiked) {
                    likeBtn.style.color = 'var(--danger-color)';
                    likeBtn.textContent = `❤️ ${currentCount}`;
                } else {
                    likeBtn.style.color = 'var(--text-secondary-color)';
                    likeBtn.textContent = `❤️ ${currentCount}`;
                }
                alert('Terjadi kesalahan saat memberikan like.');
            }
        }

        if (target.classList.contains('reply-btn') && !isDiscussionClosed) {
            const postCard = target.closest('.post-card');
            const replyForm = postCard.querySelector('.reply-form');

            if (replyForm) {
                replyForm.remove();
            } else {
                const newReplyForm = document.createElement('form');
                newReplyForm.classList.add('reply-form');
                newReplyForm.innerHTML = `
                    <div class="form-group" style="margin-top: 1rem;">
                        <textarea class="form-input" rows="3" placeholder="Tulis balasan..." required></textarea>
                    </div>
                    <button type="submit" class="btn btn-primary" style="margin-top: 0.5rem;">Kirim Balasan</button>
                `;

                postCard.querySelector('.replies').appendChild(newReplyForm);

                newReplyForm.addEventListener('submit', async (e) => {
                    e.preventDefault();
                    const content = newReplyForm.querySelector('textarea').value;
                    const parentId = postCard.dataset.postId;

                    try {
                        const response = await fetch(`/api/discussions/${discussionId}/posts`, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({ content, parent_id: parentId })
                        });

                        const data = await response.json();

                        if (data.success) {
                            fetchPosts();
                        } else {
                            alert(data.message || 'Gagal mengirim balasan.');
                        }
                    } catch (error) {
                        alert('Terjadi kesalahan saat mengirim balasan.');
                    }
                });
            }
        }
    });

    // Initial load
    fetchPosts();
});
