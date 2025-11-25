# Уровень 1
#
# С помощью библиотеки sqlite3 создайте базу данных и подключитесь к ней.
# Создайте в ней таблицы:
# Students
# Поля: (id, name, surname, age, city)
# Courses
# Поля: (id, name, time_start, time_end)
# Student_courses
# Поля: (student_id, course_id)
# course_id - id курса, который проходит студент (Foreign key)
# student_id - id студента, который проходит курс (Foreign key)

"""
Создание базы данных SQLite с тремя таблицами:
Students — студенты
Courses — курсы
Student_courses — связь студентов с курсами
"""

import sqlite3

# Подключаемся к базе данных (если файл не существует, он будет создан автоматически)
conn = sqlite3.connect('school.db')  # Устанавливаем соединение с базой данных
cursor = conn.cursor()  # Получаем объект курсора для выполнения SQL-запросов

# Создание таблиц через скрипт SQL
cursor.executescript('''
    -- Таблица Студентов
    CREATE TABLE IF NOT EXISTS Students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Уникальный идентификатор студента
        name TEXT,                            
        surname TEXT,                         
        age INTEGER,                          
        city TEXT                             
    );

    -- Таблица Курсов
    CREATE TABLE IF NOT EXISTS Courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Уникальный идентификатор курса
        name TEXT,                            -- Название курса
        time_start TEXT,                      -- Дата начала курса
        time_end TEXT                         -- Дата окончания курса
    );

    -- Таблица Связей Студенты-Курсы
    CREATE TABLE IF NOT EXISTS Student_courses (
        student_id INTEGER,                   -- Идентификатор студента
        course_id INTEGER,                    -- Идентификатор курса
        FOREIGN KEY(student_id) REFERENCES Students(id),  -- Внешний ключ на таблицу Студентов
        FOREIGN KEY(course_id) REFERENCES Courses(id)     -- Внешний ключ на таблицу Курсов
    );
''')

# Подготовленные данные для вставки в таблицы
students_data = [
    (1, 'Max', 'Brooks', 24, 'Spb'),  # Строка с данными студента
    (2, 'John', 'Stones', 15, 'Spb'),
    (3, 'Andy', 'Wings', 45, 'Manchester')
]

courses_data = [
    (1, 'Python', '2021-07-21', '2021-08-21'),  # Строка с данными курса
    (2, 'Java', '2021-07-13', '2021-08-16')
]

student_courses_data = [
    (1, 1),  # Макс Брукс записан на курс Python
    (2, 1),  # Джон Стоунз записан на курс Python
    (3, 1)  # Энди Вингс записан на курс Python
]

# Добавляем данные в таблицы с защитой от дублирования записей
cursor.executemany("INSERT OR IGNORE INTO Students VALUES(?, ?, ?, ?, ?)", students_data)
cursor.executemany("INSERT OR IGNORE INTO Courses VALUES(?, ?, ?, ?)", courses_data)
cursor.executemany("INSERT OR IGNORE INTO Student_courses VALUES(?, ?)", student_courses_data)

# Сохраняем изменения в базе данных
conn.commit()

# Закрываем подключение к базе данных
conn.close()


