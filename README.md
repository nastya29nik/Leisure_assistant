# Ассистент по досугу
## Состав команды
+ Гузова Виктория - фронтенд и презентация
+ Никитина Анастасия - бэкенд и гит
+ Павлова Юлия - бэкенд и отчет

## Описание проекта
**Ассистент по досугу** - это веб-приложение,для поиска мест отдыха и развлечений. Система помогает пользователям находить интересные места (парки, театры, музеи и т.д.) на основе их предпочтений. Главные возможности:
+ Диалоговый интерфейс для выбора категорий досуга
+ Фотография, рейтинг, описание места
+ Система отметки посещенных мест
+ Добавление своих оценок и отзывов о посещенном месте
+ Добавление своего места
+ Краткие сводки отзывов с использованием YandexGPT
## Структура проекта
leisure_bot/  
├── core/  
│   ├── settings.py      
│   └── urls.py         
├── places/             
│   ├── migrations/     
│   ├── templates/      
│   ├── admin.py        
│   ├── models.py      
│   ├── views.py
│   ├── utils.py       
│   └── urls.py        
├── users/               
│   ├── migrations/  
│   ├── templates/  
│   ├── admin.py  
│   ├── models.py  
│   ├── views.py  
│   └── urls.py  
├── templates/          
├── static/             
│   ├── css/            
│   ├── js/             
│   └── images/  
├── media/places/images\         
├── manage.py           
└── requirements.txt    
## База данных
**Таблицы:**
+ Users: 
  + username 
  + password 
  + first_name
  + last_name
+ Places_category: 
  + id
  + name
+ Places: 
  + id
  + name
  + image
  + description
  + short_description
  + category_id
+ Places_visited:
  + id
  + place_id
  + user_id
  + mark
  + feedback
  + visited_at
+ Reviews:
  + id
  + place_id
  + mark
  + comment 
## Технологии
**Backend:**
- Python 3
- Django (веб-фреймворк)
- PostgreSQL 14 (база данных)
- Requests (HTTP-запросы)
- YandexGPT API (суммаризация отзывов)

**Frontend:**
- HTML5 (разметка)
- CSS3 (стилизация)
- JavaScript (логика)
- Fetch API (асинхронные запросы)

