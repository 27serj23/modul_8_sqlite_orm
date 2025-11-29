# Уровень 3.
#
# Напишите ORM для этой базы данных, то есть функции, которые
# позволят быстро выполнять данные запросы без дублирования кода SQL.

"""
School ORM System - Уровень 3
🎓 Объектно-реляционное отображение (ORM) для школьной базы данных.
"""

import sqlite3
import os
from typing import List, Optional, Protocol
from dataclasses import dataclass

# =============================================================================
# PROTOCOLS (ПРОТОКОЛЫ ДЛЯ ТИПИЗАЦИИ)
# =============================================================================

class StudentProtocol(Protocol):
    """Протокол для типизации объектов студента"""
    id: Optional[int]
    name: str
    surname: str
    age: int
    city: str


class CourseProtocol(Protocol):
    """Протокол для типизации объектов курса"""
    id: Optional[int]
    name: str
    time_start: str
    time_end: str

# =============================================================================
# ENTITY LAYER (СЛОЙ СУЩНОСТЕЙ)
# =============================================================================

@dataclass
class Student:
    """
    Сущность студента - объектное представление строки таблицы Students.
    Реализует StudentProtocol для типизации.
    """
    id: Optional[int] = None
    name: str = ""
    surname: str = ""
    age: int = 0
    city: str = ""

    def __str__(self) -> str:
        return f"{self.name} {self.surname}, {self.age} лет, {self.city}"

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> 'Student':
        """
        Создает объект Student напрямую из строки БД.
        Args:
            row: Строка результата SQLite запроса
        Returns:
            Student: Объект студента
        """
        return cls(
            id=row['id'],
            name=row['name'],
            surname=row['surname'],
            age=row['age'],
            city=row['city']
        )

@dataclass
class Course:
    """
    Сущность курса - объектное представление строки таблицы Courses.
    Реализует CourseProtocol для типизации.
    """
    id: Optional[int] = None
    name: str = ""
    time_start: str = ""
    time_end: str = ""

    def __str__(self) -> str:
        return f"{self.name} ({self.time_start} - {self.time_end})"

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> 'Course':
        """
        Создает объект Course напрямую из строки БД.
        Args:
            row: Строка результата SQLite запроса
        Returns:
            Course: Объект курса
        """
        return cls(
            id=row['id'],
            name=row['name'],
            time_start=row['time_start'],
            time_end=row['time_end']
        )

# =============================================================================
# REPOSITORY LAYER (СЛОЙ ДОСТУПА К ДАННЫМ)
# =============================================================================

class StudentRepository:
    """
    Репозиторий для работы со студентами в базе данных.
    """

    def __init__(self, db_connection: sqlite3.Connection):
        self.db = db_connection

    def create(self, student: StudentProtocol) -> int:
        """Создает нового студента в базе данных."""
        cursor = self.db.cursor()
        cursor.execute(
            "INSERT INTO Students (name, surname, age, city) VALUES (?, ?, ?, ?)",
            (student.name, student.surname, student.age, student.city)
        )
        self.db.commit()
        return cursor.lastrowid

    def get_all(self) -> List[Student]:
        """Получает всех студентов из базы данных."""
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM Students")
        # Оптимизация: прямой вызов from_row вместо преобразования через dict
        return [Student.from_row(row) for row in cursor.fetchall()]

    def get_by_id(self, student_id: int) -> Optional[Student]:
        """Находит студента по его ID."""
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM Students WHERE id = ?", (student_id,))
        row = cursor.fetchone()
        return Student.from_row(row) if row else None

    def update(self, student: StudentProtocol) -> bool:
        """Обновляет данные существующего студента."""
        if student.id is None:
            raise ValueError("Нельзя обновить студента без ID")

        cursor = self.db.cursor()
        cursor.execute(
            "UPDATE Students SET name = ?, surname = ?, age = ?, city = ? WHERE id = ?",
            (student.name, student.surname, student.age, student.city, student.id)
        )
        self.db.commit()
        return cursor.rowcount > 0

    def delete(self, student_id: int) -> bool:
        """Удаляет студента по ID."""
        cursor = self.db.cursor()
        cursor.execute("DELETE FROM Students WHERE id = ?", (student_id,))
        self.db.commit()
        return cursor.rowcount > 0

    def get_by_age_gt(self, age: int) -> List[Student]:
        """Находит студентов старше указанного возраста."""
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM Students WHERE age > ?", (age,))
        return [Student.from_row(row) for row in cursor.fetchall()]

    def get_by_city(self, city: str) -> List[Student]:
        """Находит студентов из указанного города."""
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM Students WHERE city = ?", (city,))
        return [Student.from_row(row) for row in cursor.fetchall()]

    def count(self) -> int:
        """Возвращает общее количество студентов в базе."""
        cursor = self.db.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM Students")
        return cursor.fetchone()['count']


class CourseRepository:
    """
    Репозиторий для работы с курсами в базе данных.
    """

    def __init__(self, db_connection: sqlite3.Connection):
        self.db = db_connection

    def create(self, course: CourseProtocol) -> int:
        """Создает новый курс в базе данных."""
        cursor = self.db.cursor()
        cursor.execute(
            "INSERT INTO Courses (name, time_start, time_end) VALUES (?, ?, ?)",
            (course.name, course.time_start, course.time_end)
        )
        self.db.commit()
        return cursor.lastrowid

    def get_all(self) -> List[Course]:
        """Получает все курсы из базы данных."""
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM Courses")
        return [Course.from_row(row) for row in cursor.fetchall()]

    def get_by_id(self, course_id: int) -> Optional[Course]:
        """Находит курс по ID."""
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM Courses WHERE id = ?", (course_id,))
        row = cursor.fetchone()
        return Course.from_row(row) if row else None

    def get_by_name(self, name: str) -> Optional[Course]:
        """Находит курс по точному совпадению имени."""
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM Courses WHERE name = ?", (name,))
        row = cursor.fetchone()
        return Course.from_row(row) if row else None

    def count(self) -> int:
        """Возвращает общее количество курсов в базе."""
        cursor = self.db.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM Courses")
        return cursor.fetchone()['count']


class EnrollmentRepository:
    """
    Репозиторий для управления связями.
    """

    def __init__(self, db_connection: sqlite3.Connection):
        self.db = db_connection

    def enroll(self, student_id: int, course_id: int) -> bool:
        """Записывает студента на курс."""
        try:
            cursor = self.db.cursor()
            cursor.execute(
                "INSERT INTO Student_Courses (student_id, course_id) VALUES (?, ?)",
                (student_id, course_id)
            )
            self.db.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def unenroll(self, student_id: int, course_id: int) -> bool:
        """Отписывает студента от курса."""
        cursor = self.db.cursor()
        cursor.execute(
            "DELETE FROM Student_Courses WHERE student_id = ? AND course_id = ?",
            (student_id, course_id)
        )
        self.db.commit()
        return cursor.rowcount > 0

    def get_students_on_course(self, course_name: str) -> List[Student]:
        """Находит всех студентов, записанных на указанный курс."""
        cursor = self.db.cursor()
        cursor.execute('''
            SELECT s.* 
            FROM Students s
            JOIN Student_Courses sc ON s.id = sc.student_id
            JOIN Courses c ON sc.course_id = c.id
            WHERE c.name = ?
        ''', (course_name,))
        return [Student.from_row(row) for row in cursor.fetchall()]

    def get_students_on_course_from_city(self, course_name: str, city: str) -> List[Student]:
        """Находит студентов на курсе из указанного города."""
        cursor = self.db.cursor()
        cursor.execute('''
            SELECT s.* 
            FROM Students s
            JOIN Student_Courses sc ON s.id = sc.student_id
            JOIN Courses c ON sc.course_id = c.id
            WHERE c.name = ? AND s.city = ?
        ''', (course_name, city))
        return [Student.from_row(row) for row in cursor.fetchall()]

# =============================================================================
# SERVICE LAYER (СЛОЙ БИЗНЕС-ЛОГИКИ)
# =============================================================================

class SchoolService:
    """
    Сервисный слой с бизнес-логикой школы.
    """

    def __init__(self, db_connection: sqlite3.Connection):
        self.students = StudentRepository(db_connection)
        self.courses = CourseRepository(db_connection)
        self.enrollments = EnrollmentRepository(db_connection)

    def get_students_count(self) -> int:
        """Возвращает количество студентов через репозиторий."""
        return self.students.count()

    def get_courses_count(self) -> int:
        """Возвращает количество курсов через репозиторий."""
        return self.courses.count()

# =============================================================================
# DATABASE LAYER (СЛОЙ БАЗЫ ДАННЫХ)
# =============================================================================

class DatabaseManager:
    """
    Менеджер базы данных для управления соединениями и транзакциями.
    Типизирован с конкретными типами.
    """

    def __init__(self, db_name: str = 'school_optimized.db'):
        self.db_name = db_name
        self.conn: Optional[sqlite3.Connection] = None

    def __enter__(self) -> SchoolService:
        """Вход в контекстный менеджер."""
        self.conn = sqlite3.connect(self.db_name)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
        return SchoolService(self.conn)

    def __exit__(self, exc_type: Optional[type], exc_val: Optional[Exception], exc_tb: Optional[object]) -> None:
        """Выход из контекстного менеджера."""
        if self.conn:
            if exc_type is None:
                self.conn.commit()
            else:
                self.conn.rollback()
            self.conn.close()

    def _create_tables(self) -> None:
        """Создает таблицы базы данных если они не существуют."""
        cursor = self.conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Students(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                surname TEXT NOT NULL,
                age INTEGER NOT NULL CHECK (age > 0),
                city TEXT NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Courses(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                time_start TEXT NOT NULL,
                time_end TEXT NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Student_Courses(
                student_id INTEGER,
                course_id INTEGER,
                FOREIGN KEY (student_id) REFERENCES Students(id) ON DELETE CASCADE,
                FOREIGN KEY (course_id) REFERENCES Courses(id) ON DELETE CASCADE,
                PRIMARY KEY (student_id, course_id)
            )
        ''')
        self.conn.commit()

# =============================================================================
# UI LAYER (СЛОЙ ПОЛЬЗОВАТЕЛЬСКОГО ИНТЕРФЕЙСА)
# =============================================================================

def clear_screen() -> None:
    """Очищает экран терминала."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title: str) -> None:
    """Выводит заголовок с форматированием."""
    print("=" * 60)
    print(f"🎓 {title}")
    print("=" * 60)

def wait_for_enter() -> None:
    """Ожидает нажатия Enter для продолжения."""
    input("\n↵ Нажмите Enter чтобы продолжить...")


def input_student_data(existing_student: Optional[Student] = None) -> Student:
    """
    Вводит данные студента с клавиатуры с валидацией.
    Args:
        existing_student: Существующий студент для обновления
    Returns:
        Student: Объект студента с введенными данными
    """
    if existing_student:
        print("\nТекущие данные студента:")
        print(f"  ID: {existing_student.id}")
        print(f"  Имя: {existing_student.name}")
        print(f"  Фамилия: {existing_student.surname}")
        print(f"  Возраст: {existing_student.age}")
        print(f"  Город: {existing_student.city}")
        print("\nВведите новые данные (оставьте пустым чтобы не менять):")
    else:
        print("\nВведите данные нового студента:")

    # Валидация ввода
    while True:
        name = input("Имя: ").strip()
        if name:
            break
        print("❌ Имя не может быть пустым")

    while True:
        surname = input("Фамилия: ").strip()
        if surname:
            break
        print("❌ Фамилия не может быть пустой")

    while True:
        age_input = input("Возраст: ").strip()
        try:
            age = int(age_input)
            if age > 0:
                break
            print("❌ Возраст должен быть больше 0")
        except ValueError:
            print("❌ Возраст должен быть числом")

    while True:
        city = input("Город: ").strip()
        if city:
            break
        print("❌ Город не может быть пустым")

    if existing_student:
        return Student(
            id=existing_student.id,
            name=name,
            surname=surname,
            age=age,
            city=city
        )
    else:
        return Student(
            name=name,
            surname=surname,
            age=age,
            city=city
        )


def input_course_data(existing_course: Optional[Course] = None) -> Course:
    """
    Вводит данные курса с клавиатуры с валидацией.
    Args:
        existing_course: Существующий курс для обновления
    Returns:
        Course: Объект курса с введенными данными
    """
    if existing_course:
        print("\nТекущие данные курса:")
        print(f"  ID: {existing_course.id}")
        print(f"  Название: {existing_course.name}")
        print(f"  Начало: {existing_course.time_start}")
        print(f"  Конец: {existing_course.time_end}")
        print("\nВведите новые данные (оставьте пустым чтобы не менять):")
    else:
        print("\nВведите данные нового курса:")

    while True:
        name = input("Название курса: ").strip()
        if name:
            break
        print("❌ Название курса не может быть пустым")

    while True:
        time_start = input("Дата начала (дд.мм.гг): ").strip()
        if time_start:
            break
        print("❌ Дата начала не может быть пустой")

    while True:
        time_end = input("Дата окончания (дд.мм.гг): ").strip()
        if time_end:
            break
        print("❌ Дата окончания не может быть пустой")

    if existing_course:
        return Course(
            id=existing_course.id,
            name=name,
            time_start=time_start,
            time_end=time_end
        )
    else:
        return Course(
            name=name,
            time_start=time_start,
            time_end=time_end
        )


def show_students_table(students: List[Student]) -> None:
    """Выводит список студентов в виде форматированной таблицы."""
    if not students:
        print("┌─────────────────────────────────────────────┐")
        print("│             Нет студентов в базе            │")
        print("└─────────────────────────────────────────────┘")
        return

    print("┌───┬────────────┬───────────────┬─────┬────────────┐")
    print("│ID │    Имя     │    Фамилия    │Возр │    Город    │")
    print("├───┼────────────┼───────────────┼─────┼────────────┤")

    for student in students:
        print(f"│{student.id:3}│{student.name:12}│{student.surname:15}│{student.age:5}│{student.city:12}│")

    print("└───┴────────────┴───────────────┴─────┴────────────┘")


def show_courses_table(courses: List[Course]) -> None:
    """Выводит список курсов в виде форматированной таблицы."""
    if not courses:
        print("┌─────────────────────────────────────────────┐")
        print("│              Нет курсов в базе              │")
        print("└─────────────────────────────────────────────┘")
        return

    print("┌───┬────────────┬────────────┬────────────┐")
    print("│ID │   Название │   Начало   │   Конец    │")
    print("├───┼────────────┼────────────┼────────────┤")

    for course in courses:
        print(f"│{course.id:3}│{course.name:12}│{course.time_start:12}│{course.time_end:12}│")

    print("└───┴────────────┴────────────┴────────────┘")


# =============================================================================
# MENU SYSTEM (СИСТЕМА МЕНЮ)
# =============================================================================

def menu_manage_students(service: SchoolService) -> None:
    """Меню управления студентами."""
    while True:
        clear_screen()
        print_header("УПРАВЛЕНИЕ СТУДЕНТАМИ")
        print(f"📊 В базе: {service.get_students_count()} студентов")

        print("\nВыберите действие:")
        print("1. 📋 Показать всех студентов")
        print("2. 🆕 Добавить нового студента")
        print("3. ✏  Обновить данные студента")
        print("4. 🗑  Удалить студента")
        print("5. 🔍 Найти студента по ID")
        print("0. ↩  Назад в главное меню")

        choice = input("\nВаш выбор: ").strip()

        if choice == "1":
            clear_screen()
            print_header("ВСЕ СТУДЕНТЫ")
            students = service.students.get_all()
            show_students_table(students)
            wait_for_enter()

        elif choice == "2":
            clear_screen()
            print_header("ДОБАВЛЕНИЕ СТУДЕНТА")
            try:
                student = input_student_data()
                student_id = service.students.create(student)
                print(f"\n✅ Студент успешно добавлен! ID: {student_id}")
            except Exception as e:
                print(f"\n❌ Ошибка при добавлении: {e}")
            wait_for_enter()

        elif choice == "3":
            clear_screen()
            print_header("ОБНОВЛЕНИЕ СТУДЕНТА")
            students = service.students.get_all()
            if not students:
                print("❌ В базе нет студентов для обновления")
                wait_for_enter()
                continue

            show_students_table(students)

            try:
                student_id = int(input("\nВведите ID студента для обновления: "))
                existing_student = service.students.get_by_id(student_id)

                if not existing_student:
                    print(f"❌ Студент с ID {student_id} не найден")
                else:
                    student = input_student_data(existing_student)
                    if service.students.update(student):
                        print("\n✅ Данные студента обновлены!")
                    else:
                        print("\n❌ Ошибка при обновлении данных")
            except ValueError:
                print("❌ Неверный формат ID")
            except Exception as e:
                print(f"❌ Ошибка: {e}")

            wait_for_enter()

        elif choice == "4":
            clear_screen()
            print_header("УДАЛЕНИЕ СТУДЕНТА")
            students = service.students.get_all()
            if not students:
                print("❌ В базе нет студентов для удаления")
                wait_for_enter()
                continue

            show_students_table(students)

            try:
                student_id = int(input("\nВведите ID студента для удаления: "))

                confirm = input("Вы уверены? (д/н): ").strip().lower()
                if confirm in ['д', 'да', 'y', 'yes']:
                    if service.students.delete(student_id):
                        print("✅ Студент удален!")
                    else:
                        print(f"❌ Студент с ID {student_id} не найден")
                else:
                    print("❌ Удаление отменено")
            except ValueError:
                print("❌ Неверный формат ID")

            wait_for_enter()

        elif choice == "5":
            clear_screen()
            print_header("ПОИСК СТУДЕНТА ПО ID")
            try:
                student_id = int(input("Введите ID студента: "))
                student = service.students.get_by_id(student_id)

                if student:
                    print(f"\n✅ Найден студент:")
                    show_students_table([student])
                else:
                    print(f"\n❌ Студент с ID {student_id} не найден")
            except ValueError:
                print("❌ Неверный формат ID")

            wait_for_enter()

        elif choice == "0":
            break
        else:
            print("❌ Неверный выбор. Попробуйте снова.")
            wait_for_enter()


def menu_manage_courses(service: SchoolService) -> None:
    """Меню управления курсами."""
    while True:
        clear_screen()
        print_header("УПРАВЛЕНИЕ КУРСАМИ")
        print(f"📊 В базе: {service.get_courses_count()} курсов")

        print("\nВыберите действие:")
        print("1. 📋 Показать все курсы")
        print("2. 🆕 Добавить новый курс")
        print("3. 🔍 Найти курс по ID")
        print("0. ↩  Назад в главное меню")

        choice = input("\nВаш выбор: ").strip()

        if choice == "1":
            clear_screen()
            print_header("ВСЕ КУРСЫ")
            courses = service.courses.get_all()
            show_courses_table(courses)
            wait_for_enter()

        elif choice == "2":
            clear_screen()
            print_header("ДОБАВЛЕНИЕ КУРСА")
            try:
                course = input_course_data()
                course_id = service.courses.create(course)
                print(f"\n✅ Курс успешно добавлен! ID: {course_id}")
            except Exception as e:
                print(f"\n❌ Ошибка при добавлении: {e}")
            wait_for_enter()

        elif choice == "3":
            clear_screen()
            print_header("ПОИСК КУРСА ПО ID")
            try:
                course_id = int(input("Введите ID курса: "))
                course = service.courses.get_by_id(course_id)

                if course:
                    print(f"\n✅ Найден курс:")
                    show_courses_table([course])
                else:
                    print(f"\n❌ Курс с ID {course_id} не найден")
            except ValueError:
                print("❌ Неверный формат ID")

            wait_for_enter()

        elif choice == "0":
            break
        else:
            print("❌ Неверный выбор. Попробуйте снова.")
            wait_for_enter()


def menu_enrollments(service: SchoolService) -> None:
    """Меню записей на курсы."""
    while True:
        clear_screen()
        print_header("ЗАПИСИ НА КУРСЫ")

        print("\nВыберите действие:")
        print("1. 📝 Записать студента на курс")
        print("2. 👨‍🎓 Показать студентов на курсе")
        print("3. 🏙  Показать студентов на курсе из города")
        print("0. ↩  Назад в главное меню")

        choice = input("\nВаш выбор: ").strip()

        if choice == "1":
            clear_screen()
            print_header("ЗАПИСЬ СТУДЕНТА НА КУРС")

            students = service.students.get_all()
            if not students:
                print("❌ В базе нет студентов")
                wait_for_enter()
                continue

            print("Доступные студенты:")
            show_students_table(students)

            courses = service.courses.get_all()
            if not courses:
                print("\n❌ В базе нет курсов")
                wait_for_enter()
                continue

            print("\nДоступные курсы:")
            show_courses_table(courses)

            try:
                student_id = int(input("\nВведите ID студента: "))
                course_id = int(input("Введите ID курса: "))

                if service.enrollments.enroll(student_id, course_id):
                    print("✅ Студент успешно записан на курс!")
                else:
                    print("❌ Ошибка: студент уже записан на этот курс")

            except ValueError:
                print("❌ Неверный формат ID")
            except Exception as e:
                print(f"❌ Ошибка: {e}")

            wait_for_enter()

        elif choice == "2":
            clear_screen()
            print_header("СТУДЕНТЫ НА КУРСЕ")

            courses = service.courses.get_all()
            if not courses:
                print("❌ В базе нет курсов")
                wait_for_enter()
                continue

            show_courses_table(courses)

            course_name = input("\nВведите название курса: ").strip()
            students = service.enrollments.get_students_on_course(course_name)

            if students:
                print(f"\n📊 Студенты на курсе '{course_name}':")
                show_students_table(students)
            else:
                print(f"\n❌ На курсе '{course_name}' нет студентов или курс не существует")

            wait_for_enter()

        elif choice == "3":
            clear_screen()
            print_header("СТУДЕНТЫ НА КУРСЕ ИЗ ГОРОДА")

            courses = service.courses.get_all()
            if not courses:
                print("❌ В базе нет курсов")
                wait_for_enter()
                continue

            show_courses_table(courses)

            course_name = input("\nВведите название курса: ").strip()
            city = input("Введите город: ").strip()

            students = service.enrollments.get_students_on_course_from_city(course_name, city)

            if students:
                print(f"\n📊 Студенты на курсе '{course_name}' из города '{city}':")
                show_students_table(students)
            else:
                print(f"\n❌ На курсе '{course_name}' нет студентов из города '{city}'")

            wait_for_enter()

        elif choice == "0":
            break
        else:
            print("❌ Неверный выбор. Попробуйте снова.")
            wait_for_enter()


def menu_queries(service: SchoolService) -> None:
    """Меню специальных запросов."""
    while True:
        clear_screen()
        print_header("СПЕЦИАЛЬНЫЕ ЗАПРОСЫ")

        print("\nВыберите запрос:")
        print("1. 🎂 Студенты старше указанного возраста")
        print("2. 🏙  Студенты из указанного города")
        print("0. ↩  Назад в главное меню")

        choice = input("\nВаш выбор: ").strip()

        if choice == "1":
            clear_screen()
            print_header("СТУДЕНТЫ СТАРШЕ ВОЗРАСТА")

            try:
                age = int(input("Введите возраст: "))
                students = service.students.get_by_age_gt(age)

                if students:
                    print(f"\n📊 Студенты старше {age} лет:")
                    show_students_table(students)
                else:
                    print(f"\n❌ Нет студентов старше {age} лет")

            except ValueError:
                print("❌ Неверный формат возраста")

            wait_for_enter()

        elif choice == "2":
            clear_screen()
            print_header("СТУДЕНТЫ ИЗ ГОРОДА")

            city = input("Введите город: ").strip()
            students = service.students.get_by_city(city)

            if students:
                print(f"\n📊 Студенты из города '{city}':")
                show_students_table(students)
            else:
                print(f"\n❌ Нет студентов из города '{city}'")

            wait_for_enter()

        elif choice == "0":
            break
        else:
            print("❌ Неверный выбор. Попробуйте снова.")
            wait_for_enter()


def main_menu() -> None:
    """Главное меню приложения."""
    with DatabaseManager() as service:
        while True:
            clear_screen()
            print_header("ГЛАВНОЕ МЕНЮ - ШКОЛЬНАЯ СИСТЕМА")
            print(f"📊 Статистика: {service.get_students_count()} студентов, {service.get_courses_count()} курсов")

            print("\nВыберите раздел:")
            print("1. 👨‍🎓 Управление студентами")
            print("2. 🎯 Управление курсами")
            print("3. 📚 Записи на курсы")
            print("4. 🔍 Специальные запросы")
            print("0. 🚪 Выход")
            print("-" * 50)

            choice = input("Ваш выбор: ").strip()

            if choice == "1":
                menu_manage_students(service)
            elif choice == "2":
                menu_manage_courses(service)
            elif choice == "3":
                menu_enrollments(service)
            elif choice == "4":
                menu_queries(service)
            elif choice == "0":
                print("\n👋 До свидания!")
                break
            else:
                print("❌ Неверный выбор. Попробуйте снова.")
                wait_for_enter()


def main() -> None:
    """Главная функция приложения."""
    clear_screen()
    print("=" * 70)
    print("        🎓 ШКОЛЬНАЯ ORM СИСТЕМА ")
    print("=" * 70)
    print("📁 База данных:", os.path.abspath('school_optimized.db'))
    print("\nНажмите Enter чтобы начать...")
    input()

    try:
        main_menu()
        print(f"\n✅ Программа успешно завершена!")
        print(f"📁 Файл базы данных: {os.path.abspath('school_optimized.db')}")

    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()


