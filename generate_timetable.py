import os
import csv
import sys
import glob
import argparse
import collections
from datetime import datetime, timedelta
from room_capacities import ROOM_CAPACITIES, get_available_room

# Lector code -> full name, written as "Lastname Firstname ...".
# The order matters: when a student is listed twice, the first lector here wins.
LECTORS = {
    'AA': 'Ақша Аян Әділетұлы',
    'BZ': 'Bolatov Zh',
    'BB': 'Байсаков Бейсенбек Миятбекович',
    'MB': 'Мухсимбаев Бобур Абдирахимович',
    'UN': 'Усюкин Никита Александрович',
    'MS': 'Mosavi Sakina',
    'IT': 'Исмагамбетова Томирис Нурлановна',
    'SA': 'Садуахас Алмас',
    'KA': 'Келгенбаев Арнұр Ғалиасқарұлы',
}
STUDENT_DIR = 'students'
DEFAULT_EXAM_DATETIME = datetime(2026, 11, 15, 9, 0, 0)
EXAM_DURATION = timedelta(minutes=90)
LATEST_EXAM_END = 18  # hour, exams finishing later than this are flagged


def lector_lastname(lector: str) -> str:
    """
    Lastname of a lector, falling back to the code for lectors missing from LECTORS.
    """
    full_name = LECTORS.get(lector, '')
    return full_name.split()[0] if full_name else lector


def lector_label(lector: str) -> str:
    """
    "AA (Ақша)" for the report, just the code when the name is unknown.
    """
    lastname = lector_lastname(lector)
    return f'{lector} ({lastname})' if lastname != lector else lector


def read_lector_file(lector: str) -> tuple:
    """
    Reads one lector CSV.
    Returns (students, bad_rows) where bad_rows is a list of (line_number, row).
    Blank lines are ignored, they are not reported as problems.
    """
    file_path = os.path.join(STUDENT_DIR, f'{lector}.csv')
    students, bad_rows = [], []

    with open(file_path, 'r', encoding='utf-8') as f:
        for line_number, row in enumerate(csv.reader(f, delimiter='\t'), start=1):
            if not any(field.strip() for field in row):
                continue

            if len(row) < 2 or not row[0].strip() or not row[1].strip():
                bad_rows.append((line_number, row))
                continue

            students.append({'lector': lector, 'id': row[0].strip(), 'name': row[1].strip()})

    return students, bad_rows


def analyse(lectors: list = None) -> dict:
    """
    Reads every lector list and checks it before any timetable is built.

    Returns a report dict with the deduplicated students plus everything worth
    telling the lectors about. Errors block generation, warnings do not.
    """
    lectors = lectors or list(LECTORS)
    report = {
        'counts': {},        # lector -> rows read
        'students': [],      # deduplicated, in LECTORS order
        'missing_files': [],
        'unlisted_files': [],
        'empty_files': [],
        'bad_rows': {},      # lector -> [(line_number, row), ...]
        'repeated_in_file': collections.defaultdict(list),   # lector -> [(id, name, count)]
        'repeated_across': collections.defaultdict(list),    # id -> [(lector, name), ...]
    }

    on_disk = {os.path.basename(p)[:-4] for p in glob.glob(os.path.join(STUDENT_DIR, '*.csv'))}
    report['unlisted_files'] = sorted(on_disk - set(lectors))

    seen = {}
    for lector in lectors:
        file_path = os.path.join(STUDENT_DIR, f'{lector}.csv')
        if not os.path.exists(file_path):
            report['missing_files'].append(lector)
            report['counts'][lector] = 0
            continue

        students, bad_rows = read_lector_file(lector)
        report['counts'][lector] = len(students)

        if bad_rows:
            report['bad_rows'][lector] = bad_rows
        if not students:
            report['empty_files'].append(lector)

        # the same id twice inside one lector's own list
        within = collections.Counter(s['id'] for s in students)
        names = {s['id']: s['name'] for s in students}
        for student_id, count in within.items():
            if count > 1:
                report['repeated_in_file'][lector].append((student_id, names[student_id], count))

        for student in students:
            already_listed = seen.get(student['id'])
            if already_listed:
                # a repeat inside this same list is already reported as repeated_in_file
                if already_listed['lector'] == lector:
                    continue
                if student['id'] not in report['repeated_across']:
                    report['repeated_across'][student['id']].append(
                        (already_listed['lector'], already_listed['name']))
                report['repeated_across'][student['id']].append((lector, student['name']))
                continue

            seen[student['id']] = student
            report['students'].append(student)

    return report


def print_report(report: dict) -> tuple:
    """
    Prints the analysis. Returns (error_count, warning_count).
    """
    errors = warnings = 0
    total_rows = sum(report['counts'].values())

    print('=' * 62)
    print('VALIDATION')
    print('=' * 62)
    for lector in LECTORS:
        count = report['counts'].get(lector, 0)
        note = ''
        if lector in report['missing_files']:
            note = '  <- file missing'
        elif lector in report['empty_files']:
            note = '  <- empty'
        print(f'  {lector + ".csv":<10} {count:>5} students  '
              f'{lector_lastname(lector):<16}{note}'.rstrip())
    print(f'  {"":->10} {total_rows:>5} rows read')

    if report['unlisted_files']:
        errors += len(report['unlisted_files'])
        print('\nERROR  CSV files not listed in LECTORS (their students are ignored):')
        for lector in report['unlisted_files']:
            print(f'    students/{lector}.csv  -> add "{lector}" to LECTORS '
                  f'(with the lector name), or delete the file')

    if report['missing_files']:
        errors += len(report['missing_files'])
        print('\nERROR  lectors in LECTORS with no CSV file:')
        for lector in report['missing_files']:
            print(f'    {lector_label(lector)}  -> expected students/{lector}.csv')

    if report['bad_rows']:
        count = sum(len(rows) for rows in report['bad_rows'].values())
        errors += count
        print(f'\nERROR  malformed rows ({count}), expected "id<TAB>name":')
        for lector, rows in report['bad_rows'].items():
            for line_number, row in rows:
                print(f'    students/{lector}.csv:{line_number}  {row}')

    if report['repeated_in_file']:
        count = sum(len(items) for items in report['repeated_in_file'].values())
        errors += count
        print(f'\nERROR  same id listed twice inside one list ({count}):')
        for lector, items in report['repeated_in_file'].items():
            for student_id, name, times in items:
                print(f'    {lector_label(lector)}: {student_id}  {name}  x{times}')

    if report['repeated_across']:
        errors += len(report['repeated_across'])
        print(f'\nERROR  students listed by more than one lector ({len(report["repeated_across"])}).')
        print('       Forward the block below to each lector so they fix their list:\n')

        by_lector = collections.defaultdict(list)
        for student_id, entries in report['repeated_across'].items():
            for lector, name in entries:
                others = [f'{lector_lastname(other_lector)} ({other_lector}): "{other_name}"'
                          for other_lector, other_name in entries if other_lector != lector]
                by_lector[lector].append((student_id, name, ', '.join(others)))

        for lector in sorted(by_lector):
            print(f'    --- {lector_label(lector)} ---')
            for student_id, name, others in sorted(by_lector[lector]):
                print(f'    {student_id}  {name}')
                print(f'        -> also listed by {others}')
            print()

    if report['empty_files']:
        warnings += len(report['empty_files'])
        print('WARN   empty lists (no students scheduled for them):')
        for lector in report['empty_files']:
            print(f'    students/{lector}.csv  {lector_label(lector)}')

    capacity = sum(ROOM_CAPACITIES.values())
    students = len(report['students'])
    if capacity and students:
        slots = -(-students // capacity)
        last_end = DEFAULT_EXAM_DATETIME + EXAM_DURATION * slots
        spare = slots * capacity - students
        print(f'\n       {students} students to schedule, {capacity} seats per slot')
        print(f'       -> {slots} slot(s), ends {last_end.strftime("%d.%m.%Y / %H:%M")}, '
              f'{spare} spare seat(s)')
        if last_end.hour > LATEST_EXAM_END or last_end.date() > DEFAULT_EXAM_DATETIME.date():
            warnings += 1
            print(f'WARN   last exam ends after {LATEST_EXAM_END}:00')
        if spare < capacity // 10:
            warnings += 1
            print(f'WARN   only {spare} spare seat(s), almost no room for extra students')

    print()
    if errors:
        print(f'FAILED: {errors} error(s), {warnings} warning(s)')
    else:
        print(f'OK: no errors, {warnings} warning(s)')

    return errors, warnings


def generate_timetable(students: list) -> list:
    """
    Generates a timetable with available rooms and exam times.
    """
    final_data = []
    remaining_places = ROOM_CAPACITIES.copy()
    exam_datetime = DEFAULT_EXAM_DATETIME

    for student in students:
        available_room, remaining_places, is_available_seat = get_available_room(remaining_places)

        if not is_available_seat:
            exam_datetime += EXAM_DURATION
            remaining_places = ROOM_CAPACITIES.copy()
            available_room, remaining_places, is_available_seat = get_available_room(remaining_places)

            if not is_available_seat:
                raise ValueError('ROOM_CAPACITIES has no rooms with free seats')

        final_data.append([student['lector'], student['id'], student['name'],
                           exam_datetime.strftime('%d.%m.%Y / %H:%M'), available_room])

    return final_data


def save_file(filename='final_data.csv', data=None):
    """
    Saves the timetable data to a CSV file.
    """
    data = data or []
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerows(data)


def main():
    parser = argparse.ArgumentParser(
        description='Validate the student lists, then generate the exam timetable.')
    parser.add_argument('--check', action='store_true',
                        help='only run the validation, never write the timetable')
    parser.add_argument('--force', action='store_true',
                        help='generate even if the validation found errors '
                             '(duplicates keep the first lector in LECTORS)')
    parser.add_argument('--output', default='final_data.csv', help='output file')
    args = parser.parse_args()

    report = analyse()
    errors, _ = print_report(report)

    if args.check:
        return 1 if errors else 0

    if errors and not args.force:
        print(f'\n{args.output} was NOT written. Fix the errors above, or re-run with --force.')
        return 1

    if errors:
        print('\n--force: generating anyway, duplicates keep the first lector in LECTORS.')

    if not report['students']:
        print(f'\nNo students to schedule, {args.output} was NOT written.')
        return 1

    timetable = generate_timetable(report['students'])
    save_file(args.output, timetable)

    slots = {row[3] for row in timetable}
    print(f'\n{len(timetable)} students, {len(slots)} slot(s), '
          f'{timetable[0][3]} to {timetable[-1][3]} -> {args.output}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
