import os
import sys

from PyQt6.QtWidgets import (
    QWidget,
    QApplication,
    QTableWidgetItem,
    QMessageBox,
)
from PyQt6.QtCore import Qt

# Add main folder to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

# UI & dialogs
from app_ui.admin_ui.submenus_ui.ui_manage_sections import Ui_ManageSections
from admin.submenus.class_add_sections import AddSectionDialog
from admin.submenus.class_edit_sections import EditSectionDialog  # NEW

# Admin object
from admin.class_admin_utilities import admin
from helper_files.shared_utilities import BaseLoginForm


class ManageSectionsWidget(QWidget):
    """
    Manage Sections:
    - Display all sections in table
    - Filtering & searching
    - Delete selected rows
    - Add section dialog
    - Edit selected section (opens EditSectionDialog)
    """

    def __init__(self, admin_utils, parent=None):
        super().__init__(parent)
        self.ui = Ui_ManageSections()
        self.ui.setupUi(self)

        self.admin_utils = admin_utils
        self.animate = BaseLoginForm.animate_label_with_dots

        # Cache of all sections loaded from DB
        self._all_rows_cache = []
        # Rows after applying current filters
        self._filtered_rows = []

        # Connect buttons
        self.ui.buttonRefresh.clicked.connect(self.handle_refresh)
        self.ui.buttonRemoveSelected.clicked.connect(self.on_remove_selected_clicked)
        self.ui.buttonAddSection.clicked.connect(self.on_add_section_clicked)

        # Connect edit button if exists in UI
        if hasattr(self.ui, "buttonEditSection"):
            self.ui.buttonEditSection.clicked.connect(self.on_edit_section_clicked)

        # Filters
        self.ui.lineEditSearch.textChanged.connect(self.apply_filters)
        self.ui.comboBoxFilterCourses.currentIndexChanged.connect(self.apply_filters)
        self.ui.comboBoxStatusFilter.currentIndexChanged.connect(self.apply_filters)

        # Open/Close all
        self.ui.buttonOpenAll.clicked.connect(self.on_open_all_clicked)
        self.ui.buttonCloseAll.clicked.connect(self.on_close_all_clicked)

        # Table formatting
        self.format_table()
        self.setup_courses_combo()

        # Row selection behavior
        self.ui.tableSections.setSelectionBehavior(
            self.ui.tableSections.SelectionBehavior.SelectRows
        )
        self.ui.tableSections.setSelectionMode(
            self.ui.tableSections.SelectionMode.MultiSelection
        )

        # Track selection change to update delete button
        self.ui.tableSections.itemSelectionChanged.connect(
            self.update_remove_button_state
        )

        # Remove button initially disabled
        self.ui.buttonRemoveSelected.setEnabled(False)
        self.ui.buttonRemoveSelected.setText("Remove")

        # Load initial dataset
        self.load_sections()
        self.update_registration_label()

    # ---------------- Table appearance ----------------
    def format_table(self):
        """Set table column widths and appearance."""
        table = self.ui.tableSections
        header = table.horizontalHeader()
        header.setStretchLastSection(True)
        table.verticalHeader().setDefaultSectionSize(80)

        table.setColumnWidth(0, 60)
        table.setColumnWidth(1, 80)
        table.setColumnWidth(2, 120)
        table.setColumnWidth(3, 120)
        table.setColumnWidth(4, 340)

    # --------------- Setup ComboBox for filtering courses ------------------
    def setup_courses_combo(self):
        """Populates comboBoxFilterCourses with all courses from the DB."""
        cb = self.ui.comboBoxFilterCourses
        cb.clear()
        cb.addItem("All Courses", None)  # default

        courses = self.admin_utils.list_courses()  # (code, name, credits)
        for code, name, _ in courses:
            cb.addItem(f"{code} - {name}", code)

    # ---------------- Load sections from DB ----------------
    def load_sections(self):
        """
        Loads all sections using admin_utils.admin_list_sections()
        Stores to cache and applies filters.
        """
        result = self.admin_utils.admin_list_sections()
        if isinstance(result, str):
            # error or empty result returned as string
            self._all_rows_cache = []
            self.ui.tableSections.setRowCount(0)
            self.update_stats([])
            return

        rows = []
        for (
            section_id,
            course_code,
            doctor_id,
            days,
            time_start,
            time_end,
            room,
            capacity,
            enrolled,
            semester,
            state,
        ) in result:
            rows.append({
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

        self._all_rows_cache = rows
        self.update_stats(rows)
        self.apply_filters()

    def handle_refresh(self):
        """Play animation on labels and refresh section data."""
        labels = [
            self.ui.labelTotalSectionsCount,
            self.ui.labelOpenSectionsCount,
            self.ui.labelClosedSectionsCount,
            self.ui.labelFullSectionsCount,
        ]
        for lbl in labels:
            self.animate(
                lbl,
                "refreshing",
                interval=400,
                duration=2000,
                on_finished=self.load_sections
            )

    # ---------------- Stats calculation ----------------
    def update_stats(self, rows):
        """
        Updates the counters for total, open, full, and closed sections.
        """
        total = len(rows)
        open_count = 0
        full_count = 0
        closed_count = 0

        for r in rows:
            state = (r["state"] or "").lower()
            enrolled = r["enrolled"] or 0
            capacity = r["capacity"] or 0

            if state == "closed":
                closed_count += 1
            elif enrolled >= capacity and capacity > 0:
                full_count += 1
            else:
                open_count += 1

        self.ui.labelTotalSectionsCount.setText(str(total))
        self.ui.labelOpenSectionsCount.setText(str(open_count))
        self.ui.labelFullSectionsCount.setText(str(full_count))
        self.ui.labelClosedSectionsCount.setText(str(closed_count))

    # ---------------- Filter & search ----------------
    def apply_filters(self):
        """
        Applies search text + course filter + status filter.
        """
        search_text = self.ui.lineEditSearch.text().strip().lower()
        course_filter_code = self.ui.comboBoxFilterCourses.currentData()
        status_filter = self.ui.comboBoxStatusFilter.currentText().strip()

        filtered = []
        for r in self._all_rows_cache:

            # Search by section ID
            if search_text and search_text not in str(r["section_id"]).lower():
                continue

            # Filter by course
            if course_filter_code and str(r["course_code"]) != str(course_filter_code):
                continue

            # Filter by status
            if status_filter and status_filter != "All Status":
                if (r["state"] or "").lower() != status_filter.lower():
                    continue

            filtered.append(r)

        self.fill_table(filtered)

    # ---------------- Fill table with rows ----------------
    def fill_table(self, rows):
        """
        Populates the table with the given rows and stores filtered copy.
        """
        table = self.ui.tableSections
        table.setRowCount(len(rows))
        self._filtered_rows = list(rows)

        for row_idx, r in enumerate(rows):
            section_id = r["section_id"]
            course_code = r["course_code"]
            doctor_id = r["doctor_id"]
            days = r["days"]
            time_start = r["time_start"]
            time_end = r["time_end"]
            room = r["room"]
            capacity = r["capacity"]
            enrolled = r["enrolled"]
            semester = r["semester"]
            state = r["state"]

            # Row number
            item_num = QTableWidgetItem(str(row_idx + 1))
            item_num.setFlags(item_num.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_num.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row_idx, 0, item_num)

            # Section ID
            item_id = QTableWidgetItem(str(section_id))
            item_id.setFlags(item_id.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row_idx, 1, item_id)

            # Course
            item_course = QTableWidgetItem(str(course_code))
            item_course.setFlags(item_course.flags() & ~Qt.ItemFlag.ItemIsEditable)
            table.setItem(row_idx, 2, item_course)

            # Instructor
            item_inst = QTableWidgetItem(str(doctor_id) if doctor_id is not None else "-")
            item_inst.setFlags(item_inst.flags() & ~Qt.ItemFlag.ItemIsEditable)
            table.setItem(row_idx, 3, item_inst)

            # Schedule (days, time, room, semester)
            schedule_text = f"{days or ''} {time_start or ''}-{time_end or ''}"
            if room:
                schedule_text += f" | Room {room}"
            if semester:
                schedule_text += f" | {semester}"
            item_sched = QTableWidgetItem(schedule_text.strip())
            item_sched.setFlags(item_sched.flags() & ~Qt.ItemFlag.ItemIsEditable)
            table.setItem(row_idx, 4, item_sched)

            # Enrolled
            item_enrolled = QTableWidgetItem(str(enrolled))
            item_enrolled.setFlags(item_enrolled.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_enrolled.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row_idx, 5, item_enrolled)

            # Capacity
            item_cap = QTableWidgetItem(str(capacity))
            item_cap.setFlags(item_cap.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_cap.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row_idx, 6, item_cap)

            # Status
            nice_state = (state or "").capitalize()
            item_state = QTableWidgetItem(nice_state)
            item_state.setFlags(item_state.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_state.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row_idx, 7, item_state)

    # ---------------- EDIT SELECTED SECTION ----------------
    def on_edit_section_clicked(self):
        """
        Opens EditSectionDialog for the currently selected row.
        """
        table = self.ui.tableSections
        current_row = table.currentRow()

        if current_row < 0:
            QMessageBox.information(self, "Edit Section", "Please select a section first.")
            return

        if current_row >= len(self._filtered_rows):
            QMessageBox.warning(self, "Error", "Invalid row selected.")
            return

        section_data = self._filtered_rows[current_row]
        dlg = EditSectionDialog(self.admin_utils, section_data, self)

        if dlg.exec():
            self.load_sections()

    # ---------------- Delete selected sections ----------------
    def on_remove_selected_clicked(self):
        table = self.ui.tableSections
        selected_rows = set(item.row() for item in table.selectedItems())

        if not selected_rows:
            QMessageBox.information(self, "Info", "No sections selected.")
            return

        # Extract section IDs from selected rows
        rows_to_delete = []
        for row in selected_rows:
            item_id = table.item(row, 1)
            if item_id:
                try:
                    rows_to_delete.append(int(item_id.text()))
                except ValueError:
                    continue

        if not rows_to_delete:
            QMessageBox.information(self, "Info", "No valid sections selected.")
            return

        reply = BaseLoginForm().show_confirmation(
            "Delete Sections",
            f"Are you sure you want to delete {len(rows_to_delete)} section(s)?"
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        for sid in rows_to_delete:
            self.admin_utils.admin_delete_section(sid)

        self.load_sections()

    # ---------------- Update remove button text/state ----------------
    def update_remove_button_state(self):
        """
        Updates the 'Remove' button depending on the number of selected rows.
        """
        table = self.ui.tableSections
        selected_rows = set(item.row() for item in table.selectedItems())
        count = len(selected_rows)

        if count > 0:
            self.ui.buttonRemoveSelected.setEnabled(True)
            self.ui.buttonRemoveSelected.setText(f"Remove ({count})")
        else:
            self.ui.buttonRemoveSelected.setEnabled(False)
            self.ui.buttonRemoveSelected.setText("Remove")

    # ---------------- Add section dialog ----------------
    def on_add_section_clicked(self):
        dlg = AddSectionDialog(self.admin_utils, self)
        if dlg.exec():
            self.load_sections()

    # ---------------- Open all sections & enable registration ----------------
    def on_open_all_clicked(self):
        """
        Sets all loaded sections to 'open' and also enables global student registration.
        """
        if not self._all_rows_cache:
            QMessageBox.information(self, "Info", "No sections available.")
            return

        reply = BaseLoginForm().show_confirmation(
            "Open All Sections",
            f"Are you sure you want to open all {len(self._all_rows_cache)} sections?"
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        for r in self._all_rows_cache:
            self.admin_utils.admin_update_section(
                section_id=r["section_id"],
                state="open",
            )

        # Enable global registration
        try:
            self.admin_utils.db.set_registration_open(True)
        except Exception as e:
            print(f"[WARN] set_registration_open(True) failed: {e}")

        self.load_sections()
        self.update_registration_label()

    # ---------------- Close all sections & disable registration ----------------
    def on_close_all_clicked(self):
        """
        Sets all loaded sections to 'closed' and disables global registration.
        """
        if not self._all_rows_cache:
            QMessageBox.information(self, "Info", "No sections available.")
            return

        reply = BaseLoginForm().show_confirmation(
            "Close All Sections",
            f"Are you sure you want to close all {len(self._all_rows_cache)} sections?"
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        for r in self._all_rows_cache:
            self.admin_utils.admin_update_section(
                section_id=r["section_id"],
                state="closed",
            )

        # Disable global registration
        try:
            self.admin_utils.db.set_registration_open(False)
        except Exception as e:
            print(f"[WARN] set_registration_open(False) failed: {e}")

        self.load_sections()
        self.update_registration_label()

    # ---------------- Registration status label ----------------
    def update_registration_label(self):
        """
        Reads global registration flag from DB and updates labelRegistrationStatus.
        """
        try:
            is_open = self.admin_utils.db.is_registration_open()
        except Exception:
            is_open = False  # fallback

        if is_open:
            self.ui.labelStatus.setText("Registration: OPEN")
            self.ui.labelStatus.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.ui.labelStatus.setText("Registration: CLOSED")
            self.ui.labelStatus.setStyleSheet("color: red; font-weight: bold;")



# =============================== MAIN (Optional test run) ===============================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = ManageSectionsWidget(admin)
    w.show()
    sys.exit(app.exec())
