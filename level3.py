# Уровень 3.
#
# Напишите ORM для этой базы данных, то есть функции, которые
# позволят быстро выполнять данные запросы без дублирования кода SQL.

"""
School ORM System
Этот модуль предоставляет объектно-реляционное отображение (ORM)
для базы данных. ORM позволяет работать с базой данных
используя объекты Python вместо прямого написания SQL запросов.

Основные компоненты системы:
- DatabaseManager: управление соединением с БД и выполнение запросов
- StudentManager: операции со студентами (CRUD и специализированные запросы)
- CourseManager: операции с курсами (CRUD)
- SchoolORM: основной класс ORM, предоставляющий единую точку доступа

Особенности:
- Использование контекстных менеджеров для безопасной работы с БД
- Параметризованные запросы для защиты от SQL-инъекций
- Типизация для улучшения читаемости и поддержки кода
- Поддержка основных операций без дублирования SQL кода
"""

import sqlite3
from typing import List, Tuple, Optional, Any


class DatabaseManager:
    """
    Менеджер базы данных для управления соединениями и выполнения запросов.
    Этот класс предоставляет абстракцию для работы с SQLite базой данных,
    включая автоматическое управление соединениями и транзакциями.
    Attributes:
        db_name (str): имя файла базы данных
        conn (sqlite3.Connection): объект соединения с БД
        cursor (sqlite3.Cursor): курсор для выполнения запросов
    """

    def __init__(self, db_name: str = 'school.db'):
        """
        Инициализирует менеджер базы данных.

        Args:
            db_name (str): путь к файлу базы данных. По умолчанию 'school.db'
        """
        self.db_name = db_name
        self.conn: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None

    def __enter__(self) -> 'DatabaseManager':
        """
        Вход в контекстный менеджер.
        Открывает соединение с базой данных и создает курсор.
        Автоматически вызывается при использовании with.
        Returns:
            DatabaseManager: текущий экземпляр менеджера БД
        """
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """
        Выход из контекстного менеджера.
        Автоматически вызывается при выходе из блока with.
        Выполняет коммит при успешном выполнении или откат при ошибке.
        Args:
            exc_type: тип исключения (если было)
            exc_val: значение исключения (если было)
            exc_tb: трассировка исключения (если было)
        """
        if self.conn:
            if exc_type is None:
                # Если не было исключения - коммит(им) изменения
                self.conn.commit()
            else:
                # Если было исключение - откатываем транзакцию
                self.conn.rollback()
            self.conn.close()

    def execute_query(self, query: str, params: Tuple = ()) -> List[Tuple]:
        """
        Выполняет SQL запрос и возвращает результат.
        Использует параметризованные запросы для безопасности.
        Args:
            query (str): SQL запрос для выполнения
            params (Tuple): параметры для подстановки в запрос
        Returns:
            List[Tuple]: список кортежей с результатами запроса
        Example:
import db            >>> results = db.execute_query("SELECT * FROM Students WHERE age > ?", (20,))
        """
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def execute_script(self, script: str) -> None:
        """
        Выполняет SQL скрипт, содержащий несколько команд.

        Полезно для инициализации базы данных или массовых операций.

        Args:
            script (str): SQL скрипт для выполнения

        Example:
             db.execute_script('''
            ...     CREATE TABLE IF NOT EXISTS Students(id INTEGER PRIMARY KEY);
            ...     INSERT INTO Students VALUES (1);
            ... ''')
        """
        self.cursor.executescript(script)
        self.conn.commit()

class StudentManager:
    """
    Менеджер для работы со студентами в базе данных.
    Предоставляет методы для выполнения различных запросов связанных со студентами
    без необходимости написания прямых SQL запросов.
    Attributes:
        db (DatabaseManager): менеджер для выполнения запросов к БД
    """

    def __init__(self, db_manager: DatabaseManager):
        """
        Инициализирует менеджер студентов.
        Args:
            db_manager (DatabaseManager): менеджер для работы с БД
        """
        self.db = db_manager

    def get_all(self) -> List[Tuple]:
        """
        Получает всех студентов из базы данных.
        Returns:
            List[Tuple]: список всех студентов, где каждый студент представлен кортежем
            в формате (id, name, surname, age, city)
        """
        return self.db.execute_query("SELECT * FROM Students")

    def get_by_age_gt(self, age: int) -> List[Tuple]:
        """
        Находит студентов старше указанного возраста.
        Args:
            age (int): минимальный возраст (исключающий)
        Returns:
            List[Tuple]: список студентов старше указанного возраста
        """
        return self.db.execute_query("SELECT * FROM Students WHERE age > ?", (age,))

    def get_by_city(self, city: str) -> List[Tuple]:
        """
        Находит студентов из указанного города.
        Args:
            city (str): город для поиска
        Returns:
            List[Tuple]: список студентов из указанного города
        """
        return self.db.execute_query("SELECT * FROM Students WHERE city = ?", (city,))

    def get_by_course(self, course_name: str) -> List[Tuple]:
        """
        Находит студентов, записанных на указанный курс.
        Выполняет JOIN между таблицами Students, Student_courses и Courses
        для нахождения связи между студентами и курсами.
        Args:
            course_name (str): название курса для поиска
        Returns:
            List[Tuple]: список студентов на указанном курсе
        """
        query = '''
            SELECT s.* 
            FROM Students s
            JOIN Student_courses sc ON s.id = sc.student_id
            JOIN Courses c ON sc.course_id = c.id
            WHERE c.name = ?
        '''
        return self.db.execute_query(query, (course_name,))

    def get_by_course_and_city(self, course_name: str, city: str) -> List[Tuple]:
        """
        Находит студентов на указанном курсе из указанного города.
        Комбинирует условия по курсу и городу для точного поиска.
        Args:
            course_name (str): название курса для поиска
            city (str): город для поиска
        Returns:
            List[Tuple]: список студентов, удовлетворяющих обоим условиям
        """
        query = '''
            SELECT s.* 
            FROM Students s
            JOIN Student_courses sc ON s.id = sc.student_id
            JOIN Courses c ON sc.course_id = c.id
            WHERE c.name = ? AND s.city = ?
        '''
        return self.db.execute_query(query, (course_name, city))

class CourseManager:
    """
    Менеджер для работы с курсами в базе данных.
    Предоставляет методы для выполнения запросов связанных с курсами.
    Attributes:
        db (DatabaseManager): менеджер для выполнения запросов к БД
    """

    def __init__(self, db_manager: DatabaseManager):
        """
        Инициализирует менеджер курсов.
        Args:
            db_manager (DatabaseManager): менеджер для работы с БД
        """
        self.db = db_manager

    def get_all(self) -> List[Tuple]:
        """
        Получает все курсы из базы данных.
        Returns:
            List[Tuple]: список всех курсов, где каждый курс представлен кортежем
            в формате (id, name, time_start, time_end)
        """
        return self.db.execute_query("SELECT * FROM Courses")

    def get_by_name(self, name: str) -> List[Tuple]:
        """
        Находит курс по точному совпадению имени.
        Args:
            name (str): название курса для поиска
        Returns:
            List[Tuple]: информация о найденном курсе
        """
        return self.db.execute_query("SELECT * FROM Courses WHERE name = ?", (name,))

class SchoolORM:
    """
    Основной класс ORM для работы с учебной базой данных.
    Предоставляет единый интерфейс для работы со всеми сущностями системы
    и управляет жизненным циклом соединения с базой данных.
    Attributes:
        db_name (str): имя файла базы данных
        db_manager (DatabaseManager): менеджер для работы с БД
        students (StudentManager): менеджер для работы со студентами
        courses (CourseManager): менеджер для работы с курсами
    """

    def __init__(self, db_name: str = 'school.db'):
        """
        Инициализирует ORM систему.
        Args:
            db_name (str): путь к файлу базы данных. По умолчанию 'school.db'
        """
        self.db_name = db_name
        self.db_manager: Optional[DatabaseManager] = None
        self.students: Optional[StudentManager] = None
        self.courses: Optional[CourseManager] = None

    def __enter__(self) -> 'SchoolORM':
        """
        Вход в контекстный менеджер.
        Создает и настраивает все необходимые менеджеры для работы с БД.
        Returns:
            SchoolORM: текущий экземпляр ORM
        """
        self.db_manager = DatabaseManager(self.db_name)
        self.db_manager.__enter__()
        self.students = StudentManager(self.db_manager)
        self.courses = CourseManager(self.db_manager)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """
        Выход из контекстного менеджера.
        Корректно закрывает соединение с базой данных.
        Args:
            exc_type: тип исключения (если было)
            exc_val: значение исключения (если было)
            exc_tb: трассировка исключения (если было)
        """
        if self.db_manager:
            self.db_manager.__exit__(exc_type, exc_val, exc_tb)

    def initialize(self) -> None:
        """
        Инициализирует базу данных - создает все необходимые таблицы.

        Создает три таблицы:
        - Students: информация о студентах (id, имя, фамилия, возраст, город)
        - Courses: информация о курсах (id, название, дата начала, дата окончания)
        - Student_courses: таблица связи многие-ко-многим между студентами и курсами

        Если таблицы уже существуют, они не пересоздаются благодаря IF NOT EXISTS.
        """
        with DatabaseManager(self.db_name) as db:
            db.execute_script('''
                -- Таблица студентов с основной информацией
                CREATE TABLE IF NOT EXISTS Students(
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    surname TEXT NOT NULL, 
                    age INTEGER CHECK (age > 0),
                    city TEXT
                );

                -- Таблица курсов с расписанием
                CREATE TABLE IF NOT EXISTS Courses(
                    id INTEGER PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    time_start TEXT,
                    time_end TEXT
                );

                -- Таблица связи студентов и курсов (многие-ко-многим)
                CREATE TABLE IF NOT EXISTS Student_courses(
                    student_id INTEGER,
                    course_id INTEGER,
                    FOREIGN KEY (student_id) REFERENCES Students(id) ON DELETE CASCADE,
                    FOREIGN KEY (course_id) REFERENCES Courses(id) ON DELETE CASCADE,
                    PRIMARY KEY (student_id, course_id)
                );
            ''')

    def setup_test_data(self) -> None:
        """
        Заполняет базу данных тестовыми данными для демонстрации работы ORM.
        Очищает существующие данные и добавляет:
        - 2 курса: Python и Java
        - 4 студентов с разными характеристиками
        - Связи между студентами и курсами
        Это метод предназначен для тестирования и демонстрации возможностей системы.
        """
        with DatabaseManager(self.db_name) as db:
            # Очистка таблиц (в правильном порядке из-за внешних ключей)
            db.execute_script('''
                DELETE FROM Student_courses;
                DELETE FROM Students;
                DELETE FROM Courses;
            ''')

            # Добавление тестовых курсов
            courses_data = [
                (1, 'python', '2021-07-21', '2021-08-21'),
                (2, 'java', '2021-07-13', '2021-08-16')
            ]
            db.cursor.executemany(
                "INSERT INTO Courses VALUES (?, ?, ?, ?)",
                courses_data
            )

            # Добавление тестовых студентов
            students_data = [
                (1, 'Max', 'Brooks', 24, 'Spb'),
                (2, 'John', 'Stones', 15, 'Spb'),
                (3, 'Andy', 'Wings', 45, 'Manchester'),
                (4, 'Kate', 'Brooks', 34, 'Spb')
            ]
            db.cursor.executemany(
                "INSERT INTO Students VALUES (?, ?, ?, ?, ?)",
                students_data
            )

            # Создание связей между студентами и курсами
            student_courses_data = [
                (1, 1),  # Max на Python
                (2, 1),  # John на Python
                (3, 1),  # Andy на Python
                (4, 2)  # Kate на Java
            ]
            db.cursor.executemany(
                "INSERT INTO Student_courses VALUES (?, ?)",
                student_courses_data
            )

            db.conn.commit()

def demonstrate_orm_capabilities() -> None:
    """
    Демонстрирует все основные возможности ORM системы.
    Показывает различные сценарии использования:
    - Поиск студентов по возрасту
    - Поиск студентов по курсу
    - Комбинированные запросы
    - Получение всех данных
    """
    print("=== ДЕМОНСТРАЦИЯ ВОЗМОЖНОСТЕЙ SCHOOL ORM ===\n")

    # Использование ORM через контекстный менеджер
    with SchoolORM() as orm:
        # 1. Все студенты старше 30 лет
        print("1. Все студенты старше 30 лет:")
        students_over_30 = orm.students.get_by_age_gt(30)
        for student in students_over_30:
            print(f"   - {student[1]} {student[2]}, {student[3]} лет, г. {student[4]}")

        # 2. Все студенты на курсе Python
        print("\n2. Все студенты, которые проходят курс по Python:")
        python_students = orm.students.get_by_course('python')
        for student in python_students:
            print(f"   - {student[1]} {student[2]}, {student[3]} лет, г. {student[4]}")

        # 3. Студенты на курсе Python из Spb
        print("\n3. Все студенты, которые проходят курс по Python и из Spb:")
        python_spb_students = orm.students.get_by_course_and_city('python', 'Spb')
        for student in python_spb_students:
            print(f"   - {student[1]} {student[2]}, {student[3]} лет")

        # 4. Все студенты из Spb
        print("\n4. Все студенты из Spb:")
        spb_students = orm.students.get_by_city('Spb')
        for student in spb_students:
            print(f"   - {student[1]} {student[2]}, {student[3]} лет")

        # 5. Все курсы
        print("\n5. Все доступные курсы:")
        all_courses = orm.courses.get_all()
        for course in all_courses:
            print(f"   - {course[1]}: с {course[2]} по {course[3]}")

        # 6. Общая статистика
        print("\n6. Статистика базы данных:")
        all_students = orm.students.get_all()
        print(f"   - Всего студентов: {len(all_students)}")
        print(f"   - Всего курсов: {len(all_courses)}")
        print(f"   - Студентов старше 30: {len(students_over_30)}")
        print(f"   - Студентов на Python: {len(python_students)}")

def main() -> None:
    """
    Основная функция для запуска демонстрации ORM системы.
    Выполняет:
    1. Инициализацию базы данных
    2. Заполнение тестовыми данными
    3. Демонстрацию всех возможностей ORM
    """
    try:
        # Создание экземпляра ORM
        school_orm = SchoolORM()

        # Инициализация структуры базы данных
        print("Инициализация базы данных...")
        school_orm.initialize()

        # Заполнение тестовыми данными
        print("Заполнение тестовыми данными...")
        school_orm.setup_test_data()

        # Демонстрация возможностей
        demonstrate_orm_capabilities()

        print("\n=== ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА ===")

    except Exception as e:
        print(f"Произошла ошибка: {e}")
        # В реальном приложении здесь должно быть логирование ошибки


# Точка входа в программу
if __name__ == "__main__":
    main()
