# class_database_utilities.py

"""
DatabaseUtilities

This class provides all database operations for the system:
courses, prerequisites, sections, users, transcripts, plans,
registrations, settings, login, and some helper checks.

Now it is fully migrated to PostgreSQL (no SQLite).
"""

import time
import psycopg2
from database_files.cloud_database import get_pooled_connection


# =========================================================
# GLOBAL INITIAL CONNECTION (FROM THE POOL)
# =========================================================
def _create_initial_connection():
    """
    Creates a safe initial pooled connection.
    Prevents startup crashes and allows reconnection later.
    """
    try:
        con, cur = get_pooled_connection()
        return con, cur, time.time()
    except Exception as e:
        print(f"[DB] Initial connection failed: {e}")
        return None, None, 0


con, cur, _last_used_global = _create_initial_connection()


# =========================================================
# DATABASE UTILITIES CLASS (BACKBONE)
# =========================================================
class DatabaseUtilities:
    """
    Preserves ALL original method names.
    Adds automatic reconnection + fast pooled sessions.
    """

    _MAX_IDLE_TIME = 300  # 5 minutes

    def __init__(self, con, cur):
        self.con = con
        self.cur = cur
        self._last_used = time.time()

    # -----------------------------------------------------
    # CONNECTION MANAGEMENT (NON-BREAKING, FULLY INTERNAL)
    # -----------------------------------------------------
    def ensure_connection(self):
        """
        Ensures the database connection is alive and fast.
        Reconnects automatically when idle, broken, or closed.
        """
        now = time.time()

        # If connection is None or closed
        if self.con is None or self.con.closed != 0:
            self._connect_fresh()
            return

        # Idle too long → reconnect
        if now - self._last_used > self._MAX_IDLE_TIME:
            self._connect_fresh()
            return

        # Ping the database
        try:
            self.con.poll()
        except Exception:
            self._connect_fresh()
            return

        self._last_used = now

    def _connect_fresh(self):
        """
        Pulls a new connection from the pool safely.
        """
        try:
            self.con, self.cur = get_pooled_connection()
            self._last_used = time.time()
            print("[DB] Reconnected (fresh pooled connection).")
        except Exception as e:
            raise RuntimeError(f"[DB] Failed to reconnect: {e}")

    # -----------------------------------------------------
    # EXECUTION METHODS 
    # -----------------------------------------------------
    def execute(self, query, params=()):
        self.ensure_connection()
        self.cur.execute(query, params)
        self.con.commit()
        self._last_used = time.time()

    def fetchone(self, query, params=()):
        self.ensure_connection()
        self.cur.execute(query, params)
        result = self.cur.fetchone()
        self._last_used = time.time()
        return result

    def fetchall(self, query, params=()):
        self.ensure_connection()
        self.cur.execute(query, params)
        result = self.cur.fetchall()
        self._last_used = time.time()
        return result

    # -----------------------------------------------------
    # LEGACY API COMPATIBILITY 
    # -----------------------------------------------------
    def commit(self):
        self.ensure_connection()
        self.con.commit()
        self._last_used = time.time()

    # =========================================================
    # COURSES
    # =========================================================
    def AddCourse(self, code, name, credits):
        """
        Add a new course to the database.

        Parameters:
        - code: course code (e.g., 'EE101')
        - name: course name (e.g., 'Electric Circuits 1')
        - credits: number of credit hours (e.g., 3)
        """
        self.ensure_connection()
        try:
            self.cur.execute(
                "INSERT INTO courses(code, name, credits) VALUES(%s, %s, %s)",
                (code, name, credits),
            )
            self.commit()
            return "Course added successfully"
        except psycopg2.IntegrityError:
            # Primary key / unique conflict
            self.con.rollback()
            return "course already added"

    def UpdateCourse(self, current_code, new_code=None, new_name=None, new_credits=None):
        """
        Update course information using the current course code.

        Any of these can be changed:
        - new_code   : new course code
        - new_name   : new course name
        - new_credits: new credit hours

        If all are None -> nothing to update.
        """
        self.ensure_connection()
        if new_code is None and new_name is None and new_credits is None:
            return "Nothing to update"

        sets = []
        vals = []

        if new_code is not None:
            sets.append("code=%s")
            vals.append(new_code)

        if new_name is not None:
            sets.append("name=%s")
            vals.append(new_name)

        if new_credits is not None:
            sets.append("credits=%s")
            vals.append(new_credits)

        vals.append(current_code)

        sql = f"UPDATE courses SET {', '.join(sets)} WHERE code=%s"
        self.cur.execute(sql, vals)
        self.commit()

        return "Course updated successfully"

    def ListCourses(self):
        """
        Return a list of all courses (code, name, credits),
        ordered by course code.
        """
        self.ensure_connection()
        self.cur.execute("SELECT code, name, credits FROM courses ORDER BY code")
        return self.cur.fetchall()

    def DeleteCourse(self, code):
        """
        Delete a course by its code.
        """
        self.ensure_connection()
        self.cur.execute("DELETE FROM courses WHERE code=%s", (code,))
        self.commit()
        return "Course deleted successfully"

    # =========================================================
    # PREREQUISITES
    # =========================================================
    def list_prerequisites(self, course_code):
        """
        Return a list of prerequisite course codes for the given course.
        """
        self.ensure_connection()
        self.cur.execute(
            "SELECT prereq_code FROM requires WHERE course_code=%s ORDER BY prereq_code",
            (course_code,),
        )
        return [t[0] for t in self.cur.fetchall()]

    def add_prerequisite(self, course_code, prereq_code):
        """
        Add a prerequisite for a course.
        """
        self.ensure_connection()
        try:
            self.cur.execute(
                "INSERT INTO requires(course_code, prereq_code) VALUES(%s, %s)",
                (course_code, prereq_code),
            )
            self.commit()
            return "Prerequisite added successfully"
        except psycopg2.IntegrityError:
            self.con.rollback()
            return "Error: prerequisite already exists"

    def update_prerequisite(self, course_code, old_prereq, new_prereq):
        """
        Update an existing prerequisite for a course.
        """
        self.ensure_connection()
        self.cur.execute(
            """
            UPDATE requires
            SET prereq_code=%s
            WHERE course_code=%s AND prereq_code=%s
            """,
            (new_prereq, course_code, old_prereq),
        )
        self.commit()
        return "Prerequisite updated successfully"

    def delete_prerequisite(self, course_code, prereq_code):
        """
        Delete a specific prerequisite from a course.
        """
        self.ensure_connection()
        self.cur.execute(
            """
            DELETE FROM requires
            WHERE course_code=%s AND prereq_code=%s
            """,
            (course_code, prereq_code),
        )
        self.commit()
        return "Prerequisite deleted successfully"

    # =========================================================
    # SECTIONS
    # =========================================================
    def add_section(
        self,
        course_code,
        doctor_id,
        days,
        time_start,
        time_end,
        room,
        capacity,
        semester,
        state="open",
    ):
        """
        Add a new section for a course.
        enrolled is always started at 0.
        """
        self.ensure_connection()
        self.cur.execute(
            """
            INSERT INTO sections(
                course_code, doctor_id, days, time_start, time_end,
                room, capacity, enrolled, semester, state
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, 0, %s, %s)
            """,
            (
                course_code,
                doctor_id,
                days,
                time_start,
                time_end,
                room,
                capacity,
                semester,
                state,
            ),
        )
        self.commit()
        return "Section added successfully"

    def list_sections(self, course_code=None, semester=None):
        """
        List sections with optional filters (course_code, semester).
        Returns all columns ordered by (course_code, section_id).
        """
        self.ensure_connection()
        sql = """
        SELECT section_id, course_code, doctor_id, days, time_start,
               time_end, room, capacity, enrolled, semester, state
        FROM sections
        """
        params = []
        conds = []

        if course_code is not None:
            conds.append("course_code = %s")
            params.append(course_code)

        if semester is not None:
            conds.append("semester = %s")
            params.append(semester)

        if conds:
            sql += " WHERE " + " AND ".join(conds)

        sql += " ORDER BY course_code, section_id"

        self.cur.execute(sql, params)
        return self.cur.fetchall()

    def update_section(
        self,
        section_id,
        doctor_id=None,
        days=None,
        time_start=None,
        time_end=None,
        room=None,
        capacity=None,
        semester=None,
        state=None,
    ):
        """
        Update section data. Only provided fields will be updated.
        """
        self.ensure_connection()
        sets = []
        vals = []

        if doctor_id is not None:
            sets.append("doctor_id=%s")
            vals.append(doctor_id)

        if days is not None:
            sets.append("days=%s")
            vals.append(days)

        if time_start is not None:
            sets.append("time_start=%s")
            vals.append(time_start)

        if time_end is not None:
            sets.append("time_end=%s")
            vals.append(time_end)

        if room is not None:
            sets.append("room=%s")
            vals.append(room)

        if capacity is not None:
            sets.append("capacity=%s")
            vals.append(capacity)

        if semester is not None:
            sets.append("semester=%s")
            vals.append(semester)

        if state is not None:
            sets.append("state=%s")
            vals.append(state)

        if not sets:
            return "Nothing to update"

        vals.append(section_id)

        sql = f"UPDATE sections SET {', '.join(sets)} WHERE section_id=%s"
        self.cur.execute(sql, vals)
        self.commit()

        return "Section updated successfully" if self.cur.rowcount else "Section not found"

    def delete_section(self, section_id):
        """
        Delete a section by section_id.
        """
        self.ensure_connection()
        self.cur.execute("DELETE FROM sections WHERE section_id=%s", (section_id,))
        self.commit()
        return "Section deleted successfully" if self.cur.rowcount else "Section not found"

    # =========================================================
    # USERS
    # =========================================================
    def add_users(self, name, email, password, program, state,):
        """
        Add a new user (student / admin / instructor).
        Default account_status = 'inactive'.
        """
        self.ensure_connection()
        try:
            self.cur.execute(
                """
                INSERT INTO users(name, email, password_h, program, state, account_status)
                VALUES(%s, %s, %s, %s, %s, %s)
                """,
                (
                    name,
                    email,
                    password,
                    program,
                    state,
                    "active" if state in ("admin", "instructor") else "inactive",
                ),
            )
            self.commit()
            return "User added successfully, please wait for final acceptance"
        except psycopg2.IntegrityError:
            self.con.rollback()
            return "email already exists"

    def list_users(self):
        """
        Return a list of all users (basic info).
        """
        self.ensure_connection()
        self.cur.execute(
            """
            SELECT user_id, name, email, program, state, account_status
            FROM users
            """
        )
        return self.cur.fetchall()

    def update_user(
        self,
        user_id,
        name=None,
        email=None,
        program=None,
        password=None,
        account_status=None,
    ):
        """
        Update user information. Only provided fields will be changed.
        """
        self.ensure_connection()
        sets = []
        vals = []

        if name is not None:
            sets.append("name=%s")
            vals.append(name)

        if email is not None:
            sets.append("email=%s")
            vals.append(email)

        if program is not None:
            sets.append("program=%s")
            vals.append(program)

        if password is not None:
            sets.append("password_h=%s")
            vals.append(password)

        if account_status is not None:
            sets.append("account_status=%s")
            vals.append(account_status)

        if not sets:
            return "Nothing to update"

        vals.append(user_id)

        sql = f"UPDATE users SET {', '.join(sets)} WHERE user_id=%s"
        self.cur.execute(sql, vals)
        self.commit()

        return "User updated successfully"

    def user_login(self, user_id, password_h):
        """
        Login user using (user_id, password_h).
        Returns one row or None.
        """
        self.ensure_connection()
        self.cur.execute(
            """
            SELECT user_id, name, email, program, state, account_status
            FROM users
            WHERE user_id=%s AND password_h=%s
            """,
            (user_id, password_h),
        )
        return self.cur.fetchone()

    def get_user_by_id(self, user_id):
        """
        Return user info by user_id.
        """
        self.ensure_connection()
        self.cur.execute(
            """
            SELECT user_id, name, email, program, state, account_status
            FROM users
            WHERE user_id=%s
            """,
            (user_id,),
        )
        return self.cur.fetchone()

    def reset_password_with_email(self, user_id, email, new_password):
        """
        Reset user password if (user_id, email) match.
        """
        self.ensure_connection()
        self.cur.execute(
            """
            UPDATE users
            SET password_h=%s
            WHERE user_id=%s AND email=%s
            """,
            (new_password, user_id, email),
        )

        if self.cur.rowcount == 0:
            self.commit()
            return "Error: ID or email is incorrect"

        self.commit()
        return "Password reset successfully"

    def get_user_by_login(self, login_input):
        """
        Get user by login input (email or user_id).
        """
        self.ensure_connection()
        self.cur.execute(
            """
            SELECT user_id, name, email, program, state, account_status, password_h
            FROM users
            WHERE email=%s OR user_id::text=%s
            """,
            (login_input, login_input),
        )
        return self.cur.fetchone()

    def check_email_exists(self, email: str) -> bool:
        """
        Check if an email already exists in users table (case-insensitive).
        """
        self.ensure_connection()
        self.cur.execute(
            """
            SELECT 1 FROM users
            WHERE LOWER(email) = LOWER(%s)
            LIMIT 1
            """,
            (email,),
        )
        return self.cur.fetchone() is not None

    # =========================================================
    # TRANSCRIPTS
    # =========================================================
    def add_transcript(self, student_id, course_code, semester, grade=None):
        """
        Add a transcript record for a student/course/semester.
        """
        self.ensure_connection()
        try:
            self.cur.execute(
                """
                INSERT INTO transcripts(student_id, course_code, semester, grade)
                VALUES (%s, %s, %s, %s)
                """,
                (student_id, course_code, semester, grade),
            )
            self.commit()
            return "transcript record added successfully"
        except psycopg2.IntegrityError:
            self.con.rollback()
            return " this course/semester is already in transcript for this student"

    def list_transcript(self, student_id):
        """
        List transcript rows for a student.
        """
        self.ensure_connection()
        self.cur.execute(
            """
            SELECT course_code, semester, grade
            FROM transcripts
            WHERE student_id = %s
            ORDER BY semester, course_code
            """,
            (student_id,),
        )
        return self.cur.fetchall()

    def update_transcript_grade(self, student_id, course_code, semester, new_grade):
        """
        Update only the grade for one course in one semester.
        """
        self.ensure_connection()
        self.cur.execute(
            """
            UPDATE transcripts
            SET grade = %s
            WHERE student_id = %s AND course_code = %s AND semester = %s
            """,
            (new_grade, student_id, course_code, semester),
        )

        if self.cur.rowcount == 0:
            self.commit()
            return "Transcript record not found"

        self.commit()
        return "Grade updated successfully"

    # =========================================================
    # PROGRAM PLANS
    # =========================================================
    def add_course_to_plan(self, program, course_code, level):
        """
        Add a course to a program plan for a specific level.
        """
        self.ensure_connection()
        try:
            self.cur.execute(
                """
                INSERT INTO program_plans(program, course_code, level)
                VALUES (%s, %s, %s)
                """,
                (program, course_code, level),
            )
            self.commit()
            return "Course added to plan successfully"
        except psycopg2.IntegrityError:
            self.con.rollback()
            return "This course is already in this plan"

    def delete_course_from_plan(self, program, course_code):
        """
        Delete a course from a specific program plan.
        """
        self.ensure_connection()
        self.cur.execute(
            """
            DELETE FROM program_plans
            WHERE program=%s AND course_code=%s
            """,
            (program, course_code),
        )
        self.commit()

        if self.cur.rowcount > 0:
            return " Course removed from plan successfully"
        return " Course not found in this plan"

    def update_course_in_plan(
        self,
        old_program,
        old_course_code,
        old_level,  # kept for compatibility (even if not used in WHERE)
        new_program,
        new_course_code,
        new_level,
    ):
        """
        Update one row in program_plans:
        From (old_program, old_course_code, old_level)
        To   (new_program, new_course_code, new_level)

        We match using program + course_code (case-insensitive).
        """
        self.ensure_connection()
        old_program = (old_program or "").strip().upper()
        old_course_code = (old_course_code or "").strip().upper()
        new_program = (new_program or "").strip().upper()
        new_course_code = (new_course_code or "").strip().upper()

        try:
            self.cur.execute(
                """
                UPDATE program_plans
                SET program = %s, course_code = %s, level = %s
                WHERE UPPER(program) = %s
                  AND UPPER(course_code) = %s
                """,
                (new_program, new_course_code, new_level, old_program, old_course_code),
            )

            if self.cur.rowcount == 0:
                self.commit()
                return "✗ Course not found in this plan"

            self.commit()
            return "✓ Course in plan updated successfully"

        except psycopg2.IntegrityError:
            self.con.rollback()
            return "This course (with this level) is already in this plan"

    def list_plan_courses(self, program=None):
        """
        List program plan courses.
        If program is None -> list for all programs.
        """
        self.ensure_connection()
        if program is None:
            self.cur.execute(
                """
                SELECT p.program, c.code, c.name, c.credits, p.level
                FROM program_plans p
                JOIN courses c ON p.course_code = c.code
                ORDER BY p.program, p.level, c.code
                """
            )
        else:
            self.cur.execute(
                """
                SELECT p.program, c.code, c.name, c.credits, p.level
                FROM program_plans p
                JOIN courses c ON p.course_code = c.code
                WHERE p.program=%s
                ORDER BY p.level, c.code
                """,
                (program,),
            )

        return self.cur.fetchall()

    # =========================================================
    # STUDENT REGISTRATIONS & CHECKS
    # =========================================================
    def list_student_registrations(self, student_id, semester=None):
        """
        Return list of sections the student is registered in.
        Each item is a row from sections.
        """
        self.ensure_connection()
        # Original logic: list sections (optionally by semester),
        # then check per section if a registration exists.
        # Optimized to avoid N+1 queries by doing one query
        # for all section_ids the student is registered in.
        sections = self.list_sections(semester=semester)

        # Get all section_ids where this student is registered
        self.cur.execute(
            "SELECT section_id FROM registrations WHERE student_id=%s",
            (student_id,),
        )
        registered_ids_rows = self.cur.fetchall()
        registered_ids = {row[0] for row in registered_ids_rows}

        # Filter sections where section_id is in registered_ids
        registrations = [sec for sec in sections if sec[0] in registered_ids]

        return registrations

    def is_student_registered(self, student_id, section_id, semester=None):
        """
        Return True if the student is registered in the section.
        (Semester filter is optional and depends on schema design.)
        """
        self.ensure_connection()
        sql = """
            SELECT 1 FROM registrations
            WHERE student_id = %s AND section_id = %s
        """
        params = [student_id, section_id]

        # Note: If your registrations table has a semester column,
        # you can uncomment this part and update the schema accordingly.
        if semester is not None:
            sql += " AND semester = %s"
            params.append(semester)

        self.cur.execute(sql, params)
        return self.cur.fetchone() is not None

    def list_registrations(self, student_id=None, course_code=None, semester=None):
        """
        Returns rows from registrations table.

        NOTE:
        This assumes that the registrations table has columns:
        (student_id, section_id, course_code, semester).

        If your current schema only has (student_id, section_id),
        you should add those two extra columns or adjust this function.
        """
        self.ensure_connection()
        query = "SELECT student_id, section_id, course_code, semester FROM registrations WHERE 1=1"
        params = []

        if student_id is not None:
            query += " AND student_id = %s"
            params.append(student_id)

        if course_code is not None:
            query += " AND course_code = %s"
            params.append(course_code)

        if semester is not None:
            query += " AND semester = %s"
            params.append(semester)

        self.cur.execute(query, params)
        return self.cur.fetchall()

    def register_student_to_section(
        self, student_id: int, section_id: int, course_code: str, semester: str
    ) -> bool:
        """
        Register a student in a specific section for a given semester.

        Rules:
        - Prevent duplicate registration for (student_id, course_code, semester).
        - Check section state (open/closed).
        - Check capacity/enrolled.
        - Update enrolled count in sections.
        """
        self.ensure_connection()
        try:
            # 1) Get section data
            self.cur.execute(
                """
                SELECT capacity, enrolled, state
                FROM sections
                WHERE section_id = %s
                """,
                (section_id,),
            )
            row = self.cur.fetchone()
            if not row:
                print(f"[DB] Section {section_id} not found")
                return False

            capacity, enrolled, state = row
            capacity = capacity or 0
            enrolled = enrolled or 0
            state_str = (state or "").lower()

            # 2) Check section state
            if state_str == "closed":
                print("[DB] Section is closed.")
                return False

            # 3) Check capacity
            if capacity > 0 and enrolled >= capacity:
                print("[DB] Section is full.")
                return False

            # 4) Check if same course already registered in same semester
            self.cur.execute(
                """
                SELECT 1 FROM registrations
                WHERE student_id = %s AND course_code = %s AND semester = %s
                """,
                (student_id, course_code, semester),
            )
            if self.cur.fetchone():
                print("[DB] Already registered for this course in this semester.")
                return False

            # 5) Insert into registrations
            self.cur.execute(
                """
                INSERT INTO registrations (student_id, section_id, course_code, semester)
                VALUES (%s, %s, %s, %s)
                """,
                (student_id, section_id, course_code, semester),
            )

            # 6) Update enrolled count
            self.cur.execute(
                """
                UPDATE sections
                SET enrolled = COALESCE(enrolled, 0) + 1
                WHERE section_id = %s
                """,
                (section_id,),
            )

            self.con.commit()
            return True

        except Exception as e:
            self.con.rollback()
            print(f"DB Error in register_student_to_section: {e}")
            return False

    def remove_student_registration(self, student_id: int, course_code: str) -> bool:
        """
        Delete a student's registration for a specific course.
        - Delete from registrations
        - Decrease enrolled in sections

        Returns True if something was deleted, False otherwise.
        """
        self.ensure_connection()
        try:
            # 1) Get section_ids where student is registered in this course
            self.cur.execute(
                """
                SELECT section_id
                FROM registrations
                WHERE student_id = %s AND course_code = %s
                """,
                (student_id, course_code),
            )
            rows = self.cur.fetchall()
            if not rows:
                return False

            section_ids = [r[0] for r in rows]

            # 2) Delete registrations
            placeholders = ", ".join(["%s"] * len(section_ids))
            self.cur.execute(
                f"""
                DELETE FROM registrations
                WHERE student_id = %s
                  AND section_id IN ({placeholders})
                """,
                [student_id, *section_ids],
            )

            if self.cur.rowcount == 0:
                self.con.commit()
                return False

            # 3) Decrease enrolled for each section
            self.cur.execute(
                f"""
                UPDATE sections
                SET enrolled = CASE
                    WHEN enrolled IS NULL THEN 0
                    WHEN enrolled - 1 < 0 THEN 0
                    ELSE enrolled - 1
                END
                WHERE section_id IN ({placeholders})
                """,
                section_ids,
            )

            self.con.commit()
            return True

        except Exception as e:
            self.con.rollback()
            print(f"[ERROR] remove_student_registration failed: {e}")
            return False

    # =========================================================
    # SETTINGS (GLOBAL FLAGS)
    # =========================================================
    def get_setting(self, key: str, default: str | None = None) -> str | None:
        """
        Return the value for a setting key from the settings table.
        If the key does not exist or an error occurs, return default.

        NOTE: Make sure you created a table:
        CREATE TABLE settings(
            key   TEXT PRIMARY KEY,
            value TEXT
        );
        """
        self.ensure_connection()
        try:
            self.cur.execute("SELECT value FROM settings WHERE key = %s", (key,))
            row = self.cur.fetchone()
            if row:
                return row[0]
            return default
        except Exception as e:
            print(f"[ERROR] get_setting({key!r}) failed: {e}")
            return default

    def set_setting(self, key: str, value: str) -> None:
        """
        Insert or update a setting key/value.
        """
        self.ensure_connection()
        try:
            self.cur.execute(
                """
                INSERT INTO settings(key, value) VALUES(%s, %s)
                ON CONFLICT(key) DO UPDATE
                SET value = EXCLUDED.value
                """,
                (key, value),
            )
            self.con.commit()
        except Exception as e:
            self.con.rollback()
            print(f"[ERROR] set_setting({key!r}) failed: {e}")

    def is_registration_open(self) -> bool:
        """
        Global registration flag.
        Returns True if registration is open, False otherwise.
        Default is True when the key is missing.
        """
        # get_setting already ensures connection
        val = self.get_setting("registration_open", default="1")
        return str(val) == "1"

    def set_registration_open(self, is_open: bool) -> None:
        """
        Set the global registration flag.
        True  -> students can register/drop.
        False -> registration operations are blocked.
        """
        # set_setting already ensures connection
        self.set_setting("registration_open", "1" if is_open else "0")

    # =========================================================
    # PENDING USERS (INACTIVE ACCOUNTS)
    # =========================================================
    def list_inactive_users(self):
        """
        Return all users whose account_status = 'inactive'.
        """
        self.ensure_connection()
        self.cur.execute(
            """
            SELECT user_id, name, email, program, state
            FROM users
            WHERE account_status = 'inactive'
            """
        )
        return self.cur.fetchall()

    def approve_all_inactive_users(self):
        """
        Change all inactive users to active.
        """
        self.ensure_connection()
        self.cur.execute(
            """
            UPDATE users
            SET account_status = 'active'
            WHERE account_status = 'inactive'
            """
        )
        self.commit()

    def delete_all_inactive_users(self):
        """
        Delete all users whose account_status = 'inactive'.
        """
        self.ensure_connection()
        self.cur.execute("DELETE FROM users WHERE account_status = 'inactive'")
        self.commit()

    # =========================================================
    # TIME CONFLICT CHECK
    # =========================================================
    def has_time_conflict(self, student_id, new_section_id):
        """
        Check if a student has a time conflict with a new section.
        Compares (days, time_start, time_end) with current registrations.
        """
        self.ensure_connection()
        # New section
        self.cur.execute(
            """
            SELECT days, time_start, time_end
            FROM sections
            WHERE section_id = %s
            """,
            (new_section_id,),
        )
        new_row = self.cur.fetchone()
        if not new_row:
            return False

        new_days, new_start, new_end = new_row

        # Current sections of the student
        self.cur.execute(
            """
            SELECT s.section_id, s.days, s.time_start, s.time_end
            FROM registrations r
            JOIN sections s ON r.section_id = s.section_id
            WHERE r.student_id = %s
            """,
            (student_id,),
        )
        registered_sections = self.cur.fetchall()

        for sid, days, start, end in registered_sections:
            # Different days → no conflict
            if days != new_days:
                continue

            # Time overlap check:
            # No conflict if new_end <= start OR new_start >= end
            if not (new_end <= start or new_start >= end):
                return True  # conflict

        return False

    # =========================================================
    # LOGIN HISTORY
    # =========================================================
    def get_last_login(self, user_id: int):
        """
        Returns the last login timestamp for the user.
        """
        self.ensure_connection()
        self.cur.execute(
            "SELECT last_login FROM login WHERE user_id = %s ORDER BY last_login DESC LIMIT 1",
            (user_id,),
        )
        row = self.cur.fetchone()
        return row[0] if row else None

    def update_last_login(self, user_id: int):
        """
        Update last login for a user in login table.
        If a row exists -> update; else -> insert new.
        """
        self.ensure_connection()
        import datetime

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.cur.execute("SELECT 1 FROM login WHERE user_id = %s", (user_id,))
        exists = self.cur.fetchone()

        if exists:
            self.cur.execute(
                "UPDATE login SET last_login = %s WHERE user_id = %s",
                (timestamp, user_id),
            )
        else:
            self.cur.execute(
                "INSERT INTO login (user_id, last_login) VALUES (%s, %s)",
                (user_id, timestamp),
            )

        self.con.commit()
        return timestamp

    # =========================================================
    # USER DELETION
    # =========================================================
    def delete_all_users(self):
        """
        Delete all users from the users table.
        Use carefully!
        """
        self.ensure_connection()
        self.cur.execute("DELETE FROM users")
        self.commit()

    def delete_user(self, user_id: int):
        """
        Delete a single user by user_id.
        """
        self.ensure_connection()
        self.cur.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
        self.commit()
