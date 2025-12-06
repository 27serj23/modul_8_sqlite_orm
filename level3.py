# Уровень 3.
#
# Напишите ORM для этой базы данных, то есть функции, которые
# позволят быстро выполнять данные запросы без дублирования кода SQL.
"""
School ORM System - Компактная версия с правильными транзакциями
"""

import sqlite3
import os
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from contextlib import contextmanager

# =============================================================================
# ИСКЛЮЧЕНИЯ
# =============================================================================

class ValidationError(Exception):
    """Ошибка валидации данных"""
    pass

class DatabaseError(Exception):
    """Ошибка базы данных"""
    pass

# =============================================================================
# СЛОЙ СУЩНОСТЕЙ
# =============================================================================

@dataclass
class Student:
    id: Optional[int] = None
    name: str = ""
    surname: str = ""
    age: int = 0
    city: str = ""

    def _post_init_(self):
        """Валидация данных студента"""
        if not self.name or len(self.name.strip()) < 2:
            raise ValidationError("Имя должно содержать минимум 2 символа")
        if not self.surname or len(self.surname.strip()) < 2:
            raise ValidationError("Фамилия должна содержать минимум 2 символа")
        if not 14 <= self.age <= 100:
            raise ValidationError("Возраст должен быть от 14 до 100 лет")
        if not self.city or len(self.city.strip()) < 2:
            raise ValidationError("Город должен содержать минимум 2 символа")

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> 'Student':
        return cls(
            id=row['id'],
            name=row['name'],
            surname=row['surname'],
            age=row['age'],
            city=row['city']
        )


@dataclass
class Course:
    id: Optional[int] = None
    name: str = ""
    time_start: str = ""
    time_end: str = ""

    def _post_init_(self):
        """Валидация данных курса"""
        if not self.name or len(self.name.strip()) < 3:
            raise ValidationError("Название курса должно содержать минимум 3 символа")
        # Простая проверка формата даты (можно расширить при необходимости)
        if not self.time_start or not self.time_end:
            raise ValidationError("Даты начала и окончания обязательны")

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> 'Course':
        return cls(
            id=row['id'],
            name=row['name'],
            time_start=row['time_start'],
            time_end=row['time_end']
        )

# =============================================================================
# СЛОЙ РЕПОЗИТОРИЕВ
# =============================================================================

class StudentRepository:
    def __init__(self, db_connection: sqlite3.Connection):
        self.db = db_connection

    def create(self, student: Student) -> int:
        """Создание студента БЕЗ коммита"""
        cursor = self.db.cursor()
        cursor.execute(
            "INSERT INTO Students (name, surname, age, city) VALUES (?, ?, ?, ?)",
            (student.name, student.surname, student.age, student.city)
        )
        return cursor.lastrowid

    def get_all(self) -> List[Student]:
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM Students")
        return [Student.from_row(row) for row in cursor.fetchall()]

    def get_by_id(self, student_id: int) -> Optional[Student]:
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM Students WHERE id = ?", (student_id,))
        row = cursor.fetchone()
        return Student.from_row(row) if row else None

    def update(self, student: Student) -> bool:
        if student.id is None:
            raise ValueError("Нельзя обновить студента без ID")
        cursor = self.db.cursor()
        cursor.execute(
            "UPDATE Students SET name = ?, surname = ?, age = ?, city = ? WHERE id = ?",
            (student.name, student.surname, student.age, student.city, student.id)
        )
        return cursor.rowcount > 0

    def delete(self, student_id: int) -> bool:
        cursor = self.db.cursor()
        cursor.execute("DELETE FROM Students WHERE id = ?", (student_id,))
        return cursor.rowcount > 0

    def count(self) -> int:
        cursor = self.db.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM Students")
        return cursor.fetchone()['count']


class CourseRepository:
    def __init__(self, db_connection: sqlite3.Connection):
        self.db = db_connection

    def create(self, course: Course) -> int:
        """Создание курса БЕЗ коммита"""
        cursor = self.db.cursor()
        cursor.execute(
            "INSERT INTO Courses (name, time_start, time_end) VALUES (?, ?, ?)",
            (course.name, course.time_start, course.time_end)
        )
        return cursor.lastrowid

    def get_all(self) -> List[Course]:
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM Courses")
        return [Course.from_row(row) for row in cursor.fetchall()]

    def get_by_id(self, course_id: int) -> Optional[Course]:
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM Courses WHERE id = ?", (course_id,))
        row = cursor.fetchone()
        return Course.from_row(row) if row else None

    def count(self) -> int:
        cursor = self.db.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM Courses")
        return cursor.fetchone()['count']


class EnrollmentRepository:
    def __init__(self, db_connection: sqlite3.Connection):
        self.db = db_connection

    def enroll(self, student_id: int, course_id: int) -> bool:
        """Запись на курс с обработкой ошибок"""
        try:
            cursor = self.db.cursor()
            cursor.execute(
                "INSERT INTO Student_Courses (student_id, course_id) VALUES (?, ?)",
                (student_id, course_id)
            )
            return True
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValidationError(f"Студент уже записан на этот курс")
            elif "FOREIGN KEY constraint failed" in str(e):
                raise ValidationError(f"Студент или курс не найден")
            raise DatabaseError(f"Ошибка записи на курс: {e}")
        except sqlite3.Error as e:
            raise DatabaseError(f"Ошибка базы данных: {e}")

    def get_students_on_course(self, course_id: int) -> List[Student]:
        cursor = self.db.cursor()
        cursor.execute('''
            SELECT s.* FROM Students s
            JOIN Student_Courses sc ON s.id = sc.student_id
            WHERE sc.course_id = ?
        ''', (course_id,))
        return [Student.from_row(row) for row in cursor.fetchall()]

# =============================================================================
# СЛОЙ БИЗНЕС-ЛОГИКИ (УПРАВЛЕНИЕ ТРАНЗАКЦИЯМИ)
# =============================================================================

class SchoolService:
    """Сервисный слой управляет транзакциями на уровне бизнес-операций"""

    def __init__(self, db_connection: sqlite3.Connection):
        self.db = db_connection
        self.students = StudentRepository(db_connection)
        self.courses = CourseRepository(db_connection)
        self.enrollments = EnrollmentRepository(db_connection)

    def commit(self) -> None:
        """Явный коммит изменений"""
        self.db.commit()

    def rollback(self) -> None:
        """Откат изменений"""
        self.db.rollback()

    @contextmanager
    def transaction(self):
        """
        Контекстный менеджер для атомарных операций.
        Автоматически коммитит при успехе, откатывает при ошибке.
        """
        try:
            yield self
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    # Бизнес-методы с транзакциями
    def create_student(self, student_data: Dict[str, Any]) -> int:
        """Создание студента в транзакции"""
        with self.transaction():
            student = Student(**student_data)
            return self.students.create(student)

    def create_student_with_enrollment(self, student_data: Dict[str, Any], course_id: int) -> int:
        """Атомарная операция: студент + запись на курс"""
        with self.transaction():
            student = Student(**student_data)
            student_id = self.students.create(student)

            if not self.enrollments.enroll(student_id, course_id):
                raise ValidationError("Не удалось записать студента на курс")

            return student_id

    def update_student(self, student_id: int, update_data: Dict[str, Any]) -> bool:
        """Обновление студента в транзакции"""
        with self.transaction():
            student = self.students.get_by_id(student_id)
            if not student:
                raise ValidationError(f"Студент с ID {student_id} не найден")

            for key, value in update_data.items():
                if hasattr(student, key) and value is not None:
                    setattr(student, key, value)

            return self.students.update(student)

    def delete_student(self, student_id: int) -> bool:
        """Удаление студента в транзакции"""
        with self.transaction():
            student = self.students.get_by_id(student_id)
            if not student:
                raise ValidationError(f"Студент с ID {student_id} не найден")
            return self.students.delete(student_id)

# =============================================================================
# СЛОЙ БАЗЫ ДАННЫХ
# =============================================================================

class DatabaseManager:
    """Менеджер БД создает подключение и таблицы"""

    def __init__(self, db_name: str = 'school.db'):
        self.db_name = db_name
        self.conn: Optional[sqlite3.Connection] = None

    def __enter__(self) -> SchoolService:
        self.conn = sqlite3.connect(self.db_name)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")

        self._create_tables()
        return SchoolService(self.conn)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.close()

    def _create_tables(self) -> None:
        """Создание таблиц (коммит только для DDL)"""
        cursor = self.conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Students(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                surname TEXT NOT NULL,
                age INTEGER NOT NULL CHECK (age >= 14),
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
# ПОЛЬЗОВАТЕЛЬСКИЙ ИНТЕРФЕЙС
# =============================================================================

class SchoolUI:
    """Компактный пользовательский интерфейс"""

    def __init__(self, service: SchoolService):
        self.service = service

    @staticmethod
    def clear_screen():
        os.system('cls' if os.name == 'nt' else 'clear')

    @staticmethod
    def print_header(title: str):
        print("\n" + "=" * 50)
        print(f"🎓 {title}")
        print("=" * 50)

    @staticmethod
    def wait_for_enter():
        input("\n↵ Нажмите Enter чтобы продолжить...")

    def input_student_data(self, existing=None) -> Dict[str, Any]:
        """Ввод данных студента с валидацией"""
        if existing:
            print(f"Текущие данные: {existing}")
            print("Оставьте поле пустым чтобы не изменять")

        data = {}

        name = input("Имя: ").strip()
        if name or not existing:
            data['name'] = name

        surname = input("Фамилия: ").strip()
        if surname or not existing:
            data['surname'] = surname

        age_str = input("Возраст: ").strip()
        if age_str or not existing:
            if age_str:
                try:
                    data['age'] = int(age_str)
                except ValueError:
                    print("⚠  Возраст должен быть числом")

        city = input("Город: ").strip()
        if city or not existing:
            data['city'] = city

        return data

    def show_students(self, students: List[Student]):
        """Отображение списка студентов"""
        if not students:
            print("📭 Нет данных для отображения")
            return

        print(f"\n📋 Найдено студентов: {len(students)}")
        print("-" * 60)
        print(f"{'ID':<4} {'Имя':<15} {'Фамилия':<15} {'Возраст':<8} {'Город':<15}")
        print("-" * 60)

        for student in students:
            print(f"{student.id:<4} {student.name:<15} {student.surname:<15} "
                  f"{student.age:<8} {student.city:<15}")
        print("-" * 60)

    def menu_manage_students(self):
        """Главное меню управления студентами"""
        while True:
            self.clear_screen()
            self.print_header("УПРАВЛЕНИЕ СТУДЕНТАМИ")
            print(f"📊 Всего студентов: {self.service.students.count()}")

            print("\nВыберите действие:")
            print("1. 📋 Показать всех студентов")
            print("2. 🆕 Добавить студента")
            print("3. ✏  Обновить студента")
            print("4. 🗑  Удалить студента")
            print("5. 🔍 Найти студента по ID")
            print("0. ↩  Назад")

            choice = input("\nВаш выбор: ").strip()

            if choice == "1":
                self.clear_screen()
                self.print_header("ВСЕ СТУДЕНТЫ")
                try:
                    students = self.service.students.get_all()
                    self.show_students(students)
                except Exception as e:
                    print(f"❌ Ошибка: {e}")
                self.wait_for_enter()

            elif choice == "2":
                self.clear_screen()
                self.print_header("ДОБАВЛЕНИЕ СТУДЕНТА")
                try:
                    data = self.input_student_data()
                    if data:
                        student_id = self.service.create_student(data)
                        print(f"\n✅ Студент создан! ID: {student_id}")
                    else:
                        print("❌ Необходимо ввести данные")
                except ValidationError as e:
                    print(f"❌ Ошибка валидации: {e}")
                except DatabaseError as e:
                    print(f"❌ Ошибка базы данных: {e}")
                except Exception as e:
                    print(f"❌ Ошибка: {e}")
                self.wait_for_enter()

            elif choice == "3":
                self.clear_screen()
                self.print_header("ОБНОВЛЕНИЕ СТУДЕНТА")
                try:
                    students = self.service.students.get_all()
                    self.show_students(students)

                    student_id = int(input("\nВведите ID студента: "))
                    existing = self.service.students.get_by_id(student_id)

                    if not existing:
                        print(f"❌ Студент с ID {student_id} не найден")
                    else:
                        data = self.input_student_data(existing)
                        if data:
                            if self.service.update_student(student_id, data):
                                print("✅ Данные обновлены!")
                            else:
                                print("❌ Ошибка при обновлении")
                        else:
                            print("ℹ  Нет изменений")
                except ValueError:
                    print("❌ Неверный формат ID")
                except ValidationError as e:
                    print(f"❌ Ошибка валидации: {e}")
                except Exception as e:
                    print(f"❌ Ошибка: {e}")
                self.wait_for_enter()

            elif choice == "4":
                self.clear_screen()
                self.print_header("УДАЛЕНИЕ СТУДЕНТА")
                try:
                    students = self.service.students.get_all()
                    self.show_students(students)

                    student_id = int(input("\nВведите ID студента: "))

                    confirm = input("Удалить? (д/н): ").strip().lower()
                    if confirm in ['д', 'да', 'y', 'yes']:
                        if self.service.delete_student(student_id):
                            print("✅ Студент удален!")
                        else:
                            print(f"❌ Студент с ID {student_id} не найден")
                    else:
                        print("ℹ  Удаление отменено")
                except ValueError:
                    print("❌ Неверный формат ID")
                except ValidationError as e:
                    print(f"❌ Ошибка валидации: {e}")
                except Exception as e:
                    print(f"❌ Ошибка: {e}")
                self.wait_for_enter()

            elif choice == "5":
                self.clear_screen()
                self.print_header("ПОИСК СТУДЕНТА")
                try:
                    student_id = int(input("Введите ID студента: "))
                    student = self.service.students.get_by_id(student_id)

                    if student:
                        self.show_students([student])
                    else:
                        print(f"❌ Студент с ID {student_id} не найден")
                except ValueError:
                    print("❌ Неверный формат ID")
                except Exception as e:
                    print(f"❌ Ошибка: {e}")
                self.wait_for_enter()

            elif choice == "0":
                break

    def menu_atomic_operations(self):
        """Меню атомарных операций"""
        self.clear_screen()
        self.print_header("АТОМАРНЫЕ ОПЕРАЦИИ")

        print("\nПример атомарной операции:")
        print("1. Записать студента")
        print("2. Создать курс")
        print("3. Зачислить студента с записью на курс")
        print("0. ↩  Назад")

        choice = input("\nВаш выбор: ").strip()

        if choice == "1":
            try:
                data = self.input_student_data()
                student_id = self.service.create_student(data)
                print(f"\n✅ Студент создан в транзакции! ID: {student_id}")
            except Exception as e:
                print(f"❌ Ошибка: {e}")

        elif choice == "3":
            print("\n📝 Создание студента с записью на курс:")
            try:
                # Показываем доступные курсы
                courses = self.service.courses.get_all()
                if not courses:
                    print("❌ Нет доступных курсов")
                else:
                    print("\nДоступные курсы:")
                    for course in courses:
                        print(f"  {course.id}. {course.name}")

                    course_id = int(input("\nID курса для записи: "))
                    student_data = self.input_student_data()

                    # Атомарная операция
                    student_id = self.service.create_student_with_enrollment(
                        student_data, course_id
                    )
                    print(f"\n✅ Студент создан и записан на курс! ID: {student_id}")
            except Exception as e:
                print(f"❌ Ошибка в атомарной операции: {e}")
                print("ℹ  Все изменения откачены автоматически")

        self.wait_for_enter()

    def main_menu(self):
        """Главное меню системы"""
        while True:
            self.clear_screen()
            print("=" * 50)
            print("🎓 ШКОЛЬНАЯ ORM СИСТЕМА".center(50))
            print("=" * 50)
            print(f"📊 Студентов: {self.service.students.count()}")
            print(f"📚 Курсов: {self.service.courses.count()}")

            print("\nВыберите раздел:")
            print("1. 👨‍🎓 Управление студентами")
            print("2. ⚡ Атомарные операции")
            print("3. 💾 Сохранить")
            print("4. ↩  Отменить изменения")
            print("0. 🚪 Выход")
            print("-" * 50)

            choice = input("\nВаш выбор: ").strip()

            if choice == "1":
                self.menu_manage_students()
            elif choice == "2":
                self.menu_atomic_operations()
            elif choice == "3":
                self.service.commit()
                print("✅ Изменения сохранены!")
                self.wait_for_enter()
            elif choice == "4":
                self.service.rollback()
                print("✅ Изменения откачены!")
                self.wait_for_enter()
            elif choice == "0":
                print("\n👋 До свидания!")
                break

# =============================================================================
# ТОЧКА ВХОДА
# =============================================================================

def main():
    """Главная функция приложения"""
    try:
        with DatabaseManager() as service:
            ui = SchoolUI(service)
            ui.main_menu()

        print(f"\n✅ Программа завершена")
        print(f"📁 База данных: {os.path.abspath('school.db')}")

    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")


if __name__ == "__main__":
    main()

