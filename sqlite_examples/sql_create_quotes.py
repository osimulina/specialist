import sqlite3

create_authors = """
INSERT INTO authors (name,surname) VALUES 
('Rick', 'Cook'),
('Waldi', 'Ravens'),
('Mosher''s Law of Software Engineering', NULL),
('Yoggi', 'Berra'),
('Народная мудрость', NULL);
"""

create_quotes = """
INSERT INTO quotes (author_id, text, rating) VALUES 
((SELECT id FROM authors WHERE name = 'Rick' AND surname = 'Cook'), 
 'Программирование сегодня — это гонка разработчиков программ...', 1),
 
((SELECT id FROM authors WHERE name = 'Waldi' AND surname = 'Ravens'), 
 'Программирование на С похоже на быстрые танцы на только...', 1),
 
((SELECT id FROM authors WHERE name = 'Mosher''s Law of Software Engineering'), 
 'Не волнуйтесь, если что-то не работает. Если бы всё работало, вас бы уволили.', 1),
 
((SELECT id FROM authors WHERE name = 'Yoggi' AND surname = 'Berra'), 
 'В теории, теория и практика неразделимы. На практике это не так.', 1),
 
((SELECT id FROM authors WHERE name = 'Народная мудрость'), 
 'Нет пламя без огня', 1);
"""

# Подключение в БД
connection = sqlite3.connect("quotes.db")
# Создаем cursor, он позволяет делать SQL-запросы
cursor = connection.cursor()
# Выполняем запрос:
cursor.execute(create_authors)
cursor.execute(create_quotes)
# Фиксируем выполнение(транзакцию)
connection.commit()
# Закрыть курсор:
cursor.close()
# Закрыть соединение:
connection.close()
