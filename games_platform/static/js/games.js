// Функции для работы с играми
document.addEventListener('DOMContentLoaded', function() {

    // Лайки/дизлайки
    const likeButtons = document.querySelectorAll('.like-btn, .dislike-btn');
    likeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const gameId = this.dataset.gameId;
            const action = this.dataset.action;

            fetch(`/games/${gameId}/toggle-like/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: `action=${action}`
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Обновляем счетчики
                    const likeBtn = document.querySelector(`.like-btn[data-game-id="${gameId}"]`);
                    const dislikeBtn = document.querySelector(`.dislike-btn[data-game-id="${gameId}"]`);

                    if (likeBtn) {
                        likeBtn.querySelector('.like-count').textContent = data.likes;
                    }
                    if (dislikeBtn) {
                        dislikeBtn.querySelector('.dislike-count').textContent = data.dislikes;
                    }

                    // Визуальная обратная связь
                    this.classList.add('active');
                    setTimeout(() => {
                        this.classList.remove('active');
                    }, 300);
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
        });
    });

    // Запуск игры
    const incrementPlayBtn = document.getElementById('increment-play');
    const gameFrame = document.getElementById('game-frame');
    const gamePlaceholder = document.getElementById('game-placeholder');

    if (incrementPlayBtn && gameFrame) {
        incrementPlayBtn.addEventListener('click', function() {
            // Показываем iframe
            gamePlaceholder.style.display = 'none';
            gameFrame.style.display = 'block';

            // Отправляем запрос на увеличение счетчика
            const gameId = window.location.pathname.split('/').filter(p => p).pop();

            fetch(`/games/${gameId}/increment-play/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': getCookie('csrftoken')
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success && data.play_count !== undefined) {
                    // Обновляем счетчик на странице
                    const playCountElement = document.querySelector('.play-count');
                    if (playCountElement) {
                        playCountElement.textContent = `Запусков: ${data.play_count}`;
                    }
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
        });
    }

    // Редактирование комментариев
    const editButtons = document.querySelectorAll('.btn-edit-comment');
    editButtons.forEach(button => {
        button.addEventListener('click', function() {
            const commentId = this.dataset.commentId;
            const textElement = document.getElementById(`comment-text-${commentId}`);
            const editForm = document.getElementById(`edit-form-${commentId}`);

            if (textElement && editForm) {
                textElement.style.display = 'none';
                editForm.style.display = 'block';
            }
        });
    });

    const cancelButtons = document.querySelectorAll('.cancel-edit');
    cancelButtons.forEach(button => {
        button.addEventListener('click', function() {
            const commentId = this.dataset.commentId;
            const textElement = document.getElementById(`comment-text-${commentId}`);
            const editForm = document.getElementById(`edit-form-${commentId}`);

            if (textElement && editForm) {
                textElement.style.display = 'block';
                editForm.style.display = 'none';
            }
        });
    });

    // Рейтинг звездами
    const starLabels = document.querySelectorAll('.star-label');
    starLabels.forEach(label => {
        label.addEventListener('click', function() {
            const stars = this.closest('.rating-stars');
            const labels = stars.querySelectorAll('.star-label');
            const clickedIndex = Array.from(labels).indexOf(this);

            // Удаляем активный класс со всех звезд
            labels.forEach(l => l.classList.remove('active'));

            // Добавляем активный класс до кликнутой звезды включительно
            for (let i = 0; i <= clickedIndex; i++) {
                labels[i].classList.add('active');
            }
        });
    });

    // Инициализация активных звезд для текущей оценки пользователя
    const currentRating = document.querySelector('input[name="rating"]:checked');
    if (currentRating) {
        const ratingValue = parseInt(currentRating.value);
        const stars = document.querySelector('.rating-stars');
        const labels = stars.querySelectorAll('.star-label');

        for (let i = 0; i < ratingValue; i++) {
            labels[i].classList.add('active');
        }
    }
});

// Вспомогательная функция для получения CSRF токена
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}