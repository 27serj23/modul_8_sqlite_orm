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
Расширенная версия системы управления школьными курсами с дополнительными методами
фильтрации и предустановленными данными для демонстрации сложных запросов.
Добавленные возможности:
- Фильтрация студентов по возрасту (старше указанного)
- Комбинированная фильтрация по курсу и городу
- Предустановленные данные для тестирования
- Расширенные SQL запросы с JOIN и условиями
"""

import sqlite3
from typing import List, Optional
from dataclasses import dataclass

@dataclass
class Student:
    """Data class для представления студента
    Attributes:
        id: Уникальный идентификатор студента
        name: Имя студента
        surname: Фамилия студента
        age: Возраст студента (должен быть > 0)
        city: Город проживания
    """
    id: Optional[int] = None
    name: str = ""
    surname: str = ""
    age: int = 0
    city: str = ""

@dataclass
class Course:
    """Data class для представления курса

    Attributes:
        id: Уникальный идентификатор курса
        name: Название курса (уникальное)
        time_start: Дата начала курса в формате DD.MM.YY
        time_end: Дата окончания курса в формате DD.MM.YY
    """
    id: Optional[int] = None
    name: str = ""
    time_start: str = ""
    time_end: str = ""

class DatabaseManager:
    """Менеджер базы данных для обработки подключений и транзакций.
    Реализует контекстный менеджер для автоматического управления подключениями
    и обеспечения целостности транзакций.
    Args:
        db_name: Имя файла базы данных (по умолчанию 'school.db')
    """

    def __init__(self, db_name: str = 'school.db'):
        self.db_name = db_name
        self.conn = None
        self.cursor = None

    def __enter__(self):
        """Вход в контекстный менеджер - устанавливает соединение с БД"""
        self.conn = sqlite3.connect(self.db_name)
        self.conn.row_factory = sqlite3.Row  # Возвращает результаты как словари
        self.cursor = self.conn.cursor()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Выход из контекстного менеджера - закрывает соединение с БД
        Автоматически коммитит транзакции при успешном выполнении
        или откатывает при возникновении исключения
        """
        if self.conn:
            if exc_type is None:
                self.conn.commit()  # Сохраняем изменения если нет ошибок
            else:
                self.conn.rollback()  # Откатываем при ошибке
            self.conn.close()

    def execute(self, query: str, params: tuple = ()):
        """Выполняет SQL запрос с параметрами"""
        return self.cursor.execute(query, params)

    def fetch_all(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """Выполняет запрос и возвращает все результаты"""
        return self.cursor.execute(query, params).fetchall()

    def fetch_one(self, query: str, params: tuple = ()):
        """Выполняет запрос и возвращает один результат (первую строку)"""
        return self.cursor.execute(query, params).fetchone()

    def execute_script(self, script: str):
        """Выполняет SQL скрипт, содержащий несколько команд"""
        self.cursor.executescript(script)

class StudentRepository:
    """Репозиторий для расширенных операций со студентами.
    Добавлены новые методы фильтрации для выполнения сложных запросов.
    Args:
        db_manager: Экземпляр DatabaseManager для работы с БД
    """

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def create(self, student: Student) -> int:
        """Создает нового студента в базе данных"""
        query = "INSERT INTO Students (name, surname, age, city) VALUES (?, ?, ?, ?)"
        result = self.db.execute(query, (student.name, student.surname, student.age, student.city))
        return result.lastrowid

    def get_all(self) -> List[sqlite3.Row]:
        """Получает список всех студентов"""
        return self.db.fetch_all("SELECT * FROM Students")

    def get_by_id(self, student_id: int):
        """Находит студента по его ID"""
        return self.db.fetch_one("SELECT * FROM Students WHERE id = ?", (student_id,))

    def get_by_age_gt(self, age: int) -> List[sqlite3.Row]:
        """Находит всех студентов старше указанного возраста
        Args:
            age: Минимальный возраст для фильтрации (исключительно)
        Returns:
            Список студентов старше указанного возраста
        """
        return self.db.fetch_all("SELECT * FROM Students WHERE age > ?", (age,))

    def get_by_city(self, city: str) -> List[sqlite3.Row]:
        """Находит всех студентов из указанного города"""
        return self.db.fetch_all("SELECT * FROM Students WHERE city = ?", (city,))

    def get_by_course(self, course_name: str) -> List[sqlite3.Row]:
        """Находит всех студентов, записанных на указанный курс.
        Выполняет JOIN через таблицу связей Student_courses.
        """
        query = '''
            SELECT s.* 
            FROM Students s
            JOIN Student_courses sc ON s.id = sc.student_id
            JOIN Courses c ON sc.course_id = c.id
            WHERE c.name = ?
        '''
        return self.db.fetch_all(query, (course_name,))

    def get_by_course_and_city(self, course_name: str, city: str) -> List[sqlite3.Row]:
        """Находит студентов на курсе из указанного города
        Комбинированный запрос с двумя условиями фильтрации.
        Полезен для анализа географического распределения студентов на курсах.
        Args:
            course_name: Название курса для фильтрации
            city: Город для фильтрации
        Returns:
            Список студентов, удовлетворяющих обоим условиям
        """
        query = '''
            SELECT s.* 
            FROM Students s
            JOIN Student_courses sc ON s.id = sc.student_id
            JOIN Courses c ON sc.course_id = c.id
            WHERE c.name = ? AND s.city = ?
        '''
        return self.db.fetch_all(query, (course_name, city))

    def update(self, student: Student) -> bool:
        """Обновляет данные существующего студента"""
        query = "UPDATE Students SET name = ?, surname = ?, age = ?, city = ? WHERE id = ?"
        self.db.execute(query, (student.name, student.surname, student.age, student.city, student.id))
        return True

    def delete(self, student_id: int) -> bool:
        """Удаляет студента по ID"""
        self.db.execute("DELETE FROM Students WHERE id = ?", (student_id,))
        return True

class CourseRepository:
    """Репозиторий для операций с курсами в базе данных"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def create(self, course: Course) -> int:
        """Создает новый курс в базе данных"""
        query = "INSERT INTO Courses (name, time_start, time_end) VALUES (?, ?, ?)"
        result = self.db.execute(query, (course.name, course.time_start, course.time_end))
        return result.lastrowid

    def get_all(self) -> List[sqlite3.Row]:
        """Получает список всех курсов"""
        return self.db.fetch_all("SELECT * FROM Courses")

    def get_by_id(self, course_id: int):
        """Находит курс по его ID"""
        return self.db.fetch_one("SELECT * FROM Courses WHERE id = ?", (course_id,))


class EnrollmentRepository:
    """Репозиторий для управления записями студентов на курсы"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def enroll(self, student_id: int, course_id: int) -> bool:
        """Записывает студента на курс
        Returns:
            True при успешной записи, False при нарушении уникальности
        """
        try:
            self.db.execute(
                "INSERT INTO Student_courses (student_id, course_id) VALUES (?, ?)",
                (student_id, course_id)
            )
            return True
        except sqlite3.IntegrityError:
            # Происходит если запись уже существует
            return False

    def get_course_students(self, course_id: int) -> List[sqlite3.Row]:
        """Получает всех студентов, записанных на указанный курс"""
        query = '''
            SELECT s.* 
            FROM Students s
            JOIN Student_courses sc ON s.id = sc.student_id
            WHERE sc.course_id = ?
        '''
        return self.db.fetch_all(query, (course_id,))

class SchoolSystem:
    """Расширенный класс системы управления школой
    Добавлены методы для работы с предустановленными данными
    и демонстрации сложных запросов уровня 2.
    """

    def __init__(self, db_name: str = 'school.db'):
        self.db_name = db_name

    def initialize_database(self):
        """Инициализирует структуру базы данных.
        Создает таблицы:
        - Students: информация о студентах с проверкой возраста
        - Courses: информация о курсах с уникальными названиями
        - Student_courses: таблица связей с каскадным удалением
        """
        with DatabaseManager(self.db_name) as db:
            db.execute_script('''
                CREATE TABLE IF NOT EXISTS Students(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    surname TEXT NOT NULL, 
                    age INTEGER CHECK (age > 0),
                    city TEXT
                );

                CREATE TABLE IF NOT EXISTS Courses(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    time_start TEXT,
                    time_end TEXT
                );

                CREATE TABLE IF NOT EXISTS Student_courses(
                    student_id INTEGER,
                    course_id INTEGER,
                    FOREIGN KEY (student_id) REFERENCES Students(id) ON DELETE CASCADE,
                    FOREIGN KEY (course_id) REFERENCES Courses(id) ON DELETE CASCADE,
                    PRIMARY KEY (student_id, course_id)
                );
            ''')
        print(f"База данных {self.db_name} инициализирована")

    def add_level2_data(self):
        """Добавляет предустановленные данные для демонстрации уровня 2

        Создает тестовый набор данных:
        - 2 курса: Python и Java с конкретными датами
        - 4 студентов с различными возрастами и городами
        - Распределение студентов по курсам

        Использует явные ID для гарантированного воспроизведения связей.
        """
        with DatabaseManager(self.db_name) as db:
            # Очистка предыдущих данных для чистоты демонстрации
            db.execute_script('''
                DELETE FROM Student_courses;
                DELETE FROM Students;
                DELETE FROM Courses;
            ''')

            # Создание курсов с фиксированными ID для стабильных связей
            courses_data = [
                Course(id=1, name='python', time_start='21.07.21', time_end='21.08.21'),
                Course(id=2, name='java', time_start='13.07.21', time_end='16.08.21')
            ]

            # Используем прямой SQL для вставки с явными ID
            for course in courses_data:
                db.execute(
                    "INSERT INTO Courses (id, name, time_start, time_end) VALUES (?, ?, ?, ?)",
                    (course.id, course.name, course.time_start, course.time_end)
                )

            # Создание студентов с различными характеристиками для демонстрации фильтрации
            students_data = [
                Student(id=1, name='Max', surname='Brooks', age=24, city='Spb'),
                Student(id=2, name='John', surname='Stones', age=15, city='Spb'),
                Student(id=3, name='Andy', surname='Wings', age=45, city='Manchester'),
                Student(id=4, name='Kate', surname='Brooks', age=34, city='Spb')
            ]

            for student in students_data:
                db.execute(
                    "INSERT INTO Students (id, name, surname, age, city) VALUES (?, ?, ?, ?, ?)",
                    (student.id, student.name, student.surname, student.age, student.city)
                )

            # Создание связей студентов с курсами
            # Распределение специально подобрано для демонстрации запросов
            enrollments_data = [
                (1, 1),  # Max (24 года, Spb) на python
                (2, 1),  # John (15 лет, Spb) на python
                (3, 1),  # Andy (45 лет, Manchester) на python
                (4, 2)  # Kate (34 года, Spb) на java
            ]

            for student_id, course_id in enrollments_data:
                db.execute(
                    "INSERT INTO Student_courses (student_id, course_id) VALUES (?, ?)",
                    (student_id, course_id)
                )

            print("Данные уровня 2 добавлены в базу")

    def demonstrate_queries(self):
        """Демонстрирует расширенные запросы уровня 2.
        Выполняет три ключевых сценария:
        1. Фильтрация студентов по возрасту (>30 лет)
        2. Фильтрация студентов по курсу (python)
        3. Комбинированная фильтрация по курсу и городу (python + Spb)
        Каждый запрос демонстрирует различные аспекты работы с данными
        и возможности системы фильтрации.
        """
        print("\n=== ВЫПОЛНЕНИЕ ЗАПРОСОВ УРОВНЯ 2 ===\n")

        with DatabaseManager(self.db_name) as db:
            student_repo = StudentRepository(db)

            # 1. ДЕМОНСТРАЦИЯ ФИЛЬТРАЦИИ ПО ВОЗРАСТУ
            print("1. Все студенты старше 30 лет:")
            students_over_30 = student_repo.get_by_age_gt(30)
            # Ожидаем 2 студента: Andy (45) и Kate (34)
            for student in students_over_30:
                print(f"   - {student['name']} {student['surname']}, {student['age']} лет, {student['city']}")

            # 2. ДЕМОНСТРАЦИЯ ФИЛЬТРАЦИИ ПО КУРСУ
            print("\n2. Все студенты на курсе python:")
            python_students = student_repo.get_by_course('python')
            # Ожидаем 3 студентов: Max, John, Andy
            for student in python_students:
                print(f"   - {student['name']} {student['surname']}, {student['age']} лет, {student['city']}")

            # 3. ДЕМОНСТРАЦИЯ КОМБИНИРОВАННОЙ ФИЛЬТРАЦИИ
            print("\n3. Все студенты на курсе python из Spb:")
            python_spb_students = student_repo.get_by_course_and_city('python', 'Spb')
            # Ожидаем 2 студентов: Max и John (оба из Spb на python)
            for student in python_spb_students:
                print(f"   - {student['name']} {student['surname']}, {student['age']} лет")


def main():
    """Основная функция для запуска демонстрации уровня 2"""
    try:
        # Инициализация системы
        school = SchoolSystem()

        print("Инициализация базы данных...")
        school.initialize_database()

        # Загрузка тестовых данных
        print("Добавление данных уровня 2...")
        school.add_level2_data()

        # Демонстрация расширенного функционала
        school.demonstrate_queries()
        print("\n=== ВЫПОЛНЕНИЕ ЗАВЕРШЕНО ===")

    except Exception as e:
        print(f"Произошла ошибка: {e}")

# Точка входа в программу
if __name__ == "__main__":
    main()
