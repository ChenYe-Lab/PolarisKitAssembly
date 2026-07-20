
import io
import time
from django.shortcuts import render,redirect
from django.http import JsonResponse,HttpResponse,FileResponse,Http404
from django.views import View
from django.contrib import messages
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from LabDatabase.excel_processor import ExcelProcessor
from LabDatabase.map_processor import process_map_file
from LabDatabase.genbank_format_checker import process_uploaded_genbank
import requests
from LabDatabase.CaculateModule import GGAssembly
import threading
import openpyxl
import os
import pandas as pd
import json
from Bio.Seq import Seq
import re
from .CaculateModule.FeatureIdentify import featureIdentify
from .CaculateModule.FileGenerator import SequenceAnnotator
from .CaculateModule.ScarIdentify import scarPosition,scarFunction,scarIdentSitePosition
from .CaculateModule.snapgene_reader import snapgene_to_dict
from .ControllerModule import FittingLabels
from .CaculateModule.KmerIndex import KmerIndex
# from GGModule izmport SupportGG
from .GGModule import SupportGG
from Bio.SeqIO import parse
import queue
import shutil
import zipfile
from django.utils import timezone
from urllib.parse import quote
from datetime import datetime, timedelta
from LabDatabaseException import LabDatabaseException,LabDatabasePOSTMethodException,LabDatabaseGETMethodException
from CacheInfo import CacheClass

import uuid
from .design_engine import (
    create_design_repository,
    get_design_form_context,
    recommend_design,
    search_gene_candidates,
)


TEXT_MAP_FILE_TYPES = {"fasta", "gb", "gbk", "ape", "str"}
BINARY_MAP_FILE_TYPES = {"dna"}
TEXT_ENCODINGS = ("utf-8", "utf-8-sig", "gb18030", "gbk", "latin-1")

Base_URL = "http://10.30.76.2:8080/WebDatabase/"
Exp_URL = "http://10.30.76.75:8009/"
# File_Address = r"C:\Users\admin\Desktop\WebDatabase\WebDataWorld\LabDatabase\static\LabDatabase\DownloadFile\GenerateFile\\"
Assembly_File_Address = r"C:\Users\admin\Desktop\WebDatabase\WebDataWorld\output"
TASK_STATUS_PREFIX = 'file_task_'
TASK_STATUS_LOCK = threading.Lock()
CUSTOM_SCAR_LOCK = threading.Lock()
CUSTOM_SCAR_FILE = os.path.join(settings.BASE_DIR, "LabDatabase", "static", "LabDatabase", "CustomScarInfo.txt")
ASSEMBLY_DIR = r"C:\Users\admin\Desktop\WebDatabase\WebDataWorld\LabDatabase\static\LabDatabase\DownloadFile\GenerateFile\AssemblyFile\\"
GENBANK_FIXED_OUTPUT_DIR = r"C:\Users\admin\Desktop\WebDatabase\WebDataWorld\LabDatabase\static\LabDatabase\DownloadFile\GenerateFile"
DOWNLOAD_FILE_ADDRESS = r"C:\Users\admin\Desktop\WebDatabase\WebDataWorld\LabDatabase\static\LabDatabase\DownloadFile\\"

UPLOAD_DATE_TABLE_CONFIG = {
    "parttable": {
        "id_field": "partid",
        "fields": ("partid", "name", "alias", "type", "user", "tag", "uploaddate", "updatedate"),
    },
    "backbonetable": {
        "id_field": "id",
        "fields": ("id", "name", "alias", "species", "copynumber", "user", "tag", "uploaddate", "updatedate"),
    },
    "plasmidneed": {
        "id_field": "plasmidid",
        "fields": ("plasmidid", "name", "alias", "level", "state", "user", "tag", "uploaddate", "updatedate"),
    },
}


def _normalize_text(value):
    if value is None:
        return ""
    return str(value).strip()


def _unique_non_empty(values):
    ordered_values = []
    seen = set()
    for value in values:
        text = _normalize_text(value)
        if not text:
            continue
        lowered = text.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        ordered_values.append(text)
    return ordered_values


def _parse_remote_list(value):
    if isinstance(value, list):
        return _unique_non_empty(value)
    if isinstance(value, str):
        return _unique_non_empty(item.strip() for item in value.split(","))
    return []


def _build_related_parent_map(plasmid_ids, session=None, cookies=None):
    plasmid_ids = [int(item) for item in plasmid_ids if item]
    if not plasmid_ids:
        return {}

    client = session or requests.Session()
    response = client.get(
        f"{Base_URL}GetPlasmidRelations",
        params={"plasmidids": ",".join(map(str, plasmid_ids))},
        cookies=cookies,
        timeout=30,
    )
    if response.status_code != 200:
        raise LabDatabaseException(message="获取 Plasmid 父级关系失败")
    payload = response.json()
    remote_relations = payload.get("data", {})
    related_map = {}
    for plasmid_id in plasmid_ids:
        remote = remote_relations.get(str(plasmid_id), {})
        related_map[plasmid_id] = {
            "related_parts": _unique_non_empty(remote.get("related_parts", [])),
            "related_backbones": _unique_non_empty(remote.get("related_backbones", [])),
            "related_plasmids": _unique_non_empty(remote.get("related_plasmids", [])),
        }

    for related in related_map.values():
        related["related_parts"] = _unique_non_empty(related["related_parts"])
        related["related_backbones"] = _unique_non_empty(related["related_backbones"])
        related["related_plasmids"] = _unique_non_empty(related["related_plasmids"])
        summary = []
        if related["related_parts"]:
            summary.append(f"Part: {', '.join(related['related_parts'])}")
        if related["related_backbones"]:
            summary.append(f"Backbone: {', '.join(related['related_backbones'])}")
        if related["related_plasmids"]:
            summary.append(f"Plasmid: {', '.join(related['related_plasmids'])}")
        related["related_summary"] = " | ".join(summary)

    return related_map


def _attach_related_parent_info(plasmid_records, session=None, cookies=None):
    plasmid_ids = [item.get("plasmidid") for item in plasmid_records if item.get("plasmidid")]
    related_map = _build_related_parent_map(plasmid_ids, session=session, cookies=cookies)
    for item in plasmid_records:
        related = related_map.get(item.get("plasmidid"), {})
        item["related_parts"] = related.get("related_parts", [])
        item["related_backbones"] = related.get("related_backbones", [])
        item["related_plasmids"] = related.get("related_plasmids", [])
        item["related_summary"] = related.get("related_summary", "")
    return plasmid_records


def _plasmid_matches_advanced_filters(record, ori_value="", marker_value="", enzyme_value="", scar_value=""):
    ori_value = _normalize_text(ori_value)
    marker_value = _normalize_text(marker_value)
    enzyme_value = _normalize_text(enzyme_value)
    scar_value = _normalize_text(scar_value)

    ori_info = _parse_remote_list(record.get("ori_info"))
    marker_info = _parse_remote_list(record.get("marker_info"))
    scar_info = _normalize_text(record.get("scar"))

    if ori_value and ori_value not in ori_info:
        return False
    if marker_value and marker_value not in marker_info:
        return False
    if enzyme_value and enzyme_value not in scar_info:
        return False
    if scar_value and scar_value not in scar_info:
        return False
    return True


def _fetch_remote_plasmid_record(session, plasmid_id, cookies):
    plasmid_response = session.get(f"{Base_URL}PlasmidByID?ID={plasmid_id}", cookies=cookies)
    if plasmid_response.status_code != 200:
        return None

    plasmid_payload = plasmid_response.json()
    if not plasmid_payload:
        return None

    plasmid_record = plasmid_payload[0]
    scar_response = session.get(f"{Base_URL}getPlasmidScar?plasmidid={plasmid_id}", cookies=cookies)
    plasmid_record["scar"] = ""
    if scar_response.status_code == 200:
        scar_payload = scar_response.json()
        if scar_payload.get("success") and scar_payload.get("scar_info"):
            scar_info = scar_payload["scar_info"][0]
            plasmid_record["scar"] = " ".join(_unique_non_empty([
                f"BsmBI({scar_info.get('bsmbi', '')})" if scar_info.get("bsmbi") else "",
                f"BsaI({scar_info.get('bsai', '')})" if scar_info.get("bsai") else "",
                f"BbsI({scar_info.get('bbsi', '')})" if scar_info.get("bbsi") else "",
                f"AarI({scar_info.get('aari', '')})" if scar_info.get("aari") else "",
                f"SapI({scar_info.get('sapi', '')})" if scar_info.get("sapi") else "",
            ]))

    plasmid_record["ori_info"] = _parse_remote_list(plasmid_record.get("ori_info"))
    plasmid_record["marker_info"] = _parse_remote_list(plasmid_record.get("marker_info"))
    return plasmid_record


def _search_related_plasmid_ids(keyword, session=None, cookies=None):
    keyword = _normalize_text(keyword)
    if not keyword:
        return []

    client = session or requests.Session()
    response = client.get(
        f"{Base_URL}GetPlasmidRelations",
        params={"keyword": keyword},
        cookies=cookies,
        timeout=30,
    )
    if response.status_code != 200:
        raise LabDatabaseException(message="关联 Plasmid 查询失败")
    return [item for item in response.json().get("plasmid_ids", []) if item]


def _paginate_local_records(records, page, page_size):
    total_count = len(records)
    total_pages = max((total_count + page_size - 1) // page_size, 1)
    safe_page = min(max(int(page), 1), total_pages)
    start = (safe_page - 1) * page_size
    end = start + page_size
    return {
        "data": records[start:end],
        "pagination": {
            "total_count": total_count,
            "total_pages": total_pages,
            "current_page": safe_page,
            "offset": start + 1 if total_count else 0,
        },
    }



def _sanitize_assembly_name(name):
    text = str(name or "").strip()
    if not text:
        return "unnamed"
    invalid_chars = '\\/:*?"<>|'
    sanitized = "".join("_" if char in invalid_chars else char for char in text)
    sanitized = sanitized.rstrip(". ")
    return sanitized or "unnamed"


def _assembly_file_basename(name):
    return _sanitize_assembly_name(name)


def _assembly_file_path(name):
    return os.path.join(ASSEMBLY_DIR, f"{_assembly_file_basename(name)}.gbk")


def _get_task_output_dir(task_id):
    return os.path.join(Assembly_File_Address, str(task_id))


def _ensure_task_output_dir(task_id):
    task_output_dir = _get_task_output_dir(task_id)
    os.makedirs(task_output_dir, exist_ok=True)
    return task_output_dir


def _ensure_task_assembly_output_dir(task_id, assembly_name):
    task_output_dir = _ensure_task_output_dir(task_id)
    assembly_output_dir = os.path.join(task_output_dir, _sanitize_assembly_name(assembly_name))
    os.makedirs(assembly_output_dir, exist_ok=True)
    return assembly_output_dir


def _get_task_assembly_file(task_id, file_name):
    return os.path.join(_get_task_output_dir(task_id), f"{file_name}.gb")


def _resolve_task_assembly_file(task_id, file_name):
    default_file = _get_task_assembly_file(task_id, file_name)
    if os.path.exists(default_file):
        return default_file
    assembly_subdir_file = os.path.join(
        _get_task_output_dir(task_id),
        _sanitize_assembly_name(file_name),
        f"{file_name}.gb"
    )
    if os.path.exists(assembly_subdir_file):
        return assembly_subdir_file
    return default_file


def _list_task_generated_gb_files(task_id):
    task_output_dir = _get_task_output_dir(task_id)
    generated_files = []
    if not os.path.exists(task_output_dir):
        return generated_files

    for root, _, files in os.walk(task_output_dir):
        for file_name in files:
            if not file_name.lower().endswith(".gb"):
                continue
            file_stem = os.path.splitext(file_name)[0]
            generated_files.append({
                "file_name": file_name,
                "file_path": f"/LabDatabase/getAssembly/{quote(file_stem)}?task_id={task_id}",
            })

    generated_files.sort(key=lambda item: item["file_name"])
    return generated_files


def _list_task_repository_result_gb_paths(task_id):
    task_output_dir = _get_task_output_dir(task_id)
    result_files = []
    if not os.path.exists(task_output_dir):
        return result_files

    for root, _, files in os.walk(task_output_dir):
        for file_name in files:
            if not file_name.lower().endswith(".gb"):
                continue
            file_path = os.path.join(root, file_name)
            file_stem = os.path.splitext(file_name)[0]
            parent_name = os.path.basename(root)
            if root == task_output_dir or parent_name == _sanitize_assembly_name(file_stem):
                result_files.append(file_path)

    result_files.sort()
    return result_files


def _get_task_archive_file(task_id):
    return os.path.join(_get_task_output_dir(task_id), f"{task_id}_assembly_results.zip")


def _build_task_archive_download_url(task_id):
    return f"/LabDatabase/getAssemblyArchive/{quote(str(task_id))}"


def _create_task_result_archive(task_id):
    gb_files = _list_task_repository_result_gb_paths(task_id)
    if not gb_files:
        return None

    archive_path = _get_task_archive_file(task_id)
    os.makedirs(os.path.dirname(archive_path), exist_ok=True)

    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file_path in gb_files:
            zip_file.write(file_path, arcname=os.path.basename(file_path))

    return archive_path


def _build_task_result_payload(task_id, final_name=None):
    payload = {
        "success": True,
        "generated_gb_files": _list_task_generated_gb_files(task_id),
    }

    archive_path = _create_task_result_archive(task_id)
    if archive_path and os.path.exists(archive_path):
        payload["archive_download_url"] = _build_task_archive_download_url(task_id)
        payload["archive_file_name"] = os.path.basename(archive_path)

    if final_name:
        payload["file_name"] = f"{final_name}.gb"
        payload["download_url"] = f"/LabDatabase/getAssembly/{quote(final_name)}?task_id={task_id}"

    return payload


def _looks_like_binary(content: bytes) -> bool:
    if not content:
        return False
    if b"\x00" in content:
        return True

    sample = content[:1024]
    text_bytes = set(range(32, 127)) | {9, 10, 13}
    non_text_count = sum(1 for byte in sample if byte not in text_bytes)
    return non_text_count / max(len(sample), 1) > 0.30


def _decode_uploaded_text(content: bytes) -> str:
    last_error = None
    for encoding in TEXT_ENCODINGS:
        try:
            return content.decode(encoding)
        except UnicodeDecodeError as exc:
            last_error = exc

    if last_error is not None:
        raise ValueError(
            "Unable to detect uploaded file encoding. Please save the file as UTF-8, GBK, or GB18030 and try again."
        ) from last_error
    raise ValueError("Uploaded file is empty or cannot be decoded.")


def _build_map_file_object(file_content: bytes, file_type: str):
    try:
        file_type = (file_type or "").lower()
    
        if file_type in BINARY_MAP_FILE_TYPES:
            return io.BytesIO(file_content)

        if file_type in TEXT_MAP_FILE_TYPES:
            if _looks_like_binary(file_content):
                raise LabDatabaseException(message=f".{file_type} 不是文本类文件")
                # raise ValueError(f".{file_type} file looks like binary content and cannot be parsed as text.")
            return io.StringIO(_decode_uploaded_text(file_content))

        if _looks_like_binary(file_content):
            return io.BytesIO(file_content)
        return io.StringIO(_decode_uploaded_text(file_content))
    except Exception as exc:
        raise exc
# class User_auth(MiddlewareMixin):

#     def process_request(self,request):
#         #閹烘帡娅庢稉宥夋付鐟曚胶娅ヨぐ鏇炴皑閼冲€燁問闂傤喚娈戞い鐢告桨
#         if request.path_info == "/WebDatabase/login" or request.path_info == "":
#             return
#         info = request.session.get('info')
#         print(info)
#         if not info:
#             return redirect('/WebDatabase/login')
#         else:
#             return

#     def process_response(self,request,response):
#         return response



def index(request):
    if(request.method == "GET"):
        session = requests.Session()
        session.headers.update({
            'User-Agent':'Django-App/1.0',
            'Content-Type':'application/json',
        })
        print(request.session.get('info'))
        print(request.user)
        try:
            username = request.user.uname
            userid = request.user.uid
            user_repository_count = session.get(f"{Base_URL}getrepocountbyuser/{userid}",cookies=request.COOKIES).json()['count']
            user_part_count = session.get(f"{Base_URL}getuserpartcount/{username}",cookies=request.COOKIES).json()['count']
            user_backbone_count = session.get(f"{Base_URL}getuserbackbonecount/{username}",cookies=request.COOKIES).json()['count']
            user_plasmid_count = session.get(f"{Base_URL}getuserplasmidcount/{username}",cookies=request.COOKIES).json()['count']
            user_info = {}
            user_info['repoCount'] = user_repository_count
            user_info['partCount'] = user_part_count
            user_info['backboneCount'] = user_backbone_count
            user_info['plasmidCount'] = user_plasmid_count
            return render(request,'index.html',{"user":request.user,"user_info":user_info})
        except AttributeError as e:
            return redirect("/WebDatabase/login")
    else:
        return LabDatabaseGETMethodException().to_response()


def _load_custom_scar_records():
    if not os.path.exists(CUSTOM_SCAR_FILE):
        return []

    records = []
    with open(CUSTOM_SCAR_FILE, "r", encoding="utf-8") as file_obj:
        for line in file_obj:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def CustomScar(request):
    try:
        if request.method == "GET":
            try:
                with CUSTOM_SCAR_LOCK:
                    records = _load_custom_scar_records()
                return JsonResponse({"success": True, "data": records}, status=200, safe=False)
            except Exception as exc:
                return JsonResponse({"success": False, "message": str(exc)}, status=400, safe=False)

        if request.method != "POST":
            return LabDatabasePOSTMethodException().to_response()

        try:
            if request.content_type and "application/json" in request.content_type:
                request_data = json.loads(request.body.decode("utf-8") or "{}")
            else:
                request_data = request.POST

            scar_name = str(request_data.get("scar_name") or request_data.get("name") or "").strip()
            scar_sequence = str(request_data.get("scar_sequence") or request_data.get("sequence") or "").strip().upper()
            scar_description = str(request_data.get("scar_description") or request_data.get("description") or "").strip()
            scar_sequence = re.sub(r"\s+", "", scar_sequence)
    
            if not scar_name:
                return LabDatabaseException(message="scar_name cannot be empty",status_code=400).to_response()
                # return JsonResponse({"success": False, "message": "scar_name cannot be empty"}, status=400, safe=False)
            if not scar_sequence:
                return LabDatabaseException(message="scar_sequence cannot be empty",status_code=400).to_response()
                # return JsonResponse({"success": False, "message": "scar_sequence cannot be empty"}, status=400, safe=False)
            if not re.fullmatch(r"[ACGTRYSWKMBDHVN]+", scar_sequence):
                return LabDatabaseException(message="scar_sequence contains invalid base characters", status_code=400).to_response()
            # return JsonResponse({"success": False, "message": "scar_sequence contains invalid base characters"}, status=400, safe=False)
    
            username = getattr(request.user, "username", "") or getattr(request.user, "uname", "")
            record = {
                "scar_name": scar_name,
                "scar_sequence": scar_sequence,
                "scar_description": scar_description,
                "created_by": username,
                "created_at": timezone.now().isoformat(),
            }

            os.makedirs(os.path.dirname(CUSTOM_SCAR_FILE), exist_ok=True)
            with CUSTOM_SCAR_LOCK:
                records = _load_custom_scar_records()
                if any(item.get("scar_name", "").lower() == scar_name.lower() for item in records):
                    return JsonResponse({"success": False, "message": "scar_name already exists"}, status=409, safe=False)
                with open(CUSTOM_SCAR_FILE, "a", encoding="utf-8") as file_obj:
                    file_obj.write(json.dumps(record, ensure_ascii=False) + "\n")

            return JsonResponse({"success": True, "data": record}, status=200, safe=False)
        except json.JSONDecodeError:
            return LabDatabaseException(message="Invalid JSON format").to_response()
            # return JsonResponse({"success": False, "message": "Invalid JSON format"}, status=400, safe=False)
        except Exception as exc:
            return LabDatabaseException(message=str(exc)).to_response()
        # return JsonResponse({"success": False, "message": str(exc)}, status=400, safe=False)
    except Exception as exc:
        return LabDatabaseException(message=str(exc)).to_response()

def design_builder(request):
    if request.method != "GET":
        return LabDatabaseGETMethodException().to_response()
        # return JsonResponse({"success": False, "message": "Just GET method"}, status=405)
    context = get_design_form_context()
    context["user"] = request.user
    return render(request, "design_builder.html", context)


def design_gene_search(request):
    if request.method != "GET":
        return LabDatabaseGETMethodException().to_response()
        # return JsonResponse({"success": False, "message": "Just GET method"}, status=405)

    query = request.GET.get("q", "")
    genes = search_gene_candidates(query)
    return JsonResponse({"success": True, "data": genes}, status=200)


def submit_design_assembly(request):
    try:
        if request.method != "POST":
            raise LabDatabasePOSTMethodException()
            # return JsonResponse({"success": False, "message": "Just POST method"}, status=405)
        payload = json.loads(request.body)
        design_result = recommend_design(payload)
        repository = create_design_repository(request, design_result)

        task_id = str(uuid.uuid4())
        
        cache_obj = CacheClass("processing",0)
        
        cache.set(f"{TASK_STATUS_PREFIX}{task_id}",cache_obj,timeout=100000)
        # cache.set(
        #     f"{TASK_STATUS_PREFIX}{task_id}",
        #     {"status": "processing", "progress": 0, "result": None, "error": None},
        #     timeout=100000,
        # )

        thread = threading.Thread(
            target=process_assembly_repo,
            args=(repository.name, request, task_id),
        )
        thread.daemon = False
        thread.start()

        return JsonResponse(
            {
                "success": True,
                "task_id": task_id,
                "repository_name": repository.name,
                "selected_parts": design_result["selected_parts"],
                "selected_backbone": design_result["selected_backbone"],
                "strengths": design_result["strengths"],
                "message": "仓库创建成功",
            },
            status=200,
        )
    except LabDatabaseException as exc:
        return exc.to_response()
    except ValueError as exc:
        return JsonResponse({"success": False, "message": str(exc)}, status=400)
    except Exception as exc:
        return JsonResponse({"success": False, "message": str(exc)}, status=500)
    
    
    
def getData(request):
    # print(request.session['info']['uname'])
    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent':'Django-App/1.0',
            'Content-Type':'application/json',
        })
        if(request.method == "GET"):
            type = request.GET.get("type")
            page = request.GET.get("page",1)
            if(type == "part"):
                # try:
                    # sessionid = request.COOKIES.get(settings.SESSION_COOKIE_NAME)
                    # print(sessionid)
                    # cookies = {}
                    # if(sessionid):
                    #     cookies[settings.SESSION_COOKIE_NAME] = sessionid
                promoterResponse = requests.get(f'{Base_URL}Part?page={page}',cookies=request.COOKIES)
                # print(promoterResponse.url)
                if(promoterResponse.status_code == 200):
                    promoter = promoterResponse.json()
                    return JsonResponse(promoter,status=200,safe=False)
                else:
                    raise LabDatabaseException(message="Part 请求失败")
                # except requests.exceptions.RequestException as e:
                #     return JsonResponse(str(e),status = 400, safe=False)
            elif(type == "backbone"):
                # try:
                backboneResponse = requests.get(f'{Base_URL}Backbone?page={page}',cookies=request.COOKIES)
                if(backboneResponse.status_code == 200):
                    backbone = backboneResponse.json()
                    return JsonResponse(backbone,status=200,safe=False)
                else:
                    raise LabDatabaseException(message="Backbone 请求失败")
                    # raise requests.exceptions.RequestException
                # except requests.exceptions.RequestException as e:
                #     return JsonResponse(str(e),status = 400, safe=False)
            elif(type == "plasmid"):
                # try:
                plasmidResponse = session.get(f'{Base_URL}Plasmid?page={page}',cookies=request.COOKIES)
                if(plasmidResponse.status_code == 200):
                    plasmid = plasmidResponse.json()
                    if isinstance(plasmid, dict) and isinstance(plasmid.get("data"), list):
                        for item in plasmid["data"]:
                            item["ori_info"] = _parse_remote_list(item.get("ori_info"))
                            item["marker_info"] = _parse_remote_list(item.get("marker_info"))
                            item["scar"] = _normalize_text(item.get("scar"))
                        plasmid["data"] = _attach_related_parent_info(
                            plasmid["data"], session=session, cookies=request.COOKIES
                        )
                    return JsonResponse(plasmid,status=200,safe=False)
                else:
                    raise LabDatabaseException(message="Plasmid 请求失败")
                # except requests.exceptions.RequestException as e:
                #     return JsonResponse(str(e),status = 400, safe=False)
        else:
            raise LabDatabaseGETMethodException()
    except LabDatabaseException as exc:
        return exc.to_response()
    except Exception as exc:
        return JsonResponse({"success":False,"message":str(exc)},status = 400)
            

def DataFilter(request):
    # print(request.session['info']['uname'])
    try:
        session = requests.Session()
        token = request.COOKIES.get('csrftoken')
        session.headers.update({
            'User-Agent':'Django-App/1.0',
            'Content-Type':'application/json',
            'X-CSRFToken':token,
        })
        if(request.method == "POST"):
            data = json.loads(request.body)
            type = data.get("SearchType")
            page = data.get("page",1)
            if(type == "part"):
                # try:
                request_body = {'type':data.get('Type',""),"Enzyme":data.get('Enzyme',""),"Scar":data.get('Scar',""),"name":data.get('name',""),"page":page,"page_size":10}
                promoterResponse = session.post(f'{Base_URL}PartFilter',json=request_body,cookies=request.COOKIES)
                if(promoterResponse.status_code == 200):
                    promoter = promoterResponse.json()
                    return JsonResponse(promoter,status=200,safe=False)
                else:
                    raise LabDatabaseException(message="没有匹配的搜索结果")
            # except requests.exceptions.RequestException as e:
            #     return JsonResponse({'success':False,'error':str(e)},status = 400, safe=False)
            elif(type == "backbone"):
            # try:
                request_body = {'ori':data.get('Ori',""),'marker':data.get('Marker',""),'Enzyme':data.get('Enzyme',""),'Scar':data.get('Scar',""),'name':data.get("name",""),"page":page,"page_size":10}
                backboneResponse = session.post(f'{Base_URL}BackboneFilter',json=request_body,cookies=request.COOKIES)
                if(backboneResponse.status_code == 200):
                    backbone = backboneResponse.json()
                    # print(backbone)
                    return JsonResponse(backbone,status=200,safe=False)
                else:
                    raise LabDatabaseException(message="没有匹配的搜索结果")
            # except requests.exceptions.RequestException as e:
            #     return JsonResponse(str(e),status = 400, safe=False)
            elif(type == "plasmid"):
                page_size = int(data.get("page_size", 10) or 10)
                keyword = _normalize_text(data.get("name", ""))
                ori_value = data.get("Ori", "")
                marker_value = data.get("Marker", "")
                enzyme_value = data.get("Enzyme", "")
                scar_value = data.get("Scar", "")
                request_body = {
                    'ori': ori_value,
                    'marker': marker_value,
                    'Enzyme': enzyme_value,
                    'Scar': scar_value,
                    'name': keyword,
                    'page': page,
                    "page_size": page_size,
                }
                plasmidResponse = session.post(f'{Base_URL}PlasmidFilter',json=request_body,cookies=request.COOKIES)
                if(plasmidResponse.status_code != 200):
                    raise LabDatabaseException(message="没有匹配的搜索结果")

                plasmid = plasmidResponse.json()
                base_records = plasmid.get("data", []) if isinstance(plasmid, dict) else []
                for item in base_records:
                    item["ori_info"] = _parse_remote_list(item.get("ori_info"))
                    item["marker_info"] = _parse_remote_list(item.get("marker_info"))

                if keyword:
                    seen_ids = set()
                    combined_records = []
                    for item in base_records:
                        plasmid_id = item.get("plasmidid")
                        if not plasmid_id or plasmid_id in seen_ids:
                            continue
                        seen_ids.add(plasmid_id)
                        combined_records.append(item)

                    for plasmid_id in _search_related_plasmid_ids(
                        keyword, session=session, cookies=request.COOKIES
                    ):
                        if plasmid_id in seen_ids:
                            continue
                        extra_record = _fetch_remote_plasmid_record(session, plasmid_id, request.COOKIES)
                        if extra_record is None:
                            continue
                        if not _plasmid_matches_advanced_filters(
                            extra_record,
                            ori_value=ori_value,
                            marker_value=marker_value,
                            enzyme_value=enzyme_value,
                            scar_value=scar_value,
                        ):
                            continue
                        seen_ids.add(plasmid_id)
                        combined_records.append(extra_record)

                    combined_records = _attach_related_parent_info(
                        combined_records, session=session, cookies=request.COOKIES
                    )
                    paginated_payload = _paginate_local_records(combined_records, page, page_size)
                    return JsonResponse(
                        {
                            "success": True,
                            "data": paginated_payload["data"],
                            "pagination": paginated_payload["pagination"],
                        },
                        status=200,
                        safe=False,
                    )

                plasmid["data"] = _attach_related_parent_info(
                    base_records, session=session, cookies=request.COOKIES
                )
                return JsonResponse(plasmid,status=200,safe=False)
                    # raise requests.exceptions.RequestException
            # except requests.exceptions.RequestException as e:
            #     return JsonResponse(str(e),status = 400, safe=False)
        else:
            raise LabDatabasePOSTMethodException()
    except LabDatabaseException as exc:
        return exc.to_response()
    except Exception as exc:
        return JsonResponse({"success":False, "message":str(exc)}, status=400)

def UploadPartMap(request):
    try:
        if(request.method == 'POST' and request.FILES):
            return JsonResponse(data={'success':True},status = 200, safe=False)
        else:
            return JsonResponse({'success':False,'message':'上传内容不存在'},status = 400, safe = False)
    except LabDatabaseException as exc:
        return exc.to_response()
    except Exception as exc:
        return JsonResponse({"success":False,"message":str(exc)},status = 400)

def UploadBackboneMap(request):
    pass

def UploadPlasmidMap(request):
    pass

def download_template(request,type):
    print(type)
    try:
        if(type == 'part'):
            template_path = f'{DOWNLOAD_FILE_ADDRESS}PartColumn.xlsx'
            if(os.path.exists(template_path)):
                response = FileResponse(open(template_path,'rb'),as_attachment=True,filename='part_template.xlsx')
                return response
        elif(type == 'backbone'):
            template_path = f'{DOWNLOAD_FILE_ADDRESS}BackboneColumn.xlsx'
            if(os.path.exists(template_path)):
                response = FileResponse(open(template_path,'rb'),as_attachment=True,filename='Backbone_template.xlsx')
                return response
        elif(type == 'plasmid'):
            template_path = f'{DOWNLOAD_FILE_ADDRESS}\PlasmidColumn.xlsx'
            if(os.path.exists(template_path)):
                response = FileResponse(open(template_path,'rb'),as_attachment=True,filename='plasmid_template.xlsx')
                return response
        elif(type == "assembly"):
            template_path = f'{DOWNLOAD_FILE_ADDRESS}\AssemblyPlan.xlsx'
            print(template_path)
            if(os.path.exists(template_path)):
                print("aaaaaaaa")
                response = FileResponse(open(template_path,'rb'),as_attachment=True,filename='AssemblyPlan_template.xlsx')
                return response
        else:
            raise LabDatabaseException(message="模板文件不存在")
            # raise Http404('Template file not found.')
    except LabDatabaseException as exc:
        return exc.to_response()
    except Exception as exc:
        print(str(exc))
        return JsonResponse({"success":False,"message":str(exc)}, status = 400)


"""
file_name: [filename, file_type]
"""
def process_map_async(upload_map, file_name, upload_type, django_request, task_id, index, number_of_task, save_feature=False):
    try:
        result = False
        task_error = None
        upload_map_temp = upload_map.read()
        upload_map.seek(0)
        file_obj = _build_map_file_object(upload_map_temp, file_name[1])
        result = process_map_file(file_obj, file_name, upload_type, django_request, Base_URL, save_feature=save_feature)
        # except ValueError as e:
        #     task_error = f"{file_name[0]} upload failed: {str(e)}"
        # except Exception as e:
        #     task_error = f"{file_name[0]} upload failed"
        print(result)
        if(not result and task_error is None):
            raise LabDatabaseException(message=f"文件 {file_name[0]} 上传失败")
            # task_error = f"{file_name[0]} upload failed"
        # task_error = f"{file_name[0]} upload failed"
        with TASK_STATUS_LOCK:
            cache_obj = cache.get(f'{TASK_STATUS_PREFIX}{task_id}') or CacheClass('processing',0,total_count=number_of_task)
        # task_status = cache.get(f'{TASK_STATUS_PREFIX}{task_id}') or {
        #     'status':'processing',
        #     'progress':0,
        #     'result':None,
        #     'error':[],
        #     'processed_count':0,
        #     'total_count':number_of_task,
        # }
        # if(task_status.get('error') is None):
        #     task_status['error'] = []
        # if(task_error is not None):
        #     task_status['error'].append(task_error)
            cache_obj.setProcessedCount(cache_obj.getProcessedCount() + 1)
            # processed_count = task_status.get('processed_count', 0) + 1
            cache_obj.setTotalCount(cache_obj.getTotalCount())
            # total_count = task_status.get('total_count', number_of_task)
            cache_obj.setProgress(int(cache_obj.getProcessedCount() * 100 / max(cache_obj.getTotalCount(),1)))
            # progress = int(processed_count * 100 / max(total_count, 1))
            cache_obj.setStatus("completed" if cache_obj.getProcessedCount() >= cache_obj.getTotalCount() else "processing")
        cache.set(f'{TASK_STATUS_PREFIX}{task_id}',cache_obj,timeout=3600)
    except LabDatabaseException as exc:
        print(exc.message)
        with TASK_STATUS_LOCK:
            cache_obj = cache.get(f'{TASK_STATUS_PREFIX}{task_id}') or CacheClass('processing',0,total_count=number_of_task)
            cache_obj.setProcessedCount(cache_obj.getProcessedCount() + 1)
            cache_obj.setTotalCount(cache_obj.getTotalCount())
            cache_obj.setProgress(int(cache_obj.getProcessedCount() * 100 / max(cache_obj.getTotalCount(),1)))
            cache_obj.setStatus("completed" if cache_obj.getProcessedCount() >= cache_obj.getTotalCount() else "processing")
            cache_obj.setMessage(cache_obj.getMessage() + ", " + exc.message)
        cache.set(f'{TASK_STATUS_PREFIX}{task_id}',cache_obj,timeout=3600)
    except Exception as exc:
        print(str(exc))
        with TASK_STATUS_LOCK:
            cache_obj = cache.get(f'{TASK_STATUS_PREFIX}{task_id}') or CacheClass('processing',0,total_count=number_of_task)
            cache_obj.setProcessedCount(cache_obj.getProcessedCount() + 1)
            cache_obj.setTotalCount(cache_obj.getTotalCount())
            cache_obj.setProgress(int(cache_obj.getProcessedCount() * 100 / max(cache_obj.getTotalCount(),1)))
            cache_obj.setStatus("completed" if cache_obj.getProcessedCount() >= cache_obj.getTotalCount() else "processing")
            cache_obj.setMessage(cache_obj.getMessage() + f", {file_name[0]} " + str(exc))
        cache.set(f'{TASK_STATUS_PREFIX}{task_id}',cache_obj,timeout=3600)

def process_excel_async(upload_record,django_request,task_id):
    try:
        Error_rows = []
        Empty_sequence_rows = []
        # task_status = {
        #     'status':'processing',
        #     'progress':10,
        #     'result':None,
        #     'error':[]
        # }
        cache_obj = CacheClass("processing",10)
        cache.set(f"{TASK_STATUS_PREFIX}{task_id}",cache_obj,timeout=3600)
            # cache.set(f'{TASK_STATUS_PREFIX}{task_id}',task_status,timeout=3600)
        file_content = upload_record.read()
        excel_data = pd.read_excel(io.BytesIO(file_content))
        # print(excel_data.columns)
        if(excel_data.columns.tolist()[0] == "PartName"):
            type = "part"
        elif(excel_data.columns.tolist()[0] == "BackboneName"):
            type = "backbone"
        elif(excel_data.columns.tolist()[0] == "PlasmidName"):
            type = "plasmid"
        if(type == None):
            raise LabDatabaseException(message="无法识别上传文件的数据类型,请检查上传文件的列名")
        print(type)
        result = ExcelProcessor.process_excel_file(django_request,excel_data,type,Base_URL)
            # print(result)
        if(result["success"]):
            print("success")
            # task_status['progress'] = 100
            # task_status['status'] = 'completed'
            with TASK_STATUS_LOCK:
                cache_obj.setProgress(100)
                cache_obj.setStatus("completed")
                if(len(result["error_row"]) != 0 or len(result["empty_Seq_rows"])):
                    cache_obj.setMessage(f"上传出错的数据行有: {', '.join(result['error_row'])}, 需要补充序列的数据行有: {', '.join(result['empty_Seq_rows'])}")
                else:
                    cache_obj.setMessage(f"上传成功")
            cache.set(f"{TASK_STATUS_PREFIX}{task_id}",cache_obj)
                # Empty_sequence_rows = result['empty_Seq_rows']
                # if len(Error_rows) == 0 and len(Empty_sequence_rows) == 0:
                #     task_status['result'] = {
                #         'success':True,
                #         'message':"上传成功"
                #     }
                # else:
                #     message = ""
                #     if(len(Error_rows) != 0):
                #         message += "有上传错误行，如下" + str(Error_rows) + "\n"
                #     if(len(Empty_sequence_rows) != 0):
                #         message += "后续需要补充序列信息，如下" + str(Empty_sequence_rows)
                #     task_status['result'] = {
                #         'success':True,
                #         'message':message,
                #     }
        else:
            with TASK_STATUS_LOCK:
                cache_obj.setProgress(0)
                cache_obj.setStatus("failed")
                cache_obj.setMessage(result['error'])
            cache.set(f"{TASK_STATUS_PREFIX}{task_id}",cache_obj)
        # print(Empty_sequence_rows)
    except Exception as e:
        with TASK_STATUS_LOCK:
            cache_obj.setProgress(0)
            cache_obj.setStatus("failed")
            cache_obj.setMessage(str(e))
        cache.set(f"{TASK_STATUS_PREFIX}{task_id}",cache_obj)
        # task_status = {
        #     'status':'failed',
        #     'progress':100,
        #     'result':None,
        #     'error':str(e.args),
        # }
    # ExcelProcessor.process_excel_file(upload_record)

def process_gg_assembly_async(upload_file, django_request, task_id):
    try:
        # task_status = {
        #     'status':'processing',
        #     'progress':10,
        #     'result':None,
        #     'error':[]
        # }
        cache_obj = CacheClass("processing",0)
        cache.set(f'{TASK_STATUS_PREFIX}{task_id}',cache_obj,timeout=3600)
        file_content = upload_file.read()
        excel_data = pd.read_excel(io.BytesIO(file_content),engine='openpyxl')
        if 'Assembly' in excel_data.columns and 'AssemblyName' not in excel_data.columns:
            excel_data = excel_data.rename(columns={'Assembly':'AssemblyName'})
        if 'Level' not in excel_data.columns:
            with TASK_STATUS_LOCK:
                cache_obj.setStatus("failed")
                cache_obj.setProgress(100)
                cache_obj.setMessage("上传表格中没有Level信息列,请更新组装表格模板")
            cache.set(f"{TASK_STATUS_PREFIX}{task_id}",cache_obj)
            return
            # task_status['status'] = 'failed'
            # task_status['progress'] = 100
            # task_status['error'] = 'Excel is missing the Level column.'
            # task_status['result'] = {
            #     'success':False,
            #     'message':'Excel is missing the Level column.'
            # }
            # cache.set(f'{TASK_STATUS_PREFIX}{task_id}',task_status,timeout=3600)
            # return
        excel_data = excel_data.copy()
        fill_column = ['AssemblyName','Alias','Level','Backbone','Plasmid','Note']
        for col in excel_data.columns:
            if col in fill_column:
                excel_data[col] = excel_data[col].ffill()
        excel_data['Level'] = excel_data['Level'].apply(
            lambda value: str(value).strip().replace('.0', '') if pd.notna(value) else ''
        )
        assembly_groups = {}
        for name, group in excel_data.groupby('AssemblyName'):
            assembly_name = str(name).strip()
            if not assembly_name:
                continue
            assembly_groups[assembly_name] = group.drop(columns='AssemblyName').copy()
        
        completed_assemblies = []
        failed_assemblies = {}
        # total_assemblies = sum(
        #     1 for name in excel_data.get('AssemblyName', pd.Series(dtype=object)).tolist()
        #     if str(name).strip()
        # )
        total_assemblies = len(assembly_groups)
        if total_assemblies == 0:
            with TASK_STATUS_LOCK:
                cache_obj.setStatus('failed')
                cache_obj.setProgress(100)
                cache_obj.setMessage("组装文件为空")
            cache.set(f"{TASK_STATUS_PREFIX}{task_id}",cache_obj)
            # task_status['status'] = 'failed'
            # task_status['progress'] = 100
            # task_status['error'] = '组装文件为空'
            # task_status['result'] = {
            #     'success':False,
            #     'message':'组装文件为空'
            # }
            # cache.set(f'{TASK_STATUS_PREFIX}{task_id}',task_status,timeout=3600)
            return

        session = requests.Session()
        session.headers.update({
            'User-Agent':'Django-App/1.0',
            'Content-Type':'application/json',
        })

        for level_index, level_value in enumerate(['1', '2', '3'], start=1):
            level_frames = []
            assembly_names = []
            level_data = []
            for assembly_name, assembly_df in assembly_groups.items():
                if assembly_df.empty:
                    continue
                assembly_level = str(assembly_df['Level'].iloc[0]).strip().replace('.0','')
                if assembly_level != level_value:
                    continue
                level_frame = assembly_df.copy()
                level_frame.insert(0,'AssemblyName',assembly_name)
                level_frames.append(level_frame)
                level_data.append({"name":assembly_name,"data":level_frame})
                assembly_names.append(assembly_name)
            # level_data = excel_data[excel_data['Level'] == level_value].copy()
            if not level_frames:
                continue
            # level_data = pd.concat(level_frames,ignore_index = True)
            
            result = GGAssembly.GGFileProcessor.createTemporaryRepo(
                django_request,
                level_data,
                Base_URL,
            )
            if not result['success']:
                with TASK_STATUS_LOCK:
                    cache_obj.setStatus("processing")
                    if(level_index == 1):
                        cache_obj.setProgress(10)
                    elif(level_index == 2):
                        cache_obj.setProgress(20)
                    elif(level_index == 3):
                        cache_obj.setProgress(30)
                    cache_obj.setMessage(cache_obj.getMessage() + "\n" + f"Level {level_index} 上传仓库失败: {result['error_row'] if 'error_row' in result else result['error']}")
                cache.set(f"{TASK_STATUS_PREFIX}{task_id}",cache_obj)
                # task_status['status'] = 'failed'
                # task_status['progress'] = 100
                # task_status['error'] = result['error']
                # task_status['result'] = {
                #     'success':False,
                #     'message':'仓库创建失败'
                # }
                # cache.set(f'{TASK_STATUS_PREFIX}{task_id}',task_status,timeout=3600)
                continue
            if 'error_row' in result:
                with TASK_STATUS_LOCK:
                    cache_obj.setStatus("processing")
                    if(level_index == 1):
                        cache_obj.setProgress(10)
                    elif(level_index == 2):
                        cache_obj.setProgress(20)
                    elif(level_index == 3):
                        cache_obj.setProgress(30)
                    cache_obj.setMessage(cache_obj.getMessage() + "\n" + f"Level {level_index} 上传中出现如下错误 {result['error_row']}")
                cache.set(f"{TASK_STATUS_PREFIX}{task_id}",cache_obj)
                    # task_status['progress'] = 100
                # task_status['status'] = 'completed'
                # task_status['result'] = {
                #     'success':True,
                #     'message':result['error_row']
                # }
                # cache.set(f'{TASK_STATUS_PREFIX}{task_id}',task_status,timeout=3600)
                continue
            print("上传完成")
            empty_repositories = []
            assembly_queue = queue.Queue()
            for assembly_name in assembly_names:
                repository_response = session.post(
                    f"{Base_URL}getrepo",
                    json={'Name':assembly_name},
                    cookies=django_request.COOKIES
                )
                if repository_response.status_code != 200:
                    if(repository_response.status_code == 404):
                        failed_assemblies[assembly_name] = f'获取仓库 {assembly_name} 失败'
                        continue
                    else:
                        failed_assemblies[assembly_name] = f'{assembly_name} {repository_response.json()["message"]}'
                        continue
                repository_data = repository_response.json().get('data', {})
                if (
                    repository_data.get('total_parts', 0) == 0 and
                    repository_data.get('total_plasmids', 0) == 0 and
                    repository_data.get('total_backbones', 0) == 0
                ):
                    empty_repositories.append(assembly_name)
                    continue
                assembly_queue.put(assembly_name)

            if empty_repositories:
                with TASK_STATUS_LOCK:
                    cache_obj.setStatus('processing')
                    cache_obj.setProgress(40)
                    cache_obj.setMessage(cache_obj.getMessage() + "\n" + f"本批上传的仓库中空仓库有: {','.join(empty_repositories)}")
                    cache.set(f"{TASK_STATUS_PREFIX}{task_id}",cache_obj)
                # task_status['status'] = 'failed'
                # task_status['progress'] = 100
                # task_status['error'] = f"空仓库: {', '.join(empty_repositories)}"
                # task_status['result'] = {
                #     'success':False,
                #     'message':f"空仓库: {', '.join(empty_repositories)}"
                # }
                # cache.set(f'{TASK_STATUS_PREFIX}{task_id}',task_status,timeout=3600)

            while not assembly_queue.empty():
                queue_size = assembly_queue.qsize()
                completed_this_round = 0
                for _ in range(queue_size):
                    assembly_name = assembly_queue.get()
                    cache_obj.setStatus('processing')
                    cache_obj.setProgress(40 + int((len(completed_assemblies) / max(total_assemblies, 1)) * 60))
                    # current_task_status = cache.get(f'{TASK_STATUS_PREFIX}{task_id}', task_status)
                    # current_task_status['status'] = 'processing'
                    # current_task_status['progress'] = 40 + int((len(completed_assemblies) / max(total_assemblies, 1)) * 60)
                    # current_task_status['result'] = {
                    #     'completed': completed_assemblies,
                    #     'current': assembly_name,
                    #     'current_level': level_value,
                    #     'queue': list(assembly_queue.queue),
                    #     'levels': {
                    #         'current': level_value,
                    #         'step': f'{level_index}/3',
                    #     },
                    # }
                    # cache.set(f'{TASK_STATUS_PREFIX}{task_id}',current_task_status,timeout=3600)

                    try:
                        process_assembly_repo(assembly_name, django_request, task_id)
                        completed_assemblies.append(assembly_name)
                        failed_assemblies.pop(assembly_name, None)
                        completed_this_round += 1
                    except LabDatabaseException as exc:
                        error_message = exc.message
                        cache_obj.setMessage(cache_obj.getMessage() + "\n" + f"仓库 {assembly_name} 组装失败, {error_message}")
                        failed_assemblies[assembly_name] = error_message or 'assembly failed'
                        assembly_queue.put(assembly_name)
                        print(failed_assemblies)
                        print(error_message)
                        # cache_obj.setMessage(cache_obj.getMessage() + "\n" + f"仓库 {assembly_name} 组装失败, {error_message}")
                    except Exception as exc:
                        with TASK_STATUS_LOCK:
                            cache_obj.setMessage(cache_obj.getMessage() + "\n" + f"仓库 {assembly_name} 组装失败, {str(exc)}")
                    # completed_assemblies.append(assembly_name)
                    # failed_assemblies.pop(assembly_name, None)
                    # completed_this_round += 1
                    # else:
                    #     failed_assemblies[assembly_name] = current_task_status.get('error') or 'assembly failed'
                    #     assembly_queue.put(assembly_name)
                        # current_task_status = {'status':'failed','error':str(e.args)}
                print(completed_this_round)
                print(assembly_queue.empty())
                if completed_this_round == 0 and not assembly_queue.empty():
                    with TASK_STATUS_LOCK:
                        cache_obj.setStatus("failed")
                        cache_obj.setProgress(100)
                        error = ""
                        for each_key in failed_assemblies:
                            error += failed_assemblies[each_key]+"\n"
                        cache_obj.setMessage(cache_obj.getMessage() + "\n" + error+"\n" + "批量组装失败")
                        cache.set(f'{TASK_STATUS_PREFIX}{task_id}',cache_obj)
                        return
                    # task_status = {
                    #     'status':'failed',
                    #     'progress':100,
                    #     'result':{
                    #         'completed': completed_assemblies,
                    #         'pending': list(assembly_queue.queue),
                    #         'current_level': level_value,
                    #     },
                    #     'error': failed_assemblies,
                    # }
                    # cache.set(f'{TASK_STATUS_PREFIX}{task_id}',task_status,timeout=3600)
                    # return
        
        with TASK_STATUS_LOCK:
            cache_obj.setStatus('completed')
            cache_obj.setProgress(100)
            result_payload = _build_task_result_payload(task_id)
            result_payload.update({
                'success': True,
                'completed': completed_assemblies,
            })
            cache_obj.setResult(result_payload)
            cache_obj.setMessage(cache_obj.getMessage() + "\n" + "组装结束")
            print(result_payload)
            print(cache_obj.getMessage() + "\n" + "组装结束")
            cache.set(f"{TASK_STATUS_PREFIX}{task_id}",cache_obj)
        # task_status['progress'] = 100
        # task_status['status'] = 'completed'
        # task_status['result'] = {
        #     'success':True,
        #     'message':'组装结束',
        #     'completed': completed_assemblies,
        # }
        # cache.set(f'{TASK_STATUS_PREFIX}{task_id}',task_status,timeout=3600)
    except LabDatabaseException as exc:
        with TASK_STATUS_LOCK:
            cache_obj.setStatus("failed")
            cache_obj.setProgress(100)
            cache_obj.setMessage(cache_obj.getMessage() + "\n" + f"组装失败,{exc.message}")
            cache.set(f"{TASK_STATUS_PREFIX}{task_id}",cache_obj)
    except Exception as e:
        with TASK_STATUS_LOCK:
            cache_obj.setStatus("failed")
            cache_obj.setProgress(100)
            cache_obj.setMessage(cache_obj.getMessage() + "\n" + f"组装失败,{str(e)}")
            cache.set(f"{TASK_STATUS_PREFIX}{task_id}",cache_obj)
        # task_status = {
        #     'status':'failed',
        #     'progress':100,
        #     'result':None,
        #     'error':str(e.args),
        # }
        # cache.set(f'{TASK_STATUS_PREFIX}{task_id}',task_status,timeout=3600)



def CreateTempRepository(request):
    # print(request.FILES)
    try:
        if(request.method == "POST" and request.FILES):
            file = request.FILES.get('file')
            
            task_id = str(uuid.uuid4())
            cache_obj = CacheClass("processing",0)
            # task_status = {
            #     'status':'processing',
            #     'progress':0,
            #     'result':None,
            #     'error':None,
            # }
            cache.set(f'{TASK_STATUS_PREFIX}{task_id}',cache_obj,timeout=3600)
        
            thread = threading.Thread(
                target=process_gg_assembly_async,
                args=(file, request, task_id)
            )
            thread.daemon = False
            thread.start()
            return JsonResponse({'task_id':task_id,'status':'processing','message':"上传成功，数据分析中"},status = 200, safe = False)
        else:
            if(request.method != "POST"):
                raise LabDatabasePOSTMethodException()
            if(request.FILES == None):
                raise LabDatabaseException(message="上传文件为空")
            # return JsonResponse({'success':False,'message':'上传失败'},status = 405, safe = False)
    except LabDatabaseException as exc:
        return exc.to_response()
    except Exception as exc:
        return JsonResponse({"success":False,"message":str(exc)},status=400)
    
    
@csrf_exempt
def UploadFile(request):
    # print(request.FILES)
    try:
        if(request.method == 'POST' and request.FILES):
            file = request.FILES.get('file')
            title = request.POST.get('title', file.name)

            task_id = str(uuid.uuid4())
            cache_obj = CacheClass("processing",0)
            # print(title)
            # task_status = {
            #     'status':'processing',
            #     'progress':0,
            #     'result':None,
            #     'error':None,
            # }
            cache.set(f'{TASK_STATUS_PREFIX}{task_id}',cache_obj,timeout=3600)
            thread = threading.Thread(
                target = process_excel_async,
                args= (file,request,task_id)
            )
            thread.daemon = False
            thread.start()
            return JsonResponse({'task_id':task_id,'status':'processing','message':"上传成功，数据处理中"},status = 200, safe = False)
    #     print(len(Empty_sequence_rows))
    #     if(len(Error_rows) == 0 and len(Empty_sequence_rows) == 0):
    #         return JsonResponse(data={'success':True,'message':"閺傚洣娆㈡稉濠佺炊閹存劕濮?},status = 200, safe=False)
    #     else:
    #         message = ""
    #         if(len(Error_rows) != 0):
    #             message += "娑撳﹣绱堕崙娲晩閻ㄥ嫯顢戦張澶変簰娑撳绱癨n"+str(Error_rows)+"\n"
    #         if(len(Empty_sequence_rows) != 0):
    #             print("aaaaaaa")
    #             message += "闂団偓鐟曚浇藟閸忓懎绨崚妤冩畱閺堝浜掓稉瀣剁窗\n"+str(Empty_sequence_rows)
    #         return JsonResponse(data = {'success':True, 'message': message},status = 200, safe=False)
        else:
            if(request.method != "POST"):
                raise LabDatabasePOSTMethodException()
            if(request.FILES == None):
                raise LabDatabaseException(message = "上传文件为空")
    except LabDatabaseException as exc:
        return exc.to_response()
    except Exception as exc:
        return JsonResponse({"success":False,"message":str(exc)})
    
def task_status(request, task_id):
    try:
        cache_obj = cache.get(f'{TASK_STATUS_PREFIX}{task_id}')
        if(not cache_obj):
            raise LabDatabaseException(message = "任务已过期")
        # return JsonResponse({
        #     'task_id':task_id,
        #     'status':'failed',
        #     'progress':0,
        #     'error':"Task does not exist or has expired."
        # },status=404)
        if(cache_obj.getProgress() == 100 and cache_obj.getStatus() != "failed"):
            cache_obj.setStatus("completed")
        # if(task_status['progress'] == 100 and task_status['status'] != "failed"):
        #     task_status['status'] = 'completed'
    # response_data = {
    #     'task_id':task_id,
    #     'status':task_status['status'],
    #     'progress':task_status['progress'],
    # }
        response_data = {
            'task_id':task_id,
            'status':cache_obj.getStatus(),
            'progress':cache_obj.getProgress(),
            'success':cache_obj.getStatus() != "failed",
            'message':cache_obj.getMessage() or ""
        }
        if cache_obj.getStatus() == "failed":
            response_data['error'] = cache_obj.getError() or cache_obj.getMessage() or "任务处理失败"
        if cache_obj.getResult() not in ("", None):
            response_data['result'] = cache_obj.getResult()
    #     if(cache_obj.getStatus() == "completed"):
    #         response_data["error"] = cache_obj.getMessage()
        
    # # if task_status['status'] == 'completed':
    # #     if(task_status['result'] != None):
    # #         response_data['result']=task_status['result']
    # #     if(task_status['error'] != None):
    # #         response_data['error'] = task_status['error']
    # elif task_status['status'] == 'failed':
    #     response_data['error'] = task_status['error']
    #     # print(response_data)
        print(response_data)
        return JsonResponse(response_data)
    except LabDatabaseException as exc:
        return exc.to_response()
    except Exception as exc:
        return JsonResponse({"success":False,"message":str(exc)},status=400)

def excel_task_status(request, task_id):
    try:
        cache_obj = cache.get(f'{TASK_STATUS_PREFIX}{task_id}')
        print()
        if(not cache_obj):
            return JsonResponse({"status":"failed","message":"任务已过期"},status=404)
            # raise LabDatabaseException(message="任务已过期")
            # return JsonResponse({'error':"Task does not exist or has expired."},status=404)
        if(cache_obj.getProgress() == 100 and cache_obj.getStatus() != "failed"):
            cache_obj.setStatus("completed")
        # if(task_status['progress'] == 100 and task_status['status'] != "failed"):
        #     task_status['status'] = 'completed'
        print(cache_obj.getStatus())
        if(cache_obj.getStatus() == "completed"):
            if(os.path.exists(cache_obj.getMessage())):
                response_status = {
                    "status":"completed",
                    "file_id":task_id,
                }
                return JsonResponse(response_status)
            else:
                return JsonResponse({"status":"failed","message":"文件不存在"},status=404)
        elif(cache_obj.getStatus() == "failed"):
            return JsonResponse({"status":"failed","message":cache_obj.getMessage()},status=400)
        else:
            return JsonResponse({"success":True})
            # raise LabDatabaseException(message = cache_obj.getMessage())
    except LabDatabaseException as exc:
        return JsonResponse({"status":"failed","message":exc.message},status=400)
    except Exception as exc:
        return JsonResponse({"status":"failed","message":str(exc)},status=400)


# @csrf_exempt
def UploadMap(request):
    try:
        if request.method == 'POST' and request.FILES.getlist('files'):
            files = request.FILES.getlist('files')
            number_of_task = len(files)
            cache_obj = CacheClass("processing",0,total_count = number_of_task)
            # task_status = {
            #     'status':'processing',
            #     'progress':0,
            #     'result':None,
            #     'error':[],
            #     'processed_count':0,
            #     'total_count':number_of_task,
            # }
            task_id = str(uuid.uuid4())
            cache.set(f'{TASK_STATUS_PREFIX}{task_id}',cache_obj,timeout=3600)
            # upload_map,file_name,upload_type,django_request, task_id
        
            # title = request.POST.get('title', file.name)
            pattern = r'^([^\_|.]+)'
            # print(number_of_task)
            index = 0
            save_feature = str(request.POST.get('save_feature', 'false')).lower() in ['true', '1', 'yes', 'on']
            for each in files:
                suffix = each.name.split('.')[1]
                each_name = []
                match = re.match(pattern, each.name)
                each_name.append(match.group(1).strip())
                each_name.append(suffix)
                print(each_name)
                type = request.POST.get('type')
                thread = threading.Thread(
                    target = process_map_async,
                    args= (each,each_name,type,request,task_id,index,number_of_task,save_feature)
                )
                thread.daemon = False
                thread.start()
                index+=1
            return JsonResponse({'task_id':task_id,'status':'processing','message':"上传成功，数据处理中"},status = 200, safe = False)
        else:
            raise LabDatabaseException(message="未选择上传文件")
            # return JsonResponse({'success':False,'message':'Upload record is empty'})
    except LabDatabaseException as exc:
        return exc.to_response()
    except Exception as exc:
        return JsonResponse({"success":False,"message":str(exc)},status=400)


@csrf_exempt
def CheckAndFixGenBank(request):
    try:
        if request.method != "POST":
            return JsonResponse({"success": False, "message": "Only POST method is allowed"}, status=405, safe=False)

        upload_file = request.FILES.get("file")
        if upload_file is None:
            return JsonResponse({"success": False, "message": "file is required"}, status=400, safe=False)

        result = process_uploaded_genbank(upload_file)
        fixed_text = result["fixed_bytes"].decode(result["encoding"], errors="replace")

        upload_name = os.path.basename(getattr(upload_file, "name", "uploaded"))
        upload_base = os.path.splitext(upload_name)[0].strip()
        if not upload_base:
            upload_base = "uploaded"
        safe_base = re.sub(r'[\\/:*?"<>|]+', "_", upload_base)
        save_name = f"{safe_base}.gb"

        os.makedirs(GENBANK_FIXED_OUTPUT_DIR, exist_ok=True)
        save_path = os.path.join(GENBANK_FIXED_OUTPUT_DIR, save_name)

        with open(save_path, "wb") as f:
            f.write(result["fixed_bytes"])

        response = {
            "success": True,
            "changed": result["changed"],
            "issue_count": len(result["issues"]),
            "issues": result["issues"],
            "fixed_filename": save_name,
            "fixed_content": fixed_text,
            "file_path": save_path,
        }
        return JsonResponse(response, status=200, safe=False)
    except LabDatabaseException as exc:
        return exc.to_response()
    except Exception as exc:
        return JsonResponse({"success":False,"message":str(exc)})
    # except Exception as e:
    #     return JsonResponse({"success": False, "message": str(e)}, status=500, safe=False)



def part_detail_show(request,partid):
    try:
        if(request.method == "GET"):
            session = requests.Session()
            session.headers.update({
                'User-Agent':'Django-App/1.0',
                'Content-Type':'application/json',
            })
            partResponse = session.get(f'{Base_URL}PartByID?ID={partid}',cookies=request.COOKIES)
            if(partResponse.status_code == 200):
                part = partResponse.json()[0]
                if(part['type'] == 1):
                    part['type'] = "Promoter"
                elif(part['type'] == 2):
                    part['type'] = "CDS"
                elif(part['type'] == 3):
                    part['type'] = "Terminator"
                elif(part['type'] == 4):
                    part['type'] = "RBS"
                elif(part['type'] == 5):
                    part['type'] = "P+R"
                # print(part)
                return render(request,'part.html',{'part':part})
            else:
                raise LabDatabaseException(message = partResponse.json()["message"])
                # return render(request,'error.html',{'error':partResponse.json()["message"]})
        else:
            raise LabDatabaseGETMethodException()
    except LabDatabaseException as exc:
        return render(request, 'error.html',{'error':exc.message})
    except Exception as exc:
        return render(request, 'error.html',{'error':str(exc)})
        # return JsonResponse({"success":False,"message":str(exc)},status=400)



def backbone_detail_show(request,backboneid):
    try:
        if(request.method == "GET"):
            session = requests.Session()
            session.headers.update({
                'User-Agent':'Django-App/1.0',
                'Content-Type':'application/json',
            })
            backboneResponse = session.get(f'{Base_URL}BackboneByID?ID={backboneid}',cookies=request.COOKIES)
            backbonescar = session.get(f"{Base_URL}getBackboneScar?id={backboneid}",cookies=request.COOKIES)
            if(backboneResponse.status_code == 200):
                backbone = backboneResponse.json()[0]
                backbone['ori'] = ", ".join(backbone['ori'])
                backbone['marker'] = ", ".join(backbone['marker'])
                # print(backbone)
                # print(backbonescar.json())
                if(backbonescar.json()['success']):
                    scar_info = backbonescar.json()['scar_info'][0]
                else:
                    scar_info = {"bsmbi":"","bsai":"","bbsi":"","aari":"","sapi":""}
                return render(request,'backbone.html',{'backbone':backbone, "scar":scar_info})
            else:
                raise LabDatabaseException(message=backboneResponse.json()["message"])
                # return render(request,'error.html',{'error':backboneResponse.text})
        else:
            raise LabDatabaseGETMethodException()
    except LabDatabaseException as exc:
        return render(request,"error.html",{"error":exc.message})
    except Exception as exc:
        return render(request,"error.html",{"error":str(exc)})



def plasmid_detail_show(request,plasmidid):
    try:
        if(request.method == "GET"):
            session = requests.Session()
            session.headers.update({
                'User-Agent':'Django-App/1.0',
                'Content-Type':'application/json',
            })
            plasmidResponse = session.get(f'{Base_URL}PlasmidByID?ID={plasmidid}',cookies=request.COOKIES)
            plasmidScar = session.get(f'{Base_URL}getPlasmidScar?plasmidid={plasmidid}',cookies = request.COOKIES)
            # print(plasmidScar)
            # print(plasmidScar.json()["scar_info"][0])
            plasmidParentPart = session.get(f'{Base_URL}GetPartParent?plasmidid={plasmidid}',cookies=request.COOKIES)
            print(plasmidParentPart.json())
            plasmidParentBackbone = session.get(f'{Base_URL}GetBackboneParent?plasmidid={plasmidid}',cookies=request.COOKIES)
            print(plasmidParentBackbone.json())
            plasmidParentPlasmid = session.get(f'{Base_URL}GetPlasmidParent?plasmidid={plasmidid}',cookies=request.COOKIES)
            print(plasmidParentPlasmid.json())
            plasmidSonPlasmid = session.get(f'{Base_URL}GetPlasmidSon?plasmidid={plasmidid}',cookies = request.COOKIES)

            print(plasmidResponse.json())
            print(plasmidScar.json())
            if(plasmidResponse.status_code == 200):
                plasmid = plasmidResponse.json()[0]
                plasmid["ori_info"] = ", ".join(plasmid["ori_info"])
                plasmid["marker_info"] = ", ".join(plasmid["marker_info"])
                result = {
                        'Part':[],
                        "Backbone":[],
                        "Plasmid":[],
                    }
                # print(plasmidScar.json())
                if(plasmidScar.json()['success']):
                    scar_info = plasmidScar.json()['scar_info'][0]
                else:
                    scar_info = {"bsmbi":"","bsai":"","bbsi":"","aari":"","sapi":""}
                if(plasmid['customparentinformation'] != None and plasmid['customparentinformation']!= "" and plasmid['customparentinformation'] != 'None' and plasmid['customparentinformation'] != 'NULL'):
                    plasmidParentInfo = plasmid['customparentinformation']
                    pattern = r'(\w+)\(([ a-zA-z0-9]+)\)'
                    matches = re.findall(pattern, plasmidParentInfo)
                    # print(result)
                    for component_type, letter in matches:
                        if(component_type == "Part"):
                            result['Part'].append(letter)
                        elif(component_type == "Backbone"):
                            result['Backbone'].append(letter)
                        elif(component_type == "Plasmid"):
                            result['Plasmid'].append(letter)
                return render(request,'plasmid.html',{'plasmid':plasmid,'partparent':plasmidParentPart.json()['data'] if (plasmidParentPart.json()["success"] and len(plasmidParentPart.json()['data']) >0) else [],'backboneparent':plasmidParentBackbone.json()['data'] if (plasmidParentBackbone.json()["success"] and len(plasmidParentBackbone.json()['data']) > 0) else [],
                                        'plasmidparent':plasmidParentPlasmid.json()['data'] if (plasmidParentPlasmid.json()["success"] and len(plasmidParentPlasmid.json()['data']) > 0) else [],'plasmidson':plasmidSonPlasmid.json()['data'] if (plasmidSonPlasmid.json()["success"] and len(plasmidSonPlasmid.json()['data']) > 0) else [], 'ParentPartInfo':result["Part"],
                                        'ParentBackboneInfo':result['Backbone'],'ParentPlasmidInfo':result['Plasmid'],"scar":scar_info})
            else:
                if(plasmidResponse.json()['success'] == False):
                    raise LabDatabaseException(message = plasmidResponse.json()['message'])
                elif(plasmidScar.json()['success'] == False):
                    raise LabDatabaseException(message = plasmidScar.json()['message'])
                # return render(request,'error.html',{'error':plasmidResponse.text})
        else:
            raise LabDatabaseGETMethodException()
    except LabDatabaseException as exc:
        print(exc.message)
        return render(request,'error.html',{'error':exc.message})
    except Exception as exc:
        print(str(exc))
        return render(request,'error.html',{"error":str(exc)})

def downloadPartMap(request,partid):
    try:
        if(request.method == "GET"):
            session = requests.Session()
            session.headers.update({
                'User-Agent':'Django-App/1.0',
                'Content-Type':'application/json',
            })
            sequence = (session.get(f'{Base_URL}GetPartSeqByID?partid={partid}',cookies = request.COOKIES)).json()['data']['level0sequence'].lower()
            name = (session.get(f"{Base_URL}PartNameByID?ID={partid}",cookies=request.COOKIES)).json()['PartName']
            alias = (session.get(f"{Base_URL}PartAliasByID?ID={partid}",cookies=request.COOKIES)).json()['PartAlias']
            if(os.path.exists(os.path.join(ASSEMBLY_DIR,f'part-{partid}-{name}-{alias}.gbk'))):
                response = FileResponse(open(os.path.join(ASSEMBLY_DIR,f'part-{partid}-{name}-{alias}.gbk'),'rb'),as_attachment=True,filename=f'part-{partid}-{name}-{alias}.gbk')
                return response
            if(len(sequence) == 0 or sequence == ""):
                raise LabDatabaseException(message = "此Part序列为空, 无法生成文件")
            type = (session.get(f"{Base_URL}TypeByID?ID={partid}",cookies=request.COOKIES)).json()['Type'].lower()
            part_feature_response = session.get(f"{Base_URL}GetPartFeature/{partid}", cookies=request.COOKIES).json()
            map_path = rf'{ASSEMBLY_DIR}\part-{partid}-{name}-{alias}.gbk'
            if(part_feature_response.get("success") and part_feature_response.get("data")):
                thread = threading.Thread(
                    target = SequenceAnnotator.GeneratorPartNoSa,
                    args = (f'part-{partid}-{name}-{alias}',sequence,ASSEMBLY_DIR,part_feature_response['data'])
                )
                    # thread.daemon = False
                    # thread.start()
                    # start_time = time.time()
                    # max_wait_time = 5
                    # while time.time() - start_time < max_wait_time:
                    #     if(os.path.exists(map_path) and os.stat(map_path).st_size != 0):
                    #         response = FileResponse(open(map_path,'rb'),as_attachment=True,filename=f'part-{partid}-{name}-{alias}.gbk')
                    #         return response
                    #     time.sleep(1)
            else:
                seq_obj = Seq(sequence)
                # seq_reverse = str(seq_obj.reverse_complement())
                feature_list = {}
                reverse_feature_list = {}
                # fi = featureIdentify()
                # feature_list = fi.featureMatch(sequence)
                # reverse_feature_list = fi.featureMatch(seq_reverse)
                scar_list = scarPosition(sequence)
                sa = SequenceAnnotator(sequence,feature_list,reverse_feature_list,scar_list,name=f'part-{partid}-{name}-{alias}')
                thread = threading.Thread(
                    target = sa.GenerateGBKFile,
                    args= (ASSEMBLY_DIR,type)
                )
            thread.daemon = False
            thread.start()
            # sa.GenerateGBKFile()
            max_wait_time = 5
            start_time = time.time()
            while time.time() - start_time < max_wait_time:
                if(os.path.exists(map_path) and os.stat(map_path).st_size != 0):
                    response = FileResponse(open(map_path,'rb'),as_attachment=True,filename=f'part-{partid}-{name}-{alias}.gbk')
                    return response
                else:
                    time.sleep(1)
                    continue
            raise LabDatabaseException(message="生成图谱失败")
            # return JsonResponse(data={'success':False,'data':'Generate fail'},status = 400, safe = False)
        else:
            raise LabDatabaseGETMethodException()
    except LabDatabaseException as exc:
        return exc.to_response()
    except Exception as exc:
        return JsonResponse({"success":False,"message":str(exc)},status = 400)
        # return render(request,'error.html',{'error':exc.message})



def downloadBackboneMap(request,backboneid):
    try:
        if(request.method == "GET"):
            session = requests.Session()
            session.headers.update({
                'User-Agent':'Django-App/1.0',
                'Content-Type':'application/json',
            })
            sequence = (session.get(f'{Base_URL}GetBackboneSeqByID?backboneid={backboneid}',cookies = request.COOKIES)).json()['data']['sequence'].lower()
            name = (session.get(f"{Base_URL}BackboneNameByID?ID={backboneid}",cookies=request.COOKIES)).json()['BackboneName']
            alias = (session.get(f"{Base_URL}BackboneAliasByID?ID={backboneid}",cookies=request.COOKIES)).json()['BackboneAlias']
            backboneFeature = (session.get(f"{Base_URL}GetBackboneFeature/{backboneid}",cookies=request.COOKIES)).json()
            if(os.path.exists(os.path.join(ASSEMBLY_DIR,f"backbone-{backboneid}-{name}-{alias}.gbk"))):
                response = FileResponse(open(os.path.join(ASSEMBLY_DIR,f"backbone-{backboneid}-{name}-{alias}.gbk"),'rb'),as_attachment=True,filename=f'backbone-{backboneid}-{name}-{alias}.gbk')
                return response
            if(len(sequence) == 0 or sequence == ""):
                raise LabDatabaseException(message = "此Backbone序列为空, 无法生成文件")
            if(backboneFeature["success"] != True):
                seq_obj = Seq(sequence)
                # seq_reverse = str(seq_obj.reverse_complement())
                # fi = featureIdentify()
                # feature_list = fi.featureMatch(sequence)
                # reverse_feature_list = fi.featureMatch(seq_reverse)
                feature_list = {}
                reverse_feature_list = {}
                scar_list = scarPosition(sequence)
                sa = SequenceAnnotator(sequence,feature_list,reverse_feature_list,scar_list,name=f'backbone-{backboneid}-{name}-{alias}')
                thread = threading.Thread(
                    target = sa.GenerateGBKFile,
                    args= (ASSEMBLY_DIR,)
                )
                # thread.daemon = False
                # thread.start()
            else:
                thread = threading.Thread(
                    target = SequenceAnnotator.GeneratorBackboneNoSa,
                    args = (f'backbone-{backboneid}-{name}-{alias}',sequence,ASSEMBLY_DIR,backboneFeature['data'])
                )
                # sa.GenerateGBKFile()
            thread.daemon = False
            thread.start()
            map_path = rf'{ASSEMBLY_DIR}backbone-{backboneid}-{name}-{alias}.gbk'
            start_time = time.time()
            max_wait_time = 5
            while time.time() - start_time < max_wait_time:
                if(os.path.exists(map_path) and os.stat(map_path).st_size != 0):
                    response = FileResponse(open(map_path,'rb'),as_attachment=True,filename=f'backbone-{backboneid}-{name}-{alias}.gbk')
                    return response
                else:
                    time.sleep(1)
                    continue
            raise LabDatabaseException(message="生成文件失败")
            # return JsonResponse(data={'success':False,'data':'Generate fail'},status = 400, safe = False)
        else:
            raise LabDatabaseGETMethodException()
    except LabDatabaseException as exc:
        return exc.to_response()
    except Exception as exc:
        return JsonResponse({"success":False, "message":str(exc)})
    
    
    
def downloadPlasmidMap(request,plasmidid):
    try:
        if(request.method == "GET"):
            session = requests.Session()
            session.headers.update({
                'User-Agent':'Django-App/1.0',
                'Content-Type':'application/json',
            })
        
            sequence = (session.get(f'{Base_URL}PlasmidSeqByID?plasmidid={plasmidid}',cookies = request.COOKIES)).json()['data']['sequenceconfirm'].lower()
            name = (session.get(f"{Base_URL}PlasmidNameByID?ID={plasmidid}",cookies=request.COOKIES)).json()["PlasmidName"]
            alias = (session.get(f"{Base_URL}PlasmidAliasByID?ID={plasmidid}",cookies=request.COOKIES)).json()["PlasmidAlias"]
            if(os.path.exists(os.path.join(ASSEMBLY_DIR,f"{name}.gbk"))):
                response = FileResponse(open(os.path.join(ASSEMBLY_DIR,f"{name}.gbk"),'rb'),as_attachment=True,filename=f'plasmid-{plasmidid}-{name}-{alias}.gbk')
                return response
            elif(os.path.exists(os.path.join(ASSEMBLY_DIR,f"plasmid-{plasmidid}-{name}-{alias}.gbk"))):
                response = FileResponse(open(os.path.join(ASSEMBLY_DIR,f"plasmid-{plasmidid}-{name}-{alias}.gbk"),'rb'),as_attachment=True,filename=f'plasmid-{plasmidid}-{name}-{alias}.gbk')
                return response
            if(len(sequence) == 0 or sequence == ""):
                raise LabDatabaseException(message = "此Plasmid序列为空, 无法生成文件")
            plasmid_feature_response = session.get(f"{Base_URL}GetPlasmidFeature/{plasmidid}", cookies=request.COOKIES).json()
            map_path = rf'{ASSEMBLY_DIR}plasmid-{plasmidid}-{name}-{alias}.gbk'
            if(plasmid_feature_response.get("success") and plasmid_feature_response.get("data")):
                thread = threading.Thread(
                    target = SequenceAnnotator.GeneratorBackboneNoSa,
                    args = (f'plasmid-{plasmidid}-{name}-{alias}',sequence,ASSEMBLY_DIR,plasmid_feature_response['data'])
                )
                thread.daemon = False
                thread.start()
                start_time = time.time()
                max_wait_time = 5
                while time.time() - start_time < max_wait_time:
                    if(os.path.exists(map_path) and os.stat(map_path).st_size != 0):
                        response = FileResponse(open(map_path,'rb'),as_attachment=True,filename=f'plasmid-{plasmidid}-{name}-{alias}.gbk')
                        return response
                    time.sleep(1)
            seq_obj = Seq(sequence)
            scar_list = scarPosition(sequence)
            seq_reverse = str(seq_obj.reverse_complement())
            PlasmidParentBackboneResponse = (session.get(f"{Base_URL}GetBackboneParent?plasmidid={plasmidid}",cookies=request.COOKIES)).json()
            print(PlasmidParentBackboneResponse)
            sa = SequenceAnnotator(sequence,{},{},scar_list,name=f'plasmid-{plasmidid}-{name}-{alias}')
            if(PlasmidParentBackboneResponse['success'] and len(PlasmidParentBackboneResponse['data']) != 0):
                PlasmidParentBackbone = PlasmidParentBackboneResponse['data'][0]['id']
                ParentBackboneSequenceResponse = (session.get(f"{Base_URL}GetBackboneSeqByID?backboneid={PlasmidParentBackbone}", cookies=request.COOKIES)).json()
                if(ParentBackboneSequenceResponse['success']):
                    ParentBackboneSequence = ParentBackboneSequenceResponse['data']['sequence']
                    BackboneFeatureListResponse = (session.get(f"{Base_URL}GetBackboneFeature/{PlasmidParentBackbone}", cookies=request.COOKIES)).json()
                    if(BackboneFeatureListResponse['success']):
                        backbone_fetch_kmer = KmerIndex()
                        for each_feature in BackboneFeatureListResponse['data']:
                            if(each_feature['feature_start']<each_feature['feature_end']):
                                backbone_fetch_kmer.add_sequence(each_feature["feature_label"],ParentBackboneSequence[each_feature["feature_start"]:each_feature["feature_end"]])
                            else:
                                backbone_fetch_kmer.add_sequence(each_feature["feature_label"],ParentBackboneSequence[each_feature["feature_start"]:]+ParentBackboneSequence[:each_feature["feature_end"]])
                        fetch_result = backbone_fetch_kmer.query(sequence)
                        for each_key in fetch_result.keys():
                            for each_feature in BackboneFeatureListResponse['data']:
                                if(each_feature["feature_label"] == fetch_result[each_key]["seq_id"]):
                                    type = each_feature["feature_type"]
                                    color = each_feature["feature_color"] if each_feature["feature_color"] != "" else each_feature["feature_apeinfo"]
                                    print(color)
                                    break
                            new_feature = {fetch_result[each_key]["seq_id"]:[fetch_result[each_key]["start"],fetch_result[each_key]['end'],type,color]}
                            sa.add_feature(new_feature)
                    else:
                        fi = featureIdentify()
                        feature_list = fi.featureMatch(sequence)
                        reverse_feature_list = fi.featureMatch(seq_reverse)
                        sa.add_features(feature_list)
                        sa.add_reverse_features(reverse_feature_list)
                    # sa = SequenceAnnotator(sequence,feature_list,reverse_feature_list,scar_list,name=f'plasmid-{plasmidid}')
        # PlasmidParentPartResponse = (session.get(f"{Base_URL}GetPartParent?plasmidid={plasmidid}",cookies=request.COOKIES)).json()
        # Part_fetch_kmer = KmerIndex()
        # if(PlasmidParentPartResponse['success']):
        #     PlasmidParentPart = PlasmidParentPartResponse['data']
        #     print(PlasmidParentPart)
        #     for each_part in PlasmidParentPart:
        #         partSeqResponse = (session.get(f"{Base_URL}GetPartSeqByID?partid={each_part['partid']}",cookies=request.COOKIES)).json()
        #         if(partSeqResponse['success']):
        #             partSeq = partSeqResponse['data']['level0sequence']
        #             part_reverse_Seq = str(Seq(partSeq).reverse_complement())
        #             Part_fetch_kmer.add_sequence(each_part['name'],partSeq)
        #             Part_fetch_kmer.add_sequence(each_part['name']+"'",part_reverse_Seq)
        #     fetch_result = Part_fetch_kmer.query(sequence)
        #     for each_key in fetch_result:
        #         if(each_key[-1] == "'"):
        #             each_key_temp = each_key[:-1]
        #             typeResponse = (session.get(f"{Base_URL}TypeByName?name={each_key_temp}",cookies=request.COOKIES))
        #         else:
        #             typeResponse = (session.get(f"{Base_URL}TypeByName?name={each_key}",cookies=request.COOKIES))
        #         if(typeResponse.status_code == 200):
        #             type = typeResponse.json()['Type'].lower()
        #             if(each_key[-1] == "'"):
        #                 new_feature = {each_key[:-1]:[fetch_result[each_key]['start'],fetch_result[each_key]['end'],type]}
        #             else:
        #                 new_feature = {each_key:[fetch_result[each_key]['start'],fetch_result[each_key]['end'],type]}
        #             sa.add_feature(new_feature)
            PlasmidParentPlasmidResponse = (session.get(f"{Base_URL}GetPlasmidParent?plasmidid={plasmidid}",cookies=request.COOKIES)).json()
            plasmid_fetch_kmer = KmerIndex()
            plasmid_parent_kmer = KmerIndex()
            if(PlasmidParentPlasmidResponse['success'] and len(PlasmidParentPlasmidResponse['data']) != 0):
                PlasmidParentPlasmid = PlasmidParentPlasmidResponse['data']
                for each_plasmid in PlasmidParentPlasmid:
                    ParentPlasmidSequence = (session.get(f'{Base_URL}PlasmidSeqByID?plasmidid={each_plasmid["plasmidid"]}',cookies = request.COOKIES)).json()['data']['sequenceconfirm'].lower()
                    plasmid_parent_kmer.add_sequence(each_plasmid["name"],ParentPlasmidSequence)
                    plasmid_parent_kmer.add_sequence(each_plasmid["name"]+"'",str(Seq(ParentPlasmidSequence).reverse_complement()))
                plasmid_parent_fetch_result = plasmid_parent_kmer.query(sequence)
                for each_key in plasmid_parent_fetch_result.keys():
                    if(each_key[-1] == "'"):
                        new_feature = {each_key[:-1]:[plasmid_parent_fetch_result[each_key]["start"],plasmid_parent_fetch_result[each_key]["end"],""]}
                    else:
                        new_feature = {each_key:[plasmid_parent_fetch_result[each_key]["start"],plasmid_parent_fetch_result[each_key]["end"],""]}
                    sa.add_feature(new_feature)
                ParentPartList = getplasmidAllParentPart(request,session,PlasmidParentPlasmid)
                for each_part in ParentPartList.keys():
                    plasmid_fetch_kmer.add_sequence(each_part,ParentPartList[each_part])
                    plasmid_fetch_kmer.add_sequence(each_part+"'",str(Seq(ParentPartList[each_part]).reverse_complement()))
                fetch_result = plasmid_fetch_kmer.query(sequence)
                fetch_result = Remove_duplicated_Part(fetch_result)
                # print(fetch_result)
                for each_key in fetch_result.keys():
                    if(each_key[-1] == "'"):
                        each_key_temp = each_key[:-1]
                        typeResponse = (session.get(f"{Base_URL}TypeByName?name={each_key_temp}",cookies=request.COOKIES))
                    else:
                        typeResponse = (session.get(f"{Base_URL}TypeByName?name={each_key}",cookies=request.COOKIES))
                    if(typeResponse.status_code == 200):
                        type = typeResponse.json()['Type'].lower()
                        if(each_key[-1] == "'"):
                            new_feature = {each_key[:-1]:[fetch_result[each_key]["start"],fetch_result[each_key]["end"],type]}
                        else:
                            new_feature = {each_key:[fetch_result[each_key]["start"],fetch_result[each_key]["end"],type]}
                        sa.add_feature(new_feature)
        
            if(PlasmidParentBackboneResponse["success"] == False or PlasmidParentPlasmidResponse["success"] == False):
                fi = featureIdentify()
                feature_list = fi.featureMatch(sequence)
                reverse_feature_list = fi.featureMatch(seq_reverse)
                sa.add_features(feature_list)
                sa.add_reverse_features(reverse_feature_list)
            # print(sa.feature_list)
            print("start generating")
            thread = threading.Thread(
                target = sa.GenerateGBKFile,
                args= (ASSEMBLY_DIR,)
            )
            thread.daemon = False
            thread.start()
            # sa.GenerateGBKFile()
            max_wait_time = 5
            start_time = time.time()
            while time.time() - start_time < max_wait_time:
                if(os.path.exists(map_path) and os.stat(map_path).st_size != 0):
                    response = FileResponse(open(map_path,'rb'),as_attachment=True,filename=f'plasmid-{plasmidid}-{name}-{alias}.gbk')
                    return response
                else:
                    time.sleep(1)
                    continue
            return JsonResponse(data={'success':False,'data':'Generate fail'},status = 400, safe = False)
        else:
            raise LabDatabaseGETMethodException()
    except LabDatabaseException as exc:
        return exc.to_response()
    except Exception as exc:
        return JsonResponse({"success":False,"message":str(exc)})

def Remove_duplicated_Part(fetch_result):
    fetch_result_keys = list(fetch_result.keys())
    for each_key in fetch_result_keys:
        try:
            if(each_key[-1] == "'" and fetch_result[each_key[:-1]] != None):
                density_reverse = fetch_result[each_key]["density"]
                density = fetch_result[each_key[:-1]]["density"]
                if(density_reverse >= density):
                    fetch_result.pop(each_key[:-1],None)
                else:
                    fetch_result.pop(each_key,None)
            else:
                density_reverse = fetch_result[each_key+"'"]["density"]
                density = fetch_result[each_key]["density"]
                if(density_reverse >= density):
                    fetch_result.pop(each_key,None)
                else:
                    fetch_result.pop(each_key+"'",None)
        except KeyError:
            continue
    return fetch_result
            

def getplasmidAllParentPart(django_request, session, PlasmidParentPlasmid):
    try:
        ParentPartList = {}
        PlasmidParentPlasmidQueue = queue.Queue()
        for each_plasmid in PlasmidParentPlasmid:
            PlasmidParentPlasmidQueue.put(each_plasmid['plasmidid'])
        while not PlasmidParentPlasmidQueue.empty():
            plasmidid = PlasmidParentPlasmidQueue.get()
            ParentPartResponse = (session.get(f"{Base_URL}GetPartParent?plasmidid={plasmidid}",cookies = django_request.COOKIES)).json()
            if(ParentPartResponse['success']):
                for each_part in ParentPartResponse['data']:
                    partSeqResponse = (session.get(f"{Base_URL}GetPartSeqByID?partid={each_part['partid']}",cookies=django_request.COOKIES)).json()
                    if(partSeqResponse['success']):
                        partSeq = partSeqResponse['data']['level0sequence'].lower()
                        ParentPartList[each_part['name']] = partSeq
            ParentPlasmidResponse = (session.get(f"{Base_URL}GetPlasmidParent?plasmidid={plasmidid}",cookies=django_request.COOKIES)).json()
            if(ParentPlasmidResponse['success']):
                for each_plasmid in ParentPlasmidResponse['data']:
                    PlasmidParentPlasmidQueue.put(each_plasmid['plasmidid'])
        return ParentPartList
    except LabDatabaseException as exc:
        raise exc
    except Exception as exc:
        raise exc
# def adminPage(request):
#     pass

def delete_part(request):
    try:
        if(request.method == "POST"):
            session = requests.Session()
            session.headers.update({
                'User-Agent':'Django-App/1.0',
                'Content-Type':'application/json',
            })
            partid = json.loads(request.body)["partid"]
            delete_part_response = session.get(f"{Base_URL}deletePart?partid={partid}", cookies = request.COOKIES)
            if(delete_part_response.json()["success"] == False):
                raise LabDatabaseException(message=delete_part_response.json()["message"])
                # return JsonResponse(data = {"success":False, "message":delete_part_response.json()["message"]},status = 400, safe = False)
            else:
                return JsonResponse(data={"success":True},status = 200, safe=False)
        else:
            raise LabDatabasePOSTMethodException()
            # return JsonResponse(data = {"success":False, "message":"Just GET Method"}, status = 404, safe = False)
    except LabDatabaseException as exc:
        return exc.to_response()
    except Exception as exc:
        return JsonResponse({"success":False,"message":str(exc)},status=400)



def delete_backbone(request):
    try:
        if(request.method == "POST"):
            session = requests.Session()
            session.headers.update({
                'User-Agent':'Django-App/1.0',
                'Content-Type':'application/json',
            })
            backboneid = json.loads(request.body)["backboneid"]
            print(backboneid)
            delete_backbone_response = session.get(f"{Base_URL}deleteBackbone?backboneid={backboneid}", cookies = request.COOKIES)
            
            if(delete_backbone_response.json()["success"] == False):
                print(delete_backbone_response.json())
                raise LabDatabaseException(message = delete_backbone_response.json()["message"])
                # return JsonResponse(data = {"success":False, "message":delete_backbone_response.json()["message"]},status = 400, safe = False)
            else:
                return JsonResponse(data={"success":True},status = 200, safe=False)
        else:
            raise LabDatabasePOSTMethodException()
            # return JsonResponse(data = {"success":False, "message":"Just GET Method"}, status = 404, safe = False)
    except LabDatabaseException as exc:
        print(exc)
        return exc.to_response()
    except Exception as exc:
        print(exc.args)
        return JsonResponse({"success":False, "message":str(exc)},status=400)



def delete_plasmid(request):
    try:
        if(request.method == "POST"):
            session = requests.Session()
            session.headers.update({
                'User-Agent':'Django-App/1.0',
                'Content-Type':'application/json',
            })
            plasmidid = json.loads(request.body)["Plasmidid"]
            delete_plasmid_response = session.get(f"{Base_URL}deletePlasmid?plasmidid={plasmidid}", cookies=request.COOKIES)
            if(delete_plasmid_response.json()["success"] == False):
                raise LabDatabaseException(message=delete_plasmid_response.json()["message"])
                # return JsonResponse(data = {"success":False, "message":delete_plasmid_response.json()["message"]},status = 400, safe = False)
            else:
                return JsonResponse(data={"success":True},status = 200, safe=False)
        else:
            raise LabDatabasePOSTMethodException()
            # return JsonResponse(data = {"success":False, "message":"Just GET Method"}, status = 404, safe = False)
    except LabDatabaseException as exc:
        return exc.to_response()
    except Exception as exc:
        return JsonResponse({"success":False,"message":str(exc)},status=400)

def exportuserdata(request,username):
    try:
        if(request.method == "GET"):
            session = requests.Session()
            session.headers.update({
                'User-Agent':'Django-App/1.0',
                'Content-Type':'application/json',
            })
            if(username != None and username != ""):
                excel_id = str(uuid.uuid4())
                excel_address = rf"{GENBANK_FIXED_OUTPUT_DIR}{username}-{excel_id}.xlsx"
                # task_status = {
                #     'status':'processing',
                #     'progress':0,
                #     'result':None,
                #     'error':[],
                #     'file_name':f"{username}-status.xlsx",
                #     'file_address':excel_address,
                #     'file_id':f"{username}-{excel_id}"
                # }
                cache_obj = CacheClass("processing",0)
                cache.set(f'{TASK_STATUS_PREFIX}{excel_id}',cache_obj,timeout=3600)
                thread = threading.Thread(
                    target = exportuserdataprocess,
                    args=(request, session, excel_id,username)
                )
                thread.daemon = False
                thread.start()
                return JsonResponse(data={'task_id':excel_id,'status':'processing','message':"导出任务已创建,请等待文件生成"},status=200, safe = False)
            else:
                raise LabDatabaseException(message = "username 不能为空")
                # return JsonResponse(data={"success":False,"message":"parameter cannot be empty"}, status=400, safe=False)
        else:
            raise LabDatabaseGETMethodException()
            # return JsonResponse(data={"success":False,"message":"Just GET method"}, status=400, safe=False)
    except LabDatabaseException as exc:
        return exc.to_response()
    except Exception as exc:
        return JsonResponse({"success":False,"message":str(exc)},status=400)
            
            
        # if(os.path.exists(excel_address)):
        #     response = FileResponse(open(excel_address,'rb'),as_attachment=True,filename=f'{username}-stats.xlsx')
        #     return response
        # else:
        #     return JsonResponse(data={'success':False,'data':'Generate fail'},status = 400, safe = False)




def exportuserdataprocess(request,session,task_id,username):
    try:
        # excel_address = cache.get(f'{TASK_STATUS_PREFIX}{task_id}')['file_address']
        excel_address = rf"{GENBANK_FIXED_OUTPUT_DIR}{username}-{task_id}.xlsx"
        excel_part_data = {}
        part_field = (session.get(f"{Base_URL}partfields",cookies=request.COOKIES)).json()['data']
        for each_field in part_field:
            excel_part_data[each_field] = []
        part_result = session.get(f"{Base_URL}partlistbyuser/{username}", cookies=request.COOKIES)
        if(part_result.json()["success"]):
            part_data = part_result.json()['data']
            for each_data in part_data:
                for each_key in each_data.keys():
                    excel_part_data[each_key].append(each_data[each_key])
        df_part = pd.DataFrame(excel_part_data)



        excel_backbone_data = {}
        backbone_field = (session.get(f"{Base_URL}backbonefields",cookies=request.COOKIES)).json()['data']
        for each_field in backbone_field:
            excel_backbone_data[each_field] = []
        backbone_result = session.get(f"{Base_URL}backbonelistbyuser/{username}", cookies=request.COOKIES)
        if(backbone_result.json()["success"]):
            backbone_data = backbone_result.json()['data']
            for each_data in backbone_data:
                for each_key in each_data.keys():
                    excel_backbone_data[each_key].append(each_data[each_key])
        df_backbone = pd.DataFrame(excel_backbone_data)




        excel_plasmid_data = {}
        plasmid_field = (session.get(f"{Base_URL}plasmidfields",cookies=request.COOKIES)).json()['data']
        for each_field in plasmid_field:
            excel_plasmid_data[each_field] = []
        plasmid_result = session.get(f"{Base_URL}plasmidlistbyuser/{username}", cookies=request.COOKIES)
        if(plasmid_result.status_code == 200):
            plasmid_data = plasmid_result.json()['data']
            for each_data in plasmid_data:
                for each_key in each_data.keys():
                    excel_plasmid_data[each_key].append(each_data[each_key])
        df_plasmid = pd.DataFrame(excel_plasmid_data)

        with pd.ExcelWriter(excel_address, engine="openpyxl") as writer:
            df_part.to_excel(writer, sheet_name="part",index = False)

            df_backbone.to_excel(writer, sheet_name="backbone", index = False)

            df_plasmid.to_excel(writer, sheet_name="plasmid",index=False)

        cache_obj = cache.get(f'{TASK_STATUS_PREFIX}{task_id}')
        cache_obj.setStatus("completed")
        cache_obj.setProgress(100)
        cache_obj.setMessage(excel_address)
        cache.set(f'{TASK_STATUS_PREFIX}{task_id}',cache_obj)
        
        
        # cache.set(f'{TASK_STATUS_PREFIX}{task_id}',cache_obj,timeout=3600)
    except LabDatabaseException as exc:
        with TASK_STATUS_LOCK:
            cache_obj = cache.get(f'{TASK_STATUS_PREFIX}{task_id}')
            cache_obj.setStatus("failed")
            cache_obj.setProgress(100)
            cache_obj.setMessage(exc.message())
        cache.set(f"{TASK_STATUS_PREFIX}{task_id}",cache_obj)
    except Exception as exc:
        with TASK_STATUS_LOCK:
            cache_obj = cache.get(f'{TASK_STATUS_PREFIX}{task_id}')
            cache_obj.setStatus("failed")
            cache_obj.setProgress(100)
            cache_obj.setMessage(exc.message())
        cache.set(f"{TASK_STATUS_PREFIX}{task_id}",cache_obj)
    
def ExportAllData(request):
    try:
        if(request.method == "GET"):
            session = requests.Session()
            session.headers.update({
                'User-Agent':'Django-App/1.0',
                'Content-Type':'application/json',
            })
            excel_id = str(uuid.uuid4())
            
            cache_obj = CacheClass("processing",0)
            cache.set(f'{TASK_STATUS_PREFIX}{excel_id}',cache_obj,timeout=3600)
            thread = threading.Thread(
                target = ExportAllDataProcess,
                args=(request, session, excel_id)
            )
            thread.daemon = False
            thread.start()

            return JsonResponse(data={'task_id':excel_id,'status':'processing','message':"导出任务已创建,请等待文件生成"}, status=200, safe=False)
        else:
            raise LabDatabaseGETMethodException()
            # return JsonResponse(data={'success':False,'message':"Just GET method"}, status=400, safe=False)
    except LabDatabaseException as exc:
        return exc.to_response()
    except Exception as exc:
        return JsonResponse({"success":False,"message":str(exc)},status=400)
    
    
    
def ExportAllDataProcess(request, session, task_id):
    try:
        # excel_address = cache.get(f'{TASK_STATUS_PREFIX}{task_id}')['file_address']
        # print(excel_address)
        # excel_address = f"{GENBANK_FIXED_OUTPUT_DIR}{task_id}.xlsx"
        excel_address = os.path.join(GENBANK_FIXED_OUTPUT_DIR,f"{task_id}.xlsx")
        print(excel_address)
        userlist = (session.get(f"{Base_URL}getuserlist",cookies=request.COOKIES)).json()['data']
        print(userlist)
        for each_user in userlist:
            print(each_user)
            excel_part_data = {}
            part_field = (session.get(f"{Base_URL}partfields",cookies=request.COOKIES)).json()['data']
            for each_field in part_field:
                excel_part_data[each_field] = []
            part_result = session.get(f"{Base_URL}partlistbyuser/{each_user['uname']}", cookies=request.COOKIES)
            print(part_result)
            if(part_result.status_code == 200):
                part_data = part_result.json()['data']
                for each_data in part_data:
                    for each_key in each_data.keys():
                        excel_part_data[each_key].append(each_data[each_key])
            df_part = pd.DataFrame(excel_part_data)
            
            
            excel_backbone_data = {}
            backbone_field = (session.get(f"{Base_URL}backbonefields",cookies=request.COOKIES)).json()['data']
            for each_field in backbone_field:
                excel_backbone_data[each_field] = []
            backbone_result = session.get(f"{Base_URL}backbonelistbyuser/{each_user['uname']}", cookies=request.COOKIES)
            print(backbone_result)
            if(backbone_result.status_code == 200):
                backbone_data = backbone_result.json()['data']
                for each_data in backbone_data:
                    for each_key in each_data.keys():
                        excel_backbone_data[each_key].append(each_data[each_key])
            df_backbone = pd.DataFrame(excel_backbone_data)



            excel_plasmid_data = {}
            plasmid_field = (session.get(f"{Base_URL}plasmidfields",cookies=request.COOKIES)).json()['data']
            for each_field in plasmid_field:
                excel_plasmid_data[each_field] = []
            plasmid_result = session.get(f"{Base_URL}plasmidlistbyuser/{each_user['uname']}", cookies=request.COOKIES)
            print(plasmid_result)
            if(plasmid_result.status_code == 200):
                plasmid_data = plasmid_result.json()['data']
                for each_data in plasmid_data:
                    for each_key in each_data.keys():
                        excel_plasmid_data[each_key].append(each_data[each_key])
            df_plasmid = pd.DataFrame(excel_plasmid_data)


            print(os.path.exists(excel_address))
            if(os.path.exists(excel_address) == False):

                with pd.ExcelWriter(excel_address, engine="openpyxl") as writer:
                    df_part.to_excel(writer, sheet_name=f"{each_user['uname']}(part)",index = False)

                    df_backbone.to_excel(writer, sheet_name=f"{each_user['uname']}(backbone)", index = False)

                    df_plasmid.to_excel(writer, sheet_name=f"{each_user['uname']}(plasmid)",index=False)
            else:
                with pd.ExcelWriter(excel_address, engine="openpyxl",mode='a',if_sheet_exists='replace') as writer:
                    df_part.to_excel(writer, sheet_name=f"{each_user['uname']}(part)",index = False)

                    df_backbone.to_excel(writer, sheet_name=f"{each_user['uname']}(backbone)", index = False)

                    df_plasmid.to_excel(writer, sheet_name=f"{each_user['uname']}(plasmid)",index=False)
        cache_obj = cache.get(f'{TASK_STATUS_PREFIX}{task_id}')
        cache_obj.setStatus("completed")
        cache_obj.setProgress(100)
        cache_obj.setMessage(excel_address)
        cache.set(f"{TASK_STATUS_PREFIX}{task_id}",cache_obj)
        print("completed")
        print("\n")
        print("\n")
        print("\n")
        print("\n")
        print("\n")
        print("\n")
        # task_status['status'] = "completed"
        # task_status['progress'] = 100
        # cache.set(f'{TASK_STATUS_PREFIX}{task_id}',task_status, timeout=3600)
    except LabDatabaseException as exc:
        with TASK_STATUS_LOCK:
            print("LabDatabaseException")
            print(exc.message)
            cache_obj = cache.get(f'{TASK_STATUS_PREFIX}{task_id}')
            cache_obj.setStatus("failed")
            cache_obj.setProgress(100)
            cache_obj.setMessage(exc.message)
        cache.set(f"{TASK_STATUS_PREFIX}{task_id}",cache_obj)
    except Exception as exc:
        with TASK_STATUS_LOCK:
            cache_obj = cache.get(f'{TASK_STATUS_PREFIX}{task_id}')
            cache_obj.setStatus("failed")
            cache_obj.setProgress(100)
            cache_obj.setMessage(str(exc))
        cache.set(f"{TASK_STATUS_PREFIX}{task_id}",cache_obj)


def getDocument(request, fileid):
    try:
        if(request.method == "GET"):
            # file_address = rf"{GENBANK_FIXED_OUTPUT_DIR}{fileid}.xlsx"
            file_address = os.path.join(GENBANK_FIXED_OUTPUT_DIR,f"{fileid}.xlsx")
            if(os.path.exists(file_address)):
                response = FileResponse(open(file_address,'rb'),as_attachment=True)
                return response
            else:
                raise LabDatabaseException(message="文件不存在")
                # return JsonResponse(data={"success":False},status=400, safe=False)
    except LabDatabaseException as exc:
        return exc.to_response()
    except Exception as exc:
        return JsonResponse({"success":False,'message':str(exc)},status=400)


def getDocumentByAddress(request):
    try:
        if(request.method == "GET"):
            file_address = request.GET.get("address")
            if(os.path.exists(file_address)):
                response = FileResponse(open(file_address,'rb'),as_attachment=True)
                return response
            else:
                raise LabDatabaseException(message="文件不存在")
                # return JsonResponse(data={"success":False},status=400)
        else:
            raise LabDatabaseGETMethodException()
    except LabDatabaseException as exc:
        return exc.to_response()
    except Exception as exc:
        return JsonResponse({"success":False,"message":str(exc)},status=400)


def getAssemblyFile(request, fileName):
    try:
        if(request.method == "GET"):
            task_id = request.GET.get("task_id")
            if task_id:
                file_address = _resolve_task_assembly_file(task_id, fileName)
            else:
                file_address = os.path.join(Assembly_File_Address,f"{fileName}.gb")
            if(os.path.exists(file_address)):
                copy_address = os.path.join(ASSEMBLY_DIR,f"{fileName}.gbk")
                shutil.copy(file_address,copy_address)
                response = FileResponse(open(file_address,'rb'),as_attachment=True)
                return response
            else:
                raise LabDatabaseException(message="文件不存在")
                # return JsonResponse(data={"success":False},status=400, safe=False)
        else:
            raise LabDatabaseGETMethodException()
    except LabDatabaseException as exc:
        return exc.to_response()
    except Exception as exc:
        return JsonResponse({"success":False,"message":str(exc)},status=400)


def getAssemblyArchive(request, task_id):
    try:
        if request.method != "GET":
            raise LabDatabaseGETMethodException()

        archive_path = _get_task_archive_file(task_id)
        if os.path.exists(archive_path):
            os.remove(archive_path)
        archive_path = _create_task_result_archive(task_id)

        if archive_path and os.path.exists(archive_path):
            return FileResponse(
                open(archive_path, "rb"),
                as_attachment=True,
                filename=os.path.basename(archive_path),
            )

        raise LabDatabaseException(message="压缩包不存在")
    except LabDatabaseException as exc:
        return exc.to_response()
    except Exception as exc:
        return JsonResponse({"success":False,"message":str(exc)},status=400)


def _create_api_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent':'Django-App/1.0',
        'Content-Type':'application/json',
    })
    return session


def _determine_target_enzyme(sequence):
    try:
        ccdb_sequence = "ggcttactaaaagccagataacagtatgcatatttgcgcgctgatttttgcggtataagaatatatactgatatgtatacccgaagtatgtcaaaaagaggtatgctatgaagcagcgtattacagtgacagttgacagcgacagctatcagttgctcaaggcatatatgatgtcaatatctccggtctggtaagcacaaccatgcagaatgaagcccgtcgtctgcgtgccgaacgctggaaagcggaaaatcaggaagggatggctgaggtcgcccggtttattgaaatgaacggctcttttgctgacgagaacaggggctggtgaaatgcagtttaaggtttacacctataaaagagagagccgttatcgtctgtttgtggatgtacagagtgatattattgacacgcccgggcgacggatggtgatccccctggccagtgcacgtctgctgtcagataaagtctcccgtgaactttacccggtggtgcatatcggggatgaaagctggcgcatgatgaccaccgatatggccagtgtgccggtttccgttatcggggaagaagtggctgatctcagccaccgcgaaaatgacatcaaaaacgccattaacctgatgttctggggaatataa"
        ccdb_reverse_sequence = "ttatattccccagaacatcaggttaatggcgtttttgatgtcattttcgcggtggctgagatcagccacttcttccccgataacggaaaccggcacactggccatatcggtggtcatcatgcgccagctttcatccccgatatgcaccaccgggtaaagttcacgggagactttatctgacagcagacgtgcactggccagggggatcaccatccgtcgcccgggcgtgtcaataatatcactctgtacatccacaaacagacgataacggctctctcttttataggtgtaaaccttaaactgcatttcaccagcccctgttctcgtcagcaaaagagccgttcatttcaataaaccgggcgacctcagccatcccttcctgattttccgctttccagcgttcggcacgcagacgacgggcttcattctgcatggttgtgcttaccagaccggagatattgacatcatatatgccttgagcaactgatagctgtcgctgtcaactgtcactgtaatacgctgcttcatagcatacctctttttgacatacttcgggtatacatatcagtatatattcttataccgcaaaaatcagcgcgcaaatatgcatactgttatctggcttttagtaagcc"
        ccdb_fi = KmerIndex()
        ccdb_fi.add_sequence("ccdb", ccdb_sequence)
        ccdb_fi.add_sequence("ccdb1", ccdb_reverse_sequence)
        ccdb_position = ccdb_fi.query(sequence)
        scar_ident_list = scarIdentSitePosition(sequence)
        print(ccdb_position)
        print(scar_ident_list)
        # print(scar_ident_list)
        if "ccdb" in ccdb_position.keys():
            ccdb_start_position = ccdb_position["ccdb"]["start"]
            ccdb_end_position = ccdb_position["ccdb"]["end"]
        elif "ccdb1" in ccdb_position.keys():
            ccdb_start_position = ccdb_position["ccdb1"]["start"]
            ccdb_end_position = ccdb_position["ccdb1"]["end"]
        else:
            return ""
        # print(f"ccdb_start_position:{ccdb_start_position}")
        # print(f"ccdb_end_position:{ccdb_end_position}")
        min_difference = 222222
        target_enzyme = ""
        for each_scar in scar_ident_list:
            scar_name = list(each_scar.keys())[0]
            scar_position = each_scar[scar_name]["index"]
            if(len(scar_position) >= 2):
                ccdb_min_position = min(ccdb_start_position, ccdb_end_position)
                ccdb_max_position = max(ccdb_start_position, ccdb_end_position)
                scar_min_position = min(scar_position[0], scar_position[1])
                scar_max_position = max(scar_position[0], scar_position[1])
                if(scar_min_position == 1):
                    scar_min_position = len(sequence)
                if(abs(ccdb_min_position-scar_min_position) + abs(ccdb_max_position - scar_max_position) < min_difference):
                    min_difference = abs(ccdb_min_position-scar_min_position) + abs(ccdb_max_position - scar_max_position)
                    target_enzyme = scar_name
        print(f"target enzyme: {target_enzyme}")
        return target_enzyme
    except LabDatabaseException as exc:
        raise exc
    except Exception as exc:
        raise exc


def _generate_plasmid_map_from_parents(session, django_request, plasmid_id, sequence, output_name):
    try:
        scar_list = scarPosition(sequence)
        seq_reverse = str(Seq(sequence).reverse_complement())
        PlasmidParentBackboneResponse = (session.get(f"{Base_URL}GetBackboneParent?plasmidid={plasmid_id}",cookies=django_request.COOKIES)).json()
        sa = SequenceAnnotator(sequence,{},{},scar_list,name=output_name)
        if(PlasmidParentBackboneResponse['success']):
            PlasmidParentBackbone = PlasmidParentBackboneResponse['data'][0]['id']
            ParentBackboneSequenceResponse = (session.get(f"{Base_URL}GetBackboneSeqByID?backboneid={PlasmidParentBackbone}", cookies=django_request.COOKIES)).json()
            if(ParentBackboneSequenceResponse['success']):
                ParentBackboneSequence = ParentBackboneSequenceResponse['data']['sequence']
                BackboneFeatureListResponse = (session.get(f"{Base_URL}GetBackboneFeature/{PlasmidParentBackbone}", cookies=django_request.COOKIES)).json()
                if(BackboneFeatureListResponse['success']):
                    backbone_fetch_kmer = KmerIndex()
                    for each_feature in BackboneFeatureListResponse['data']:
                        if(each_feature['feature_start']<each_feature['feature_end']):
                            backbone_fetch_kmer.add_sequence(each_feature["feature_label"],ParentBackboneSequence[each_feature["feature_start"]:each_feature["feature_end"]])
                        else:
                            backbone_fetch_kmer.add_sequence(each_feature["feature_label"],ParentBackboneSequence[each_feature["feature_start"]:]+ParentBackboneSequence[:each_feature["feature_end"]])
                    fetch_result = backbone_fetch_kmer.query(sequence)
                    for each_key in fetch_result.keys():
                        for each_feature in BackboneFeatureListResponse['data']:
                            if(each_feature["feature_label"] == fetch_result[each_key]["seq_id"]):
                                feature_type = each_feature["feature_type"]
                                break
                        new_feature = {fetch_result[each_key]["seq_id"]:[fetch_result[each_key]["start"],fetch_result[each_key]['end'],feature_type]}
                        sa.add_feature(new_feature)
                else:
                    fi = featureIdentify()
                    feature_list = fi.featureMatch(sequence)
                    reverse_feature_list = fi.featureMatch(seq_reverse)
                    sa.add_features(feature_list)
                    sa.add_reverse_features(reverse_feature_list)
        PlasmidParentPartResponse = (session.get(f"{Base_URL}GetPartParent?plasmidid={plasmid_id}",cookies=django_request.COOKIES)).json()
        Part_fetch_kmer = KmerIndex()
        if(PlasmidParentPartResponse['success']):
            PlasmidParentPart = PlasmidParentPartResponse['data']
            for each_part in PlasmidParentPart:
                partSeqResponse = (session.get(f"{Base_URL}GetPartSeqByID?partid={each_part['partid']}",cookies=django_request.COOKIES)).json()
                if(partSeqResponse['success']):
                    partSeq = partSeqResponse['data']['level0sequence']
                    Part_fetch_kmer.add_sequence(each_part['name'],partSeq)
            fetch_result = Part_fetch_kmer.query(sequence)
            for each_key in fetch_result:
                typeResponse = (session.get(f"{Base_URL}TypeByName?name={each_key}",cookies=django_request.COOKIES))
                if(typeResponse.status_code == 200):
                    feature_type = typeResponse.json()['Type'].lower()
                    new_feature = {each_key:[fetch_result[each_key]['start'],fetch_result[each_key]['end'],feature_type]}
                    sa.add_feature(new_feature)
        PlasmidParentPlasmidResponse = (session.get(f"{Base_URL}GetPlasmidParent?plasmidid={plasmid_id}",cookies=django_request.COOKIES)).json()
        plasmid_fetch_kmer = KmerIndex()
        if(PlasmidParentPlasmidResponse['success']):
            PlasmidParentPlasmid = PlasmidParentPlasmidResponse['data']
            ParentPartList = getplasmidAllParentPart(django_request,session,PlasmidParentPlasmid)
            for each_part in ParentPartList.keys():
                plasmid_fetch_kmer.add_sequence(each_part,ParentPartList[each_part])
            fetch_result = plasmid_fetch_kmer.query(sequence)
            for each_key in fetch_result.keys():
                typeResponse = (session.get(f"{Base_URL}TypeByName?name={each_key}",cookies=django_request.COOKIES))
                if(typeResponse.status_code == 200):
                    feature_type = typeResponse.json()['Type'].lower()
                    new_feature = {each_key:[fetch_result[each_key]["start"],fetch_result[each_key]["end"],feature_type]}
                    sa.add_feature(new_feature)
        if(PlasmidParentBackboneResponse["success"] == False or PlasmidParentPlasmidResponse["success"] == False):
            fi = featureIdentify()
            feature_list = fi.featureMatch(sequence)
            reverse_feature_list = fi.featureMatch(seq_reverse)
            sa.add_features(feature_list)
            sa.add_reverse_features(reverse_feature_list)
        sa.GenerateGBKFile(ASSEMBLY_DIR)
    except LabDatabaseException as exc:
        raise exc
    except Exception as exc:
        raise exc


def _run_assembly_simulation(file_address_list, file_name_list, assembly_name, task_output_dir, task_id,enzyme):
    try:
        cache_obj = cache.get(f'{TASK_STATUS_PREFIX}{task_id}')
        cache_obj.setStatus("processing")
        cache_obj.setProgress(50)
        # task_status = cache.get(f'{TASK_STATUS_PREFIX}{task_id}')
        # task_status["status"] = "processing"
        # task_status['progress'] = 50
        # cache.set(f"{TASK_STATUS_PREFIX}{task_id}",task_status)
        GG = SupportGG.SupportGG(file_address_list,file_name_list)
        GG.assemblyPart(assembly_name,enzyme)
        GG.show(output_dir=task_output_dir)
        print("end _run_assembly_simulation")
    except LabDatabaseException as exc:
        raise exc
        # cache_obj.setStatus("failed")
        # cache_obj.setMessage(exc.message)
        # cache.set(f"{TASK_STATUS_PREFIX}{task_id}",cache_obj)
    except Exception as exc:
        raise exc
        # cache_obj.setStatus("failed")
        # cache_obj.setMessage(str(exc))
        # cache.set(f"{TASK_STATUS_PREFIX}{task_id}",cache_obj)

def _finalize_assembly_result(django_request, task_id, assembly_result_file, final_name, part, backbone, plasmid,output_dir, alias="", Note="", Level=None, publish_task_result=True):
    try:
        max_wait_time = 20
        start_time = time.time()
        while time.time() - start_time < max_wait_time:
            if(os.path.exists(assembly_result_file)):
                print("exists file")
                records = parse(assembly_result_file, "genbank")
                for record in records:
                    Sequence = str(record.seq)
                response = AssemblyResultUpload(django_request, final_name[:20], Sequence, part, backbone, plasmid, alias, Note, Level)
                if(response["success"]):
                    copy_address = os.path.join(ASSEMBLY_DIR,f"{final_name}.gbk")
                    shutil.copy(os.path.join(output_dir,f"{final_name}.gb"),copy_address)
                    if publish_task_result:
                        cache_obj = cache.get(f"{TASK_STATUS_PREFIX}{task_id}")
                        cache_obj.setStatus("completed")
                        cache_obj.setProgress(100)
                        cache_obj.setResult(_build_task_result_payload(task_id, final_name))
                        cache_obj.setMessage("组装完成")
                        cache.set(f"{TASK_STATUS_PREFIX}{task_id}",cache_obj)
                    
                    # task_status = cache.get(f'{TASK_STATUS_PREFIX}{task_id}')
                    # task_status["status"] = "completed"
                    # task_status['progress'] = 100
                    # task_status["result"] = {
                    #     "task_id": task_id,
                    #     "file_name": final_name,
                    #     "file_path": assembly_result_file,
                    #     "download_url": f"/LabDatabase/getAssembly/{final_name}?task_id={task_id}",
                    # }
                    # cache.set(f"{TASK_STATUS_PREFIX}{task_id}",task_status)
                    
                    return True
                else:
                    cache_obj = cache.get(f"{TASK_STATUS_PREFIX}{task_id}")
                    cache_obj.setStatus("failed")
                    cache_obj.setProgress(100)
                    cache_obj.setMessage(response.json()["message"])
                    cache.set(f"{TASK_STATUS_PREFIX}{task_id}",cache_obj)
                # task_status = cache.get(f'{TASK_STATUS_PREFIX}{task_id}')
                # task_status["status"] = "failed"
                # task_status['progress'] = 100
                # task_status["result"] = None
                # task_status["error"] = response.get("message", "组装结果上传失败")
                # cache.set(f"{TASK_STATUS_PREFIX}{task_id}",task_status)
                    return False
            time.sleep(0.5)
        cache_obj = cache.get(f"{TASK_STATUS_PREFIX}{task_id}")
        cache_obj.setStatus("failed")
        cache_obj.setProgress(100)
        cache_obj.setMessage("组装scar错误")
        cache.set(f"{TASK_STATUS_PREFIX}{task_id}",cache_obj)
        # task_status = cache.get(f'{TASK_STATUS_PREFIX}{task_id}')
        # task_status["status"] = "failed"
        # task_status['progress'] = 100
        # task_status["result"] = None
        # task_status["error"] = "组装失败"
        # cache.set(f"{TASK_STATUS_PREFIX}{task_id}",cache_obj)
        return False
    except LabDatabaseException as exc:
        cache_obj = cache.get(f"{TASK_STATUS_PREFIX}{task_id}")
        cache_obj.setStatus("failed")
        cache_obj.setProgress(100)
        cache_obj.setMessage(exc.message)
        cache.set(f"{TASK_STATUS_PREFIX}{task_id}",cache_obj)
        return False
    except Exception as exc:
        cache_obj = cache.get(f"{TASK_STATUS_PREFIX}{task_id}")
        cache_obj.setStatus("failed")
        cache_obj.setProgress(100)
        cache_obj.setMessage(str(exc))
        cache.set(f"{TASK_STATUS_PREFIX}{task_id}",cache_obj)
        return False



def AssemblyRepo(request):
    try:
        if(request.method == "POST"):
            data = json.loads(request.body)
            repositoryName = data['repositoryName']
            if(repositoryName == ""):
                raise LabDatabaseException(message = f"参数{repositoryName}不能为空")
            task_id = str(uuid.uuid4())
            # task_status = {
            #     'status':'processing',
            #     'progress':0,
            #     'result':None,
            #     'error':None,
            # }
            cache_obj = CacheClass("processing",0)
            cache.set(f'{TASK_STATUS_PREFIX}{task_id}',cache_obj,timeout=100000)
            thread = threading.Thread(
                target=process_assembly_repo_async,
                args=(repositoryName,request,task_id)
            )
            thread.daemon = False
            thread.start()
            return JsonResponse({"task_id":task_id,'status':'processing','message':"正在组装..."},status=200,safe=False)
        else:
            return LabDatabasePOSTMethodException()
    except LabDatabaseException as exc:
        return exc.to_response()
    except Exception as exc:
        return JsonResponse({"success":False,"message":str(exc)},status=400)


    
def _assemble_repository(repositoryName, django_request, task_id,publish=True):
    
    session = _create_api_session()
    task_output_dir = _ensure_task_assembly_output_dir(task_id, repositoryName)
    assembly_result_file = os.path.join(task_output_dir, f"{repositoryName}.gb")
    request_body = {"Name": repositoryName}
    repository_response = session.post(f"{Base_URL}getrepo", json=request_body, cookies=django_request.COOKIES)

    if repository_response.json()["success"] == False:
        raise LabDatabaseException(message=f"仓库:{repositoryName} 不存在")

    repository_payload = repository_response.json()
    repository_data = repository_payload["data"]
    part = repository_data["parts"]
    backbone = repository_data["backbones"]
    plasmid = repository_data["plasmids"]
    Level = repository_payload.get("level", repository_data.get("level"))
    Note = repository_payload.get("note", repository_data.get("note"))
    repo_alias = repository_payload.get("alias", repository_data.get("alias"))
    part_start_scar = repository_data.get("part_start_scar",[])
    part_end_scar = repository_data.get("part_end_scar",[])
    
    
    file_address_list = []
    file_name_list = []
    target_enzyme = ""
    for each_backbone in backbone:
        backboneName = (session.get(f"{Base_URL}BackboneNameByID?ID={each_backbone}", cookies=django_request.COOKIES)).json()["BackboneName"]
        sequence = (session.get(f"{Base_URL}GetBackboneSeqByID?backboneid={each_backbone}", cookies=django_request.COOKIES)).json()["data"]["sequence"].lower()
        if len(sequence) == 0:
            raise LabDatabaseException(message=f"Backbone:{backboneName} 序列信息缺失，请补充序列后重新组装")
        target_enzyme = _determine_target_enzyme(sequence)
        alias = (session.get(f"{Base_URL}BackboneAliasByID?ID={each_backbone}", cookies=django_request.COOKIES)).json()["BackboneAlias"]
        backbone_file_name = _assembly_file_basename(f"backbone-{each_backbone}-{backboneName}-{alias}")
        backbone_file_path = _assembly_file_path(backbone_file_name)
        if os.path.exists(backbone_file_path):
            file_address_list.append(backbone_file_path)
            file_name_list.append(backbone_file_name)
        else:
            backboneFeature = (session.get(f"{Base_URL}GetBackboneFeature/{each_backbone}", cookies=django_request.COOKIES)).json()
            if backboneFeature["success"] != True:
                seq_obj = Seq(sequence)
                seq_reverse = str(seq_obj.reverse_complement())
                fi = featureIdentify()
                feature_list = fi.featureMatch(sequence)
                reverse_feature_list = fi.featureMatch(seq_reverse)
                scar_list = scarPosition(sequence)
                sa = SequenceAnnotator(sequence, feature_list, reverse_feature_list, scar_list, name=backbone_file_name)
                sa.GenerateGBKFile(ASSEMBLY_DIR)
            else:
                SequenceAnnotator.GeneratorBackboneNoSa(backbone_file_name, sequence, ASSEMBLY_DIR, backboneFeature["data"])
            file_address_list.append(backbone_file_path)
            file_name_list.append(backbone_file_name)
    part_index = 0
    for each_part in part:
        alias = (session.get(f"{Base_URL}PartAliasByID?ID={each_part}", cookies=django_request.COOKIES)).json()["PartAlias"]
        partName = (session.get(f"{Base_URL}PartNameByID?ID={each_part}", cookies=django_request.COOKIES)).json()["PartName"]
        partType = (session.get(f"{Base_URL}TypeByID?ID={each_part}", cookies=django_request.COOKIES)).json()["Type"].lower()
        part_feature_response = (session.get(f"{Base_URL}GetPartFeature/{each_part}", cookies=django_request.COOKIES)).json()
        sequence = (session.get(f"{Base_URL}GetPartSeqByID?partid={each_part}", cookies=django_request.COOKIES)).json()["data"]["level0sequence"].lower()
        print(len(sequence))
        if len(sequence) == 0:
            raise LabDatabaseException(message=f"Part:{partName} 序列信息缺失，请补充序列后重新组装")
        partSource = (session.get(f"{Base_URL}partSource/{each_part}", cookies=django_request.COOKIES)).json()
        if partSource["success"] != True:
            raise LabDatabaseException(message=f"Part:{partName} 来源物种信息缺失，请补充信息后重新组装")
        try:
            partAlias = (session.get(f"{Base_URL}PartAliasByID?ID={each_part}", cookies=django_request.COOKIES)).json()["PartAlias"]
        except Exception:
            partAlias = ""
        # part_start_scar = ""
        # part_end_scar = ""
        # part_start_scar = repository_payload.get("part_start_scar") if repository_payload.get("part_start_scar") != None else ""
        # part_end_scar = repository_payload.get("part_end_scar") if repository_payload.get("part_end_scar") != None else ""
        # sequence = __process_part_sequence(sequence, partType, target_enzyme, partSource, partAlias, partName, part_start_scar, part_end_scar)
        if(partSource["source"] != None):
            if(len(part_start_scar) == 0 and len(part_end_scar) == 0):
                sequence = __process_part_sequence(sequence,partType,target_enzyme,partSource,partAlias,partName)
            else:
                if(len(part_start_scar) != 0 and len(part_end_scar) != 0):
                    the_part_start_scar = part_start_scar[part_index]
                    the_part_end_scar = part_end_scar[part_index]
                    sequence = __process_part_sequence(sequence,partType,target_enzyme,partSource,partAlias,partName,part_start_scar=the_part_start_scar,part_end_scar=the_part_end_scar)
                elif(len(part_start_scar) != 0):
                    sequence = __process_part_sequence(sequence,partType,target_enzyme,partSource,partAlias,partName,part_start_scar=part_start_scar[part_index])
                elif(len(part_end_scar) !=0):
                    sequence = __process_part_sequence(sequence,partType,target_enzyme,partSource,partAlias,partName,part_end_scar=part_end_scar[part_index])
            # sequence = __process_part_sequence(sequence,partType,target_enzyme,partSource,partAlias,partName)
        else:
            raise LabDatabaseException(message=f"元件 {partName} 来源物种未知，补充信息后再次组装本仓库")
        part_file_name = _assembly_file_basename(f"part-{partType}-{partName}-{each_part}-{alias}")
        part_file_path = _assembly_file_path(part_file_name)
        print(f"part_file_path{part_file_path}")
        if part_feature_response["success"]:
            SequenceAnnotator.GeneratorPartNoSa(part_file_name, sequence, ASSEMBLY_DIR, part_feature_response["data"], target_enzyme.upper())
        else:
            feature_list = {}
            reverse_feature_list = {}
            scar_list = scarPosition(sequence)
            sa = SequenceAnnotator(sequence, feature_list, reverse_feature_list, scar_list, name=part_file_name)
            sa.GenerateGBKFile(ASSEMBLY_DIR)
        file_address_list.append(part_file_path)
        file_name_list.append(part_file_name)
        part_index += 1

    for each_plasmid in plasmid:
        plasmidName = (session.get(f"{Base_URL}PlasmidNameByID?ID={each_plasmid}", cookies=django_request.COOKIES)).json()["PlasmidName"]
        alias = (session.get(f"{Base_URL}PlasmidAliasByID?ID={each_plasmid}", cookies=django_request.COOKIES)).json()["PlasmidAlias"]
        if os.path.exists(os.path.join(ASSEMBLY_DIR, f"{plasmidName}.gbk")):
            file_address_list.append(os.path.join(ASSEMBLY_DIR, f"{plasmidName}.gbk"))
            file_name_list.append(plasmidName)
        elif os.path.exists(os.path.join(ASSEMBLY_DIR, f"plasmid-{each_plasmid}-{plasmidName}-{alias}.gbk")):
            file_address_list.append(os.path.join(ASSEMBLY_DIR, f"plasmid-{each_plasmid}-{plasmidName}-{alias}.gbk"))
            file_name_list.append(f"plasmid-{each_plasmid}-{plasmidName}-{alias}")
        else:
            sequence = (session.get(f"{Base_URL}PlasmidSeqByID?plasmidid={each_plasmid}", cookies=django_request.COOKIES)).json()["data"]["sequenceconfirm"].lower()
            if len(sequence) == 0 or sequence == "":
                raise LabDatabaseException(message=f"plasmid:{plasmidName} 序列信息缺失，请补充序列后重新组装")
            plasmid_feature_response = (session.get(f"{Base_URL}GetPlasmidFeature/{each_plasmid}", cookies=django_request.COOKIES)).json()
            if plasmid_feature_response["success"]:
                SequenceAnnotator.GeneratorBackboneNoSa(f"plasmid-{each_plasmid}-{plasmidName}-{alias}", sequence, ASSEMBLY_DIR, plasmid_feature_response["data"])
            else:
                _generate_plasmid_map_from_parents(
                    session,
                    django_request,
                    each_plasmid,
                    sequence,
                    f"plasmid-{each_plasmid}-{plasmidName}-{alias}"
                )
            file_address_list.append(os.path.join(ASSEMBLY_DIR, f"plasmid-{each_plasmid}-{plasmidName}-{alias}.gbk"))
            file_name_list.append(f"plasmid-{each_plasmid}-{plasmidName}-{alias}")
    # print("befor _run_assembly_simulation")
    try:
        _run_assembly_simulation(file_address_list, file_name_list, repositoryName, task_output_dir, task_id, target_enzyme)
        _finalize_assembly_result(
        django_request,
        task_id,
        assembly_result_file,
        repositoryName,
        part,
        backbone,
        plasmid,
        task_output_dir,
        repo_alias,
        Note,
        Level,
        publish_task_result=publish,
        )
    except Exception as exc:
        raise exc

#循环组装调用
def process_assembly_repo(repositoryName, django_request,task_id):
    cache_obj = cache.get(f"{TASK_STATUS_PREFIX}{task_id}")
    try:
        _assemble_repository(repositoryName, django_request, task_id,publish=False)
    except LabDatabaseException as exc:
        raise exc
        # print(exc.message)
        # cache_obj.setStatus("failed")
        # cache_obj.setMessage(exc.message)
        # cache.set(f"{TASK_STATUS_PREFIX}{task_id}",cache_obj)
    except Exception as exc:
        raise exc
        # print(str(exc))
        # cache_obj.setStatus("failed")
        # cache_obj.setMessage(str(exc))
        # cache.set(f"{TASK_STATUS_PREFIX}{task_id}",cache_obj)

#单个调用
def process_assembly_repo_async(repositoryName, django_request,task_id):
    try:
        _assemble_repository(repositoryName, django_request, task_id,publish=True)
    except LabDatabaseException as exc:
        cache_obj = cache.get(f"{TASK_STATUS_PREFIX}{task_id}")
        cache_obj.setStatus("failed")
        cache_obj.setProgress(100)
        cache_obj.setMessage(exc.message)
        cache.set(f"{TASK_STATUS_PREFIX}{task_id}",cache_obj)
    except Exception as exc:
        cache_obj = cache.get(f"{TASK_STATUS_PREFIX}{task_id}")
        cache_obj.setStatus("failed")
        cache_obj.setProgress(100)
        cache_obj.setMessage(str(exc))
        cache.set(f"{TASK_STATUS_PREFIX}{task_id}",cache_obj)
                        
def AssemblyWithoutRepo(request):
    try:
        if(request.method == "POST"):
            data = json.loads(request.body)
            plan_name = data.get('uuid')
            partList = data.get('part')
            backboneList = data.get('backbone')
            plasmidList = data.get('plasmid')
            task_id = str(uuid.uuid4())
            cache_obj = CacheClass("processing",0)
            # cache_obj = CacheClass("processing",0)
            # cache.set(f'{TASK_STATUS_PREFIX}{task_id}',cache_obj,timeout=100000)
            # task_status = {
            #     'status':'processing',
            #     'progress':0,
            #     'result':None,
            #     'error':None,
            # }
            cache.set(f'{TASK_STATUS_PREFIX}{task_id}',cache_obj,timeout=100000)
            thread = threading.Thread(
                target=process_assembly_without_repo,
                args=(partList, backboneList, plasmidList,request,task_id,plan_name)
            )
            thread.daemon = False
            thread.start()
            return JsonResponse({"task_id":task_id,'status':'processing','message':"正在组装..."},status=200,safe=False)
        else:
            raise LabDatabasePOSTMethodException()
            # return JsonResponse({'success':False,'message':'Just POST Method'},status = 405, safe = False)
    except LabDatabaseException as exc:
        return exc.to_response()
    except Exception as exc:
        return JsonResponse({"success":False,"message":str(exc)},status=400)

def process_assembly_without_repo(partList, backboneList, plasmidList, django_request,task_id,plan_name):
    try:
        session = _create_api_session()
        task_output_dir = _ensure_task_output_dir(task_id)
        assembly_result_file = _get_task_assembly_file(task_id, plan_name)
        file_address_list = []
        file_name_list = []
        part = []
        backbone = []
        plasmid = []
        target_enzyme = ""
        for each_backbone in backboneList:
            backbone_id = (session.get(f'{Base_URL}BackboneID?name={each_backbone}',cookies=django_request.COOKIES)).json()["BackboneID"]
            backbone.append(backbone_id)
            sequence = (session.get(f'{Base_URL}GetBackboneSeqByID?backboneid={backbone_id}',cookies = django_request.COOKIES)).json()['data']['sequence'].lower()
            backboneFeature = (session.get(f"{Base_URL}GetBackboneFeature/{backbone_id}",cookies=django_request.COOKIES)).json()
            
            target_enzyme = _determine_target_enzyme(sequence)
            # print(f"target:{target_enzyme}")
            alias = (session.get(f"{Base_URL}BackboneAliasByID?ID={backbone_id}",cookies=django_request.COOKIES)).json()['BackboneAlias']
            backbone_file_name = _assembly_file_basename(f"backbone-{backbone_id}-{each_backbone}-{alias}")
            if(os.path.exists(os.path.join(ASSEMBLY_DIR,f"backbone-{each_backbone}.gbk"))):
                file_address_list.append(os.path.join(ASSEMBLY_DIR,f"backbone-{each_backbone}.gbk"))
                file_name_list.append(f"backbone-{each_backbone}")
            elif(os.path.exists(os.path.join(ASSEMBLY_DIR,f"backbone-{backbone_id}-{each_backbone}-{alias}.gbk"))):
                file_address_list.append(os.path.join(ASSEMBLY_DIR,f"backbone-{backbone_id}-{each_backbone}-{alias}.gbk"))
                file_name_list.append(f"backbone-{backbone_id}-{each_backbone}-{alias}")
            else:
                if(backboneFeature["success"] != True):
                    seq_obj = Seq(sequence)
                    seq_reverse = str(seq_obj.reverse_complement())
                    fi = featureIdentify()
                    feature_list = fi.featureMatch(sequence)
                    reverse_feature_list = fi.featureMatch(seq_reverse)
                    scar_list = scarPosition(sequence)
                    sa = SequenceAnnotator(sequence,feature_list,reverse_feature_list,scar_list,name=backbone_file_name)
                    sa.GenerateGBKFile(ASSEMBLY_DIR)
                else:
                    SequenceAnnotator.GeneratorBackboneNoSa(backbone_file_name,sequence,ASSEMBLY_DIR,backboneFeature['data'])
                file_address_list.append(_assembly_file_path(backbone_file_name))
                file_name_list.append(backbone_file_name)
                
        for each_part in partList:
            part.append(each_part)
            part_name = (session.get(f"{Base_URL}PartNameByID?ID={each_part}",cookies=django_request.COOKIES)).json()["PartName"]
            partType = (session.get(f"{Base_URL}TypeByID?ID={each_part}", cookies=django_request.COOKIES)).json()['Type'].lower()
            try:
                partAlias = (session.get(f"{Base_URL}PartAliasByID?ID={each_part}",cookies=django_request.COOKIES)).json()["PartAlias"]
            except Exception as e:
                partAlias = ""
            if(os.path.exists(os.path.join(ASSEMBLY_DIR,f"part-{partType}-{part_name}.gbk"))):
                file_address_list.append(os.path.join(ASSEMBLY_DIR,f"part-{partType}-{part_name}.gbk"))
                file_name_list.append(f"part-{partType}-{part_name}")
            elif(os.path.exists(os.path.join(ASSEMBLY_DIR,f"{part_name}.gbk"))):
                file_address_list.append(os.path.join(ASSEMBLY_DIR,f"{part_name}.gbk"))
                file_name_list.append(f"{part_name}")
            elif(os.path.exists(os.path.join(ASSEMBLY_DIR,f"part-{each_part}-{partType}-{part_name}-{partAlias}.gbk"))):
                file_address_list.append(os.path.join(ASSEMBLY_DIR,f"part-{each_part}-{partType}-{part_name}-{partAlias}.gbk"))
                file_name_list.append(f"part-{each_part}-{partType}-{part_name}-{partAlias}")
            # print(each_part)
            else:
                sequence_response = (session.get(f'{Base_URL}GetPartSeqByID?partid={each_part}',cookies = django_request.COOKIES)).json()
                # print(sequence_response)
                sequence = sequence_response['data']['level0sequence'].lower()
                part_feature_response = (session.get(f'{Base_URL}GetPartFeature/{each_part}',cookies=django_request.COOKIES)).json()
                print(part_feature_response)
                partSource = (session.get(f"{Base_URL}partSource/{each_part}",cookies=django_request.COOKIES)).json()
                if(partSource['success'] != True):
                    raise LabDatabaseException(message=f"元件 {part_name} 来源物种未知，补充信息后再次组装本仓库")
                # print(partType)
                if(partSource["source"] != None):
                    sequence = __process_part_sequence(sequence,partType,target_enzyme,partSource,partAlias,part_name)
                else:
                    raise LabDatabaseException(message=f"元件 {part_name} 来源物种未知，补充信息后再次组装本仓库")

                part_file_name = _assembly_file_basename(f"part-{each_part}-{partType}-{part_name}-{alias}")
                if(part_feature_response["success"]):
                    SequenceAnnotator.GeneratorPartNoSa(part_file_name,sequence,ASSEMBLY_DIR,part_feature_response["data"],target_enzyme.upper())
                else:
                    
                    seq_obj = Seq(sequence)
                    seq_reverse = str(seq_obj.reverse_complement())
                    # fi = featureIdentify()
                    # feature_list = fi.featureMatch(sequence)
                    # reverse_feature_list = fi.featureMatch(seq_reverse)
                    feature_list = {}
                    reverse_feature_list = {}
                    scar_list = scarPosition(sequence)
                    sa = SequenceAnnotator(sequence,feature_list,reverse_feature_list,scar_list,name=part_file_name)

                    sa.GenerateGBKFile(ASSEMBLY_DIR)
                file_address_list.append(_assembly_file_path(part_file_name))
                file_name_list.append(part_file_name)
        for each_plasmid in plasmidList:
            plasmidID = (session.get(f"{Base_URL}PlasmidID?name={each_plasmid[:20]}",cookies=django_request.COOKIES)).json()['PlasmidID']
            plasmid.append(plasmidID)
            alias = (session.get(f"{Base_URL}PlasmidAliasByID?ID={plasmidID}",cookies=django_request.COOKIES)).json()["PlasmidAlias"]
            if(os.path.exists(os.path.join(ASSEMBLY_DIR,f"{each_plasmid[:20]}.gbk"))):
                file_address_list.append(os.path.join(ASSEMBLY_DIR,f"{each_plasmid[:20]}.gbk"))
                file_name_list.append(each_plasmid[:20])
            elif(os.path.exists(os.path.join(ASSEMBLY_DIR,f"plasmid-{each_plasmid[:20]}.gbk"))):
                file_address_list.append(os.path.join(ASSEMBLY_DIR,f"plasmid-{each_plasmid[:20]}.gbk"))
                file_name_list.append(f"plasmid-{each_plasmid[:20]}")
            elif(os.path.exists(os.path.join(ASSEMBLY_DIR,f"plasmid-{plasmidID}-{each_plasmid[:20]}-{alias}.gbk"))):
                file_address_list.append(os.path.join(ASSEMBLY_DIR,f"plasmid-{plasmidID}-{each_plasmid[:20]}-{alias}.gbk"))
                file_name_list.append(f"plasmid-{plasmidID}-{each_plasmid[:20]}-{alias}")
            else:
                sequence = (session.get(f'{Base_URL}PlasmidSeqByID?plasmidid={plasmidID}',cookies = django_request.COOKIES)).json()['data']['sequenceconfirm'].lower()
                _generate_plasmid_map_from_parents(
                    session,
                    django_request,
                    plasmidID,
                    sequence,
                    f"plasmid-{plasmidID}-{each_plasmid[:20]}-{alias}"
                )
                file_address_list.append(os.path.join(ASSEMBLY_DIR,f"plasmid-{plasmidID}-{each_plasmid[:20]}-{alias}.gbk"))
                file_name_list.append(f"plasmid-{plasmidID}-{each_plasmid[:20]}-{alias}")
        print(file_address_list)
        try:
            _run_assembly_simulation(file_address_list, file_name_list, plan_name, task_output_dir, task_id,target_enzyme)
        except Exception as e:
            raise LabDatabaseException(message=f"组装过程中出错：{str(e)}")
            # task_status = cache.get(f'{TASK_STATUS_PREFIX}{task_id}')
            # task_status["status"] = "failed"
            # task_status["error"] = ("PermissionError: filename=%s, errno=%s, strerror=%s",getattr(e, "filename", None), e.errno, e.strerror)
            # cache.set(f"{TASK_STATUS_PREFIX}{task_id}",task_status)
            # return
        _finalize_assembly_result(
            django_request,
            task_id,
            assembly_result_file,
            plan_name,
            part,
            backbone,
            plasmid,
            task_output_dir
        )
    except LabDatabaseException as exc:
        cache_obj = cache.get(f"{TASK_STATUS_PREFIX}{task_id}")
        cache_obj.setStatus("failed")
        cache_obj.setProgress(100)
        cache_obj.setMessage(exc.message)
        cache.set(f"{TASK_STATUS_PREFIX}{task_id}",cache_obj)
    except Exception as exc:
        cache_obj = cache.get(f"{TASK_STATUS_PREFIX}{task_id}")
        cache_obj.setStatus("failed")
        cache_obj.setProgress(100)
        cache_obj.setMessage(str(exc))
        cache.set(f"{TASK_STATUS_PREFIX}{task_id}",cache_obj)
        
        
        
        
def __process_part_sequence(sequence,partType,target_enzyme,partSource,partAlias,partName,part_start_scar="",part_end_scar=""):
    try:
        original_sequence = sequence
        if(target_enzyme != ""):
            if(target_enzyme == "BbsI"):
                if(part_start_scar != "" and part_end_scar != ""):
                    sequence = "GAAGACCT"+part_start_scar+sequence+part_end_scar+"AGGTCTTC"
                else:
                    if "saccharomyces" in partSource['source'].lower():
                        if(partType == "promoter"):
                            sequence = "GAAGACCTGTGC" + sequence + "AATGAGGTCTTC"
                        elif(partType == "terminator"):
                            sequence = "GAAGACCTTAAA" + sequence + "CCTCAGGTCTTC"
                        elif(partType == "cds"):
                            if(sequence[:3] == "atg"):
                                sequence = "GAAGACCTA" + sequence
                            else:
                                sequence = "GAAGACCTAATG" + sequence
                            if(sequence[-3:] == "taa"):
                                sequence = sequence + "AAGGTCTTC"
                            else:
                                sequence = sequence + "TAAAAGGTCTTC"
                    elif "plant" in partSource['source'].lower():
                        if(partType == "promoter"):
                            sequence = "GAAGACCTTTTT" + sequence + "TATTAGGTCTTC"
                        elif(partType == "terminator"):
                            sequence = "GAAGACCTTAAA" + sequence + "CCTCAGGTCTTC"
                        elif(partType == "cds"):
                            if(sequence[:3] == "atg"):
                                sequence = "GAAGACCTA" + sequence
                                # sequence = "GAAGACCTA" + sequence + "TAAAAGGTCTTC"
                            else:
                                sequence = "GAAGACCTAATG" + sequence
                            if(sequence[-3:] == "taa"):
                                sequence = sequence + "AAGGTCTTC"
                            else:
                                sequence = sequence + "TAAAAGGTCTTC"
                                # sequence = "GAAGACCTAATG" + sequence + "TAAAAGGTCTTC"
                        elif(partType == "rbs"):
                                #TODO: 澶勭悊Overlapping鐨勯棶棰?
                            # partAlias = (session.get(f"{Base_URL}PartAliasByID?ID={each_part}",cookies=django_request.COOKIES)).json()["PartAlias"]
                            #鍋囪Lac搴忓垪鍦ㄥ簭鍒椾腑
                            if(("AATTAAATTAATTGTGAGCGGATAACAATT".lower() in sequence) == True):
                                sequence = "GAAGACCTTATT" + sequence
                                if(sequence[-2:] == "aa"):
                                    sequence = sequence + "TGAGGTCTTC"
                                elif(sequence[-1] == "a"):
                                    sequence = sequence + "ATGAGGTCTTC"
                                else:
                                    sequence = sequence + "AATGAGGTCTTC"
                            else:
                                if(sequence[:4] == "tatt"):
                                    sequence = "GAAGACCT" + sequence
                                elif(sequence[:2] == "tt"):
                                    sequence = "GAAGACCTTA" + sequence
                                else:
                                    sequence = "GAAGACCTTATT" + sequence
                                if(sequence[-1] == "a"):
                                    sequence = sequence + "ATGAGGTCTTC"
                                else:
                                    sequence = sequence + "AATGAGGTCTTC"
                        elif(partType == "p+r"):
                                sequence = "GAAGACCTTTTT" + sequence + "AATGAGGTCTTC"
                    else:
                        if(partType == "promoter"):
                            sequence = "GAAGACCTGTGC" + sequence + "ATCAAGGTCTTC"
                        elif(partType == "terminator"):
                            sequence = "GAAGACCTTAAA" + sequence + "CCTCAGGTCTTC"
                        elif(partType == "cds"):
                            if(sequence[:3] == "atg"):
                                sequence = "GAAGACCTA" + sequence
                                # sequence = "GAAGACCTA" + sequence + "TAAAAGGTCTTC"
                            else:
                                sequence = "GAAGACCTAATG" + sequence
                            if(sequence[-3:] == "taa"):
                                sequence = sequence + "AAGGTCTTC"
                            else:
                                sequence = sequence + "TAAAAGGTCTTC"
                                # sequence = "GAAGACCTAATG" + sequence + "TAAAAGGTCTTC"
                        elif(partType == "rbs"):
                                #TODO: 澶勭悊Overlapping鐨勯棶棰?
                            # partAlias = (session.get(f"{Base_URL}PartAliasByID?ID={each_part}",cookies=django_request.COOKIES)).json()["PartAlias"]
                            #鍋囪Lac搴忓垪鍦ㄥ簭鍒椾腑
                            if(("AATTAAATTAATTGTGAGCGGATAACAATT".lower() in sequence) == True):
                                sequence = "GAAGACCTATCA" + sequence
                                if(sequence[-2:] == "aa"):
                                    sequence = sequence + "TGAGGTCTTC"
                                elif(sequence[-1] == "a"):
                                    sequence = sequence + "ATGAGGTCTTC"
                                else:
                                    sequence = sequence + "AATGAGGTCTTC"
                            elif((("BCD" in partName) or ("BCD" in partAlias))):
                                if(sequence[:2] == "ca"):
                                    sequence = "GAAGACCTAT" + sequence
                                elif(sequence[:4] == "atca"):
                                    sequence = "GAAGACCT" + sequence
                                else:
                                    sequence = "GAAGACCTATCA" + sequence
                                if(sequence[-2:] == "aa"):
                                    sequence = sequence + "TGAGGTCTTC"
                                elif(sequence[-1] == "a"):
                                    sequence = sequence + "ATGAGGTCTTC"
                                else:
                                    sequence = sequence + "AATGAGGTCTTC"
                            else:
                                if(sequence[:4] == "atca"):
                                    sequence = "GAAGACCT" + sequence
                                elif(sequence[:2] == "ca"):
                                    sequence = "GAAGACCTAT" + sequence
                                else:
                                    sequence = "GAAGACCTATCA" + sequence
                                if(sequence[-1] == "a"):
                                    sequence = sequence + "ATGAGGTCTTC"
                                else:
                                    sequence = sequence + "AATGAGGTCTTC"
                        elif(partType == "p+r"):
                                sequence = "GAAGACCTGTGC" + sequence + "AATGAGGTCTTC"

            elif(target_enzyme == "BsaI"):
                if(part_start_scar != "" and part_end_scar != ""):
                    sequence = "GGTCTCA"+part_start_scar + sequence + part_end_scar+"AGAGACC"
                else:
                    if "saccharomyces" in partSource['source'].lower():
                        if(partType == "promoter"):
                            sequence = "GGTCTCAGTGC" + sequence + "AATGAGAGACC"
                        elif(partType == "terminator"):
                            sequence = "GGTCTCATAAA" + sequence + "CCTCAGAGACC"
                        elif(partType == "cds"):
                            if(sequence[:3] == "atg"):
                                sequence = "GGTCTCAA" + sequence
                            else:
                                sequence = "GGTCTCAAATG" + sequence
                            if(sequence[-3:] == "taa"):
                                sequence = sequence + "AAGAGACC"
                            else:
                                sequence = sequence + "TAAAAGAGACC"
                    elif "plant" in partSource['source'].lower():
                        if(partType == "promoter"):
                            sequence = "GGTCTCATTTT" + sequence + "TATTAGAGACC"
                        elif(partType == "terminator"):
                            sequence = "GGTCTCATAAA" + sequence + "CCTCAGAGACC"
                        elif(partType == "cds"):
                            if(sequence[:3] == "atg"):
                                sequence = "GGTCTCAA" + sequence
                            else:
                                sequence = "GGTCTCAAATG" + sequence
                            if(sequence[-3:] == "taa"):
                                sequence = sequence + "AAGAGACC"
                            else:
                                sequence = sequence + "TAAAAGAGACC"
                        elif(partType == "rbs"):
                            # partAlias = (session.get(f"{Base_URL}PartAliasByID?ID={each_part}",cookies=django_request.COOKIES)).json()["PartAlias"]
                            if(("AATTAAATTAATTGTGAGCGGATAACAATT".lower() in sequence) == True):
                                sequence = "GGTCTCATATT" + sequence
                                if(sequence[-2:] == "aa"):
                                    sequence = sequence + "TGAGAGACC"
                                elif(sequence[-1] == "a"):
                                    sequence = sequence + "ATGAGAGACC"
                                else:
                                    sequence = sequence + "AATGAGAGACC"
                            else:
                                if(sequence[:4] == "tatt"):
                                    sequence = "GGTCTCA" + sequence
                                elif(sequence[:2] == "tt"):
                                    sequence = "GGTCTCAta" + sequence
                                else:
                                    sequence = "GGTCTCATATT" + sequence
                                if(sequence[-1] == "a"):
                                    sequence = sequence + "ATGAGAGACC"
                                else:
                                    sequence = sequence + "AATGAGAGACC"
                        elif(partType == "p+r"):
                                sequence = "GGTCTCATTTT" + sequence + "AATGAGAGACC"
                    else:
                        if(partType == "promoter"):
                            sequence = "GGTCTCAGTGC" + sequence + "ATCAAGAGACC"
                        elif(partType == "terminator"):
                            sequence = "GGTCTCATAAA" + sequence + "CCTCAGAGACC"
                        elif(partType == "cds"):
                            if(sequence[:3] == "atg"):
                                sequence = "GGTCTCAA" + sequence
                            else:
                                sequence = "GGTCTCAAATG" + sequence
                            if(sequence[-3:] == "taa"):
                                sequence = sequence + "AAGAGACC"
                            else:
                                sequence = sequence + "TAAAAGAGACC"
                        elif(partType == "rbs"):
                            # partAlias = (session.get(f"{Base_URL}PartAliasByID?ID={each_part}",cookies=django_request.COOKIES)).json()["PartAlias"]
                            if(("AATTAAATTAATTGTGAGCGGATAACAATT".lower() in sequence) == True):
                                sequence = "GGTCTCAATCA" + sequence
                                if(sequence[-2:] == "aa"):
                                    sequence = sequence + "TGAGAGACC"
                                elif(sequence[-1] == "a"):
                                    sequence = sequence + "ATGAGAGACC"
                                else:
                                    sequence = sequence + "AATGAGAGACC"
                            elif((("BCD" in partName) or ("BCD" in partAlias))):
                                if(sequence[:2] == "ca"):
                                    sequence = "GGTCTCAAT" + sequence
                                elif(sequence[:4] == "atca"):
                                    sequence = "GGTCTCA" + sequence
                                else:
                                    sequence = "GGTCTCAATCA" + sequence
                                if(sequence[-2:] == "aa"):
                                    sequence = sequence + "TGAGAGACC"
                                elif(sequence[-1] == "a"):
                                    sequence = sequence + "ATGAGAGACC"
                                else:
                                    sequence = sequence + "AATGAGAGACC"
                            else:
                                if(sequence[:4] == "atca"):
                                    sequence = "GGTCTCA" + sequence
                                elif(sequence[:2] == "ca"):
                                    sequence = "GGTCTCAAT" + sequence
                                else:
                                    sequence = "GGTCTCAATCA" + sequence
                                if(sequence[-1] == "a"):
                                    sequence = sequence + "ATGAGAGACC"
                                else:
                                    sequence = sequence + "AATGAGAGACC"
                        elif(partType == "p+r"):
                                sequence = "GGTCTCAGTGC" + sequence + "AATGAGAGACC"
                    
        else:
            if(part_start_scar != "" and part_end_scar != ""):
                sequence = "GAAGACCT" + part_start_scar + sequence + part_end_scar + "AGGTCTTC"
            else:
                if "saccharomyces" in partSource['source'].lower():
                    if(partType == "promoter"):
                        sequence = "GAAGACCTGTGC" + sequence + "AATGAGGTCTTC"
                    elif(partType == "terminator"):
                        sequence = "GAAGACCTTAAA" + sequence + "CCTCAGGTCTTC"
                    elif(partType == "cds"):
                        if(sequence[:3] == "atg"):
                            sequence = "GAAGACCTA" + sequence
                        else:
                            sequence = "GAAGACCTAATG" + sequence
                        if(sequence[-3:] == "taa"):
                            sequence = sequence + "AAGGTCTTC"
                        else:
                            sequence = sequence + "TAAAAGGTCTTC"
                elif "plant" in partSource['source'].lower():
                    if(partType == "promoter"):
                        sequence = "GAAGACCTTTTT" + sequence + "TATTAGGTCTTC"
                    elif(partType == "terminator"):
                        sequence = "GAAGACCTTAAA" + sequence + "CCTCAGGTCTTC"
                    elif(partType == "cds"):
                        if(sequence[:3] == "atg"):
                            sequence = "GAAGACCTA" + sequence
                        else:
                            sequence = "GAAGACCTAATG" + sequence
                        if sequence[-3:] == "taa":
                            sequence = sequence + "AAGGTCTTC"
                        else:
                            sequence = sequence + "TAAAAGGTCTTC"
                    elif(partType == "rbs"):
                        # partAlias = (session.get(f"{Base_URL}PartAliasByID?ID={each_part}",cookies=django_request.COOKIES)).json()["PartAlias"]
                        if(("AATTAAATTAATTGTGAGCGGATAACAATT".lower() in sequence) == True):
                            sequence = "GAAGACCTTATT" + sequence
                            if(sequence[-2:] == "aa"):
                                sequence = sequence + "TGAGGTCTTC"
                            elif(sequence[-1] == "a"):
                                sequence = sequence + "ATGAGGTCTTC"
                            else:
                                sequence = sequence + "AATGAGGTCTTC"
                        else:
                            if(sequence[:4] == "tatt"):
                                sequence = "GAAGACCT" + sequence
                            elif(sequence[:2] == "tt"):
                                sequence = "GAAGACCTTA" + sequence
                            else:
                                sequence = "GAAGACCTTATT" + sequence
                            if(sequence[-1] == "a"):
                                sequence = sequence + "ATGAGGTCTTC"
                            else:
                                sequence = sequence + "AATGAGGTCTTC"
                    elif(partType == "p+r"):
                        sequence = "GAAGACCTTTTT" + sequence + "AATGAGGTCTTC"
                else:
                    if(partType == "promoter"):
                        sequence = "GAAGACCTGTGC" + sequence + "ATCAAGGTCTTC"
                    elif(partType == "terminator"):
                        sequence = "GAAGACCTTAAA" + sequence + "CCTCAGGTCTTC"
                    elif(partType == "cds"):
                        if(sequence[:3] == "atg"):
                            sequence = "GAAGACCTA" + sequence
                        else:
                            sequence = "GAAGACCTAATG" + sequence
                        if sequence[-3:] == "taa":
                            sequence = sequence + "AAGGTCTTC"
                        else:
                            sequence = sequence + "TAAAAGGTCTTC"
                    elif(partType == "rbs"):
                        # partAlias = (session.get(f"{Base_URL}PartAliasByID?ID={each_part}",cookies=django_request.COOKIES)).json()["PartAlias"]
                        if(("AATTAAATTAATTGTGAGCGGATAACAATT".lower() in sequence) == True):
                            sequence = "GAAGACCTATCA" + sequence
                            if(sequence[-2:] == "aa"):
                                sequence = sequence + "TGAGGTCTTC"
                            elif(sequence[-1] == "a"):
                                sequence = sequence + "ATGAGGTCTTC"
                            else:
                                sequence = sequence + "AATGAGGTCTTC"
                        elif((("BCD" in partName) or ("BCD" in partAlias))):
                            if(sequence[:2] == "ca"):
                                sequence = "GAAGACCTAT" + sequence
                            elif(sequence[:4] == "atca"):
                                sequence = "GAAGACCT" + sequence
                            else:
                                sequence = "GAAGACCTATCA" + sequence
                            if(sequence[-2:] == "aa"):
                                sequence = sequence + "TGAGGTCTTC"
                            elif(sequence[-1] == "a"):
                                sequence = sequence + "ATGAGGTCTTC"
                            else:
                                sequence = sequence + "AATGAGGTCTTC"
                        else:
                            if(sequence[:4] == "atca"):
                                sequence = "GAAGACCT" + sequence
                            elif(sequence[:2] == "ca"):
                                sequence = "GAAGACCTAT" + sequence
                            else:
                                sequence = "GAAGACCTATCA" + sequence
                            if(sequence[-1] == "a"):
                                sequence = sequence + "ATGAGGTCTTC"
                            else:
                                sequence = sequence + "AATGAGGTCTTC"
                    elif(partType == "p+r"):
                        sequence = "GAAGACCTGTGC" + sequence + "AATGAGGTCTTC"
                
        # When only one scar is supplied, keep the sequence originally added by
        # each branch at the other end and replace only the supplied end.
        if((part_start_scar != "") != (part_end_scar != "")):
            if(target_enzyme == "BsaI"):
                enzyme_start = "GGTCTCA"
                enzyme_end = "AGAGACC"
            else:
                enzyme_start = "GAAGACCT"
                enzyme_end = "AGGTCTTC"

            original_sequence_start = sequence.find(original_sequence, len(enzyme_start))
            if(original_sequence_start != -1):
                original_sequence_end = original_sequence_start + len(original_sequence)
                if(part_start_scar != ""):
                    sequence = enzyme_start + part_start_scar + sequence[original_sequence_start:]
                else:
                    sequence = sequence[:original_sequence_end] + part_end_scar + enzyme_end

        return sequence
    except LabDatabaseException as exc:
        raise exc
    except Exception as exc:
        raise exc
    
    


def AssemblyResultUpload(django_request,Name, Sequence, partList, BackboneList, PlasmidList, alias = "", Note = "", Level = None):
    try:
        session = requests.Session()
        token = django_request.COOKIES.get('csrftoken')
        session.headers.update({
            'User-Agent':'Django-App/1.0',
            'Content-Type':'application/json',
            'X-CSRFToken':token,
        })
        if(Level == None):
            if(len(partList) == 1):
                Level = 1
            if(len(PlasmidList) == 3 or len(PlasmidList) == 4):
                Level = 2
            else:
                Level = 3
        # print(f"alias:{alias}")
        print("AssemblyResultUpload")
        data_body = {'name':Name,'alias':alias,'level':Level,'sequence':Sequence,'note':Note,'ParentInfo':""}
        response = session.post(f'{Base_URL}AddPlasmidData',json=data_body,cookies=django_request.COOKIES)
        if(response.json()["success"] == False):
            # print(response.json())
            raise LabDatabaseException(message = "添加质粒数据失败")
        plasmidid = session.get(f'{Base_URL}PlasmidID?name={Name}',cookies=django_request.COOKIES)
        Ori_list = []
        Marker_list = []
        OriAndMarkerLabel = FittingLabels(Sequence)
        for each_ori in OriAndMarkerLabel['Origin']:
            Ori_list.append(each_ori['Name'])
        for each_marker in OriAndMarkerLabel['Marker']:
            Marker_list.append(each_marker['Name'])
        plasmid_culture_body = {"name":Name, "ori":Ori_list,"marker":Marker_list}
        plasmid_culture_response = session.post(f"{Base_URL}setPlasmidCulture",json = plasmid_culture_body, cookies=django_request.COOKIES)
        if(plasmid_culture_response.json()["success"] == False):
            raise LabDatabaseException(message = "添加质粒培养信息失败")
            # return {"success":False, "message":"添加质粒培养信息失败"}
        scar_result_list = scarFunction(Sequence)
        scar_data_body = {'name':Name,'bsmbi':scar_result_list[0],'bsai':scar_result_list[1],'bbsi':scar_result_list[2],'aari':scar_result_list[3],'sapi':scar_result_list[4]}
        scar_response = session.post(f'{Base_URL}setPlasmidScar',json=scar_data_body,cookies=django_request.COOKIES)
        if(scar_response.json()["success"] == False):
            raise LabDatabaseException(message="添加质粒scar信息失败")
            # return {"success":False, "message":"添加质粒Scar失败"}
        delete_parent_info_thread = threading.Thread(target=delete_parent_info, args=(session,plasmidid.json()["PlasmidID"],django_request))
        add_parent_info_thread = threading.Thread(target=add_parent_info,args=(session,django_request,Name,partList,BackboneList,PlasmidList))

        delete_parent_info_thread.start()
        delete_parent_info_thread.join()

        add_parent_info_thread.start()
        add_parent_info_thread.join()
        # delete_parent_info_response = session.get(f"{Base_URL}DeletePlasmidParent")
        # for each_part in partList:
        #     request_body = {"SonPlasmidName":Name,"ParentPartID":each_part}
        #     part_response = session.post(f"{Base_URL}AddPartParentByID",json=request_body,cookies=django_request.COOKIES)
        #     if(part_response.status_code != 200):
        #         return {"success":False,"message":"Parent Part 濞ｈ濮炴径杈Е"}
        # for each_backbone in BackboneList:
        #     request_body = {"SonPlasmidName":Name,"ParentBackboneID":each_backbone}
        #     backbone_response = session.post(f"{Base_URL}AddBackboneParentByID",json=request_body,cookies=django_request.COOKIES)
        #     if(backbone_response.status_code != 200):
        #         return {"success":False,"message":"Parent Backbone 濞ｈ濮炴径杈Е"}
        # for each_plasmid in PlasmidList:
        #     request_body = {"SonPlasmidName":Name,"ParentPlasmidID":each_plasmid}
        #     plasmid_response = session.post(f"{Base_URL}AddPlasmidParentByID",json=request_body,cookies=django_request.COOKIES)
        #     if(plasmid_response.status_code != 200):
        #         return {"success":False,"message":"Parent Plasmid 濞ｈ濮炴径杈Е"}
        return {"success":True}
    except LabDatabaseException as exc:
        return {"success":False,"message":str(exc)}
    except Exception as exc:
        return {"success":False,"message":str(exc)}



def delete_parent_info(session,plasmidid,django_request):
    delete_parent_info_response = session.get(f"{Base_URL}DeletePlasmidParent?plasmidid={plasmidid}",cookies=django_request.COOKIES)



def add_parent_info(session,django_request,Name,partList,BackboneList,PlasmidList):
    for each_part in partList:
        request_body = {"SonPlasmidName":Name,"ParentPartID":each_part}
        part_response = session.post(f"{Base_URL}AddPartParentByID",json=request_body,cookies=django_request.COOKIES)
    for each_backbone in BackboneList:
        request_body = {"SonPlasmidName":Name,"ParentBackboneID":each_backbone}
        backbone_response = session.post(f"{Base_URL}AddBackboneParentByID",json=request_body,cookies=django_request.COOKIES)
    for each_plasmid in PlasmidList:
        request_body = {"SonPlasmidName":Name,"ParentPlasmidID":each_plasmid}
        plasmid_response = session.post(f"{Base_URL}AddPlasmidParentByID",json=request_body,cookies=django_request.COOKIES)


def modify_part(request,partid):
    try:
        session = requests.Session()
        token = request.COOKIES.get('csrftoken')
        session.headers.update({
            'User-Agent':'Django-App/1.0',
            'Content-Type':'application/json',
            'X-CSRFToken':token,
        })

        if(request.method != "POST"):
            if(partid == None or partid == ""):
                raise LabDatabaseException(message=f"参数{partid}不能为空")
                # return JsonResponse({"success":False,"message":"Parameter is empty"},status = 400, safe = False)
            part_obj = (session.get(f"{Base_URL}PartByID?ID={partid}",cookies=request.COOKIES).json())[0]
            return render(request,"PartEdit.html",{"part":part_obj})
        else:
            data = json.loads(request.body)
            if(data['elementType'].lower() == "promoter"):
                type = 1
            elif(data['elementType'].lower() == "rbs"):
                type = 4
            elif(data['elementType'].lower() == "terminator"):
                type = 3
            elif(data['elementType'].lower() == "cds"):
                type = 2
            elif(data['elementType'].lower() == "p+r"):
                type = 5
            request_body = {"PartID":partid,"Name":data['geneName'],"Alias":data['geneAlias'],"Type":type,"Level0Sequence":data['sequence'],
                            "ConfirmedSequence":"","InsertSequence":"","source":data["speciesSource"],"reference":data["references"],
                                "note":data["notes"]}
            part_update_response = (session.post(f'{Base_URL}UpdatePart',json=request_body,cookies=request.COOKIES))
            if(part_update_response.status_code != 200):
                raise LabDatabaseException(message=part_update_response.json()["message"])
                # return JsonResponse({"success":False,"message":part_update_response.json()},status = 400, safe=False)
            else:
                return JsonResponse({"success":True},status=200,safe=False)
    except LabDatabaseException as exc:
        return exc.to_response()
    except Exception as exc:
        return JsonResponse({"success":False,"message":str(exc)},status=400)
        
        
def modify_backbone(request,backboneid):
    try:
        session = requests.Session()
        token = request.COOKIES.get('csrftoken')
        session.headers.update({
            'User-Agent':'Django-App/1.0',
            'Content-Type':'application/json',
            'X-CSRFToken':token,
        })
        if(request.method != "POST"):
            if(backboneid == None or backboneid == ""):
                raise LabDatabaseException(message=f"参数{backboneid}不能为空")
                # return JsonResponse({"success":False,"message":"Parameter cannot be empty"}, status = 400, safe=False)
            Backbone_obj = (session.get(f"{Base_URL}BackboneByID?ID={backboneid}",cookies=request.COOKIES).json())[0]
            backbonescar = session.get(f"{Base_URL}getBackboneScar?id={backboneid}",cookies=request.COOKIES)
            if(backbonescar.json()['success']):
                Backbone_obj['scar_info'] = backbonescar.json()['scar_info'][0]
            return render(request,"BackboneEdit.html",{"backbone":Backbone_obj})
        else:
            data = json.loads(request.body)
            request_body = {"BackboneID":data['vectorId'],"newName":data['vectorName'],"sequence":data['sequence'],"species":data['host'],"copynumber":data['copyNumber'],"note":data['notes'],"alias":data['vectorAlias'],"tag":"abnormal" if (len(data['ori']) > 1 or len(data['marker']) > 1) else "normal"}

            update_backbone_response = session.post(f"{Base_URL}UpdateBackbone",json=request_body,cookies = request.COOKIES)
            update_backbone_culture_response = session.post(f"{Base_URL}setBackboneCulture",json={"id":data["vectorId"],"ori":data['ori'],"marker":data['marker']},cookies=request.COOKIES)
            update_backbone_scar_response = session.post(f"{Base_URL}setBackboneScar",json={"backboneid":data['vectorId'],'bsmbi':data['scarSites']['BsmBI'],'bsai':data['scarSites']['BsaI'],
                                                                                            'bbsi':data['scarSites']['BbsI'],'aari':data['scarSites']['Aari'],'sapi':data['scarSites']['Sapi']},cookies=request.COOKIES)
            if(update_backbone_response.status_code == 200 and update_backbone_culture_response.json()["success"] and update_backbone_scar_response.json()["success"]):
                return JsonResponse({"success":True},status = 200, safe=False)
            else:
                if(update_backbone_response.json()["success"] == False):
                    raise LabDatabaseException(message = "Backbone 数据更新失败")
                if(update_backbone_culture_response.json()["success"] == False):
                    raise LabDatabaseException(message = "Backbone 培养信息更新失败")
                if(update_backbone_scar_response.json()["success"] == False):
                    raise LabDatabaseException(message = "Backbone Scar信息更新失败")
                # return JsonResponse({"success":False,"message":"淇濆瓨澶辫触"},status=400,safe=False)
    except LabDatabaseException as exc:
        return exc.to_response()
    except Exception as exc:
        return JsonResponse({"success":False,"message":str(exc)},status=400)




def modify_plasmid(request,plasmidid):
    try:
        session = requests.Session()
        token = request.COOKIES.get('csrftoken')
        session.headers.update({
            'User-Agent':'Django-App/1.0',
            'Content-Type':'application/json',
            'X-CSRFToken':token,
        })
        if(request.method != "POST"):
            if(plasmidid == None or plasmidid == ""):
                return JsonResponse({"success":False,"message":"Parameter cannot be empty"}, status = 400, safe=False)
            Plasmid_obj = (session.get(f"{Base_URL}PlasmidByID?ID={plasmidid}",cookies=request.COOKIES).json())[0]
            plasmidscar = session.get(f"{Base_URL}getPlasmidScar?plasmidid={plasmidid}",cookies=request.COOKIES)
            if(plasmidscar.json()['success']):
                Plasmid_obj['scar_info'] = plasmidscar.json()['scar_info'][0]
            else:
                raise LabDatabaseException(message = "Plasmid 数据获取失败")
            plasmidParentPart = session.get(f'{Base_URL}GetPartParent?plasmidid={plasmidid}',cookies=request.COOKIES)

            plasmidParentBackbone = session.get(f'{Base_URL}GetBackboneParent?plasmidid={plasmidid}',cookies=request.COOKIES)

            plasmidParentPlasmid = session.get(f'{Base_URL}GetPlasmidParent?plasmidid={plasmidid}',cookies=request.COOKIES)

            result = {
                        'Part':[],
                        "Backbone":[],
                        "Plasmid":[],
                    }
            if(plasmidParentPart.status_code == 200 and "data" in plasmidParentPart.json()):
                for each_Part in plasmidParentPart.json()['data']:
                    result['Part'].append(each_Part["name"])
            if(plasmidParentBackbone.status_code == 200 and "data" in plasmidParentBackbone.json()):
                for each_Backbone in plasmidParentBackbone.json()['data']:
                    result['Backbone'].append(each_Backbone["name"])
            if(plasmidParentPlasmid.status_code == 200 and "data" in plasmidParentPlasmid.json()):
                for each_Plasmid in plasmidParentPlasmid.json()['data']:
                    result['Plasmid'].append(each_Plasmid["name"])
            if(Plasmid_obj['customparentinformation'] != "" and Plasmid_obj['customparentinformation']!= None and Plasmid_obj['customparentinformation'] != 'None' and Plasmid_obj['customparentinformation'] != 'NULL' and Plasmid_obj['customparentinformation'] != 'nan'):
                plasmidParentInfo = Plasmid_obj['customparentinformation']
                pattern = r'(\w+)\(([ a-zA-z0-9]+)\)'
                matches = re.findall(pattern, plasmidParentInfo)
                for component_type, letter in matches:
                    if(component_type == "Part"):
                        result['Part'].append(letter)
                    elif(component_type == "Backbone"):
                        result['Backbone'].append(letter)
                    elif(component_type == "Plasmid"):
                        result['Plasmid'].append(letter)
            return render(request,'PlasmidEdit.html',{'plasmid':Plasmid_obj,'partparent':result['Part'],'backboneparent':result['Backbone'],
                                        'plasmidparent':result['Plasmid']})
        else:
            data = json.loads(request.body)
            # UpdatePlasmid
            request_body = {"id":data['plasmidId'],"newName":data['plasmidName'],"newAlias":data["plasmidAlias"],"newLevel":data['level'],"newSequence":data['sequence'],"newOri":data['ori'],"newMarker":data['marker'],"newNote":data['notes'],"tag":"abnormal" if (len(data['ori']) > 1 or len(data['marker']) > 1) else "normal"}

            update_plasmid_response = session.post(f"{Base_URL}UpdatePlasmid",json=request_body,cookies=request.COOKIES)
        
        
        
            update_plasmid_scar_response = session.post(f"{Base_URL}setPlasmidScar",json={"plasmidid":plasmidid,'bsmbi':data['scarSites']['BsmBI'],'bsai':data['scarSites']['BsaI'],
                                                                                            'bbsi':data['scarSites']['BbsI'],'aari':data['scarSites']['Aari'],'sapi':data['scarSites']['Sapi']},cookies=request.COOKIES)
        
            delete_parent = session.get(f"{Base_URL}DeletePlasmidParent?plasmidid={plasmidid}",cookies=request.COOKIES)
            # if(delete_parent.status_code ==200):
            customParentInfo = ""
            parent_part_list = session.get(f"{Base_URL}")
            for each_part in data['parentPart']:
                addPartResponse = session.post(f"{Base_URL}AddPartParent",json={"SonPlasmidId":plasmidid,"ParentPartName":each_part},cookies=request.COOKIES)
                if(addPartResponse.status_code != 200):
                    customParentInfo += f"Part({each_part})"
            for each_backbone in data['parentBackbone']:
                addBackboneResponse = session.post(f"{Base_URL}AddBackboneParent",json={"SonPlasmidId":plasmidid,"ParentBackboneName":each_backbone},cookies=request.COOKIES)
                if(addBackboneResponse.status_code != 200):
                    customParentInfo += f"Backbone({each_backbone})"
            for each_plasmid in data['parentPlasmid']:
                addPlasmidResponse = session.post(f"{Base_URL}AddPlasmidParent",json={"SonPlasmidId":plasmidid,"ParentPlasmidName":each_plasmid},cookies=request.COOKIES)
                if(addPlasmidResponse.status_code != 200):
                    customParentInfo += f"Plasmid({each_plasmid})"
            print(f"CustomParent:{customParentInfo}")
            request_body = {"PlasmidID":plasmidid,"PlasmidParentInfo":customParentInfo}
            session.post(f'{Base_URL}UpdateParentInfo',json=request_body,cookies=request.COOKIES)

            if(update_plasmid_response.status_code == 200 and update_plasmid_scar_response.status_code == 200):
                return JsonResponse({"success":True},status = 200, safe=False)
            else:
                if(update_plasmid_response.status_code != 200):
                    
                    raise LabDatabaseException(message = f"Plasmid 数据更新失败，{update_plasmid_response.json()['message']}")
                if(update_plasmid_scar_response.json()["success"] == False):
                    raise LabDatabaseException(message = f"Plasmid Scar 数据更新失败，{update_plasmid_scar_response.json()['message']}")
                # return JsonResponse({"success":False,"message":"淇濆瓨澶辫触"},status=400,safe=False)
    except LabDatabaseException as exc:
        return exc.to_response()
    except Exception as exc:
        return JsonResponse({"success":False,"message":str(exc)},status = 400)
    
    
    
def GetExperienceDetail(request, partName):
    try:
        session = requests.session()
        session.headers.update({
            'User-Agent':'Django-App/1.0',
            'Content-Type':'application/json',
        })
        response = session.get(f"{Exp_URL}/api/part/view?filter=name={partName}")
        if(len(response.json()['parts']) == 0):
            raise LabDatabaseException(message = "获取数据为空")
        ID = response.json()['parts'][0]['ID']
        return redirect(f"{Exp_URL}/part/{ID}")
    except LabDatabaseException as exc:
        return exc.to_response()
    except Exception as exc:
        return JsonResponse({"success":False,"message":str(exc)})


def view_upload_records(request):
    try:
        if request.method != "GET":
            raise LabDatabaseGETMethodException()
        table_name = request.GET.get("table","")
        if table_name not in UPLOAD_DATE_TABLE_CONFIG:
            raise LabDatabaseException(message="table 只支持 parttable、backbonetable、plasmidneed")

        page = max(int(request.GET.get("page", 1)), 1)
        page_size = min(max(int(request.GET.get("pagesize", 100)), 1), 5000)
        filter_expr = request.GET.get("filter", "")

        session = requests.Session()
        response = session.get(
            f"{Base_URL}GetUploadRecords",
            params={
                "table": table_name,
                "page": page,
                "pagesize": page_size,
                "filter": filter_expr,
            },
            cookies=request.COOKIES,
            timeout=30,
        )
        try:
            payload = response.json()
        except ValueError:
            payload = {"success": False, "message": "WebDatabase 返回了无效响应"}
        return JsonResponse(payload, status=response.status_code, safe=False)
    except LabDatabaseException as exc:
        return exc.to_response()
    except ValueError:
        return JsonResponse({"success": False, "message": "page 和 pagesize 必须为整数"}, status=400)
    except Exception as exc:
        return JsonResponse({"success": False, "message": str(exc)}, status=400)


def user(request, username):
    try:
        session = requests.session()
        session.headers.update({
            'User-Agent':'Django-App/1.0',
            'Content-Type':'application/json',
        })
        if(request.method == "GET"):
            username = request.session['info']['uname']
            user = request.user
            userid = request.user.uid
            user_repository_count = session.get(f"{Base_URL}getrepocountbyuser/{userid}",cookies=request.COOKIES).json()['count']
            user_part_count = session.get(f"{Base_URL}getuserpartcount/{username}",cookies=request.COOKIES).json()['count']
            user_backbone_count = session.get(f"{Base_URL}getuserbackbonecount/{username}",cookies=request.COOKIES).json()['count']
            user_plasmid_count = session.get(f"{Base_URL}getuserplasmidcount/{username}",cookies=request.COOKIES).json()['count']
            user_info = {}
            user_info['repoCount'] = user_repository_count
            user_info['partCount'] = user_part_count
            user_info['backboneCount'] = user_backbone_count
            user_info['plasmidCount'] = user_plasmid_count
            return render(request,'ProfilePage.html',{"user":request.user,"user_info":user_info})
    except LabDatabaseException as exc:
        return exc.to_response()
    except Exception as exc:
        return JsonResponse({"success":False,"message":str(exc)},status = 400)
    


def GetParentInfo(request):
    try:
        session = requests.session()
        session.headers.update({
            'User-Agent':'Django-App/1.0',
            'Content-Type':'application/json',
        })
        if(request.method == "GET"):
            plasmidName = request.GET.get("PlasmidName");
            plasmidID = session.get(f"{Base_URL}PlasmidID?name={plasmidName}",cookies=request.COOKIES).json()["PlasmidID"];

            plasmidParentPart = session.get(f'{Base_URL}GetPartParent?plasmidid={plasmidID}',cookies=request.COOKIES)

            plasmidParentBackbone = session.get(f'{Base_URL}GetBackboneParent?plasmidid={plasmidID}',cookies=request.COOKIES)

            plasmidParentPlasmid = session.get(f'{Base_URL}GetPlasmidParent?plasmidid={plasmidID}',cookies=request.COOKIES)

            plasmidSonPlasmid = session.get(f'{Base_URL}GetPlasmidSon?plasmidid={plasmidID}',cookies = request.COOKIES)

            plasmidCustomInfo = session.get(f"{Base_URL}getPlasmidCulture?plasmidId={plasmidID}",cookies=request.COOKIES)
            print(plasmidParentPlasmid.json())
            if(plasmidParentPart.status_code == 200 and plasmidParentBackbone.status_code == 200 and
                plasmidParentPlasmid.status_code == 200 and plasmidSonPlasmid.status_code == 200 and plasmidCustomInfo.status_code == 200):
                result = {
                        'Part':[],
                        "Backbone":[],
                        "Plasmid":[],
                    }
                CustomInfo = plasmidCustomInfo.json()['customInfo']
                if(CustomInfo != None and CustomInfo != 'None' and CustomInfo != 'NULL' and CustomInfo != "nan"):
                    pattern = r'(\w+)\(([ a-zA-z0-9]+)\)'
                    matches = re.findall(pattern, CustomInfo)
                    for component_type, letter in matches:
                        if(component_type == "Part"):
                            result['Part'].append(letter)
                        elif(component_type == "Backbone"):
                            result['Backbone'].append(letter)
                        elif(component_type == "Plasmid"):
                            result['Plasmid'].append(letter)
                # print({"parentPart":plasmidParentPart.json()['data'],"parentBackbone":plasmidParentBackbone.json()['data'],
                                            # "parentPlasmid":plasmidParentPlasmid.json()['data'],"parentInfo":result})
                print(f"parentPart:{plasmidParentBackbone.json()}")
                return JsonResponse(data = {"success":True,"parentPart":plasmidParentPart.json()['data'] if 'data' in plasmidParentPart.json() else [],"parentBackbone":plasmidParentBackbone.json()['data'] if 'data' in plasmidParentBackbone.json() else [],
                                            "parentPlasmid":plasmidParentPlasmid.json()['data'] if 'data' in plasmidParentPlasmid.json() else [],"parentInfo":result},status=200,safe=False)
            else:
                if(plasmidParentPart.json()["success"] == False):
                    raise LabDatabaseException(message=f"Plasmid 上级元件获取失败，{plasmidParentPart.json()['message']}")
                if(plasmidParentBackbone.json()["success"] == False):
                    raise LabDatabaseException(message = f"Plasmid 上级载体获取失败，{plasmidParentBackbone.json()['message']}")
                if(plasmidParentPlasmid.json()["success"] == False):
                    raise LabDatabaseException(message = f"Plasmid 上级质粒获取失败，{plasmidParentPlasmid.json()['message']}")
                # return render(request,'error.html',{'error':"鑾峰彇鐖剁骇淇℃伅澶辫触"})
    except LabDatabaseException as exc:
        return exc.to_response()
    except Exception as exc:
        return JsonResponse({"success":False,"message":str(exc)},status=400)
    

def showRepository(request, repositoryName):
    try:
        session = requests.Session()
        token = request.COOKIES.get('csrftoken')
        session.headers.update({
            'User-Agent':'Django-App/1.0',
            'Content-Type':'application/json',
            'X-CSRFToken':token,
        })
        if(request.method == "GET"):
            request_body = {"Name":repositoryName}
            response = session.post(f"{Base_URL}getrepo",json=request_body,cookies=request.COOKIES)
            print(response.json())
            user = request.session['info']['uname']
            if(response.status_code == 200):
                part_id_list = response.json()["data"]["parts"]
                backbone_id_list = response.json()["data"]["backbones"]
                plasmid_id_list = response.json()["data"]["plasmids"]
                part_info_list = []
                for each_part in part_id_list:
                    part_name_response = session.get(f"{Base_URL}PartNameByID?ID={each_part}",cookies=request.COOKIES)
                    if(part_name_response.status_code == 200):
                        part_name = part_name_response.json()["PartName"]
                    else:
                        # part name fetch failed
                        raise LabDatabaseException(message = f"Part {each_part} 不存在")
                        # return HttpResponse("False",content_type="text")
                    part_type_response = session.get(f"{Base_URL}TypeByID?ID={each_part}",cookies=request.COOKIES)
                    if(part_type_response.status_code == 200):
                        part_type = part_type_response.json()["Type"]
                    else:
                        # part type fetch failed
                        raise LabDatabaseException(message=f"Part {part_name} type 未标注")
                        # return HttpResponse("False",content_type="text")
                    # part_scar_response = session.get(f"{Base_URL}getPartScar?id={each_part}",cookies=request.COOKIES).json()
                    # print(part_scar_response)
                    # if(part_scar_response["success"] and len(part_scar_response["scar_info"])!=0):
                    #     part_scar = f"BsmBI({part_scar_response['scar_info'][0]['bsmbi']})BsaI({part_scar_response['scar_info'][0]['bsai']})BbsI({part_scar_response['scar_info'][0]['bbsi']})"

                    # else:
                    #     part_scar = f""
                    part_info_list.append({"name":part_name,"Type":part_type,"scar":""})
                backbone_info_list = []
                for each_backbone in backbone_id_list:
                    backbone_response = session.get(f"{Base_URL}BackboneByID?ID={each_backbone}",cookies=request.COOKIES)
                    if(backbone_response.status_code == 200):
                        backbone_scar_response = session.get(f"{Base_URL}getBackboneScar?id={each_backbone}",cookies=request.COOKIES).json()
                        if(backbone_scar_response["success"]):
                            backbone_scar = f"BsmBI({backbone_scar_response['scar_info'][0]['bsmbi']})BsaI({backbone_scar_response['scar_info'][0]['bsai']})BbsI({backbone_scar_response['scar_info'][0]['bbsi']})"
                            backbone_info_list.append({"name":backbone_response.json()[0]["name"],"ori":", ".join(backbone_response.json()[0]["ori"]),"marker":", ".join(backbone_response.json()[0]["marker"]),"scar":backbone_scar})
                        else:
                            raise LabDatabaseException(message=f"Backbone {each_backbone} Scar 信息不存在")
                            # return HttpResponse("False",content_type="text")
                    else:
                        raise LabDatabaseException(message = f"Backbone {each_backbone} 不存在")
                        # return HttpResponse("False",content_type="text")
                plasmid_info_list = []
                for each_plasmid in plasmid_id_list:
                    plasmid_response = session.get(f"{Base_URL}PlasmidByID?ID={each_plasmid}",cookies=request.COOKIES)
                    if(plasmid_response.status_code == 200):
                        plasmid_scar_response = session.get(f"{Base_URL}getPlasmidScar?plasmidid={each_plasmid}",cookies=request.COOKIES).json()
                        if(plasmid_scar_response['success']):
                            backbone_scar = f"BsmBI({plasmid_scar_response['scar_info'][0]['bsmbi']})BsaI({plasmid_scar_response['scar_info'][0]['bsai']})BbsI({plasmid_scar_response['scar_info'][0]['bbsi']})"
                            plasmid_info_list.append({"name":plasmid_response.json()[0]["name"],"length":plasmid_response.json()[0]["length"],"scar":backbone_scar})
                        else:
                            raise LabDatabaseException(message=f"Plasmid {each_plasmid} Scar 信息不存在")
                            # return HttpResponse("False",content_type="text")
                    else:
                        raise LabDatabaseException(message = f"Plasmid {each_plasmid} 不存在")
                        # return HttpResponse("False",content_type="text")
                repository_data = {"user":user,"name":repositoryName,"created_time":response.json()["created_time"],"expired_time":response.json()["expired_time"],"part_number":response.json()["data"]["total_parts"],"plasmid_number":response.json()["data"]["total_plasmids"],"parts":part_info_list,"backbones":backbone_info_list,"plasmids":plasmid_info_list}
                print(repository_data)
                return render(request, "repositoryPage.html",{"repository":repository_data})
            else:
                raise LabDatabaseException(message = "获取仓库失败")
        else:
            raise LabDatabaseGETMethodException()
    except LabDatabaseException as exc:
        return exc.to_response()
    except Exception as exc:
        return JsonResponse({"success":False,"message":str(exc)},status=400)



if __name__ == "__main__":
    _determine_target_enzyme("cctcctgagaaatctgctcgtcagtggtgctcacactgacgaatcatgtacagatcataccgatgactgcctggcgactcacaactaagcaagacagccggaaccagcgccggcgaacaccactgcatatatggcatatcacaacagtccacgtctcaagcagttacagagatgttacgaaccactagtgcactgcagtacaagcttgccttgtccccgccgggtcacccggccagcgacatggaggcccagaataccctccttgacagtcttgacgtgcgcagctcaggggcatgatgtgactgtcgcccgtacatttagcccatacatccccatgtataatcatttgcatccatacattttgatggccgcacggcgcgaagcaaaaattacggctcctcgctgcagacctgcgagcagggaaacgctcccctcacagacgcgttgaattgtccccacgccgcgcccctgtagagaaatataaaaggttaggatttgccactgaggttcttctttcatatacttccttttaaaatcttgctaggatacagttctcacatcacatccgaacataaacaacaatgacagtcaacactaagacctatagtgagagagcagaaactcatgcctcaccagtagcacaacgattatttcgattaatggaactgaagaaaaccaatttatgtgcatcaattgatgttgataccactaaggaattccttgaattaattgataaattgggtccttatgtatgcttaatcaagacacatattgatataatcaatgatttttcctatgaatccactattgaaccattattagaactttcacgtaaacatcaatttatgatttttgaagatagaaaatttgctgatattggtaataccgtgaagaaacaatatattggtggagtttataaaattagtagttgggcagatattactaatgctcatggtgtcactgggaatggagtagttgaaggattaaaacagggagctaaagaaaccaccaccaaccaagagccaagagggttattgatgttagctgaattatcatcagtgggatcattagcatatggagaatattctcaaaaaactgttgaaattgctaaatccgataaggaatttgttattggatttattgcccaacgtgatatgggtggacaagaagaaggatttgattggcttattatgacacctggagttggattagatgataaaggtgatggattaggacaacaatatagaactgttgatgaagttgttagcactggaactgatattatcattgttggtagaggattgtttggtaaaggaagagatccagatattgaaggtaaaaggtatagagatgctggttggaatgcttatttgaaaaagactggccaattataaacagtactgacaataaaaagattcttgttttcaagaacttgtcatttgtatagtttttttatattgtagttgttctattttaatcaaatgttagcgtgatttatattttttttcgcctcgacatcatctgcccagatgcgaagttaagtgcgcagaaagtaatatcatgcgtcaatcgtatgtgaatgctggtcgctatactgctgtcgattcgatactaacgccgccatccagtgtcgagagtagagcacttgaatccactgccccgggaatctcggtcgtaatgatttctataatgacgaaaaaaaaaaaattggaaagaaaaagcttcatggcctttataaaaaggaactatccaatacctcgccagaaccaagtaacagtattttacggggcacaaatcaagaacaataagacaggactgtaaagatggacgcattgaactccaaagaacaacaagagttccaaaaagtagtggaacaaaagcaaatgaaggatttcatgcgtttgtactctaatctggtagaaagatgtttcacagactgtgtcaatgacttcacaacatcaaagctaaccaataaggaacaaacatgcatcatgaagtgctcagaaaagttcttgaagcatagcgaacgtgtagggcagcgtttccaagaacaaaacgctgccttgggacaaggcttgggccgataaggtgtactggcgtatatatatctaattatgtatctctggtgtagcccatttttagcatgtaaatataaagaagagacctatcagctcactcaaaggcggtaatacggttatccacagaatcaggggataacgcaggaaagaacatgtgagcaaaaggccagcaaaaggccaggaaccgtaaaaaggccgcgttgctggcgtttttccataggctccgcccccctgacgagcatcacaaaaatcgacgctcaagtcagaggtggcgaaacccgacaggactataaagataccaggcgtttccccctggaagctccctcgtgcgctctcctgttccgaccctgccgcttaccggatacctgtccgcctttctcccttcgggaagcgtggcgctttctcatagctcacgctgtaggtatctcagttcggtgtaggtcgttcgctccaagctgggctgtgtgcacgaaccccccgttcagcccgaccgctgcgccttatccggtaactatcgtcttgagcccaacccggtaagacacgacttatcgccactggcagcagccactggtaacaggattagcagagcgaggtatgtaggcggtgctacagagttcttgaagtggtggcctaactacggctacactagaagaacagtatttggtatctgcgctctgctgaagccagttaccttcggaaaaagagttggtagctcttgatccggcaaacaaaccaccgctggtagcggtggtttttttgtttgcaagcagcagattacgcgcagaaaaaaaggatctcaagaagatcctttgatcttttctacggggtctgacgctcagtggaacgaaaactcacgttaagggattttggtcatgagattatcaaaaagtatcttcacctagatccttttaaattaaaaatgaagttttaaatcaatctaaagtatatatgagtaaacttggtctgacagagttctgaggtcattactggatctatcaacagcagtccaagcgagctcgatatcaaattacgccccgccctgccactcatcgcagtactgttgtaattcattaagcattctgccgacatggaagccatcacaaacggcatgatgaacctgaatcgccagcggcatcagcaccttgtcgccttgcgtataatatttgcccatggtgaaaacgggggcgaagaagttgtccatattggccacgtttaaatcaaaactggtgaaactcacccagggattggctgagacgaaaaacatattctcaataaaccctttagggaaataggccaggttttcaccgtaacacgccacatcttgcgaatatatgtgtagaaactgccggaaatcgtcgtggtattcactccagagcgatgaaaacgtttcagtttgctcatggaaaacggtgtaacaagggtgaacactatcccatatcaccagctcaccgtctttcattgccatacgaaattccggatgagcattcatcaggcgggcaagaatgtgaataaaggccggataaaacttgtgcttatttttctttacggtctttaaaaaggccgtaatatccagctgaacggtctggttataggtacattgagcaactgactgaaatgcctcaaaatgttctttacgatgccattgggatatatcaacggtggtatatccagtgatttttttctccattttagcttccttagctcctgaaaatctcgataactcaaaaaatacgcccggtagtgatcttatttcattatggtgaaagttggaacctcttacgtgcccgatcaactcgcgcgtttgccacctgacgtctaagaaaaggaatattcagcaatttgcccgtgccgaagaaaggcccacccgtgaaggtgagccggtctcggctaaattcgagtgaaacacaggaagatcagaaaatcctcatttcatccatattaacaataatttcaaatgtttatttgcattatttgaaactaggcaagacaagcaacgaaacgtttttgaaaattttgagtattttcaataaatttgtagaggactcagatattgaaaaaaagctacagcaattaatacttgataagaagagtattgagaagggcaacggttcatcatctcatggatctgcacatgaacaaacaccagagtcaaacgacgttgaaattgaggctactgcgccaattgatgacaatacagacgatgataacaaaccgaagttatctgatgtagaaaaggattaaagatgctaagagatagtgatgatatttcataaataatgtaattctatatatgttaattaccttttttgcgaggcatatttatggtgaaggataagttttgaccatcaaagaaggttaatgtggctgtggtttcagggtccataaagcccacatggataacattacgcttgctatgtcgtcggaggagatatttattacttttattattctagttttttacagttatttattaattaattatttttatatgcatgcgaataaaaagtctatatttaagttcttttatttattaatacattttcctctacgagctgtcaccggatgtgctttccggtctgatgagtccgtgaggacgaaacagcctctacaaataattttgtttaagagcaggttgttcatggccgtgcgtatgatgtggggggctcgggcgttgaaaccggggttcggagcgccaggggggtgcttttttattttgttttttttttgcagtataaaaagttagtttgtttaaacaacaaacttttttcatttcttttgtttccccttctcttcttttagttagtttgtttaaacaacaaactagaatatcaagctacaaaaataaataaaaaatgtctaaaggtgaagaattattcactggtgttgtcccaattttggttgaattagatggtgatgttaatggtcacaaattttctgtctccggtgaaggtgaaggtgatgctacttacggtaaattgaccttaaaatttatttgtactactggtaaattgccagttccatggccaaccttagtcactactttaggttatggtttgatgtgttttgctagatacccagatcatatgaaacaacatgactttttcaagtctgccatgccagaaggttatgttcaagaaagaactatttttttcaaagatgacggtaactacaagaccagagctgaagtcaagtttgaaggtgataccttagttaatagaatcgaattaaaaggtattgattttaaagaagatggtaacattttaggtcacaaattggaatacaactataactctcacaatgtttacatcatggctgacaaacaaaagaatggtatcaaagttaacttcaaaattagacacaacattgaagatggttctgttcaattagctgaccattatcaacaaaatactccaattggtgatggtccagtcttgttaccagacaaccattacttatcctatcaatctagattatccaaagatccaaacgaaaagagggatcacatggtcttgttagaatttgttactgctgctggtattacccatggtatggatgaattgtacaaataataaatggtcttcggcttactaaaagccagataacagtatgcatatttgcgcgctgatttttgcggtataagaatatatactgatatgtatacccgaagtatgtcaaaaagaggtatgctatgaagcagcgtattacagtgacagttgacagcgacagctatcagttgctcaaggcatatatgatgtcaatatctccggtctggtaagcacaaccatgcagaatgaagcccgtcgtctgcgtgccgaacgctggaaagcggaaaatcaggaagggatggctgaggtcgcccggtttattgaaatgaacggctcttttgctgacgagaacaggggctggtgaaatgcagtttaaggtttacacctataaaagagagagccgttatcgtctgtttgtggatgtacagagtgatattattgacacgcccgggcgacggatggtgatccccctggccagtgcacgtctgctgtcagataaagtctcccgtgaactttacccggtggtgcatatcggggatgaaagctggcgcatgatgaccaccgatatggccagtgtgccggtttccgttatcggggaagaagtggctgatctcagccaccgcgaaaatgacatcaaaaacgccattaacctgatgttctggggaatataagaagacta")
