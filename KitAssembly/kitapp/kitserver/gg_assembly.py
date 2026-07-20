import copy
from typing import Dict, List, Optional

from Bio import SeqIO
from Bio.Restriction import BbsI, BsaI, BsmBI
from Bio.Seq import Seq
from Bio.SeqFeature import FeatureLocation
from Bio.SeqRecord import SeqRecord


GG_ENZYME_RULES = {
    "bsai": {
        "enzyme_cls": BsaI,
        "site_fwd": "GGTCTC",
        "site_rev": "GAGACC",
        "fwd_cut_after_site": 1,
        "rev_cut_before_site": 5,
        "overhang_len": 4,
    },
    "bsmbi": {
        "enzyme_cls": BsmBI,
        "site_fwd": "CGTCTC",
        "site_rev": "GAGACG",
        "fwd_cut_after_site": 1,
        "rev_cut_before_site": 5,
        "overhang_len": 4,
    },
    "bbsi": {
        "enzyme_cls": BbsI,
        "site_fwd": "GAAGAC",
        "site_rev": "GTCTTC",
        "fwd_cut_after_site": 2,
        "rev_cut_before_site": 6,
        "overhang_len": 4,
    },
}


def _find_recognition_starts_with_biopython(seq_text: str, enzyme_key: str) -> List[int]:
    # Use BioPython Restriction search to detect sites, then map each cut position
    # back to recognition-site start (0-based index).
    rule = GG_ENZYME_RULES[enzyme_key]
    enzyme_cls = rule["enzyme_cls"]
    motif = rule["site_fwd"]
    seq_obj = Seq(seq_text)
    cut_positions = enzyme_cls.search(seq_obj)
    starts = []
    motif_len = len(motif)

    for cut_pos_1b in cut_positions:
        # First guess based on enzyme fst5 definition.
        guess_0b = (cut_pos_1b - enzyme_cls.fst5)  # convert to 0-based start
        matched = None
        for cand in range(guess_0b - motif_len, guess_0b + motif_len + 1):
            if cand < 0 or cand + motif_len > len(seq_text):
                continue
            if seq_text[cand:cand + motif_len] == motif:
                matched = cand
                break
        if matched is not None:
            starts.append(matched)

    return sorted(set(starts))


def _extract_fragment_core(record: SeqRecord, enzyme_key: str) -> Optional[Dict]:
    # Find one inward-facing Type IIS site pair and extract:
    # 1) left/right 4bp overhangs
    # 2) insert sequence between cut positions
    # 3) coordinates used for feature remapping.
    rule = GG_ENZYME_RULES[enzyme_key]
    seq_text = str(record.seq).upper()
    fwd_sites = _find_recognition_starts_with_biopython(seq_text, enzyme_key)
    rev_sites = _find_recognition_starts_with_biopython(str(Seq(seq_text).reverse_complement()), enzyme_key)
    # Convert reverse-complement coordinates back to original sequence coordinates.
    motif_len = len(rule["site_rev"])
    rev_sites = sorted(set(len(seq_text) - (p + motif_len) for p in rev_sites))
    site_len = len(rule["site_fwd"])
    overhang_len = rule["overhang_len"]

    for lf in fwd_sites:
        for rr in rev_sites:
            if rr <= lf:
                continue
            left_cut = lf + site_len + rule["fwd_cut_after_site"]
            right_cut = rr - rule["rev_cut_before_site"]
            if right_cut <= left_cut:
                continue
            if left_cut + overhang_len > len(seq_text):
                continue
            if right_cut - overhang_len < 0:
                continue
            left_overhang = seq_text[left_cut:left_cut + overhang_len]
            right_overhang = seq_text[right_cut - overhang_len:right_cut]
            insert_seq = seq_text[left_cut:right_cut]
            if len(left_overhang) != overhang_len or len(right_overhang) != overhang_len:
                continue
            return {
                "record": record,
                "enzyme": enzyme_key,
                "left_overhang": left_overhang,
                "right_overhang": right_overhang,
                "insert_seq": insert_seq,
                "insert_start": left_cut,
                "insert_end": right_cut,
            }
    return None


def _parse_single_record(record: SeqRecord, enzyme: str) -> Optional[Dict]:
    # Parse a GenBank record into a Golden Gate-ready fragment.
    # If enzyme=auto, try supported enzymes in predefined order.
    if enzyme != "auto":
        if enzyme not in GG_ENZYME_RULES:
            return None
        return _extract_fragment_core(record, enzyme)
    for ek in GG_ENZYME_RULES:
        found = _extract_fragment_core(record, ek)
        if found:
            return found
    return None


def _remap_features_forward(record: SeqRecord, insert_start: int, insert_end: int, offset: int):
    # Map source features that overlap the insert region onto assembled sequence
    # when fragment orientation is forward.
    out = []
    for f in record.features:
        if not isinstance(f.location, FeatureLocation):
            continue
        os_ = int(f.location.start)
        oe = int(f.location.end)
        if oe <= insert_start or os_ >= insert_end:
            continue
        ns = max(os_, insert_start) - insert_start + offset
        ne = min(oe, insert_end) - insert_start + offset
        if ne <= ns:
            continue
        nf = copy.deepcopy(f)
        nf.location = FeatureLocation(ns, ne, strand=f.location.strand)
        out.append(nf)
    return out


def _remap_features_reverse(record: SeqRecord, insert_start: int, insert_end: int, offset: int):
    # Map source features for reverse orientation:
    # coordinates are mirrored and strand is flipped.
    out = []
    for f in record.features:
        if not isinstance(f.location, FeatureLocation):
            continue
        os_ = int(f.location.start)
        oe = int(f.location.end)
        if oe <= insert_start or os_ >= insert_end:
            continue
        cs = max(os_, insert_start)
        ce = min(oe, insert_end)
        if ce <= cs:
            continue
        ns = offset + (insert_end - ce)
        ne = offset + (insert_end - cs)
        strand = None if f.location.strand is None else -f.location.strand
        nf = copy.deepcopy(f)
        nf.location = FeatureLocation(ns, ne, strand=strand)
        out.append(nf)
    return out


def _build_variants(parsed_items: List[Dict]) -> Dict[int, List[Dict]]:
    # For each parsed fragment, build two assembly variants:
    # forward orientation and reverse-complement orientation.
    by_fragment = {}
    for idx, item in enumerate(parsed_items):
        rec = item["record"]
        insert_seq = item["insert_seq"]
        lo = item["left_overhang"]
        ro = item["right_overhang"]
        ins_s = item["insert_start"]
        ins_e = item["insert_end"]

        by_fragment.setdefault(idx, []).append({
            "fragment_id": idx,
            "name": rec.id or rec.name or f"fragment_{idx + 1}",
            "orientation": "forward",
            "left_overhang": lo,
            "right_overhang": ro,
            "insert_seq": insert_seq,
            "features_fn": lambda offset, rec=rec, s=ins_s, e=ins_e: _remap_features_forward(rec, s, e, offset),
        })

        by_fragment[idx].append({
            "fragment_id": idx,
            "name": rec.id or rec.name or f"fragment_{idx + 1}",
            "orientation": "reverse",
            "left_overhang": str(Seq(ro).reverse_complement()),
            "right_overhang": str(Seq(lo).reverse_complement()),
            "insert_seq": str(Seq(insert_seq).reverse_complement()),
            "features_fn": lambda offset, rec=rec, s=ins_s, e=ins_e: _remap_features_reverse(rec, s, e, offset),
        })
    return by_fragment


def _dfs_assemble(variants_by_fragment: Dict[int, List[Dict]], used: set, path: List[Dict]):
    # Depth-first search for an order where adjacent overhangs match:
    # previous.right_overhang == next.left_overhang.
    if len(path) == len(variants_by_fragment):
        return path
    need_left = path[-1]["right_overhang"]
    for fid, vars_ in variants_by_fragment.items():
        if fid in used:
            continue
        for v in vars_:
            if v["left_overhang"] != need_left:
                continue
            used.add(fid)
            path.append(v)
            done = _dfs_assemble(variants_by_fragment, used, path)
            if done:
                return done
            path.pop()
            used.remove(fid)
    return None


def _find_path(parsed_items: List[Dict]) -> Optional[List[Dict]]:
    # Try each oriented fragment as a seed and resolve a full assembly path.
    variants_by_fragment = _build_variants(parsed_items)
    for fid, vars_ in variants_by_fragment.items():
        for seed in vars_:
            used = {fid}
            path = [seed]
            done = _dfs_assemble(variants_by_fragment, used, path)
            if done:
                return done
    return None


def _build_record(path: List[Dict], output_name: str) -> SeqRecord:
    # Concatenate ordered inserts and merged remapped features into one GenBank record.
    parts = []
    features = []
    offset = 0
    for p in path:
        seq_part = p["insert_seq"]
        parts.append(seq_part)
        features.extend(p["features_fn"](offset))
        offset += len(seq_part)
    record = SeqRecord(
        Seq("".join(parts)),
        id=output_name,
        name=output_name,
        description="Golden Gate assembly result",
    )
    record.annotations["molecule_type"] = "DNA"
    record.features = features
    return record


def assemble_genbank_files(files, enzyme: str = "auto", output_name: str = "GG_Assembly_Result") -> SeqRecord:
    # Public API:
    # 1) parse all input GenBank files into GG-ready fragments
    # 2) infer assembly order by overhang matching
    # 3) build assembled SeqRecord with merged feature annotations
    parsed = []
    for f in files:
        record = SeqIO.read(f, "genbank")
        item = _parse_single_record(record, (enzyme or "auto").lower())
        if not item:
            raise ValueError(f"Cannot find valid inward Golden Gate sites in file: {getattr(f, 'name', 'unknown')}")
        parsed.append(item)

    if len(parsed) < 2:
        raise ValueError("At least two GenBank files are required for assembly.")

    path = _find_path(parsed)
    if not path:
        raise ValueError("Cannot resolve a unique Golden Gate assembly order from overhangs.")

    return _build_record(path, output_name)
