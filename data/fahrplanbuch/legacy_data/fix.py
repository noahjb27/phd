import csv
import ast

INPUT_FILE = './stations.csv'
OUTPUT_FILE = 'stations_modified.csv'

OMNIBUS_LINES = {'O40', 'O30', 'O37'}

def parse_lines(val):
    # Try to parse as list, fallback to split by comma
    try:
        if val.startswith('['):
            return ast.literal_eval(val)
        else:
            return [v.strip() for v in val.split(',') if v.strip()]
    except Exception:
        return [val]

def stringify_lines(lines):
    # Return as stringified list if more than one, else as string
    if len(lines) > 1:
        return str(lines)
    elif lines:
        return lines[0]
    else:
        return ''

with open(INPUT_FILE, encoding='utf-8') as fin, open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as fout:
    reader = csv.reader(fin)
    writer = csv.writer(fout)
    for row in reader:
        if len(row) < 5:
            writer.writerow(row)
            continue
        in_lines_raw = row[4]
        lines = parse_lines(in_lines_raw)
        # Flatten lines in case of nested lists
        flat_lines = []
        for l in lines:
            if isinstance(l, list):
                flat_lines.extend(l)
            else:
                flat_lines.append(l)
        has_omnibus = any(l in OMNIBUS_LINES for l in flat_lines)
        if has_omnibus:
            other_lines = [l for l in flat_lines if l not in OMNIBUS_LINES]
            omnibus_lines = [l for l in flat_lines if l in OMNIBUS_LINES]
            if other_lines:
                # Write row for other lines (original type)
                row_other = row.copy()
                row_other[4] = stringify_lines(other_lines)
                writer.writerow(row_other)
                # Write row for omnibus lines
                row_omnibus = row.copy()
                row_omnibus[4] = stringify_lines(omnibus_lines)
                row_omnibus[2] = 'omnibus'
                writer.writerow(row_omnibus)
            else:
                # Only omnibus lines, set type to omnibus
                row[2] = 'omnibus'
                writer.writerow(row)
        else:
            writer.writerow(row)