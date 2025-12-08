import os
import sys

from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QTableWidgetItem,
    QHeaderView
)
from PyQt6.QtCore import Qt

# Ensure project root is accessible
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

# UI from Qt Designer
from app_ui.student_ui.submenus_ui.ui_view_sections import Ui_ViewSections

# Replacing QMessageBox with info, warning, error
from helper_files.shared_utilities import info, warning, error


class ViewSectionsWidget(QWidget):
    """
    View available sections for selected courses.
    This version removes checkboxes and uses Qt row selection instead.
    """

    def __init__(self, student_utils, admin_utils, semester: str, course_codes, parent=None):
        super().__init__(parent)

        self.ui = Ui_ViewSections()
        self.ui.setupUi(self)

        self.student_utils = student_utils
        self.admin_utils = admin_utils
        self.db = student_utils.db  # shared pooled DB

        self.student_id = student_utils.student_id
        
        self.semester = semester
        self.course_codes = list(course_codes)

        # Section storage
        self.sections = []
        self.row_to_section = {}
        self.display_rows = []

        table = self.ui.tableSections
        table.setSelectionBehavior(table.SelectionBehavior.SelectRows)
        table.setSelectionMode(table.SelectionMode.ExtendedSelection)
        table.setEditTriggers(table.EditTrigger.NoEditTriggers)

        # Register button
        self.ui.buttonRegisterCourse.clicked.connect(self.handle_confirm_registration)

        # Load sections
        self.load_sections()
        self.format_table()
        table.setSortingEnabled(False)

    # ==================== Load Sections ====================

    def load_sections(self):
        """
        Load all available sections for each course code.
        Skip any section already registered by the student in that same semester.
        """
        self.sections = []

        for code in self.course_codes:
            rows = self.student_utils.get_sections_for_course(code, self.semester)

            for sec in rows:
                # Unpack tuple
                section_id = sec[0]
                course_code = sec[1]
                doctor_id = sec[2]
                days = sec[3] or ""
                time_start = sec[4]
                time_end = sec[5]
                room = sec[6] or ""
                capacity = sec[7]
                enrolled = sec[8]
                semester = sec[9]
                state = sec[10] or ""

                # Skip sections already registered
                try:
                    if self.student_utils.db.is_student_registered(
                        self.student_id, section_id, semester
                    ):
                        continue
                except AttributeError as e:
                    print("[WARN] is_student_registered missing:", e)
                    pass

                self.sections.append({
                    "section_id": section_id,
                    "course_code": course_code,
                    "doctor_id": doctor_id,
                    "days": days,
                    "time_start": time_start,
                    "time_end": time_end,
                    "room": room,
                    "capacity": capacity,
                    "enrolled": enrolled,
                    "semester": semester,
                    "state": state,
                })

        self.fill_table()

    # ==================== Fill Table (no checkboxes) ====================

    def fill_table(self):
        table = self.ui.tableSections
        table.clearContents()

        self.display_rows = []
        self.row_to_section = {}

        sorted_secs = sorted(
            self.sections,
            key=lambda s: (s["course_code"], s["section_id"])
        )

        last_code = None
        for sec in sorted_secs:
            if last_code is not None and sec["course_code"] != last_code:
                # Gray separator
                self.display_rows.append(None)
            self.display_rows.append(sec)
            last_code = sec["course_code"]

        table.setRowCount(len(self.display_rows))

        for row, sec in enumerate(self.display_rows):
            if sec is None:
                # Gray separator row
                for col in range(table.columnCount()):
                    item = QTableWidgetItem("")
                    item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                    item.setBackground(Qt.GlobalColor.lightGray)
                    table.setItem(row, col, item)
                continue

            # Store mapping
            self.row_to_section[row] = sec

            # Unpack
            section_id = sec["section_id"]
            course_code = sec["course_code"]
            days = sec["days"]
            time_start = sec["time_start"]
            time_end = sec["time_end"]
            room = sec["room"]
            enrolled = sec["enrolled"]
            capacity = sec["capacity"]
            state = (sec["state"] or "").capitalize()

            # Table items
            # find correct position in only the real sections (excluding separators)
            true_index = len([x for x in self.display_rows[:row] if x is not None])
            table.setItem(row, 0, QTableWidgetItem(str(true_index + 1)))

            table.setItem(row, 1, QTableWidgetItem(str(section_id)))
            table.setItem(row, 2, QTableWidgetItem(course_code))
            table.setItem(row, 3, QTableWidgetItem(""))

            schedule_str = days
            if time_start and time_end:
                schedule_str += f"  {time_start}-{time_end}"
            if room:
                schedule_str += f"  ({room})"

            table.setItem(row, 4, QTableWidgetItem(schedule_str.strip()))
            table.setItem(row, 5, QTableWidgetItem("" if enrolled is None else str(enrolled)))
            table.setItem(row, 6, QTableWidgetItem("" if capacity is None else str(capacity)))
            table.setItem(row, 7, QTableWidgetItem(state))




    def format_table(self):
        table = self.ui.tableSections
        header = table.horizontalHeader()

        table.setSortingEnabled(True)
        table.verticalHeader().setDefaultSectionSize(60)

        for col in range(table.columnCount()):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)


    # ==================== Get Selected Sections ====================

    def get_selected_sections(self):
        """Return list of dicts for selected rows."""
        table = self.ui.tableSections
        selected_rows = table.selectionModel().selectedRows()

        sections = []
        for model_index in selected_rows:
            row = model_index.row()
            if row in self.row_to_section:
                sections.append(self.row_to_section[row])

        return sections

    # ==================== Validate + Register ====================

    def handle_confirm_registration(self):
        selected = self.get_selected_sections()

        if not selected:
            warning(self, "Please select at least one section.")
            return

        # Prevent multiple sections for same course
        code_counts = {}
        for sec in selected:
            c = sec["course_code"]
            code_counts[c] = code_counts.get(c, 0) + 1

        duplicates = [c for c, n in code_counts.items() if n > 1]
        if duplicates:
            msg = "You cannot register more than one section for the same course:\n\n"
            msg += "\n".join(f"- {c}" for c in duplicates)
            warning(self, msg)
            return

        # Check for time conflicts
        if len(selected) > 1:
            for i in range(len(selected)):
                for j in range(i + 1, len(selected)):
                    if self.student_utils.check_time_conflict(selected[i], selected[j]):
                        warning(self, "Time conflict detected between selected sections.")
                        return
                    
        # -----------------------------------------------
        # Check conflicts with already registered courses
        # -----------------------------------------------
        existing = self.student_utils.get_registered_courses_full()

        for new_sec in selected:
            for old in existing:
                # Convert existing course row to same structure
                try:
                    t = old.get("time", "")
                    if t and "-" in t:
                        parts = [p.strip() for p in t.split("-")]
                        old_start, old_end = (parts[0], parts[1]) if len(parts) == 2 else (None, None)
                    else:
                        old_start, old_end = (None, None)
                except Exception:
                    old_start, old_end = (None, None)

                old_section_struct = {
                    "days": old.get("days", ""),
                    "time_start": old_start,
                    "time_end": old_end,
                }

                if self.student_utils.check_time_conflict(new_sec, old_section_struct):
                    warning(self,
                        f"Time conflict detected with an already registered course:\n\n"
                        f"{new_sec['course_code']} conflicts with an existing course."
                    )
                    return


        self.register_selected_sections(selected)

    def register_selected_sections(self, sections):
        success = 0
        fail = 0
        registered_codes = set()

        for sec in sections:
            sid = sec["section_id"]
            code = sec["course_code"]
            semester = sec["semester"]

            ok = self.student_utils.register_section(sid, code, semester)

            try:
                really = self.student_utils.db.is_student_registered(
                    self.student_utils.student_id,
                    sid,
                    semester
                )
            except Exception:
                really = False

            if ok and really:
                success += 1
                registered_codes.add(code)
            else:
                fail += 1

        if registered_codes:
            self.sections = [s for s in self.sections if s["course_code"] not in registered_codes]
            self.fill_table()

        if success and not fail:
            info(self, "All sections have been registered successfully.")
        elif success and fail:
            warning(self, f"Registered {success} sections successfully, and {fail} failed.")
        else:
            error(self, "Failed to register any sections.")

# ===== Test =====
if __name__ == "__main__":
    app = QApplication(sys.argv)

    from database_files.cloud_database import get_pooled_connection
    from database_files.class_database_uitlities import DatabaseUtilities
    from student.class_student_utilities import StudentUtilities
    from admin.class_admin_utilities import AdminUtilities

    con, cur = get_pooled_connection()
    db = DatabaseUtilities(con, cur)

    student_utils = StudentUtilities(db, 2500001)
    admin_utils = AdminUtilities(db)

    w = ViewSectionsWidget(student_utils, admin_utils, "First", ["EE202"])
    w.show()
    sys.exit(app.exec())

