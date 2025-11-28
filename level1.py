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
Многоуровневая система управления школьными курсами и студентами с использованием SQLite.
Реализует паттерн Repository для работы с данными и предоставляет полный CRUD функционал.

Основные компоненты системы:
- DatabaseManager: управление подключениями к БД
- StudentRepository: операции со студентами
- CourseRepository: операции с курсами
- EnrollmentRepository: управление записями на курсы
- SchoolSystem: основной класс системы

Пример использования:
    school = SchoolSystem()
    school.initialize_database()
    school.demonstrate_system()
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
        time_start: Дата начала курса в формате строки
        time_end: Дата окончания курса в формате строки
    """
    id: Optional[int] = None
    name: str = ""
    time_start: str = ""
    time_end: str = ""

class DatabaseManager:
    """Менеджер базы данных для обработки подключений и транзакций.
    Реализует контекстный менеджер для автоматического управления подключениями.
    Обеспечивает безопасное выполнение транзакций с автоматическим откатом при ошибках.
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
    """Репозиторий для операций со студентами в базе данных.
    Обеспечивает полный CRUD (Create, Read, Update, Delete) для сущности Student.
    Args:
        db_manager: Экземпляр DatabaseManager для работы с БД
    """

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def create(self, student: Student) -> int:
        """Создает нового студента в базе данных
        Args:
            student: Объект Student для создания
        Returns:
            ID созданного студента
        """
        query = "INSERT INTO Students (name, surname, age, city) VALUES (?, ?, ?, ?)"
        result = self.db.execute(query, (student.name, student.surname, student.age, student.city))
        return result.lastrowid

    def get_all(self) -> List[sqlite3.Row]:
        """Получает список всех студентов"""
        return self.db.fetch_all("SELECT * FROM Students")

    def get_by_id(self, student_id: int):
        """Находит студента по его ID
        Args:
            student_id: ID студента для поиска
        Returns:
            Объект студента или None если не найден
        """
        return self.db.fetch_one("SELECT * FROM Students WHERE id = ?", (student_id,))

    def get_by_city(self, city: str) -> List[sqlite3.Row]:
        """Находит всех студентов из указанного города
        Args:
            city: Название города для фильтрации
        Returns:
            Список студентов из указанного города
        """
        return self.db.fetch_all("SELECT * FROM Students WHERE city = ?", (city,))

    def get_by_course(self, course_name: str) -> List[sqlite3.Row]:
        """Находит всех студентов, записанных на указанный курс.
        Выполняет JOIN через таблицу связей Student_courses.
        Args:
            course_name: Название курса для поиска
        Returns:
            Список студентов на указанном курсе
        """
        query = '''
            SELECT s.* 
            FROM Students s
            JOIN Student_courses sc ON s.id = sc.student_id
            JOIN Courses c ON sc.course_id = c.id
            WHERE c.name = ?
        '''
        return self.db.fetch_all(query, (course_name,))

    def update(self, student: Student) -> bool:
        """Обновляет данные существующего студента
        Args:
            student: Объект Student с обновленными данными (должен содержать id)
        Returns:
            True при успешном обновлении
        """
        query = "UPDATE Students SET name = ?, surname = ?, age = ?, city = ? WHERE id = ?"
        self.db.execute(query, (student.name, student.surname, student.age, student.city, student.id))
        return True

    def delete(self, student_id: int) -> bool:
        """Удаляет студента по ID
        Args:
            student_id: ID студента для удаления
        Returns:
            True при успешном удалении
        """
        self.db.execute("DELETE FROM Students WHERE id = ?", (student_id,))
        return True

class CourseRepository:
    """Репозиторий для операций с курсами в базе данных.
    Обеспечивает CRUD операции для сущности Course.
    Args:
        db_manager: Экземпляр DatabaseManager для работы с БД
    """

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def create(self, course: Course) -> int:
        """Создает новый курс в базе данных
        Args:
            course: Объект Course для создания
        Returns:
            ID созданного курса
        """
        query = "INSERT INTO Courses (name, time_start, time_end) VALUES (?, ?, ?)"
        result = self.db.execute(query, (course.name, course.time_start, course.time_end))
        return result.lastrowid

    def get_all(self) -> List[sqlite3.Row]:
        """Получает список всех курсов"""
        return self.db.fetch_all("SELECT * FROM Courses")

    def get_by_id(self, course_id: int):
        """Находит курс по его ID
        Args:
            course_id: ID курса для поиска
        Returns:
            Объект курса или None если не найден
        """
        return self.db.fetch_one("SELECT * FROM Courses WHERE id = ?", (course_id,))

class EnrollmentRepository:
    """Репозиторий для управления записями студентов на курсы.
    Обрабатывает связи многие-ко-многим между студентами и курсами.
    Args:
        db_manager: Экземпляр DatabaseManager для работы с БД
    """

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def enroll(self, student_id: int, course_id: int) -> bool:
        """Записывает студента на курс
        Args:
            student_id: ID студента
            course_id: ID курса
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
            # Происходит если запись уже существует или нарушаются foreign key constraints
            return False

    def get_course_students(self, course_id: int) -> List[sqlite3.Row]:
        """Получает всех студентов, записанных на указанный курс
        Args:
            course_id: ID курса для поиска
        Returns:
            Список студентов на курсе
        """
        query = '''
            SELECT s.* 
            FROM Students s
            JOIN Student_courses sc ON s.id = sc.student_id
            WHERE sc.course_id = ?
        '''
        return self.db.fetch_all(query, (course_id,))

class SchoolSystem:
    """Основной класс системы управления школой.
    Координирует работу всех репозиториев и предоставляет высокоуровневый API.
    Args:
        db_name: Имя файла базы данных (по умолчанию 'school.db')
    """

    def __init__(self, db_name: str = 'school.db'):
        self.db_name = db_name

    def initialize_database(self):
        """Инициализирует структуру базы данных.
        Создает все необходимые таблицы если они не существуют:
        - Students: информация о студентах
        - Courses: информация о курсах
        - Student_courses: таблица связей многие-ко-многим.
        Использует каскадное удаление для поддержания целостности данных.
        """
        with DatabaseManager(self.db_name) as db:
            db.execute_script('''
                -- Таблица студентов с проверкой возраста
                CREATE TABLE IF NOT EXISTS Students(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    surname TEXT NOT NULL, 
                    age INTEGER CHECK (age > 0),
                    city TEXT
                );

                -- Таблица курсов с уникальными названиями
                CREATE TABLE IF NOT EXISTS Courses(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    time_start TEXT,
                    time_end TEXT
                );

                -- Таблица связей с каскадным удалением
                CREATE TABLE IF NOT EXISTS Student_courses(
                    student_id INTEGER,
                    course_id INTEGER,
                    FOREIGN KEY (student_id) REFERENCES Students(id) ON DELETE CASCADE,
                    FOREIGN KEY (course_id) REFERENCES Courses(id) ON DELETE CASCADE,
                    PRIMARY KEY (student_id, course_id)
                );
            ''')
        print(f"База данных {self.db_name} инициализирована")

    def demonstrate_system(self):
        """Демонстрирует полный функционал системы
        Последовательность демонстрации:
        1. Создание курсов
        2. Создание студентов
        3. Запись студентов на курсы
        4. Показ результатов с различными фильтрами
        """
        print("=== ДЕМОНСТРАЦИЯ РАБОТЫ ШКОЛЬНОЙ СИСТЕМЫ ===\n")

        with DatabaseManager(self.db_name) as db:
            # Инициализация репозиториев
            students_repo = StudentRepository(db)
            courses_repo = CourseRepository(db)
            enrollments_repo = EnrollmentRepository(db)

            # Очистка предыдущих демонстрационных данных
            db.execute_script('''
                DELETE FROM Student_courses;
                DELETE FROM Students;
                DELETE FROM Courses;
            ''')

            # 1. СОЗДАНИЕ КУРСОВ
            print("1. СОЗДАНИЕ КУРСОВ:")
            python_course = Course(name="Python", time_start="2024-01-15", time_end="2024-06-15")
            java_course = Course(name="Java", time_start="2024-02-01", time_end="2024-07-01")

            python_id = courses_repo.create(python_course)
            java_id = courses_repo.create(java_course)
            print(f"   Созданы курсы: Python (ID: {python_id}), Java (ID: {java_id})")

            # 2. СОЗДАНИЕ СТУДЕНТОВ
            print("\n2. СОЗДАНИЕ СТУДЕНТОВ:")
            student1 = Student(name="Иван", surname="Петров", age=22, city="Москва")
            student2 = Student(name="Мария", surname="Сидорова", age=19, city="СПб")
            student3 = Student(name="Алексей", surname="Иванов", age=25, city="Москва")

            student1_id = students_repo.create(student1)
            student2_id = students_repo.create(student2)
            student3_id = students_repo.create(student3)
            print(f"   Созданы студенты:")
            print(f"   - Иван Петров (ID: {student1_id})")
            print(f"   - Мария Сидорова (ID: {student2_id})")
            print(f"   - Алексей Иванов (ID: {student3_id})")

            # 3. ЗАПИСЬ НА КУРСЫ
            print("\n3. ЗАПИСЬ СТУДЕНТОВ НА КУРСЫ:")
            enrollments_repo.enroll(student1_id, python_id)
            enrollments_repo.enroll(student2_id, python_id)
            enrollments_repo.enroll(student3_id, java_id)
            print("   Студенты записаны на курсы:")

            # 4. ПОКАЗЫВАЕМ РЕЗУЛЬТАТЫ
            print("\n4. РЕЗУЛЬТАТЫ:")

            # Все студенты
            all_students = students_repo.get_all()
            print(f"   Все студенты ({len(all_students)}):")
            for student in all_students:
                print(f"     - {student['name']} {student['surname']}, {student['age']} лет, {student['city']}")

            # Студенты из Москвы
            moscow_students = students_repo.get_by_city("Москва")
            print(f"\n   Студенты из Москвы ({len(moscow_students)}):")
            for student in moscow_students:
                print(f"     - {student['name']} {student['surname']}")

            # Студенты на курсе Python
            python_students = students_repo.get_by_course("Python")
            print(f"\n   Студенты на курсе Python ({len(python_students)}):")
            for student in python_students:
                print(f"     - {student['name']} {student['surname']}")

            # Студенты на курсе Java
            java_students = enrollments_repo.get_course_students(java_id)
            print(f"\n   Студенты на курсе Java ({len(java_students)}):")
            for student in java_students:
                print(f"     - {student['name']} {student['surname']}")


def main():
    """Основная функция для запуска демонстрации системы"""
    try:
        # Создание экземпляра системы
        school = SchoolSystem()

        print("Инициализация базы данных...")
        school.initialize_database()

        # Запуск демонстрации функционала
        school.demonstrate_system()
        print("\n=== ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА ===")

    except Exception as e:
        print(f"Произошла ошибка: {e}")


# Точка входа в программу
if __name__ == "__main__":
    main()



