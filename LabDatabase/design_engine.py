import uuid
from typing import Dict, List, Optional

from django.db.models import Q
from django.utils import timezone

from WebDatabase.models import Backbonetable, CustomUser, Parttable, Temporaryrepository


PROMOTER_TYPE = 1
CDS_TYPE = 2
TERMINATOR_TYPE = 3
RBS_TYPE = 4
REFERENCE_STRENGTH = 20.0
PROMOTER_STRENGTH_PRESETS = [5.0, 10.0, 20.0, 35.0, 50.0, 75.0, 100.0]
RBS_STRENGTH_PRESETS = [2.0, 5.0, 10.0, 15.0, 25.0, 40.0, 60.0]
TERMINATOR_STRENGTH_PRESETS = [1.0, 2.0, 4.0, 8.0, 12.0, 16.0, 20.0]
PART_CANDIDATE_LIMIT = 20
ASSUMED_PROMOTER_STRENGTHS = [
    2.0, 4.0, 6.0, 8.0, 10.0,
    12.0, 15.0, 18.0, 22.0, 26.0,
    30.0, 35.0, 40.0, 48.0, 56.0,
    64.0, 72.0, 82.0, 92.0, 100.0,
]
ASSUMED_RBS_STRENGTHS = [
    1.0, 2.0, 3.0, 4.0, 5.0,
    6.5, 8.0, 10.0, 12.0, 14.0,
    16.0, 18.0, 21.0, 24.0, 28.0,
    32.0, 37.0, 43.0, 51.0, 60.0,
]
ASSUMED_TERMINATOR_STRENGTHS = [
    0.5, 1.0, 1.5, 2.0, 2.5,
    3.0, 4.0, 5.0, 6.0, 7.0,
    8.0, 9.0, 10.0, 11.0, 12.0,
    13.0, 15.0, 17.0, 19.0, 20.0,
]

ASSUMED_STRENGTH_PROFILES = {
    PROMOTER_TYPE: ASSUMED_PROMOTER_STRENGTHS,
    RBS_TYPE: ASSUMED_RBS_STRENGTHS,
    TERMINATOR_TYPE: ASSUMED_TERMINATOR_STRENGTHS,
}

CHASSIS_OPTIONS = [
    {"value": "ecoli", "label": "E. coli", "keywords": ["coli", "ecoli", "e. coli"]},
    {"value": "yeast", "label": "Yeast", "keywords": ["yeast", "saccharomyces"]},
    {"value": "bacillus", "label": "Bacillus", "keywords": ["bacillus"]},
    {"value": "mammalian", "label": "Mammalian", "keywords": ["mamm", "hek", "cho"]},
]

CHASSIS_MAP = {item["value"]: item for item in CHASSIS_OPTIONS}


def _parse_numeric(value: Optional[float]) -> Optional[float]:
    """Convert a user-provided numeric value into a positive float."""
    if value in (None, ""):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        raise ValueError("强度输入必须是数值")
    if parsed <= 0:
        raise ValueError("强度输入必须大于 0")
    return parsed


def _serialize_part(part: Parttable, strength: float) -> Dict:
    """Convert a part model instance into a lightweight response payload."""
    return {
        "id": part.partid,
        "name": part.name or f"Part-{part.partid}",
        "alias": part.alias or "",
        "strength": round(strength, 4),
    }


def _serialize_backbone(backbone: Backbonetable) -> Dict:
    """Convert a backbone model instance into a lightweight response payload."""
    return {
        "id": backbone.id,
        "name": backbone.name,
        "alias": backbone.alias or "",
        "species": backbone.species or "",
        "copy_number": backbone.copynumber or "",
        "strength": REFERENCE_STRENGTH,
    }


def _build_strength_series(count: int, min_value: float, max_value: float) -> List[float]:
    """Generate evenly spaced strength values for a fixed number of candidates."""
    if count <= 1:
        return [(min_value + max_value) / 2]
    step = (max_value - min_value) / (count - 1)
    return [min_value + index * step for index in range(count)]


def _fetch_part_candidates(part_type: int, min_strength: float, max_strength: float, limit: int = PART_CANDIDATE_LIMIT) -> List[Dict]:
    """Fetch part candidates and assign assumed strengths from a fixed 20-item profile."""
    parts = list(
        Parttable.objects.filter(type=part_type)
        .exclude(level0sequence__isnull=True)
        .exclude(level0sequence="")
        .order_by("name")[:limit]
    )
    if not parts:
        return []

    assumed_strengths = ASSUMED_STRENGTH_PROFILES.get(part_type, [])
    if assumed_strengths:
        strengths = assumed_strengths[: len(parts)]
    else:
        strengths = _build_strength_series(len(parts), min_strength, max_strength)
    return [_serialize_part(part, strength) for part, strength in zip(parts, strengths)]


def _fetch_backbone_candidates(chassis: str, limit: int = 12) -> List[Dict]:
    """Fetch backbone candidates that best match the requested chassis keywords."""
    # chassis_info = CHASSIS_MAP.get(chassis, CHASSIS_MAP["ecoli"])
    # queryset = Backbonetable.objects.exclude(sequence__isnull=True).exclude(sequence="")
    # species_filter = Q()
    # for keyword in chassis_info["keywords"]:
    #     species_filter |= Q(species__icontains=keyword)
    #     species_filter |= Q(notes__icontains=keyword)
    #     species_filter |= Q(alias__icontains=keyword)

    # backbones = list(queryset.filter(species_filter).order_by("name")[:limit])
    # if not backbones:
    #     backbones = list(queryset.order_by("name")[:limit])
    # return [_serialize_backbone(backbone) for backbone in backbones]

    """Fetch the fixed backbone required by the selected chassis."""
    target_name = "pEcBb15" if (chassis or "").lower() == "ecoli" else "pScBb04"
    backbone = (
        Backbonetable.objects.exclude(sequence__isnull=True)
        .exclude(sequence="")
        .filter(name__iexact=target_name)
        .first()
    )
    if backbone is None:
        return []
    return [_serialize_backbone(backbone)]

def _pick_nearest(candidates: List[Dict], target_strength: float) -> Optional[Dict]:
    """Select the candidate whose strength is closest to the target value."""
    if not candidates:
        return None
    return min(candidates, key=lambda item: abs(item["strength"] - target_strength))


def _resolve_strengths(payload: Dict) -> Dict[str, float]:
    """Resolve missing strength inputs and compute the final target expression."""
    promoter = _parse_numeric(payload.get("promoter_strength"))
    rbs = _parse_numeric(payload.get("rbs_strength"))
    terminator = _parse_numeric(payload.get("terminator_strength"))
    target_expression = _parse_numeric(payload.get("expression_strength"))

    provided = {
        "promoter": promoter,
        "rbs": rbs,
        "terminator": terminator,
    }
    missing_keys = [key for key, value in provided.items() if value is None]

    if target_expression is None:
        if missing_keys:
            raise ValueError("未输入目标表达强度时，需要填写启动子、RBS 和终止子强度")
        target_expression = promoter * rbs * terminator
    else:
        if not missing_keys:
            target_expression = promoter * rbs * terminator
        else:
            preset_space = {
                "promoter": PROMOTER_STRENGTH_PRESETS,
                "rbs": RBS_STRENGTH_PRESETS,
                "terminator": TERMINATOR_STRENGTH_PRESETS,
            }
            best_solution = None
            best_error = None
            best_distance = None

            for promoter_candidate in ([provided["promoter"]] if provided["promoter"] is not None else preset_space["promoter"]):
                for rbs_candidate in ([provided["rbs"]] if provided["rbs"] is not None else preset_space["rbs"]):
                    for terminator_candidate in ([provided["terminator"]] if provided["terminator"] is not None else preset_space["terminator"]):
                        candidate_expression = promoter_candidate * rbs_candidate * terminator_candidate
                        error = abs(candidate_expression - target_expression)
                        distance = abs(promoter_candidate - (provided["promoter"] or promoter_candidate))
                        distance += abs(rbs_candidate - (provided["rbs"] or rbs_candidate))
                        distance += abs(terminator_candidate - (provided["terminator"] or terminator_candidate))

                        if (
                            best_solution is None
                            or error < best_error
                            or (error == best_error and distance < best_distance)
                        ):
                            best_solution = {
                                "promoter": promoter_candidate,
                                "rbs": rbs_candidate,
                                "terminator": terminator_candidate,
                                "target_expression": candidate_expression,
                            }
                            best_error = error
                            best_distance = distance

            if best_solution is None:
                raise ValueError("离散强度空间中未找到可用解")

            provided["promoter"] = best_solution["promoter"]
            provided["rbs"] = best_solution["rbs"]
            provided["terminator"] = best_solution["terminator"]
            target_expression = best_solution["target_expression"]

    return {
        "promoter": round(provided["promoter"], 4),
        "rbs": round(provided["rbs"], 4),
        "terminator": round(provided["terminator"], 4),
        "target_expression": round(target_expression, 4),
        "reference": REFERENCE_STRENGTH,
    }


def get_design_form_context() -> Dict:
    """Return the preset data required to render the design form."""
    return {
        "chassis_options": CHASSIS_OPTIONS,
        "reference_strength": REFERENCE_STRENGTH,
        "promoter_strength_presets": PROMOTER_STRENGTH_PRESETS,
        "rbs_strength_presets": RBS_STRENGTH_PRESETS,
        "terminator_strength_presets": TERMINATOR_STRENGTH_PRESETS,
    }


def search_gene_candidates(query: str, limit: int = 12) -> List[Dict]:
    """Search CDS parts and return compact gene candidate summaries."""
    queryset = Parttable.objects.filter(type=CDS_TYPE)
    query = (query or "").strip()
    if query:
        keyword_filter = (
            Q(name__icontains=query)
            | Q(alias__icontains=query)
            | Q(reference__icontains=query)
            | Q(sourceorganism__icontains=query)
        )
        queryset = queryset.filter(keyword_filter)

    genes = queryset.order_by("name")[:limit]
    return [
        {
            "id": gene.partid,
            "name": gene.name or f"CDS-{gene.partid}",
            "alias": gene.alias or "",
            "source": gene.sourceorganism or "",
            "length": len((gene.level0sequence or "").strip()),
        }
        for gene in genes
    ]


def recommend_design(payload: Dict) -> Dict:
    """Build a design recommendation from the selected gene and strength inputs."""
    chassis = payload.get("chassis") or "ecoli"
    gene_id = payload.get("gene_id")
    if not gene_id:
        raise ValueError("请选择表达基因")

    gene = Parttable.objects.filter(partid=gene_id, type=CDS_TYPE).first()
    if gene is None:
        raise ValueError("未找到对应的 CDS 基因")

    resolved_strengths = _resolve_strengths(payload)

    promoter = _pick_nearest(_fetch_part_candidates(PROMOTER_TYPE, 1.0, 100.0), resolved_strengths["promoter"])
    rbs = _pick_nearest(_fetch_part_candidates(RBS_TYPE, 1.0, 100.0), resolved_strengths["rbs"])
    terminator = _pick_nearest(_fetch_part_candidates(TERMINATOR_TYPE, 1.0, 100.0), resolved_strengths["terminator"])
    backbone = _pick_nearest(_fetch_backbone_candidates(chassis), resolved_strengths["reference"])

    if not promoter or not rbs or not terminator or not backbone:
        raise ValueError("数据库中的基础元件不足，无法完成自动设计")

    timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
    safe_gene_name = (gene.name or f"gene{gene.partid}").replace(" ", "_")[:24]
    repository_name = f"design_{safe_gene_name}_{timestamp}"

    return {
        "repository_name": repository_name,
        "selected_parts": [
            promoter,
            rbs,
            {"id": gene.partid, "name": gene.name, "alias": gene.alias or "", "strength": None},
            terminator,
        ],
        "selected_backbone": backbone,
        "strengths": resolved_strengths,
        "inputs": payload,
    }


def create_design_repository(request, design_result: Dict) -> Temporaryrepository:
    """Create or replace a temporary repository for the generated design result."""
    user = CustomUser.objects.filter(uid=request.session["info"]["uid"]).first()
    if user is None:
        raise ValueError("用户未登录，无法创建设计仓库")

    repository_name = design_result["repository_name"]
    default_data = {
        "parts": [item["id"] for item in design_result["selected_parts"]],
        "plasmids": [],
        "backbones": [design_result["selected_backbone"]["id"]],
        "total_parts": len(design_result["selected_parts"]),
        "total_plasmids": 0,
        "total_backbones": 1,
        "design_metadata": {
            "design_uuid": uuid.uuid4().hex,
            "inputs": design_result["inputs"],
            "strengths": design_result["strengths"],
            "selected_part_names": [item["name"] for item in design_result["selected_parts"]],
            "selected_backbone_name": design_result["selected_backbone"]["name"],
        },
    }

    expires_at = timezone.now() + timezone.timedelta(days=30)
    Temporaryrepository.objects.filter(userid=user, name=repository_name).delete()
    return Temporaryrepository.objects.create(
        id=uuid.uuid4().hex,
        userid=user,
        repositorycreate_time=timezone.now(),
        repositoryupdate_time=timezone.now(),
        repositoryexpire_time=expires_at,
        data=default_data,
        name=repository_name,
        note="Auto-generated design repository",
    )
