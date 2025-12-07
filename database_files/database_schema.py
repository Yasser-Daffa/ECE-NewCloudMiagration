# database_schema.py  (PostgreSQL Version)

import psycopg2
from cloud_database import get_connection
con, cur = get_connection()

def initialize_schema():
    """Create all required tables & triggers inside PostgreSQL."""

    con, cur = get_connection()

    # ================= SETTINGS TABLE =================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key   TEXT PRIMARY KEY,
        value TEXT NOT NULL
    );
    """)

    # ================= COURSES TABLE =================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS courses (
        name TEXT NOT NULL,
        code TEXT PRIMARY KEY,
        credits INTEGER NOT NULL CHECK(credits >= 0)
    );
    """)

    # ================= PREREQUISITES TABLE =================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS requires (
        course_code TEXT NOT NULL,
        prereq_code TEXT NOT NULL,
        CHECK (course_code <> prereq_code),
        PRIMARY KEY (course_code, prereq_code),

        FOREIGN KEY (course_code) REFERENCES courses(code)
            ON DELETE CASCADE ON UPDATE CASCADE,

        FOREIGN KEY (prereq_code) REFERENCES courses(code)
            ON DELETE CASCADE ON UPDATE CASCADE
    );
    """)

    # ================= USERS TABLE =================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id BIGSERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        program TEXT CHECK(program IN ('PWM','BIO','COMM','COMP') OR program IS NULL),
        password_h TEXT NOT NULL,
        state TEXT NOT NULL CHECK(state IN ('admin','student','instructor')),
        account_status TEXT NOT NULL DEFAULT 'inactive'
            CHECK(account_status IN ('active','inactive'))
    );
    """)

    # ================= USER PREFIX TRIGGER =================
    cur.execute("""
    CREATE OR REPLACE FUNCTION apply_user_prefix()
    RETURNS TRIGGER AS $$
    BEGIN
        IF NEW.state = 'student' THEN
            NEW.user_id := NEW.user_id + 2500000;
        ELSIF NEW.state = 'admin' THEN
            NEW.user_id := NEW.user_id + 1100000;
        ELSIF NEW.state = 'instructor' THEN
            NEW.user_id := NEW.user_id + 3300000;
        END IF;
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """)

    cur.execute("DROP TRIGGER IF EXISTS trg_users_prefix_id ON users;")

    cur.execute("""
    CREATE TRIGGER trg_users_prefix_id
    BEFORE INSERT ON users
    FOR EACH ROW
    EXECUTE FUNCTION apply_user_prefix();
    """)

    # ================= LOGIN TABLE =================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS login (
        user_id BIGINT NOT NULL,
        last_login TEXT,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
            ON DELETE CASCADE
    );
    """)

    # ================= STUDENTS TABLE =================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS students (
        student_id BIGINT PRIMARY KEY,
        level INTEGER CHECK(level >= 1),

        FOREIGN KEY (student_id) REFERENCES users(user_id)
            ON DELETE CASCADE ON UPDATE CASCADE
    );
    """)

    # ================= SECTIONS TABLE =================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sections (
        section_id BIGSERIAL PRIMARY KEY,
        course_code TEXT NOT NULL,
        doctor_id BIGINT,
        days TEXT,
        time_start TEXT,
        time_end TEXT,
        room TEXT,
        capacity INTEGER NOT NULL CHECK(capacity >= 0),
        enrolled INTEGER NOT NULL CHECK(enrolled >= 0 AND enrolled <= capacity),
        semester TEXT NOT NULL,
        state TEXT NOT NULL CHECK(state IN ('open','closed')),

        UNIQUE (course_code, section_id, semester),
        UNIQUE (doctor_id, days, time_start, time_end),

        FOREIGN KEY (course_code) REFERENCES courses(code)
            ON DELETE CASCADE ON UPDATE CASCADE,

        FOREIGN KEY (doctor_id) REFERENCES users(user_id)
            ON DELETE CASCADE ON UPDATE CASCADE
    );
    """)

    # ================= REGISTRATIONS TABLE =================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS registrations (
        student_id BIGINT NOT NULL,
        section_id BIGINT NOT NULL,
        course_code TEXT NOT NULL,
        semester TEXT NOT NULL,

        PRIMARY KEY (student_id, course_code, semester),

        FOREIGN KEY (student_id) REFERENCES users(user_id)
            ON DELETE CASCADE ON UPDATE CASCADE,

        FOREIGN KEY (section_id) REFERENCES sections(section_id)
            ON DELETE CASCADE ON UPDATE CASCADE,

        FOREIGN KEY (course_code) REFERENCES courses(code)
            ON DELETE CASCADE ON UPDATE CASCADE
    );
    """)

    # ================= TRANSCRIPTS TABLE =================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS transcripts (
        student_id BIGINT NOT NULL,
        course_code TEXT NOT NULL,
        semester TEXT NOT NULL,
        grade TEXT,

        PRIMARY KEY (student_id, course_code, semester),

        FOREIGN KEY (student_id) REFERENCES users(user_id)
            ON DELETE CASCADE ON UPDATE CASCADE,

        FOREIGN KEY (course_code) REFERENCES courses(code)
            ON UPDATE CASCADE
    );
    """)

    # ================= PROGRAM PLANS TABLE =================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS program_plans (
        program TEXT NOT NULL,
        level INTEGER NOT NULL CHECK(level >= 1),
        course_code TEXT NOT NULL,

        PRIMARY KEY (program, course_code),

        FOREIGN KEY (course_code) REFERENCES courses(code)
            ON DELETE RESTRICT ON UPDATE CASCADE
    );
    """)

    con.commit()
    con.close()
    print("PostgreSQL schema created successfully!")


if __name__ == "__main__":
    initialize_schema()
