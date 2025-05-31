document.addEventListener('DOMContentLoaded', function() {
    const chatMessages = document.getElementById('chat-messages');
    const userMessageInput = document.getElementById('user-message');
    const sendButton = document.getElementById('send-btn');
    const categoryButtons = document.querySelectorAll('.category-btn');
    
    const API_BASE_URL = '/api';
    let isProcessing = false;
    let currentCategory = null;
    let currentOffset = 0;
    const placesPerPage = 5;

    function addMessage(text, isUser, isCard = false, isPlaceRelated = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'assistant-message'}`;
        
        if (isPlaceRelated) {
            messageDiv.dataset.placeRelated = 'true';
        }
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        if (isCard) {
            contentDiv.innerHTML = text;
        } else {
            contentDiv.innerHTML = `<p>${text}</p>`;
        }
        
        messageDiv.appendChild(contentDiv);
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        if (isCard) {
            initializeCardButtons();
            initializeVisitButtons();
            initializeSummaryButtons();
        }
    }
    
    function createPlaceCard(place) {
    let imagePath = place.image_path || '/static/images/default-place.jpg';
    const visitedBtn = place.is_visited ? 
    `<button class="btn-visited" data-id="${place.id}" disabled>
        <i class="fas fa-check-circle"></i> Посещено
    </button>` :
    `<button class="btn-visit" data-id="${place.id}">
        <i class="fas fa-map-marker-alt"></i> Отметить как посещенное
    </button>`;

    return `
        <div class="place-card" data-id="${place.id}">
            <img src="${imagePath}" 
                 class="place-image" 
                 alt="${place.name}"
                 onerror="this.src='/static/images/default-place.jpg'">
            <div class="place-info">
                <div class="place-title">${place.name}</div>
                <div class="place-description">${place.short_description || ''}</div>
                <div class="place-rating"><i class="fas fa-star"></i> ${place.rating || '0.0'}/10</div>
                <div class="action-buttons">
                    <button class="btn-details" data-id="${place.id}">
                        <i class="fas fa-info-circle"></i> Подробнее
                    </button>
                    ${visitedBtn}
                </div>
            </div>
        </div>
    `;
}

    function initializeCardButtons() {
        document.querySelectorAll('.btn-details').forEach(btn => {
            btn.addEventListener('click', function() {
                if (isProcessing) return;
                const placeId = this.getAttribute('data-id');
                showPlaceDetails(placeId);
            });
        });
    }

    function initializeVisitButtons() {
        document.querySelectorAll('.btn-visit').forEach(btn => {
            btn.addEventListener('click', function() {
                if (isProcessing) return;
                const placeId = this.getAttribute('data-id');
                markAsVisited(placeId, this);
            });
        });
    }
    function initializeSummaryButtons() {
        document.querySelectorAll('.btn-summary').forEach(btn => {
            btn.addEventListener('click', function() {
                if (isProcessing) return;
                const placeId = this.getAttribute('data-id');
                const placeName = this.getAttribute('data-name');
                showPlaceSummary(placeId, placeName);
            });
        });
        }

    function removePlaceRelatedMessages() {
        document.querySelectorAll('.message[data-place-related="true"]').forEach(el => {
            el.remove();
        });
    }

    function removePaginationControls() {
        const loadMoreContainer = document.querySelector('.load-more-container');
        if (loadMoreContainer) {
            loadMoreContainer.remove();
        }
        const endMessage = document.querySelector('.end-message');
        if (endMessage) {
            endMessage.remove();
        }
    }

    function showLoadMoreButton() {
        const buttonHtml = `
            <div class="load-more-container" data-place-related="true">
                <button id="load-more-btn" class="load-more-btn">
                    <i class="fas fa-plus-circle"></i> Показать еще
                </button>
            </div>
        `;
        
        addMessage(buttonHtml, false, true, true);
        
        document.getElementById('load-more-btn').addEventListener('click', function() {
            loadMorePlaces();
        });
    }

    function showEndOfListMessage() {
        addMessage(
            '<div class="end-message">Это все доступные места по данной категории.</div>', 
            false, 
            false, 
            true
        );
    }

    function loadMorePlaces() {
        if (isProcessing) return;
        currentOffset += placesPerPage;
        fetchPlaces(currentCategory, currentOffset, true);
    }

    async function fetchPlaces(category, offset = 0, append = false) {
        if (isProcessing) return;
        isProcessing = true;
        
        removePaginationControls();
        
        if (!append) {
            removePlaceRelatedMessages();
            currentOffset = 0;
        }

        try {
            const params = new URLSearchParams();
            params.append('category', category);
            params.append('offset', offset);
            params.append('limit', placesPerPage);
            
            const response = await fetch(`${API_BASE_URL}/places/?${params.toString()}`);
            
            if (!response.ok) throw new Error(`Ошибка: ${response.status}`);
            
            const data = await response.json();
            const places = data.places || [];
            
            if (!append && places.length > 0) {
                addMessage(`Вот что я нашёл по категории "${getCategoryName(category)}":`, false, false, true);
            }
            
            if (places.length > 0) {
                places.forEach(place => {
                    addMessage(createPlaceCard(place), false, true, true);
                });
            }
            
            if (places.length === placesPerPage) {
                showLoadMoreButton();
            } else if (places.length > 0) {
                showEndOfListMessage();
            } else if (!append) {
                addMessage(`В категории "${getCategoryName(category)}" пока нет мест.`, false, false, true);
            } else {
                addMessage(
                    '<div class="end-message">Вы достигли конца списка.</div>', 
                    false, 
                    false, 
                    true
                );
            }
        } catch (error) {
            console.error('Ошибка:', error);
            addMessage('Не удалось загрузить места. Попробуйте позже.', false, false, true);
        } finally {
            isProcessing = false;
        }
    }

    async function markAsVisited(placeId, buttonElement) {
        if (isProcessing) return;
        isProcessing = true;
        
        try {
            const response = await fetch(`${API_BASE_URL}/mark_visited/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({ place_id: placeId }),
        credentials: 'include'
        });
            
            if (!response.ok) throw new Error(`Ошибка: ${response.status}`);
            
            const data = await response.json();
            
            if (data.status === 'added') {
                const card = document.querySelector(`.place-card[data-id="${placeId}"]`);
                if (card) {
                    const visitBtn = card.querySelector('.btn-visit');
                    if (visitBtn) {
                        visitBtn.outerHTML = `
                            <button class="btn-visited visited" data-id="${placeId}" disabled>
                                <i class="fas fa-check"></i> Посещено
                            </button>
                        `;
                    }
                }
                addMessage(`Место "${data.place_name}" успешно добавлено в список посещенных!`, false, false, true);
            } else if (data.status === 'exists') {
                addMessage(`Место "${data.place_name}" уже было отмечено как посещенное ранее.`, false, false, true);
            }
            
        } catch (error) {
            console.error('Ошибка:', error);
            addMessage('Не удалось отметить место как посещенное. Попробуйте позже.', false, false, true);
        } finally {
            isProcessing = false;
        }
    }

   function getCsrfToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]').value;
}

    async function showPlaceDetails(placeId) {
    if (isProcessing) return;
    isProcessing = true;
    
    try {
        const url = `${API_BASE_URL}/place/${placeId}/`;
        const response = await fetch(url);
        
        if (!response.ok) throw new Error(`Ошибка HTTP: ${response.status}`);
        
        const place = await response.json();
        const visitedBtn = place.is_visited ? 
            `<button class="btn-visited visited" data-id="${place.id}" disabled>
                <i class="fas fa-check"></i> Посещено
            </button>` :
            `<button class="btn-visit-detail" data-id="${place.id}">
                <i class="fas fa-map-marker-alt"></i> Отметить как посещенное
            </button>`;
        
        // Добавляем кнопку сводки
        const summaryBtn = `
            <button class="btn-summary-detail" data-id="${place.id}" data-name="${place.name}">
                <i class="fas fa-comments"></i> Краткая сводка
            </button>
        `;
        
        const modalHtml = `
            <div class="place-detail-modal" data-id="${place.id}">
                <img src="${place.image_path || '/static/images/default-place.jpg'}" 
                     class="place-image"
                     onerror="this.src='/static/images/default-place.jpg'">
                <p><strong>Описание:</strong> ${place.description || 'Нет описания'}</p>
                <p><strong>Рейтинг:</strong> ${place.rating || '0.0'}/10</p>
                <div class="detail-action">
                    ${visitedBtn}
                    ${summaryBtn}
                    <button class="close-modal">Закрыть</button>
                </div>
            </div>
        `;
        
        addMessage(modalHtml, false, true, true);
        document.querySelector('.close-modal')?.addEventListener('click', function() {
            this.closest('.message').remove();
        });
        
        document.querySelector('.btn-visit-detail')?.addEventListener('click', function() {
            const placeId = this.getAttribute('data-id');
            markAsVisited(placeId, this);
        });
        document.querySelector('.btn-summary-detail')?.addEventListener('click', function() {
            const placeId = this.getAttribute('data-id');
            const placeName = this.getAttribute('data-name');
            showPlaceSummary(placeId, placeName);
        });
        
    } catch (error) {
        console.error('Ошибка при загрузке деталей:', error);
        addMessage('Не удалось загрузить подробную информацию. Попробуйте позже.', false, false, true);
    } finally {
        isProcessing = false;
    }
}

    function getCategoryName(category) {
        const categoryNames = {
            'walk': 'Прогулка',
            'theater': 'Театр',
            'museum': 'Музей',
            'restaurant': 'Ресторан',
            'cafe': 'Кафе',
            'park': 'Парк аттракционов',
            'pool': 'Бассейн',
            'kids': 'Детский досуг',
            'coworking': 'Коворкинг',
            'cinema': 'Кино',
            'entertainment': 'Развлекательные центры'
        };
        
        return categoryNames[category] || category;
    }

    categoryButtons.forEach(button => {
        button.addEventListener('click', function() {
            const category = this.getAttribute('data-category');
            const categoryName = this.textContent.trim();
            
            addMessage(`Интересуюсь категорией: ${categoryName}`, true);
            currentCategory = category;
            fetchPlaces(currentCategory);
        });
    });

    sendButton.addEventListener('click', sendMessage);
    userMessageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') sendMessage();
    });

    function sendMessage() {
        const message = userMessageInput.value.trim();
        if (message && !isProcessing) {
            addMessage(message, true);
            userMessageInput.value = '';
            addMessage("Пожалуйста, выберите категорию из списка ниже.", false);
        }
    }
    async function showPlaceSummary(placeId, placeName) {
    if (isProcessing) return;
    isProcessing = true;
    
    // Добавляем сообщение о загрузке
    addMessage(`<div class="summary-loading">Загружаю сводку для "${placeName}"...</div>`, false, false, true);
    
    try {
        const response = await fetch(`${API_BASE_URL}/place/${placeId}/summary/`);
        if (!response.ok) throw new Error(`Ошибка: ${response.status}`);
        
        const summaryData = await response.json();
        
        let summaryHtml = '<div class="place-summary">';
        summaryHtml += `<h4>Краткая сводка отзывов о "${placeName}":</h4>`;
        
        if (summaryData.positive) {
            summaryHtml += `<div class="summary-section positive-summary">
                <h5><i class="fas fa-thumbs-up"></i> Положительные моменты:</h5>
                <p>${summaryData.positive}</p>
            </div>`;
        }
        
        if (summaryData.negative) {
            summaryHtml += `<div class="summary-section negative-summary">
                <h5><i class="fas fa-thumbs-down"></i> Что можно улучшить:</h5>
                <p>${summaryData.negative}</p>
            </div>`;
        }
        
        summaryHtml += '</div>';
        
        // Заменяем сообщение о загрузке на результат
        const messages = document.querySelectorAll('.message');
        const lastMessage = messages[messages.length - 1];
        lastMessage.querySelector('.message-content').innerHTML = summaryHtml;
        
    } catch (error) {
        console.error('Ошибка:', error);
        const errorMessage = `<div class="summary-error">Не удалось загрузить сводку. Попробуйте позже.</div>`;
        const messages = document.querySelectorAll('.message');
        const lastMessage = messages[messages.length - 1];
        lastMessage.querySelector('.message-content').innerHTML = errorMessage;
    } finally {
        isProcessing = false;
    }
}

});

