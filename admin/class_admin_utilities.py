import os

# Import cloud database connection
from database_files.cloud_database import get_connection
from database_files.class_database_uitlities import DatabaseUtilities

# Initialize PostgreSQL (Cloud) connection
con, cur = get_connection()

# Pass connection to your utilities class
db = DatabaseUtilities(con, cur)


class AdminUtilities:

    def __init__(self, db):
        self.db = db


    # ------------------- COURSES -------------------
    def add_course(self, code: str, name: str, credits: int) -> str:
        """
        Adds a new course to the database.
        Returns: message string from DB layer.
        """
        msg = self.db.AddCourse(code, name, credits)
        return msg

    def update_course(
        self,
        current_code: str,
        new_code: str | None = None,
        new_name: str | None = None,
        new_credits: int | None = None
    ) -> str:
        """
        Updates an existing course based on provided new fields.
        Returns: message from DB layer.
        """
        msg = self.db.UpdateCourse(
            current_code=current_code,
            new_code=new_code,
            new_name=new_name,
            new_credits=new_credits
        )
        return msg

    def delete_course(self, code: str) -> str:
        """
        Deletes a course by code.
        Returns: message from DB layer.
        """
        msg = self.db.DeleteCourse(code)
        return msg

    def list_courses(self):
        """
        Returns a list of courses: (code, name, credits)
        """
        return self.db.ListCourses()
    

    # ------------------- PREREQUISITES -------------------
    def add_prerequisites(self, course_code: str, prereq_list: list[str]) -> list[str]:
        """
        Add multiple prerequisites for a course.
        Returns a list of DB messages for each addition.
        """
        results = []
        for prereq in prereq_list:
            msg = self.db.add_prerequisite(course_code, prereq)
            results.append(msg)
        return results
    
    def list_prerequisites(self, course_code: str) -> list[str]:
        # The database utility already returns a clean list of codes
        return self.db.list_prerequisites(course_code)

    def update_prerequisite(self, course_code: str, old: str, new: str) -> str:
        return self.db.update_prerequisite(course_code, old, new)

    def delete_prerequisite(self, course_code: str, prereq: str) -> str:
        return self.db.delete_prerequisite(course_code, prereq)

    # *****************************************************************************************************************
    # ------------------- SECTIONS -------------------
    def admin_add_section(
        self,
        course_code: str,
        doctor_id: int | None,
        days: str,
        time_start: str,
        time_end: str,
        room: str,
        capacity: int,
        semester: str,
        state: str = "open",
    ) -> str:
        """
        يضيف سكشن واحد للكورس المحدد.
        كل القيم تيجي جاهزة من الـ GUI (ما فيه input هنا).
        """
        msg = self.db.add_section(
            course_code=course_code,
            doctor_id=doctor_id,
            days=days,
            time_start=time_start,
            time_end=time_end,
            room=room,
            capacity=capacity,
            semester=semester,
            state=state,
        )
        return msg


    def admin_list_sections(self, course_code=None, semester=None):
        rows = self.db.list_sections(course_code=course_code, semester=semester)

        if not rows:
            return "No sections found."

        return rows

    def admin_update_section(self,
                             section_id,
                             doctor_id=None,
                             days=None,
                             time_start=None,
                             time_end=None,
                             room=None,
                             capacity=None,
                             semester=None,
                             state=None):
        rows = self.db.list_sections()

        if not rows:
            return "No sections found."

        msg = self.db.update_section(
            section_id=section_id,
            doctor_id=doctor_id,
            days=days,
            time_start=time_start,
            time_end=time_end,
            room=room,
            capacity=capacity,
            semester=semester,
            state=state
        )

        return msg

    def admin_delete_section(self, section_id):
        rows = self.db.list_sections()

        if not rows:
            return "No sections found."

        msg = self.db.delete_section(section_id)
        return msg

    # ***************************************************************************************************************

    def admin_add_transcript(self):

        student_id = int(input("Enter student ID: ").strip())
        course_code = input("Enter course code: ").strip()
        semester = input("Enter semester ").strip()
        grade = input("Enter grade (or press Enter if not graded yet): ").strip()

        if grade == "":
            grade = None

        msg = self.db.add_transcript(student_id, course_code, semester, grade)
        print(msg)

    def admin_show_transcript(self):

        student_id = int(input("Enter student ID to show transcript: ").strip())

        rows = self.db.list_transcript(student_id)
        if not rows:
            print("No transcript records for this student.")  # هذا بيكون بكلاس الطالب
            return

        print(f"Transcript for student {student_id}:")
        for course_code, semester, grade in rows:
            print(f"{semester} | {course_code} | Grade: {grade}")

    def admin_update_transcript_grade(self):

        student_id = int(input("Enter student ID: ").strip())
        course_code = input("Enter course code: ").strip()
        semester = input("Enter semester (e.g. 2024-1): ").strip()
        new_grade = input("Enter new grade: ").strip()

        msg = self.db.update_transcript_grade(student_id, course_code, semester, new_grade)
        print(msg)



    def admin_add_course_to_plan(self, program: str, course_code: str, level: int) -> str:
        """
        يضيف كورس إلى الخطة الدراسية لبرنامج معيّن ولمستوى معيّن.
        """
        msg = self.db.add_course_to_plan(program, course_code, level)
        return msg

        # داخل class AdminUtilities في class_admin_utilities.py

    def admin_delete_course_from_plan(self, program: str, course_code: str) -> str:
        """
        يحذف كورس من الخطة الدراسية لبرنامج معيّن.
        يستقبل:
        - program: كود البرنامج 'PWM','BIO','COMM','COMP'
        - course_code: رمز المادة المراد حذفها من الخطة
        ويرجع رسالة نصية من طبقة الداتابيس.
        """
        msg = self.db.delete_course_from_plan(program, course_code)
        return msg

    def admin_show_plans(self):
        """
        يعرض كل الخطط وكل المواد داخل كل خطة.
        """
        rows = self.db.list_plan_courses()  # نعرض كل الخطط

        if not rows:
            print("No plans found.")
            return

        current_program = None

        # كل صف يحتوي:
        # (program, course_code, course_name, credits, level)
        for program, code, name, credits, level in rows:

            # إذا تغيّر التخصص نبدأ عنوان جديد
            if program != current_program:
                current_program = program
                print(f"\n===== Plan: {program} =====")

            # نعرض المادة والمستوى
            print(f"Level {level}: {code} - {name} ({credits} credits)")



    # إدارة التسجيل
    def manage_registration_period(self):
        print("1. Open Registration")
        print("2. Close Registration")
        ch = input("Choose: ")
        sem = input("Enter Semester: ")
        if ch == '1':
            self.reg_manager.open_registration(sem)
        elif ch == '2':
            self.reg_manager.close_registration(sem)

    def admin_update_course_to_plan(self,
                                    old_program,
                                    old_course_code,
                                    old_level,
                                    new_program,
                                    new_course_code,
                                    new_level):
        """
        واجهة بسيطة للـ GUI:
        - تستقبل القيم القديمة والجديدة
        - تنادي دالة الـ DB update_course_in_plan
        - ترجع الرسالة كنص
        """
        return self.db.update_course_in_plan(
            old_program=old_program,
            old_course_code=old_course_code,
            old_level=old_level,
            new_program=new_program,
            new_course_code=new_course_code,
            new_level=new_level,
        )
    # ================ Pending Students Management ================
    def admin_list_pending_students(self):
        """
        ترجع قائمة الطلاب اللي حسابهم inactive
        على شكل list[dict] عشان الواجهة تستخدمها بسهولة.
        """
        rows = self.db.list_inactive_users()
        students = []
        for user_id, name, email, program, state in rows:
            students.append({
                "user_id": user_id,
                "name": name,
                "email": email,
                "program": program,
                "state": state,
            })
        return students

    def admin_approve_student(self, user_id: int) -> str:
        """
        تفعيل حساب طالب واحد.
        """
        self.db.update_user(user_id, account_status="active")
        return f"Student {user_id} approved."

    def admin_reject_student(self, user_id: int) -> str:
        """
        رفض (وحذف) طالب واحد.
        """
        self.db.delete_user(user_id)
        return f"Student {user_id} rejected and deleted."

    def admin_approve_all_pending_students(self) -> str:
        """
        تفعيل كل الطلاب pending.
        """
        self.db.approve_all_inactive_users()
        return "All pending students have been approved."

    def admin_reject_all_pending_students(self) -> str:
        """
        حذف كل الطلاب pending.
        """
        self.db.delete_all_inactive_users()
        return "All pending students have been rejected and deleted."
    
    def admin_delete_student(self, user_id: int) -> str:
        """
        حذف طالب (أو مستخدم) واحد نهائيًا من النظام.
        """
        self.db.delete_user(user_id)
        return f"Student {user_id} removed."

    def admin_delete_all_students(self) -> str:
        """
        حذف جميع الطلاب/المستخدمين من جدول users.
        """
        self.db.delete_all_users()
        return "All students removed."
    
    def admin_show_plans(self):
        """
        يعرض كل الخطط الدراسية لكل برنامج،
        ويعرض المواد الموجودة داخل كل خطة مرتبة حسب المستوى.
        """

        rows = self.db.list_plan_courses()
        # يرجّع صفوف بالشكل:
        # (program, course_code, course_name, credits, level)

        if not rows:
            print("No plans found.")
            return

        current_program = None

        print("\n====== Study Plans ======\n")

        for program, code, name, level in rows:

            # إذا دخلنا برنامج جديد نطبع عنوان جديد
            if program != current_program:
                current_program = program
                print(f"\n====== Program: {program} ======")

            # عرض المادة
            print(f"  Level {level}: {code} - {name} ")    

        # ---------------- ADMIN MANAGEMENT ----------------
    def delete_admin(self, user_id: int):
        """
        Delete a single admin account.
        """
        self.db.delete_user(user_id)

    def add_admin(self, name, email, password_h):
        """
        Add new admin account.
        """
        return self.db.add_users(
            name=name,
            email=email,
            password=password_h,
            program=None,
            state="admin",
        )


admin = AdminUtilities(db)
def admin_show_plans(self):
    """
    يعرض كل الخطط الدراسية لكل برنامج،
    ويعرض المواد الموجودة داخل كل خطة مرتبة حسب المستوى.
    """

    rows = self.db.list_plan_courses()
    # يرجّع صفوف بالشكل:
    # (program, course_code, course_name, credits, level)

    if not rows:
        print("No plans found.")
        return

    current_program = None

    print("\n====== Study Plans ======\n")

    for program, code, name, level in rows:

        # إذا دخلنا برنامج جديد نطبع عنوان جديد
        if program != current_program:
            current_program = program
            print(f"\n====== Program: {program} ======")

        # عرض المادة
        print(f"  Level {level}: {code} - {name} ")



if __name__ == "__main__":
    from database_files.class_database_uitlities import DatabaseUtilities, con, cur

    db = DatabaseUtilities(con, cur)
    admin = AdminUtilities(db)

    admin.admin_show_plans()

