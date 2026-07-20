import re
from typing import Dict, List, Tuple


ALLOWED_UNITS = {"bp", "aa", "rc"}
ALLOWED_TOPOLOGY = {"", "linear", "circular"}
DATE_PATTERN = re.compile(r"^\d{2}-[A-Za-z]{3}-\d{4}$")


def _safe_slice(line: str, start: int, end: int) -> str:
    if len(line) < end:
        line = line + (" " * (end - len(line)))
    return line[start:end]


def _parse_locus_tokens(line: str) -> Tuple[str, str, str, str, str, str]:
    tokens = line.strip().split()
    if tokens and tokens[0] == "LOCUS":
        tokens = tokens[1:]

    name = tokens[0] if len(tokens) >= 1 else ""
    length_token = tokens[1] if len(tokens) >= 2 else ""
    unit_token = tokens[2].lower() if len(tokens) >= 3 else "bp"

    date_token = ""
    topology_token = ""
    molecule_token = ""

    for token in reversed(tokens):
        if DATE_PATTERN.match(token):
            date_token = token.upper()
            break

    for token in tokens:
        lowered = token.lower()
        if lowered in {"linear", "circular"}:
            topology_token = lowered
            break

    for token in tokens:
        lowered = token.lower()
        if token == name:
            continue
        if token == length_token:
            continue
        if lowered == unit_token:
            continue
        if token.upper() == date_token:
            continue
        if lowered == topology_token:
            continue
        molecule_token = token
        break

    if not re.fullmatch(r"\d+", length_token or ""):
        digits = re.search(r"\d+", line)
        length_token = digits.group(0) if digits else "0"

    if unit_token not in ALLOWED_UNITS:
        unit_token = "bp"

    if topology_token not in ALLOWED_TOPOLOGY:
        topology_token = ""

    if not DATE_PATTERN.match(date_token):
        date_token = "01-JAN-2000"

    return name, length_token, unit_token, molecule_token, topology_token, date_token


def _build_locus_line(
    name: str,
    length_token: str,
    unit_token: str,
    molecule_token: str,
    topology_token: str,
    date_token: str,
) -> str:
    prefix = "LOCUS       "  # line[:12]

    # Keep length so that unit lands at line[29:33].
    working_name = name.strip() or "unnamed"
    working_len = length_token.strip() or "0"

    max_name_len = 29 - 12 - len(working_len) - 1
    if max_name_len < 1:
        max_name_len = 1
    working_name = working_name[:max_name_len]

    spaces_between = 29 - 12 - len(working_name) - len(working_len)
    if spaces_between < 1:
        spaces_between = 1

    unit_field = f" {unit_token} "  # line[29:33]
    molecule_field = (molecule_token or "").strip()[:9].ljust(9)  # line[33:42]
    topology_field = (topology_token or "").strip()[:9].ljust(9)  # line[42:51]
    # line[51:52] must be space; line[55:62] must be seven spaces
    spacer = " " + (" " * 10)  # [51] + [52:61]
    date_field = date_token[:11].ljust(11)  # starts at [62], dashes at [64] and [68]

    return (
        prefix
        + working_name
        + (" " * spaces_between)
        + working_len
        + unit_field
        + molecule_field
        + topology_field
        + spacer
        + date_field
    )


def _fix_locus_line(line: str, line_no: int) -> Tuple[str, List[Dict[str, str]]]:
    issues: List[Dict[str, str]] = []

    cond1 = _safe_slice(line, 0, 12) == "LOCUS       "
    cond2 = _safe_slice(line, 29, 33) in {" bp ", " aa ", " rc "}
    cond3 = _safe_slice(line, 55, 62) == "       "
    cond4 = _safe_slice(line, 42, 51).strip() in ALLOWED_TOPOLOGY
    cond5 = _safe_slice(line, 51, 52) == " "
    cond6 = _safe_slice(line, 64, 65) == "-"
    cond7 = _safe_slice(line, 68, 69) == "-"

    if all([cond1, cond2, cond3, cond4, cond5, cond6, cond7]):
        return line, issues

    name, length_token, unit_token, molecule_token, topology_token, date_token = _parse_locus_tokens(line)
    fixed_line = _build_locus_line(
        name=name,
        length_token=length_token,
        unit_token=unit_token,
        molecule_token=molecule_token,
        topology_token=topology_token,
        date_token=date_token,
    )

    issues.append(
        {
            "line": str(line_no),
            "type": "LOCUS",
            "problem": "LOCUS line columns are invalid. Spaces were adjusted to satisfy required column checks.",
            "original": line,
            "fixed": fixed_line,
        }
    )
    return fixed_line, issues


def _fix_feature_title_line(line: str, line_no: int) -> Tuple[str, List[Dict[str, str]]]:
    issues: List[Dict[str, str]] = []

    if line[:21].strip() == "":
        return line, issues

    title_part = line[:21]
    location_part = line[21:]
    first_non_space = len(title_part) - len(title_part.lstrip(" "))
    if first_non_space >= 21:
        return line, issues

    # Keep spaces before feature name unchanged.
    title_payload = line[first_non_space:]
    name_match = re.match(r"^([^\s/]+)", title_payload)
    if not name_match:
        return line, issues

    feature_name = name_match.group(1)
    trailing = title_payload[len(feature_name):].lstrip()
    inferred_location = location_part if location_part.strip() else trailing

    available_width = 21 - first_non_space
    if len(feature_name) > available_width:
        fixed_line = f"{line[:first_non_space]}{feature_name} {inferred_location.lstrip()}"
    else:
        gap = " " * (21 - first_non_space - len(feature_name))
        fixed_line = f"{line[:first_non_space]}{feature_name}{gap}{inferred_location.lstrip()}"

    if fixed_line != line:
        issues.append(
            {
                "line": str(line_no),
                "type": "FEATURE",
                "problem": "Feature title and location are not aligned. Spaces between them were adjusted.",
                "original": line,
                "fixed": fixed_line,
            }
        )

    return fixed_line, issues


def fix_genbank_text(text: str) -> Dict[str, object]:
    if not isinstance(text, str):
        raise TypeError("text must be str")

    newline = "\r\n" if "\r\n" in text else "\n"
    lines = text.splitlines()
    if not lines:
        return {"fixed_text": text, "issues": [], "changed": False}

    issues: List[Dict[str, str]] = []

    fixed_first, first_issues = _fix_locus_line(lines[0], 1)
    lines[0] = fixed_first
    issues.extend(first_issues)

    in_features = False
    for idx in range(1, len(lines)):
        line = lines[idx]
        stripped = line.strip()

        if stripped in {"FEATURES             Location/Qualifiers", "FEATURES"}:
            in_features = True
            continue

        if in_features and line.startswith("ORIGIN"):
            in_features = False
            continue

        if in_features:
            fixed_line, feature_issues = _fix_feature_title_line(line, idx + 1)
            lines[idx] = fixed_line
            issues.extend(feature_issues)

    fixed_text = newline.join(lines)
    if text.endswith("\n") and not fixed_text.endswith("\n"):
        fixed_text += newline

    return {
        "fixed_text": fixed_text,
        "issues": issues,
        "changed": fixed_text != text,
    }


def fix_genbank_bytes(data: bytes, encoding: str = "utf-8") -> Dict[str, object]:
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError("data must be bytes or bytearray")

    try:
        text = data.decode(encoding)
    except UnicodeDecodeError:
        text = data.decode("latin-1")
        encoding = "latin-1"

    result = fix_genbank_text(text)
    result["fixed_bytes"] = result["fixed_text"].encode(encoding)
    result["encoding"] = encoding
    return result


def process_uploaded_genbank(uploaded_file) -> Dict[str, object]:
    content = uploaded_file.read()
    uploaded_file.seek(0)

    result = fix_genbank_bytes(content)

    original_name = getattr(uploaded_file, "name", "uploaded.gb")
    if "." in original_name:
        base, ext = original_name.rsplit(".", 1)
        fixed_name = f"{base}_fixed.{ext}"
    else:
        fixed_name = f"{original_name}_fixed.gb"

    result["original_filename"] = original_name
    result["fixed_filename"] = fixed_name
    return result
