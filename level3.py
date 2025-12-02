
# Уровень 3.
#
# Напишите ORM для этой базы данных, то есть функции, которые
# позволят быстро выполнять данные запросы без дублирования кода SQL.
"""
School ORM System - Уровень 3
🎓 Объектно-реляционное отображение (ORM) для школьной базы данных
"""

import sqlite3
import os
from typing import List, Optional, Dict, Any
from dataclasses import dataclass


# =============================================================================
# ENTITY LAYER
# =============================================================================

@dataclass
class Student:
    """Сущность студента."""
    id: Optional[int] = None
    name: str = ""
    surname: str = ""
    age: int = 0
    city: str = ""

    def __str__(self) -> str:
        return f"{self.name}, {self.surname}, {self.age}, {self.city}"

    @classmethod
    def from_row(cls, row) -> 'Student':
        return cls(
            id=row['id'] if 'id' in row.keys() else row[0],
            name=row['name'] if 'name' in row.keys() else row[1],
            surname=row['surname'] if 'surname' in row.keys() else row[2],
            age=row['age'] if 'age' in row.keys() else row[3],
            city=row['city'] if 'city' in row.keys() else row[4]
        )


@dataclass
class Course:
    """Сущность курса."""
    id: Optional[int] = None
    name: str = ""
    time_start: str = ""
    time_end: str = ""

    def __str__(self) -> str:
        return f"{self.name} ({self.time_start} - {self.time_end})"

    @classmethod
    def from_row(cls, row) -> 'Course':
        return cls(
            id=row['id'] if 'id' in row.keys() else row[0],
            name=row['name'] if 'name' in row.keys() else row[1],
            time_start=row['time_start'] if 'time_start' in row.keys() else row[2],
            time_end=row['time_end'] if 'time_end' in row.keys() else row[3]
        )


# =============================================================================
# REPOSITORY LAYER
# =============================================================================

class StudentRepository:
    """Репозиторий для работы со студентами."""

    def __init__(self, db_connection: sqlite3.Connection):
        self.db = db_connection

    def create(self, student: Student) -> int:
        cursor = self.db.cursor()
        cursor.execute(
            "INSERT INTO Students (name, surname, age, city) VALUES (?, ?, ?, ?)",
            (student.name, student.surname, student.age, student.city)
        )
        self.db.commit()
        return cursor.lastrowid

    def get_all(self) -> List[Student]:
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM Students")
        rows = cursor.fetchall()
        return [Student.from_row(row) for row in rows]

    def get_by_id(self, student_id: int) -> Optional[Student]:
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM Students WHERE id = ?", (student_id,))
        row = cursor.fetchone()
        return Student.from_row(row) if row else None

    def get_by_ids(self, student_ids: List[int]) -> List[Student]:
        if not student_ids:
            return []

        placeholders = ','.join('?' for _ in student_ids)
        cursor = self.db.cursor()
        cursor.execute(f"SELECT * FROM Students WHERE id IN ({placeholders})", student_ids)
        rows = cursor.fetchall()
        return [Student.from_row(row) for row in rows]

    def update(self, student: Student) -> bool:
        if student.id is None:
            raise ValueError("Студент не имеет ID")

        cursor = self.db.cursor()
        cursor.execute(
            "UPDATE Students SET name = ?, surname = ?, age = ?, city = ? WHERE id = ?",
            (student.name, student.surname, student.age, student.city, student.id)
        )
        self.db.commit()
        return cursor.rowcount > 0

    def delete(self, student_id: int) -> bool:
        cursor = self.db.cursor()
        cursor.execute("DELETE FROM Students WHERE id = ?", (student_id,))
        self.db.commit()
        return cursor.rowcount > 0

    def get_by_age_gt(self, age: int) -> List[Student]:
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM Students WHERE age > ?", (age,))
        rows = cursor.fetchall()
        return [Student.from_row(row) for row in rows]

    def get_by_city(self, city: str) -> List[Student]:
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM Students WHERE city = ?", (city,))
        rows = cursor.fetchall()
        return [Student.from_row(row) for row in rows]

    def count(self) -> int:
        cursor = self.db.cursor()
        cursor.execute("SELECT COUNT(*) FROM Students")
        result = cursor.fetchone()
        return result[0] if result else 0


class CourseRepository:
    """Репозиторий для работы с курсами."""

    def __init__(self, db_connection: sqlite3.Connection):
        self.db = db_connection

    def create(self, course: Course) -> int:
        cursor = self.db.cursor()
        cursor.execute(
            "INSERT INTO Courses (name, time_start, time_end) VALUES (?, ?, ?)",
            (course.name, course.time_start, course.time_end)
        )
        self.db.commit()
        return cursor.lastrowid

    def get_all(self) -> List[Course]:
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM Courses")
        rows = cursor.fetchall()
        return [Course.from_row(row) for row in rows]

    def get_by_id(self, course_id: int) -> Optional[Course]:
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM Courses WHERE id = ?", (course_id,))
        row = cursor.fetchone()
        return Course.from_row(row) if row else None

    def get_by_name(self, name: str) -> Optional[Course]:
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM Courses WHERE name = ?", (name,))
        row = cursor.fetchone()
        return Course.from_row(row) if row else None

    def count(self) -> int:
        cursor = self.db.cursor()
        cursor.execute("SELECT COUNT(*) FROM Courses")
        result = cursor.fetchone()
        return result[0] if result else 0


class EnrollmentRepository:
    """Репозиторий для управления записями на курсы."""

    def __init__(self, db_connection: sqlite3.Connection):
        self.db = db_connection

    def enroll(self, student_id: int, course_id: int) -> bool:
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

    def enroll_students_to_course(self, student_ids: List[int], course_id: int) -> Dict[str, Any]:
        """Записывает нескольких студентов на курс."""
        results = {
            "successful": [],
            "already_enrolled": [],
            "errors": []
        }

        cursor = self.db.cursor()

        for student_id in student_ids:
            try:
                # Проверяем, не записан ли уже студент на курс
                cursor.execute(
                    "SELECT 1 FROM Student_Courses WHERE student_id = ? AND course_id = ?",
                    (student_id, course_id)
                )
                if cursor.fetchone():
                    results["already_enrolled"].append(student_id)
                    continue

                # Записываем на курс
                cursor.execute(
                    "INSERT INTO Student_Courses (student_id, course_id) VALUES (?, ?)",
                    (student_id, course_id)
                )
                results["successful"].append(student_id)

            except Exception as e:
                results["errors"].append(f"Студент {student_id}: {str(e)}")

        self.db.commit()
        return results

    def unenroll(self, student_id: int, course_id: int) -> bool:
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
        rows = cursor.fetchall()
        return [Student.from_row(row) for row in rows]

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
        rows = cursor.fetchall()
        return [Student.from_row(row) for row in rows]

    def get_courses_for_student(self, student_id: int) -> List[Course]:
        """Находит все курсы, на которые записан студент."""
        cursor = self.db.cursor()
        cursor.execute('''
            SELECT c.* 
            FROM Courses c
            JOIN Student_Courses sc ON c.id = sc.course_id
            WHERE sc.student_id = ?
        ''', (student_id,))
        rows = cursor.fetchall()
        return [Course.from_row(row) for row in rows]


# =============================================================================
# SERVICE LAYER (СЛОЙ БИЗНЕС-ЛОГИКИ)
# =============================================================================

class SchoolService:
    """Сервисный слой с бизнес-логикой."""

    def __init__(self, db_connection: sqlite3.Connection):
        self.students = StudentRepository(db_connection)
        self.courses = CourseRepository(db_connection)
        self.enrollments = EnrollmentRepository(db_connection)

    def get_students_count(self) -> int:
        return self.students.count()

    def get_courses_count(self) -> int:
        return self.courses.count()


# =============================================================================
# DATABASE LAYER (СЛОЙ БАЗЫ ДАННЫХ)
# =============================================================================

class DatabaseManager:
    """Менеджер базы данных."""

    def __init__(self, db_name: str = 'school_optimized.db'):
        self.db_name = db_name
        self.conn: Optional[sqlite3.Connection] = None

    def __enter__(self) -> SchoolService:
        self.conn = sqlite3.connect(self.db_name)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
        return SchoolService(self.conn)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            if exc_type is None:
                self.conn.commit()
            else:
                self.conn.rollback()
            self.conn.close()

    def _create_tables(self):
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

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header(title: str):
    print("=" * 60)
    print(f"🎓 {title}")
    print("=" * 60)


def wait_for_enter():
    input("\n↵ Нажмите Enter чтобы продолжить...")


def input_student_data(existing_student: Optional[Student] = None) -> Student:
    if existing_student:
        print("\nТекущие данные студента:")
        print(f"  ID: {existing_student.id}")
        print(f"  Имя: {existing_student.name}")
        print(f"  Фамилия: {existing_student.surname}")
        print(f"  Возраст: {existing_student.age}")
        print(f"  Город: {existing_student.city}")
        print("\nВведите новые данные:")

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
    if existing_course:
        print("\nТекущие данные курса:")
        print(f"  ID: {existing_course.id}")
        print(f"  Название: {existing_course.name}")
        print(f"  Начало: {existing_course.time_start}")
        print(f"  Конец: {existing_course.time_end}")
        print("\nВведите новые данные:")

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


def show_students_table(students: List[Student]):
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


def show_courses_table(courses: List[Course]):
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


def input_student_ids() -> List[int]:
    while True:
        try:
            input_str = input("Введите ID студентов через запятую или пробел: ").strip()
            if not input_str:
                return []

            parts = input_str.replace(',', ' ').split()
            student_ids = []
            for part in parts:
                try:
                    student_ids.append(int(part))
                except ValueError:
                    print(f"❌ '{part}' не является числом. Пропускаем.")

            return student_ids

        except Exception as e:
            print(f"❌ Ошибка при вводе: {e}")
            retry = input("Попробовать снова? (д/н): ").strip().lower()
            if retry not in ['д', 'да', 'y', 'yes']:
                return []


def select_students_interactively(service: SchoolService) -> List[int]:
    students = service.students.get_all()
    if not students:
        print("❌ В базе нет студентов")
        return []

    print("\n📋 Список студентов:")
    show_students_table(students)

    while True:
        print("\nВарианты выбора:")
        print("1. Ввести ID студентов вручную")
        print("2. Выбрать всех студентов")
        print("3. Отмена")

        choice = input("Ваш выбор: ").strip()

        if choice == "1":
            return input_student_ids()
        elif choice == "2":
            return [s.id for s in students if s.id is not None]
        elif choice == "3":
            return []
        else:
            print("❌ Неверный выбор. Попробуйте снова.")


def menu_manage_students(service: SchoolService):
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


def menu_manage_courses(service: SchoolService):
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


def menu_enroll_students_to_course(service: SchoolService):
    clear_screen()
    print_header("ЗАПИСЬ СТУДЕНТОВ НА КУРС")

    courses = service.courses.get_all()
    if not courses:
        print("❌ В базе нет курсов")
        wait_for_enter()
        return

    print("Доступные курсы:")
    show_courses_table(courses)

    try:
        course_id = int(input("\nВведите ID курса: "))
        course = service.courses.get_by_id(course_id)

        if not course:
            print(f"❌ Курс с ID {course_id} не найден")
            wait_for_enter()
            return

        print(f"\nВыбран курс: {course.name}")
        print("\nВыберите студентов для записи:")

        student_ids = select_students_interactively(service)
        if not student_ids:
            print("❌ Не выбрано ни одного студента")
            wait_for_enter()
            return

        existing_students = service.students.get_by_ids(student_ids)
        existing_ids = {s.id for s in existing_students if s.id is not None}

        if len(existing_ids) < len(student_ids):
            print(f"⚠  Некоторые студенты не найдены. Будут записаны только существующие.")
            student_ids = list(existing_ids)

        if not student_ids:
            print("❌ Не осталось действительных студентов для записи")
            wait_for_enter()
            return

        print(f"\n📋 Будет записано {len(student_ids)} студента(ов) на курс '{course.name}'")
        print("Выбранные студенты:")
        selected_students = [s for s in existing_students if s.id in student_ids]
        show_students_table(selected_students)

        confirm = input("\nПодтвердить запись? (д/н): ").strip().lower()
        if confirm not in ['д', 'да', 'y', 'yes']:
            print("❌ Запись отменена")
            wait_for_enter()
            return

        results = service.enrollments.enroll_students_to_course(student_ids, course_id)

        print(f"\n📊 Результаты записи на курс '{course.name}':")
        print(f"✅ Успешно записано: {len(results['successful'])} студента(ов)")

        if results['already_enrolled']:
            already_students = service.students.get_by_ids(results['already_enrolled'])
            print(f"⚠  Уже были записаны ({len(results['already_enrolled'])}):")
            show_students_table(already_students)

        if results['errors']:
            print(f"❌ Ошибки при записи: {len(results['errors'])}")
            for error in results['errors'][:5]:
                print(f"   {error}")

    except ValueError:
        print("❌ Неверный формат ID")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

    wait_for_enter()


def menu_enrollments(service: SchoolService):
    while True:
        clear_screen()
        print_header("ЗАПИСИ НА КУРСЫ")

        print("\nВыберите действие:")
        print("1. 📝 Записать студента(ов) на курс")
        print("2. 📋 Показать студентов на курсе")
        print("3. 🏙  Показать студентов на курсе из города")
        print("4. 📚 Показать курсы студента")
        print("5. ❌ Отписать студента от курса")
        print("0. ↩  Назад в главное меню")

        choice = input("\nВаш выбор: ").strip()

        if choice == "1":
            menu_enroll_students_to_course(service)

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

        elif choice == "4":
            clear_screen()
            print_header("КУРСЫ СТУДЕНТА")

            students = service.students.get_all()
            if not students:
                print("❌ В базе нет студентов")
                wait_for_enter()
                continue

            show_students_table(students)

            try:
                student_id = int(input("\nВведите ID студента: "))
                courses = service.enrollments.get_courses_for_student(student_id)

                if courses:
                    print(f"\n📚 Курсы студента ID {student_id}:")
                    show_courses_table(courses)
                else:
                    print(f"\n❌ Студент ID {student_id} не записан ни на один курс")
            except ValueError:
                print("❌ Неверный формат ID")
            wait_for_enter()

        elif choice == "5":
            clear_screen()
            print_header("ОТПИСАТЬ СТУДЕНТА ОТ КУРСА")

            students = service.students.get_all()
            courses = service.courses.get_all()

            if not students or not courses:
                print("❌ Нужны и студенты, и курсы")
                wait_for_enter()
                continue

            print("Студенты:")
            show_students_table(students)

            print("\nКурсы:")
            show_courses_table(courses)

            try:
                student_id = int(input("\nВведите ID студента: "))
                course_id = int(input("Введите ID курса: "))

                if service.enrollments.unenroll(student_id, course_id):
                    print("✅ Студент отписан от курса!")
                else:
                    print("❌ Студент не был записан на этот курс")
            except ValueError:
                print("❌ Неверный формат ID")
            wait_for_enter()

        elif choice == "0":
            break
        else:
            print("❌ Неверный выбор. Попробуйте снова.")
            wait_for_enter()


def menu_queries(service: SchoolService):
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


def main_menu():
    with DatabaseManager() as service:
        while True:
            clear_screen()
            print_header("ГЛАВНОЕ МЕНЮ")
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


def main():
    clear_screen()
    print("=" * 70)
    print("        🎓 ORM СИСТЕМА ДЛЯ ШКОЛЫ")
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


if __name__ == "__main__":
    main()


