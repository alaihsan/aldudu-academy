document.addEventListener('DOMContentLoaded', function() {
    const courseId = new URLSearchParams(window.location.search).get('course_id') || window.location.pathname.split('/')[2];
    const discussionId = window.location.pathname.split('/')[4];
    const currentUserId = document.body.dataset.userId;
    const currentUserRole = document.body.dataset.userRole;
    const discussionCreatorId = document.querySelector('.discussion-details').dataset.creatorId;
    const isDiscussionClosed = document.querySelector('.discussion-details p:last-child span').textContent.includes('Ditutup');

    const postsContainer = document.getElementById('posts-container');
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

        const canDeletePosts = currentUserRole === 'GURU' || currentUserId == discussionCreatorId;

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
                        ${currentUserId == post.user.id ? '<button class="edit-btn btn-link" style="margin-left: 1rem;">Edit</button>' : ''}
                        ${canDeletePosts ? '<button class="delete-btn btn-link" style="margin-left: 1rem; color: var(--danger-color);">🗑️</button>' : ''}
                    </div>
                </div>
                <div class="post-content" style="margin-bottom: 0.5rem;">
                    ${post.content.replace(/\n/g, '<br>')}
                </div>
                <div class="replies">
                    ${renderReplies(posts, post.id)}
                </div>
            </div>
        `).join('');
    }

    function renderReplies(allPosts, parentId) {
        const replies = allPosts.filter(post => post.parent_id == parentId);
        const canDeletePosts = currentUserRole === 'GURU' || currentUserId == discussionCreatorId;

        return replies.map(reply => `
            <div class="reply-card" data-post-id="${reply.id}" style="margin-top: 0.5rem;">
                <div class="post-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <div class="post-author">
                        <strong>${reply.user.name}</strong>
                        <span style="color: var(--text-secondary-color); font-size: 0.875rem;">${new Date(reply.created_at).toLocaleString()}</span>
                    </div>
                    <div class="post-actions">
                        <button class="like-btn btn-link" style="color: ${reply.likes.some(like => like.user.id == currentUserId) ? 'var(--danger-color)' : 'var(--text-secondary-color)'};">
                            ❤️ ${reply.likes.length}
                        </button>
                        ${!isDiscussionClosed ? '<button class="reply-btn btn-link" style="margin-left: 1rem;">Balas</button>' : ''}
                        ${currentUserId == reply.user.id ? '<button class="edit-btn btn-link" style="margin-left: 1rem;">Edit</button>' : ''}
                        ${canDeletePosts ? '<button class="delete-btn btn-link" style="margin-left: 1rem; color: var(--danger-color);">🗑️</button>' : ''}
                    </div>
                </div>
                <div class="post-content">
                    ${reply.content.replace(/\n/g, '<br>')}
                </div>
            </div>
        `).join('');
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

    // Handle likes, replies, and deletes
    postsContainer.addEventListener('click', async (e) => {
        const target = e.target;

        if (target.classList.contains('delete-btn')) {
            const postCard = target.closest('[data-post-id]');
            const postId = postCard.dataset.postId;

            if (confirm('Apakah Anda yakin ingin menghapus post ini?')) {
                try {
                    const response = await fetch(`/api/posts/${postId}`, {
                        method: 'DELETE'
                    });

                    const data = await response.json();

                    if (data.success) {
                        fetchPosts();
                    } else {
                        alert(data.message || 'Gagal menghapus post.');
                    }
                } catch (error) {
                    alert('Terjadi kesalahan saat menghapus post.');
                }
            }
            return;
        }

        if (target.classList.contains('edit-btn')) {
            const postCard = target.closest('[data-post-id]');
            const postId = postCard.dataset.postId;
            const postContent = postCard.querySelector('.post-content');
            const currentContent = postContent.innerHTML.replace(/<br>/g, '\n');

            const editForm = document.createElement('div');
            editForm.className = 'edit-form';
            editForm.innerHTML = `
                <textarea class="form-input" rows="3">${currentContent}</textarea>
                <button class="btn btn-primary save-edit-btn" style="margin-top: 0.5rem;">Simpan</button>
                <button class="btn btn-secondary cancel-edit-btn" style="margin-top: 0.5rem; margin-left: 0.5rem;">Batal</button>
            `;

            postContent.style.display = 'none';
            postContent.insertAdjacentElement('afterend', editForm);

            const saveBtn = editForm.querySelector('.save-edit-btn');
            const cancelBtn = editForm.querySelector('.cancel-edit-btn');
            const textarea = editForm.querySelector('textarea');

            saveBtn.addEventListener('click', async () => {
                const newContent = textarea.value.trim();
                if (!newContent) {
                    alert('Konten tidak boleh kosong.');
                    return;
                }

                try {
                    const response = await fetch(`/api/posts/${postId}`, {
                        method: 'PUT',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ content: newContent })
                    });

                    const data = await response.json();

                    if (data.success) {
                        fetchPosts();
                    } else {
                        alert(data.message || 'Gagal mengedit post.');
                    }
                } catch (error) {
                    alert('Terjadi kesalahan saat mengedit post.');
                }
            });

            cancelBtn.addEventListener('click', () => {
                editForm.remove();
                postContent.style.display = 'block';
            });
        }

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
            const postCard = target.closest('[data-post-id]');
            const postId = postCard.dataset.postId;

            // Check if reply form already exists
            if (postCard.querySelector('.reply-form-inline')) {
                return; // Don't create another form
            }

            const replyTextarea = document.createElement('textarea');
            replyTextarea.className = 'form-input';
            replyTextarea.rows = 3;
            replyTextarea.placeholder = 'Tulis balasan Anda...';
            replyTextarea.required = true;

            const submitBtn = document.createElement('button');
            submitBtn.className = 'btn btn-primary';
            submitBtn.textContent = 'Kirim Balasan';
            submitBtn.style.marginTop = '0.5rem';

            const cancelBtn = document.createElement('button');
            cancelBtn.className = 'btn btn-secondary';
            cancelBtn.textContent = 'Batal';
            cancelBtn.style.marginTop = '0.5rem';
            cancelBtn.style.marginLeft = '0.5rem';

            const replyFormDiv = document.createElement('div');
            replyFormDiv.className = 'reply-form-inline';
            replyFormDiv.style.marginTop = '1rem';
            replyFormDiv.appendChild(replyTextarea);
            replyFormDiv.appendChild(submitBtn);
            replyFormDiv.appendChild(cancelBtn);

            // Insert after the post content
            const postContent = postCard.querySelector('.post-content');
            postContent.insertAdjacentElement('afterend', replyFormDiv);

            // Focus on textarea
            replyTextarea.focus();

            // Handle submit
            submitBtn.addEventListener('click', async () => {
                const content = replyTextarea.value.trim();
                if (!content) {
                    alert('Balasan tidak boleh kosong.');
                    return;
                }

                try {
                    const response = await fetch(`/api/discussions/${discussionId}/posts`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            content: content,
                            parent_id: postId
                        })
                    });

                    const data = await response.json();

                    if (data.success) {
                        replyFormDiv.remove();
                        fetchPosts();
                    } else {
                        alert(data.message || 'Gagal mengirim balasan.');
                    }
                } catch (error) {
                    alert('Terjadi kesalahan saat mengirim balasan.');
                }
            });

            // Handle cancel
            cancelBtn.addEventListener('click', () => {
                replyFormDiv.remove();
            });
        }
    });

    // Initial load
    fetchPosts();
});
