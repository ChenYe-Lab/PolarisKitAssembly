"""Persist a construct, annotations and direct parent edges in one transaction."""
import json

from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST

from LabDatabase.feature_records import record_from_rows, normalized_record, feature_rows
from .models import (Plasmidneed, Parttable, Backbonetable, Plasmidfeaturetable,
    Parentparttable, Parentbackbonetable, Parentplasmidtable,
    Plasmidscartable, Plasmid_Culture_Functions)


def _parents(data):
    result = {}
    for key, model in [('parts', Parttable), ('backbones', Backbonetable), ('plasmids', Plasmidneed)]:
        values = data.get(key, [])
        if not isinstance(values, list):
            raise ValueError(key + ' must be a list of IDs')
        ids = list(dict.fromkeys(int(value) for value in values))
        objects = {obj.pk: obj for obj in model.objects.filter(pk__in=ids)}
        if len(objects) != len(ids):
            raise ValueError('Missing parent records: ' + key)
        result[key] = [objects[ident] for ident in ids]
    return result


def infer_level(parents, supplied=None):
    if supplied not in (None, ''):
        level = int(supplied)
    elif parents['plasmids']:
        levels = [int(obj.level) for obj in parents['plasmids']]
        level = max(levels) + 1
    elif parents['parts']:
        level = 1
    else:
        raise ValueError('At least one Part or Plasmid parent is required')
    if level not in (1, 2, 3):
        raise ValueError('Assembly level must be 1, 2 or 3')
    if any(int(obj.level) >= level for obj in parents['plasmids']):
        raise ValueError('Plasmid parents must have a lower level than the result')
    return str(level)


def validate_feature_rows(rows, length):
    if not isinstance(rows, list):
        raise ValueError('assembly_features must be a list')
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('Each feature must be an object')
        start, end = int(row['feature_start']), int(row['feature_end'])
        if not 1 <= start <= end <= length:
            raise ValueError('Feature segment outside result sequence')
        if row.get('coordinate_system') != 'one_based_closed':
            raise ValueError('Feature coordinates must be one_based_closed')
        if row.get('strand') not in (-1, 0, 1, None):
            raise ValueError('Invalid feature strand')
        if not row.get('feature_group') or not isinstance(row.get('feature_metadata', {}), dict):
            raise ValueError('Feature group and metadata are required')


@transaction.atomic
def save_assembly_result(data, username):
    name = str(data.get('name') or '').strip()
    sequence = ''.join(str(data.get('sequence') or '').split()).upper()
    if not name or len(name) > 20 or not sequence:
        raise ValueError('A name of at most 20 characters and a nonempty sequence are required')
    parents = _parents(data)
    level = infer_level(parents, data.get('level'))
    rows = data['assembly_features']
    validate_feature_rows(rows, len(sequence))
    record = normalized_record(record_from_rows(sequence, rows, name=name))
    rows = feature_rows(record)
    obj = Plasmidneed.objects.select_for_update().filter(name__iexact=name).first()
    if obj and any(parent.pk == obj.pk for parent in parents['plasmids']):
        raise ValueError('A construct cannot be its own parent')
    if obj:
        # Prevent cycles when an existing result is replaced with a descendant.
        pending = [parent.pk for parent in parents['plasmids']]
        visited = set()
        while pending:
            ident = pending.pop()
            if ident == obj.pk:
                raise ValueError('Assembly parent relationship would create a cycle')
            if ident not in visited:
                visited.add(ident)
                pending.extend(Parentplasmidtable.objects.filter(sonplasmidid_id=ident)
                               .values_list('parentplasmidid_id', flat=True))
    now = timezone.now()
    if obj is None:
        obj = Plasmidneed(name=name, uploaddate=now)
    obj.level, obj.length, obj.sequenceconfirm = level, len(sequence), sequence
    obj.user, obj.updatedate = username, now
    obj.alias, obj.note = data.get('alias') or '', data.get('note') or ''
    obj.save()
    Plasmidfeaturetable.objects.filter(plasmidid=obj).delete()
    Plasmidfeaturetable.objects.bulk_create([Plasmidfeaturetable(plasmidid=obj, **row) for row in rows])
    for key, model, field in [('parts', Parentparttable, 'parentpartid'),
                              ('backbones', Parentbackbonetable, 'parentbackboneid'),
                              ('plasmids', Parentplasmidtable, 'parentplasmidid')]:
        model.objects.filter(sonplasmidid=obj).delete()
        model.objects.bulk_create([model(sonplasmidid=obj, **{field: parent}) for parent in parents[key]])
    culture = data.get('culture', {})
    Plasmid_Culture_Functions.objects.filter(plasmid_id=obj).delete()
    for kind in ('ori', 'marker'):
        for value in dict.fromkeys(culture.get(kind, [])):
            Plasmid_Culture_Functions.objects.create(plasmid_id=obj, function_type=kind, function_content=value)
    scars = data.get('scars', {})
    Plasmidscartable.objects.filter(plasmidid=obj).delete()
    Plasmidscartable.objects.create(plasmidid=obj, **{key: str(scars.get(key, ''))
        for key in ('bsmbi', 'bsai', 'bbsi', 'aari', 'sapi')})
    return {'success': True, 'plasmid_id': obj.pk, 'level': obj.level,
            'feature_segments': len(rows)}


@require_POST
def save_assembly_result_view(request):
    try:
        data = json.loads(request.body)
        username = request.session.get('info', {}).get('uname')
        if not username:
            return JsonResponse({'success': False, 'message': 'Login required'}, status=403)
        return JsonResponse(save_assembly_result(data, username))
    except (ValueError, TypeError, KeyError) as exc:
        return JsonResponse({'success': False, 'message': str(exc)}, status=400)
