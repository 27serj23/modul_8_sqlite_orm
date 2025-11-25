# Уровень 2.
#
# Добавьте в таблицы объекты:
# Courses:
# (1, 'python', 21.07.21, 21.08.21)
# (2, 'java', 13.07.21, 16.08.21)
#
# Students:
# (1, 'Max', 'Brooks', 24, 'Spb')
# (2, 'John', 'Stones', 15, 'Spb')
# (3, 'Andy', 'Wings', 45, 'Manchester')
# (4, 'Kate', 'Brooks', 34, 'Spb')
#
# Student_courses:
# (1, 1)
# (2, 1)
# (3, 1)
# (4, 2)
#
# Напишите запросы, чтобы получить:
# 1. Всех студентов старше 30 лет.
# 2. Всех студентов, которые проходят курс по python.
# 3. Всех студентов, которые проходят курс по python и из Spb.

"""
Создание базы данных SQLite с тремя таблицами:
Students — студенты
Courses — курсы
Student_courses — связи студентов с курсами
"""

import sqlite3

# Подключение к базе данных
conn = sqlite3.connect('school.db')
cursor = conn.cursor()

# Создание таблиц (если они уже существуют, ничего не происходит)
cursor.executescript('''
    -- Таблица Студентов
    CREATE TABLE IF NOT EXISTS Students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,  -- уникальный ID студента
        name TEXT,                            
        surname TEXT,                         
        age INTEGER,                          
        city TEXT                             
    );

    -- Таблица Курсов
    CREATE TABLE IF NOT EXISTS Courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,  -- уникальный ID курса
        name TEXT,                            -- название курса
        time_start TEXT,                      -- дата начала курса
        time_end TEXT                         -- дата завершения курса
    );

    -- Таблица связей Студенты-Курсы
    CREATE TABLE IF NOT EXISTS Student_courses (
        student_id INTEGER,                   -- внешний ключ на таблицу Студентов
        course_id INTEGER,                    -- внешний ключ на таблицу Курсов
        FOREIGN KEY(student_id) REFERENCES Students(id),
        FOREIGN KEY(course_id) REFERENCES Courses(id),
        PRIMARY KEY (student_id, course_id)   -- комбинация полей как первичный ключ
    );
''')

# Удаляем все записи из таблиц перед добавлением новых данных
cursor.executescript('''
    DELETE FROM Student_courses;
    DELETE FROM Students;
    DELETE FROM Courses;
''')

# Добавление данных в таблицу Courses
courses_data = [
    (1, 'python', '2021-07-21', '2021-08-21'),
    (2, 'java', '2021-07-13', '2021-08-16')
]
cursor.executemany("INSERT INTO Courses VALUES (?, ?, ?, ?)", courses_data)

# Добавление данных в таблицу Students
students_data = [
    (1, 'Max', 'Brooks', 24, 'Spb'),
    (2, 'John', 'Stones', 15, 'Spb'),
    (3, 'Andy', 'Wings', 45, 'Manchester'),
    (4, 'Kate', 'Brooks', 34, 'Spb')
]
cursor.executemany("INSERT INTO Students VALUES (?, ?, ?, ?, ?)", students_data)

# Добавление данных в таблицу Student_courses
student_courses_data = [
    (1, 1),  # Max Brooks на курсе Python
    (2, 1),  # John Stones на курсе Python
    (3, 1),  # Andy Wings на курсе Python
    (4, 2)  # Kate Brooks на курсе Java
]
cursor.executemany("INSERT INTO Student_courses VALUES (?, ?)", student_courses_data)

# Сохраняем изменения
conn.commit()

print("База данных успешно создана и заполнена!\n")

# Выполняем необходимые запросы

# 1. ВСЕ СТУДЕНТЫ СТАРШЕ 30 ЛЕТ
print("1. Все студенты старше 30 лет:")
cursor.execute("SELECT * FROM Students WHERE age > 30")
students_over_30 = cursor.fetchall()
for student in students_over_30:
    print(f"ID: {student[0]}, Имя: {student[1]}, Фамилия: {student[2]}, Возраст: {student[3]}, Город: {student[4]}")

# 2. ВСЕ СТУДЕНТЫ НА КУРСЕ PYTHON
print("\n2. Все студенты, которые проходят курс по Python:")
cursor.execute('''
    SELECT s.id, s.name, s.surname, s.age, s.city 
    FROM Students AS s
    INNER JOIN Student_courses AS sc ON s.id = sc.student_id
    INNER JOIN Courses AS c ON sc.course_id = c.id
    WHERE c.name = 'python'
''')
python_students = cursor.fetchall()
for student in python_students:
    print(f"ID: {student[0]}, Имя: {student[1]}, Фамилия: {student[2]}, Возраст: {student[3]}, Город: {student[4]}")

# 3. ВСЕ СТУДЕНТЫ, КОТОРЫЕ ПРОХОДЯТ КУРС ПО PYTHON И ЖИВУТ В SPB
print("\n3. Все студенты, которые проходят курс по Python и живут в СПб:")
cursor.execute('''
    SELECT s.id, s.name, s.surname, s.age, s.city 
    FROM Students AS s
    INNER JOIN Student_courses AS sc ON s.id = sc.student_id
    INNER JOIN Courses AS c ON sc.course_id = c.id
    WHERE c.name = 'python' AND s.city = 'Spb'
''')
python_spb_students = cursor.fetchall()
for student in python_spb_students:
    print(f"ID: {student[0]}, Имя: {student[1]}, Фамилия: {student[2]}, Возраст: {student[3]}, Город: {student[4]}")

# Закрытие подключения к базе данных
conn.close()