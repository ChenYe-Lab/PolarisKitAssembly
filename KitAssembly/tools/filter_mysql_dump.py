import ast
import re
import shutil
from collections import defaultdict
from pathlib import Path


SOURCE = Path(r"C:\Users\admin\Desktop\mysql.sql")
BACKUP = Path(r"C:\Users\admin\Desktop\mysql.sql.bak")
OUTPUT = Path(r"C:\Users\admin\Desktop\mysql.filtered.sql")


PART_AS_PLASMID_NAMES = {
    "pEcP01", "pEcP02", "pEcP03", "pEcP04", "pEcP05", "pEcP06", "pEcP07", "pEcP08", "pEcP09", "pEcP10", "pEcP11", "pEcP12", "pEcP13",
    "pEcR01", "pEcR02", "pEcR03", "pEcR04", "pEcR05", "pEcR06",
    "pEcC01", "pEcC02", "pEcC03", "pEcC04", "pEcC05", "pEcC06", "pEcC07", "pEcC08", "pEcC09", "pEcC10", "pEcC11", "pEcC12", "pEcC13", "pEcC14", "pEcC15",
    "pEcT01", "pEcT02", "pEcT03", "pEcT04", "pEcT05",
    "pScP01", "pScP02", "pScP06", "pScP07", "pScP08", "pScP12", "pScP13", "pScP14", "pScP15", "pScP16", "pScP17", "pScP18", "pScP19", "pScP20", "pScP21",
    "pScP22", "pScP23", "pScP24", "pScP26", "pScP27", "pScP28", "pScP29", "pScP30", "pScP31",
    "pScORF01", "pScORF02", "pScORF03", "pScORF04", "pScORF05", "pScORF06", "pScORF07", "pScORF08", "pScORF09", "pScORF10", "pScORF11", "pScORF12",
    "pScTerm01", "pScTerm03", "pScTerm04", "pScTerm07", "pScTerm09", "pScTerm10", "pScTerm11", "pScTerm17", "pScTerm21",
}

BACKBONE_NAMES = {
    "pEcBB01", "pEcBB02", "pEcBB03", "pEcBB04", "pEcBB05", "pEcBB06", "pEcBB07", "pEcBB08", "pEcBB09", "pEcBB10", "pEcBB11", "pEcBB12", "pEcBB13", "pEcBB14", "pEcBB15",
    "pEcBB16", "pEcBB17", "pEcBB18", "pEcBB19", "pEcBB20", "pEcBB21", "pEcBB22", "pEcBB23", "pEcBB27", "pEcBB28", "pEcBB29", "pEcBB30",
    "pEcBB31", "pEcBB32", "pEcBB33", "pEcBB34", "pEcBB35", "pEcBB36", "pEcBB37", "pEcBB38", "pEcBB39", "pEcBB40",
    "pScbb01", "pScbb02", "pScbb03", "pScbb04", "pScbb05", "pScbb06", "pScbb07", "pScbb08", "pScbb09", "pScbb10", "pScbb11", "pScbb12", "pScbb13",
    "pScbb14", "pScbb15", "pScbb16", "pScbb17", "pScbb18", "pScbb20", "pScbb21", "pScbb22", "pScbb23", "pScbb24", "pScbb25", "pScbb31", "pScbb32", "pScbb33", "pScbb34", "pScbb35",
    "pScbb36", "pScbb37", "pScbb38", "pScbb39", "pScbb40", "pScbb41", "pScbb42", "pScbb43", "pScbb44", "pScbb45", "pScbb46", "pScbb47", "pScbb48", "pScCom02",
}

PLASMID_NAMES = {
    "pEcint01", "pEcint02", "pEcint03", "pEcint04", "pcp20", "pEcint05", "pEcint06", "pEcint07", "pEcint08", "pEcint09", "pEcint10", "pEcint11", "pEcCas", "pEcgRNA",
    "pScLv001", "pScLv002", "pScLv003", "pScLv005", "pScLv007", "pScLv008", "pScLv013", "pCfB2312",
}

TARGET_PLASMID_NAMES = PART_AS_PLASMID_NAMES | PLASMID_NAMES

KEEP_ALL_TABLES = {"django_migrations", "django_content_type", "auth_permission"}

TABLE_RE = re.compile(r"CREATE TABLE `([^`]+)`")
INSERT_RE = re.compile(r"INSERT INTO `([^`]+)` VALUES (.*);", re.S)
COL_RE = re.compile(r"^\s+`([^`]+)`")


def norm(value):
    return str(value).lower() if value is not None else ""


def input_dump():
    return BACKUP if BACKUP.exists() else SOURCE


def iter_statements(path):
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        buffer = []
        for line in handle:
            buffer.append(line)
            stripped = line.rstrip("\r\n")
            if stripped.endswith(";") or stripped.startswith("--") or stripped == "":
                yield "".join(buffer)
                buffer = []
        if buffer:
            yield "".join(buffer)


def collect_columns(path):
    columns = {}
    current = None
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            table_match = TABLE_RE.search(line)
            if table_match:
                current = table_match.group(1)
                columns[current] = []
                continue
            if current:
                if line.startswith(") ENGINE="):
                    current = None
                    continue
                column_match = COL_RE.match(line)
                if column_match:
                    columns[current].append(column_match.group(1))
    return columns


def col_index(columns, table, column):
    lowered = {name.lower(): index for index, name in enumerate(columns.get(table, []))}
    return lowered[column.lower()]


def split_tuples(values_sql):
    tuples = []
    depth = 0
    start = None
    in_string = False
    escape = False
    for index, char in enumerate(values_sql):
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == "'":
                in_string = False
            continue
        if char == "'":
            in_string = True
        elif char == "(":
            if depth == 0:
                start = index
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0 and start is not None:
                tuples.append(values_sql[start:index + 1])
                start = None
    return tuples


def parse_tuple(tuple_sql):
    sentinel = "__MYSQL_ESCAPED_SINGLE_QUOTE__"
    python_tuple = tuple_sql.replace("\\'", sentinel)
    python_tuple = re.sub(r"\bNULL\b", "None", python_tuple)
    value = ast.literal_eval(python_tuple)
    if not isinstance(value, tuple):
        value = (value,)
    return tuple(item.replace(sentinel, "'") if isinstance(item, str) else item for item in value)


def rows_from_statement(statement):
    match = INSERT_RE.match(statement.strip())
    if not match:
        return None, []
    return match.group(1), [parse_tuple(item) for item in split_tuples(match.group(2))]


def tuple_to_sql(value):
    if value is None:
        return "NULL"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value).replace("\\", "\\\\").replace("'", "\\'")
    text = text.replace("\r", "\\r").replace("\n", "\\n")
    return f"'{text}'"


def build_insert(table, rows):
    if not rows:
        return ""
    values = ",".join("(" + ",".join(tuple_to_sql(value) for value in row) + ")" for row in rows)
    return f"INSERT INTO `{table}` VALUES {values};\n"


def collect_base_ids(path, columns):
    target_plasmid_names = {norm(name) for name in TARGET_PLASMID_NAMES}
    target_backbone_names = {norm(name) for name in BACKBONE_NAMES}
    ids = defaultdict(set)
    matched = defaultdict(set)

    for statement in iter_statements(path):
        table, rows = rows_from_statement(statement)
        if table == "plasmidneed":
            id_i = col_index(columns, table, "PlasmidID")
            name_i = col_index(columns, table, "Name")
            for row in rows:
                if norm(row[name_i]) in target_plasmid_names:
                    ids["primary_plasmids"].add(row[id_i])
                    ids["plasmids"].add(row[id_i])
                    matched["plasmids"].add(row[name_i])
        elif table == "backbonetable":
            id_i = col_index(columns, table, "ID")
            name_i = col_index(columns, table, "Name")
            for row in rows:
                if norm(row[name_i]) in target_backbone_names:
                    ids["backbones"].add(row[id_i])
                    matched["backbones"].add(row[name_i])

    for statement in iter_statements(path):
        table, rows = rows_from_statement(statement)
        if table == "parentparttable":
            parent_i = col_index(columns, table, "parentpartid")
            son_i = col_index(columns, table, "sonplasmidid")
            for row in rows:
                if row[son_i] in ids["primary_plasmids"]:
                    ids["parts"].add(row[parent_i])
        elif table == "parentbackbonetable":
            parent_i = col_index(columns, table, "parentbackboneid")
            son_i = col_index(columns, table, "sonplasmidid")
            for row in rows:
                if row[son_i] in ids["primary_plasmids"]:
                    ids["backbones"].add(row[parent_i])
        elif table == "parentplasmidtable":
            parent_i = col_index(columns, table, "ParentPlasmidID")
            son_i = col_index(columns, table, "SonPlasmidID")
            for row in rows:
                if row[son_i] in ids["primary_plasmids"]:
                    ids["plasmids"].add(row[parent_i])

    return ids, matched


def keep_by_id(table, rows, columns, column, wanted_ids):
    if column.lower() not in {name.lower() for name in columns.get(table, [])}:
        return []
    index = col_index(columns, table, column)
    return [row for row in rows if row[index] in wanted_ids]


def filter_rows(table, rows, columns, ids):
    if table in KEEP_ALL_TABLES:
        return rows
    if table == "plasmidneed":
        return keep_by_id(table, rows, columns, "PlasmidID", ids["plasmids"])
    if table in {"plasmidfeaturetable", "plasmid_culture_functions", "tb_plasmid_userfileaddress"}:
        column = {"plasmidfeaturetable": "plasmidid", "plasmid_culture_functions": "plasmid_id", "tb_plasmid_userfileaddress": "plasmidid"}[table]
        return keep_by_id(table, rows, columns, column, ids["plasmids"])
    if table == "plasmidscartable":
        return keep_by_id(table, rows, columns, "PlasmidID", ids["plasmids"])
    if table == "parentplasmidtable":
        return keep_by_id(table, rows, columns, "SonPlasmidID", ids["primary_plasmids"])

    if table == "parttable":
        return keep_by_id(table, rows, columns, "PartID", ids["parts"])
    if table in {"partfeaturetable", "partscartable", "partrputable", "tb_part_userfileaddress"}:
        column = "partid" if table == "tb_part_userfileaddress" else "PartID"
        return keep_by_id(table, rows, columns, column, ids["parts"])
    if table == "parentparttable":
        return keep_by_id(table, rows, columns, "sonplasmidid", ids["primary_plasmids"])

    if table == "backbonetable":
        return keep_by_id(table, rows, columns, "ID", ids["backbones"])
    if table in {"backbonefeaturetable", "backbonescartable", "backbone_culture_functions", "tb_backbone_userfileaddress"}:
        column = {
            "backbonefeaturetable": "BackboneID",
            "backbonescartable": "BackboneID",
            "backbone_culture_functions": "backbone_id",
            "tb_backbone_userfileaddress": "backboneid",
        }[table]
        return keep_by_id(table, rows, columns, column, ids["backbones"])
    if table == "parentbackbonetable":
        return keep_by_id(table, rows, columns, "sonplasmidid", ids["primary_plasmids"])

    return []


def main():
    if not SOURCE.exists() and not BACKUP.exists():
        raise SystemExit(f"Missing source dump: {SOURCE}")
    if not BACKUP.exists():
        shutil.copy2(SOURCE, BACKUP)

    source = input_dump()
    columns = collect_columns(source)
    ids, matched = collect_base_ids(source, columns)
    counts = defaultdict(int)

    with OUTPUT.open("w", encoding="utf-8", newline="") as output:
        for statement in iter_statements(source):
            table, rows = rows_from_statement(statement)
            if table is None:
                output.write(statement)
                continue
            kept = filter_rows(table, rows, columns, ids)
            counts[table] += len(kept)
            if kept:
                output.write(build_insert(table, kept))

    shutil.copy2(OUTPUT, SOURCE)

    matched_plasmids_norm = {norm(name) for name in matched["plasmids"]}
    matched_backbones_norm = {norm(name) for name in matched["backbones"]}
    missing_plasmids = sorted([name for name in TARGET_PLASMID_NAMES if norm(name) not in matched_plasmids_norm], key=str.lower)
    missing_backbones = sorted([name for name in BACKBONE_NAMES if norm(name) not in matched_backbones_norm], key=str.lower)

    print(f"Backup: {BACKUP}")
    print(f"Filtered dump: {OUTPUT}")
    print(f"primary plasmids matched: {len(matched['plasmids'])}/{len(TARGET_PLASMID_NAMES)}")
    print(f"primary plasmid ids: {len(ids['primary_plasmids'])}; plasmid ids with parent plasmids: {len(ids['plasmids'])}")
    print(f"parent part ids: {len(ids['parts'])}; backbone ids with parent/list backbones: {len(ids['backbones'])}")
    if missing_plasmids:
        print("missing plasmid/list names: " + ", ".join(missing_plasmids))
    print(f"backbones matched by name: {len(matched['backbones'])}/{len(BACKBONE_NAMES)}")
    if missing_backbones:
        print("missing backbone names: " + ", ".join(missing_backbones))
    for table in sorted(counts):
        if counts[table]:
            print(f"{table}: {counts[table]}")


if __name__ == "__main__":
    main()
