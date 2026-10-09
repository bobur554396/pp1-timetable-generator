# 📅 Timetable Generator

This Python script generates an exam timetable by assigning students to available rooms based on predefined capacities. The script reads student data from CSV files, determines the exam schedule, and saves the final timetable.

---

## 🚀 Features
- Reads student data from CSV files.
- Assigns students to available rooms based on seat capacity.
- Automatically adjusts exam times if rooms are full.
- Saves the final schedule as a CSV file.

---

## 🛠️ Installation

1. **Clone the repository**:
   ```sh
   git clone https://github.com/bobur554396/pp1-timetable-generator.git
   cd pp1-timetable-generator
   ```

2. **Create a virtual environment (optional but recommended)**:
   ```sh
   python -m venv venv
   source venv/bin/activate  # On macOS/Linux
   venv\Scripts\activate  # On Windows
   ```

3. **Install dependencies** (if any required in `requirements.txt`):
    - script only relies on built-in modules (`os`, `csv`, `datetime`), there are no external dependencies

---

## 📂 File Structure

```
timetable-generator/
│── students/                 # Folder containing student CSV files
│   ├── TE.csv
│   ├── ZZ.csv
│   ├── AA.csv
│   └── ...  
│── room_capacities.py         # Defines available rooms and seating capacities
│── timetable_generator.py     # Main script to generate the timetable
│── final_data.csv             # Output timetable (auto-generated)
│── .gitignore                 # Excludes unnecessary files from Git
│── README.md                  # Project documentation
```

---

## 🔒 Student data is NOT tracked in git

`students/*.csv` and the generated `final_data.csv` contain **student personal data** (IDs and
names), so they are listed in `.gitignore` and are intentionally **not committed** to this public
repository. Clone the repo and add your own `students/<CODE>.csv` files locally before running.

---

## 📌 Usage

1. **Prepare Student Data:**
   - Place one student list per lector inside the `students/` folder.
   - Each file must be named `<LECTOR_CODE>.csv`, where `<LECTOR_CODE>` is the lector's (teacher's)
     code / initials. The valid codes and the lector they map to are defined in the `LECTORS`
     dictionary at the top of `generate_timetable.py`, for example:
     ```python
     LECTORS = {
         'AA': 'Ақша Аян Әділетұлы',
         'BZ': 'Bolatov Zh',
         'BB': 'Байсаков Бейсенбек Миятбекович',
         'MB': 'Мухсимбаев Бобур Абдирахимович',
         # ... one entry per lector
     }
     ```
     Order matters: if the same student ID appears in two lists, the lector listed **first** in
     `LECTORS` keeps the student. To add or rename a lector, edit `LECTORS` and add the matching
     `students/<CODE>.csv`.
   - Format each CSV file using **tab-separated values (`\t`)**, two columns `student_id` and
     `student_name` (no header row):
     ```
     12345<TAB>John Doe
     67890<TAB>Jane Smith
     ```

2. **Run the script:**
   ```sh
   python generate_timetable.py
   ```
   Exam date/time and duration are set by `DEFAULT_EXAM_DATETIME` / `EXAM_DURATION` in the script;
   room seats are set in `room_capacities.py`.

3. **View the generated timetable:**
   - The output is saved as `final_data.csv`, also **tab-separated**, with columns:
     `lector_code<TAB>student_id<TAB>student_name<TAB>exam_datetime<TAB>room`
     (e.g. `AA<TAB>12345<TAB>John Doe<TAB>18.10.2026 / 09:00<TAB>269`).

---

## ⚙️ Configuration

- Modify room capacities in `room_capacities.py` to adjust the available rooms and their seating capacities.

---