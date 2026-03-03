import sqlite3

create_quotes = """
INSERT INTO
quotes (author,text, rating)
VALUES
('Rick Cook', 'Программирование сегодня — это гонка разработчиков программ...', 1),
('Waldi Ravens', 'Программирование на С похоже на быстрые танцы на только...', 1);
"""

# Подключение в БД
connection = sqlite3.connect("store.db")
# Создаем cursor, он позволяет делать SQL-запросы
cursor = connection.cursor()
# Выполняем запрос:
cursor.execute(create_quotes)
# Фиксируем выполнение(транзакцию)
connection.commit()
# Закрыть курсор:
cursor.close()
# Закрыть соединение:
connection.close()