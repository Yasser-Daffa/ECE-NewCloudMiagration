-- WARNING: This schema is for context only and is not meant to be run.
-- Table order and constraints may not be valid for execution.

CREATE TABLE public.courses (
  name text NOT NULL,
  code text NOT NULL,
  credits integer NOT NULL CHECK (credits >= 0),
  CONSTRAINT courses_pkey PRIMARY KEY (code)
);
CREATE TABLE public.login (
  user_id bigint NOT NULL,
  last_login text,
  CONSTRAINT login_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id)
);
CREATE TABLE public.program_plans (
  program text NOT NULL,
  level integer NOT NULL CHECK (level >= 1),
  course_code text NOT NULL,
  CONSTRAINT program_plans_pkey PRIMARY KEY (program, course_code),
  CONSTRAINT program_plans_course_code_fkey FOREIGN KEY (course_code) REFERENCES public.courses(code)
);
CREATE TABLE public.registrations (
  student_id bigint NOT NULL,
  section_id bigint NOT NULL,
  course_code text NOT NULL,
  semester text NOT NULL,
  CONSTRAINT registrations_pkey PRIMARY KEY (student_id, course_code, semester),
  CONSTRAINT registrations_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.users(user_id),
  CONSTRAINT registrations_section_id_fkey FOREIGN KEY (section_id) REFERENCES public.sections(section_id),
  CONSTRAINT registrations_course_code_fkey FOREIGN KEY (course_code) REFERENCES public.courses(code)
);
CREATE TABLE public.requires (
  course_code text NOT NULL,
  prereq_code text NOT NULL,
  CONSTRAINT requires_pkey PRIMARY KEY (course_code, prereq_code),
  CONSTRAINT requires_course_code_fkey FOREIGN KEY (course_code) REFERENCES public.courses(code),
  CONSTRAINT requires_prereq_code_fkey FOREIGN KEY (prereq_code) REFERENCES public.courses(code)
);
CREATE TABLE public.sections (
  section_id bigint NOT NULL DEFAULT nextval('sections_section_id_seq'::regclass),
  course_code text NOT NULL,
  doctor_id bigint,
  days text,
  time_start text,
  time_end text,
  room text,
  capacity integer NOT NULL CHECK (capacity >= 0),
  enrolled integer NOT NULL,
  semester text NOT NULL,
  state text NOT NULL CHECK (state = ANY (ARRAY['open'::text, 'closed'::text])),
  CONSTRAINT sections_pkey PRIMARY KEY (section_id),
  CONSTRAINT sections_course_code_fkey FOREIGN KEY (course_code) REFERENCES public.courses(code),
  CONSTRAINT sections_doctor_id_fkey FOREIGN KEY (doctor_id) REFERENCES public.users(user_id)
);
CREATE TABLE public.settings (
  key text NOT NULL,
  value text NOT NULL,
  CONSTRAINT settings_pkey PRIMARY KEY (key)
);
CREATE TABLE public.students (
  student_id bigint NOT NULL,
  level integer CHECK (level >= 1),
  CONSTRAINT students_pkey PRIMARY KEY (student_id),
  CONSTRAINT students_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.users(user_id)
);
CREATE TABLE public.transcripts (
  student_id bigint NOT NULL,
  course_code text NOT NULL,
  semester text NOT NULL,
  grade text,
  CONSTRAINT transcripts_pkey PRIMARY KEY (student_id, course_code, semester),
  CONSTRAINT transcripts_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.users(user_id),
  CONSTRAINT transcripts_course_code_fkey FOREIGN KEY (course_code) REFERENCES public.courses(code)
);
CREATE TABLE public.users (
  user_id bigint NOT NULL DEFAULT nextval('users_user_id_seq'::regclass),
  name text NOT NULL,
  email text NOT NULL UNIQUE,
  program text CHECK ((program = ANY (ARRAY['PWM'::text, 'BIO'::text, 'COMM'::text, 'COMP'::text])) OR program IS NULL),
  password_h text NOT NULL,
  state text NOT NULL CHECK (state = ANY (ARRAY['admin'::text, 'student'::text, 'instructor'::text])),
  account_status text NOT NULL DEFAULT 'inactive'::text CHECK (account_status = ANY (ARRAY['active'::text, 'inactive'::text])),
  CONSTRAINT users_pkey PRIMARY KEY (user_id)
);