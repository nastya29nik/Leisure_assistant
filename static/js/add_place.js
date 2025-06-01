function initImagePreview() {
    const imageInput = document.getElementById('id_image');
    const imagePreview = document.querySelector('#image-preview img');
    const fileInfo = document.getElementById('file-info');
    
    if (!imageInput || !imagePreview || !fileInfo) return;
    
    // Сохраняем путь к изображению по умолчанию
    const defaultImageSrc = imagePreview.dataset.defaultSrc;
    
    imageInput.addEventListener('change', function() {
        const file = this.files[0];
        
        if (file) {
            // Проверяем тип файла
            const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
            if (!allowedTypes.includes(file.type)) {
                alert('Ошибка: разрешены только изображения в формате JPEG, PNG, GIF или WEBP');
                this.value = '';
                fileInfo.textContent = "Файл не выбран";
                imagePreview.src = defaultImageSrc;
                return;
            }
            
            // Обновляем информацию о файле
            fileInfo.textContent = file.name;
            
            // Создаем объект FileReader для чтения файла
            const reader = new FileReader();
            
            reader.onload = function(e) {
                // Устанавливаем источник изображения для предпросмотра
                imagePreview.src = e.target.result;
            }
            
            reader.readAsDataURL(file);
        } else {
            fileInfo.textContent = "Файл не выбран";
            imagePreview.src = defaultImageSrc;
        }
    });
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', initImagePreview);