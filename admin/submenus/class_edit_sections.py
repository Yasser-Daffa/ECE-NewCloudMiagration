import os
import sys

from PyQt6.QtWidgets import QDialog, QMessageBox
from PyQt6.QtCore import QTime

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from app_ui.admin_ui.submenus_ui.edit_section_dialog import Ui_EditSectionDialog
from helper_files.shared_utilities import BaseLoginForm


class EditSectionDialog(QDialog, BaseLoginForm):
    """
    Dialog for editing an existing section:
    - Receives admin_utils + section_data (dict) from the manage sections screen.
    - Pre-fills the UI with the existing values.
    - When Save is pressed → calls admin.admin_update_section.
    """

    def __init__(self, admin_utils, section_data: dict, parent=None):
        QDialog.__init__(self, parent)
        BaseLoginForm.__init__(self, parent)

        self.ui = Ui_EditSectionDialog()
        self.ui.setupUi(self)

        self.admin_utils = admin_utils
        self.db = admin_utils.db
        
        self.section_data = section_data
        self.section_id = section_data["section_id"]

        # Store the original days text (we currently do not modify days in this dialog)
        self.original_days = section_data.get("days") or ""

        # Prepare UI with existing data
        self.setup_initial_values()

        # Connect buttons
        self.ui.buttonSave.clicked.connect(self.handle_save)
        self.ui.buttonCancel.clicked.connect(self.reject)

    # ================= INITIAL VALUE SETUP =================

    def setup_initial_values(self):
        """
        Loads all section data into the UI fields.
        Some fields (like course code) are locked for editing.
        """
        d = self.section_data

        # ----- Course (display only, not editable here) -----
        self.ui.comboBoxSelectCourse.clear()
        self.ui.comboBoxSelectCourse.addItem(str(d["course_code"]))
        self.ui.comboBoxSelectCourse.setEnabled(False)

        # ----- Instructor (simple editable text or numeric id) -----
        self.ui.comboBoxSelectInstructor.clear()
        doctor_val = "" if d["doctor_id"] is None else str(d["doctor_id"])
        if doctor_val:
            self.ui.comboBoxSelectInstructor.addItem(doctor_val)
            self.ui.comboBoxSelectInstructor.setCurrentIndex(0)
        self.ui.comboBoxSelectInstructor.setEditable(True)

        # ----- Time fields -----
        def parse_time(value, default_h=8, default_m=0):
            """
            Convert 'HH:MM' string to QTime.
            If invalid or empty, return a default time.
            """
            if not value:
                return QTime(default_h, default_m)
            try:
                h, m = str(value).split(":")
                return QTime(int(h), int(m))
            except Exception:
                return QTime(default_h, default_m)

        self.ui.timeEditFrom.setTime(parse_time(d.get("time_start")))
        self.ui.timeEditTo.setTime(parse_time(d.get("time_end"), default_h=9))

        # ----- Building + Room parsing from room field -----
        room_val = (d.get("room") or "").strip()
        building = ""
        room = ""

        # Attempt to split building and room, e.g. "B45-201"
        if "-" in room_val:
            building, room = room_val.split("-", 1)
        elif " " in room_val:
            building, room = room_val.split(" ", 1)
        else:
            building = room_val

        self.ui.lineEditBuilding.setText(building)
        self.ui.lineEditRoom.setText(room)

        # ----- Capacity -----
        cap = d.get("capacity") or 0
        try:
            cap = int(cap)
        except ValueError:
            cap = 0
        self.ui.spinBoxCapacity.setValue(cap)

        # ----- Semester -----
        semester = (d.get("semester") or "").strip()
        if semester:
            idx = self.ui.comboBoxSelectTerm.findText(semester)
            if idx >= 0:
                self.ui.comboBoxSelectTerm.setCurrentIndex(idx)
            else:
                # If this semester is not in the list, append it
                self.ui.comboBoxSelectTerm.addItem(semester)
                self.ui.comboBoxSelectTerm.setCurrentIndex(
                    self.ui.comboBoxSelectTerm.count() - 1
                )

        # ----- State (open / closed) -----
        state = (d.get("state") or "").capitalize()
        if state:
            idx = self.ui.comboBoxSelectStatus.findText(state)
            if idx >= 0:
                self.ui.comboBoxSelectStatus.setCurrentIndex(idx)

        # ===== NOTE ABOUT DAYS =====
        # The `days` field is currently treated as a direct text copy (e.g. "UMW", "SU", etc.).
        # In this editor version, we do NOT modify days, because changing the format might
        # break schedule conflict logic elsewhere.
        # UI day buttons are cosmetic for now; the actual stored days come from original_days.
        # If future full day-edit support is needed, unify day formatting across the project.

    # ================= SAVE HANDLER =================

    def handle_save(self):
        """
        Collects new values from UI and calls admin_update_section.
        Note: course_code and section_id are not changed here.
        """

        # ---- Capacity ----
        capacity = self.ui.spinBoxCapacity.value()
        if capacity <= 0:
            QMessageBox.warning(self, "Invalid Capacity", "Capacity must be greater than 0.")
            return

        # ---- Time ----
        time_start = self.ui.timeEditFrom.time().toString("HH:mm")
        time_end = self.ui.timeEditTo.time().toString("HH:mm")
        if time_start >= time_end:
            QMessageBox.warning(self, "Invalid Time", "Start time must be before end time.")
            return

        # ---- Building + Room -> single room field ----
        building = self.ui.lineEditBuilding.text().strip()
        room_num = self.ui.lineEditRoom.text().strip()

        if building and room_num:
            room = f"{building}-{room_num}"
        else:
            room = building or room_num or None

        # ---- Instructor ----
        instr_text = self.ui.comboBoxSelectInstructor.currentText().strip()
        doctor_id = None
        if instr_text:
            if instr_text.isdigit():
                doctor_id = int(instr_text)
            else:
                # If the DB expects only numeric IDs, adjust column type accordingly.
                doctor_id = instr_text

        # ---- Semester ----
        semester = self.ui.comboBoxSelectTerm.currentText().strip() or None

        # ---- State ----
        state_text = self.ui.comboBoxSelectStatus.currentText().strip().lower() or None

        # ---- Days (keep original) ----
        days = self.original_days

        # ================= PERFORM UPDATE =================
        msg = self.admin_utils.admin_update_section(
            section_id=self.section_id,
            doctor_id=doctor_id,
            days=days,
            time_start=time_start,
            time_end=time_end,
            room=room,
            capacity=capacity,
            semester=semester,
            state=state_text,
        )

        QMessageBox.information(
            self,
            "Update Section",
            msg or "Section updated successfully."
        )
        self.accept()
