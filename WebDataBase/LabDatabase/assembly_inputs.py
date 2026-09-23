"""Fresh, annotated assembly inputs using the Desktop feature-record workflow."""
from pathlib import Path

from Bio.Seq import Seq

from .feature_records import (record_from_rows, normalized_record, write_record,
                              first, digest, feature_rows)


def source_models(kind):
    from WebDatabase.models import (Parttable, Backbonetable, Plasmidneed,
        Partfeaturetable, Backbonefeaturetable, Plasmidfeaturetable)
    return {
        'part': (Parttable, Partfeaturetable, 'partid', 'level0sequence'),
        'backbone': (Backbonetable, Backbonefeaturetable, 'backboneid', 'sequence'),
        'plasmid': (Plasmidneed, Plasmidfeaturetable, 'plasmidid', 'sequenceconfirm'),
    }[kind]


def source_record(kind, ident):
    model, feature_model, parent_key, sequence_field = source_models(kind)
    obj = model.objects.get(pk=ident)
    sequence = ''.join((getattr(obj, sequence_field) or '').split())
    if not sequence:
        raise ValueError(f'{kind} {obj.name} has no sequence')
    rows = list(feature_model.objects.filter(**{parent_key: ident})
                .order_by(feature_model._meta.pk.name).values())
    return obj, record_from_rows(sequence, rows, name=obj.name)


def attach_source(record, kind, obj):
    """Annotate internal features without adding a whole-plasmid feature."""
    revision = digest({'sequence': str(record.seq).upper(), 'features': feature_rows(record)})
    for feature in record.features:
        feature.qualifiers.setdefault('source_type', [kind])
        feature.qualifiers.setdefault('source_id', [str(obj.pk)])
        feature.qualifiers.setdefault('source_revision', [revision])
    if kind == 'backbone':
        # Only explicit container annotations are removed; real coextensive
        # biological features must survive.
        record.features = [f for f in record.features
                           if first(f.qualifiers, 'source_container') != 'true'
                           and first(f.qualifiers, 'indicates_part').lower() != 'true']
    record.annotations['assembly_source_type'] = kind
    return record


def shift_processed_part(record, processed_sequence):
    raw = str(record.seq).upper()
    offset = processed_sequence.upper().find(raw)
    if offset < 0:
        raise ValueError('Part processing changed the source sequence: ' + record.id)
    for feature in record.features:
        feature.location = feature.location + offset
    record.seq = Seq(processed_sequence)
    return record


def prepare_inputs(data, output_dir, determine_enzyme, process_part, basename):
    """Read current DB annotations each time; never reuse name-based map caches."""
    inputs = Path(output_dir) / 'inputs'
    inputs.mkdir(parents=True, exist_ok=True)
    sources = [(kind, index, *source_record(kind, ident))
               for kind, key in [('backbone', 'backbones'), ('part', 'parts'), ('plasmid', 'plasmids')]
               for index, ident in enumerate(data.get(key, []))]
    enzymes = {determine_enzyme(str(record.seq).lower())
               for kind, _, _, record in sources if kind == 'backbone'}
    if len(enzymes) != 1 or not next(iter(enzymes), ''):
        raise ValueError('A backbone with a consistent assembly enzyme is required')
    enzyme = next(iter(enzymes))
    files, names = [], []
    for kind, index, obj, record in sources:
        attach_source(record, kind, obj)
        if kind == 'part':
            starts, ends = data.get('part_start_scar') or [], data.get('part_end_scar') or []
            part_type = {1: 'promoter', 2: 'cds', 3: 'terminator', 4: 'rbs'}.get(obj.type, 'p+r')
            processed = process_part(str(record.seq).lower(), part_type, enzyme,
                {'source': obj.sourceorganism or ''}, obj.alias or '', obj.name,
                starts[index] if index < len(starts) else '',
                ends[index] if index < len(ends) else '')
            shift_processed_part(record, processed)
        # Index makes duplicate input occurrences distinct without changing labels.
        name = basename(f'{kind}-{obj.pk}-{index}-{obj.name}')
        record.id = record.name = name
        # Persist source kind across GenBank round-trips without a backbone feature.
        record.annotations['comment'] = 'polaris_source_type=' + kind
        path = inputs / (name + '.gb')
        write_record(path, normalized_record(record))
        files.append(str(path)); names.append(name)
    return files, names, enzyme
