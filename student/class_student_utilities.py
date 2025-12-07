import os

# Import cloud database connection
from database_files.cloud_database import get_connection
from database_files.class_database_uitlities import DatabaseUtilities

# Initialize PostgreSQL (Cloud) connection
con, cur = get_connection()

db = DatabaseUtilities(con, cur)


class StudentUtilities:
    def __init__(self, db_util: DatabaseUtilities, student_id):
        self.db = db_util
        self.student_id = student_id

    # ================== Student info ==================
    def get_student_program(self):
        user = self.db.get_user_by_id(self.student_id)
        return user[3] if user else None  # index 3 is 'program'

    def get_completed_courses(self):
        transcripts = self.db.list_transcript(self.student_id)
        passed_grades = {"A+", "A", "B+", "B", "C+", "C", "D+", "D"}  # اعتبرنا D ناجح

        return [
            course
            for course, _, grade in transcripts
            if grade is not None and str(grade).upper() in passed_grades]

    def get_registered_courses(self, semester=None):
        """
        ترجع قائمة بأكواد المواد اللي الطالب مسجلها (لسمستر معيّن لو انبعت).
        نعتمد على جدول sections + جدول registrations.
        """
        sections = self.db.list_sections()
        registered = []

        for sec in sections:
            # sections: section_id, course_code, doctor_id, days, time_start, time_end,
            #          room, capacity, enrolled, semester, state
            sec_id = sec[0]
            course_code = sec[1]
            sec_semester = sec[9]

            # لو حددنا سمستر نفلتر عليه
            if semester is not None and sec_semester != semester:
                continue

            # هنا نرسل السمستر للدالة الجديدة
            if self.db.is_student_registered(self.student_id, sec_id, semester):
                registered.append(course_code)

        return registered

    

    def get_registered_courses_full(self, semester=None):
        """
        Return a list of dicts representing registered courses for this student.
        Each dict contains: course_id, credit, section, days, time, room, instructor
        """
        sections = self.db.list_sections()
        registered = []

        for sec in sections:
            sec_id, course_code, instructor_name, days, start_time, end_time, room, capacity, enrolled, sec_semester, state = sec
            if self.db.is_student_registered(self.student_id, sec_id):
                if semester is None or sec_semester == semester:
                    # get course credit
                    course_info = self.db.ListCourses()
                    credit = next((c[2] for c in course_info if c[0] == course_code), 0)

                    registered.append({
                        "course_id": course_code,
                        "credit": credit,
                        "section": sec_id,
                        "days": days or "",
                        "time": f"{start_time}-{end_time}" if start_time and end_time else "",
                        "room": room or "",
                        "instructor": instructor_name or ""
                    })
        return registered


    # ================== courses ==================
    def get_available_courses(self, semester):
        """
        ترجع قائمة بالمواد المتاحة للتسجيل لهذا الطالب في سمستر معيّن.
        كل عنصر dict بالشكل التالي:
        {
            "course_code": ...,
            "course_name": ...,
            "credits": ...,
            "prereqs": [...],
            "missing_prereqs": [...],
            "can_register": True/False
        }
        """
        # 1) نجيب برنامج الطالب من جدول users
        program = self.get_student_program()
        print(f"[DEBUG] Student ID = {self.student_id}, program = {program}")

        if not program:
            print("[DEBUG] No program found for this student.")
            return []

        # 2) نجيب مواد الخطة لهذا البرنامج
        plan_rows = self.db.list_plan_courses(program)
        # شكلها: (program, code, name, credits, level)
        print(f"[DEBUG] plan_rows = {len(plan_rows)} rows")
        plan_courses = [row[1] for row in plan_rows]  # row[1] = course_code

        # 3) المواد اللي خلصها + اللي مسجلها حالياً
        completed = set(self.get_completed_courses())
        registered = set(self.get_registered_courses(semester))
        print(f"[DEBUG] completed = {completed}")
        print(f"[DEBUG] registered = {registered}")

        available = []

        # 4) نجيب كل المواد من جدول courses
        course_info_list = self.db.ListCourses()  # (code, name, credits)

        for code in plan_courses:
            # نشيل المواد اللي خلصها الطالب أو مسجلها فعلاً
            if code in completed or code in registered:
                continue

            # نجيب سطر هذه المادة
            course_info = next((c for c in course_info_list if c[0] == code), None)
            if not course_info:
                print(f"[DEBUG] course {code} not found in courses table")
                continue

            _, name, credits = course_info

            # المتطلبات (إما من db أو من كلاس الأدمن حسب ما ضبطناه عندك)
            try:
                from admin.class_admin_utilities import admin
                prereqs = admin.list_prerequisites(code)
            except ImportError:
                prereqs = self.db.list_prerequisites(code)

            missing_prereqs = [p for p in prereqs if p not in completed]
            can_register = len(missing_prereqs) == 0

            available.append({
                "course_code": code,
                "course_name": name,
                "credits": credits,
                "prereqs": prereqs,
                "missing_prereqs": missing_prereqs,
                "can_register": can_register
            })

        print(f"[DEBUG] available courses = {len(available)}")
        return available


    def show_available_courses(self, semester):
        courses = self.get_available_courses(semester)
        can = [c for c in courses if c["can_register"]]
        cannot = [c for c in courses if not c["can_register"]]

        print("\nAvailable courses for semester", semester)
        if can:
            print("\n✓ You can register these courses:")
            for c in can:
                print(f"  {c['course_code']} - {c['course_name']} ({c['credits']} credits)")

        if cannot:
            print("\n✗ You CANNOT register these courses (missing prerequisites):")
            for c in cannot:
                print(f"  {c['course_code']} - {c['course_name']}")
                print(f"    Missing: {', '.join(c['missing_prereqs'])}")

        return can
    
        # ------------------- Remove registered course -------------------
    def remove_registered_course(self, course_code):
        """
        Removes a registered course for the student.
        Returns True if successful, False otherwise.
        """
        try:
            return self.db.remove_student_registration(self.student_id, course_code)
        except Exception as e:
            print(f"[ERROR] Failed to remove course {course_code}: {e}")
            return False

    # ================== Sections ==================
    
    def get_all_sections(self):
        """
        Return all sections in a standardized dict format for the table.
        Safely parses enrolled/capacity and computes status.
        """
        sections = self.db.list_sections()  # fetch all sections from DB
        result = []

        for sec in sections:
            try:
                section_id = sec[0]
                course_code = sec[1]
                course_name = sec[2]
                instructor_name = sec[3]
                days = sec[4]
                start_time = sec[5]
                end_time = sec[6]
                room = sec[7]

                # enrolled and capacity might be invalid strings; cast safely
                try:
                    enrolled = int(sec[8])
                except (ValueError, TypeError):
                    enrolled = 0
                try:
                    capacity = int(sec[9])
                except (ValueError, TypeError, IndexError):
                    capacity = 0  # treat as unlimited if missing/invalid

                # status determination
                status_db = sec[10] if len(sec) > 10 else "Open"
                if status_db.lower() == "closed":
                    status = "Closed"
                elif capacity > 0 and enrolled >= capacity:
                    status = "Full"
                else:
                    status = "Open"

                schedule = f"{days or ''} {start_time or ''}-{end_time or ''} | {room or ''}".strip()

                result.append({
                    "id": section_id,
                    "course_code": course_code,
                    "name": course_name,
                    "instructor": instructor_name,
                    "schedule": schedule,
                    "enrolled": enrolled,
                    "capacity": capacity,
                    "status": status
                })
            except Exception as e:
                # Skip broken rows but log them
                print(f"Skipping invalid section row: {sec} -> {e}")
                continue

        return result

    def register_section(self, section_id, course_code, semester):
        """
        يسجل الطالب في السكشن بعد التحقق من:
        - التعارض
        - السعة
        - الحالة (open/closed)
        """

        # 1) تحقق من التعارض
        if self.db.has_time_conflict(self.student_id, section_id):
            return "❌ Cannot register: Time conflict with another section."

        # 2) حاول التسجيل من خلال الداتا بيس
        return self.db.register_student_to_section(
            self.student_id,
            section_id,
            course_code,
            semester
        )

    def get_sections_for_course(self, course_code, semester):
        """ for getting sections for only one course"""
        return self.db.list_sections(course_code=course_code, semester=semester)

    def get_sections_for_courses(self, course_codes, semester):
        """
        ترجع جميع السكاشن لكل المواد اللي في course_codes لهذا السمستر.
        كل سكشن نرجعه بشكل dict مناسب للجدول ولفحص التعارض:
        {
            "section_id": ...,
            "course_code": ...,
            "days": ...,
            "time_start": ...,
            "time_end": ...,
            "room": ...
        }
        """
        result = []

        for code in course_codes:
            rows = self.db.list_sections(course_code=code, semester=semester)
            for sec in rows:
                # ترتيب الأعمدة من list_sections:
                # section_id, course_code, doctor_id, days, time_start, time_end,
                # room, capacity, enrolled, semester, state
                section_id = sec[0]
                course_code = sec[1]
                days = sec[3]
                time_start = sec[4]
                time_end = sec[5]
                room = sec[6]

                result.append({
                    "section_id": section_id,
                    "course_code": course_code,
                    "days": (days or "").strip(),
                    "time_start": time_start,
                    "time_end": time_end,
                    "room": (room or "").strip(),
                })

        return result

    if __name__ == "__main__":
        # كود اختبار للسكاشن من الكونسول

        print("===== TEST: list_sections() from Database =====")

        # نطلب من المستخدم كود المادة والسمستر
        course_code = input("Enter course code (مثال PWM201): ").strip().upper()
        semester = input("Enter semester (مثال 2025-1 ، أو خليه فاضي لكل السمسترات): ").strip()

        if not course_code:
            print("You must enter a course code.")
            exit()

        # لو السمستر فاضي نخليه None
        if not semester:
            semester = None

        print("\nQuerying sections...")
        rows = db.list_sections(course_code=course_code, semester=semester)

        print(f"\nFound {len(rows)} section(s) for course {course_code} and semester={semester!r}:\n")
        for row in rows:
            # row ترتيبها من list_sections:
            # section_id, course_code, doctor_id, days, time_start, time_end, room, capacity, enrolled, semester, state
            section_id, code, doctor_id, days, t_start, t_end, room, cap, enrolled, sem, state = row
            print(
                f"SECTION {section_id} | {code} | {days} {t_start}-{t_end} | "
                f"room={room} | sem={sem} | state={state} | cap={cap} | enrolled={enrolled}"
            )

    def check_time_conflict(self, sec1, sec2):
        days1 = set(sec1["days"].upper().replace(" ", ""))
        days2 = set(sec2["days"].upper().replace(" ", ""))
        if not days1.intersection(days2):
            return False
        return sec1["time_start"] < sec2["time_end"] and sec2["time_start"] < sec1["time_end"]

    # ================== Transcript ==================
    def show_transcript(self):
        transcript = self.db.list_transcript(self.student_id)
        print(f"\nTranscript for student {self.student_id}:")
        for course_code, semester, grade in transcript:
            print(f"  {semester} | {course_code} | {grade}")

