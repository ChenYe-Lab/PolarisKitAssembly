from django.shortcuts import redirect, render
from django.http import JsonResponse,HttpResponseRedirect,StreamingHttpResponse,FileResponse, Http404
from django.views.decorators.csrf import ensure_csrf_cookie
import requests
from .http_client import ApiSession
from django.conf import settings
import json
import uuid
import threading
import io
import os
import copy
import mimetypes

from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from Bio.SeqFeature import FeatureLocation
from .gg_assembly import assemble_genbank_files

#Ecoli_Part_promoter_list
# Ecoli_Part_promoter_List = [{"name":"pEcP01","alias":"XRHL1-P020"},{"name":"pEcP02","alias":"XRHL1-P031"},{"name":"pEcP03","alias":"XRHL1-P030"},{"name":"pEcP04","alias":"CYP9"},{"name":"pEcP05","alias":"XRHL1-P021"},
#                             {"name":"pEcP06","alias":"XRHL1-P004"},{"name":"pEcP07","alias":"WHY01"},{"name":"pEcP08","alias":"XRHL1-P011"},{"name":"pEcP09","alias":"XRHL1-P025"},{"name":"pEcP10","alias":"XRHL1-P026"},
#                             {"name":"pEcP11","alias":"XRHL1-P027"},{"name":"pEcP12","alias":"XRHL1-P028"},{"name":"pEcP13","alias":"XRHL1-P029"}]
# Ecoli_Part_promoter_List = ["XRHL1-P020","XRHL1-P031","XRHL1-P030","CYP9","XRHL1-P021","XRHL1-P004","WHY01","XRHL1-P011","XRHL1-P025",
#                       "XRHL1-P026","XRHL1-P027","XRHL1-P028","XRHL1-P029"]
Ecoli_Part_promoter_List = ["pEcP01","pEcP02","pEcP03","pEcP04","pEcP05","pEcP06","pEcP07","pEcP08","pEcP09","pEcP10","pEcP11","pEcP12","pEcP13"]
#                             {"name":"pEcP06","alias":"XRHL1-P004"},{"name":"pEcP07","alias":"WHY01"},{"name":"pEcP08","alias":"XRHL1-P011"},{"name":"pEcP09","alias":"XRHL1-P025"},{"name":"pEcP10","alias":"XRHL1-P026"},
#                             {"name":"pEcP11","alias":"XRHL1-P027"},{"name":"pEcP12","alias":"XRHL1-P028"},{"name":"pEcP13","alias":"XRHL1-P029"}]
#Ecoli_Part_RBS_list
# Ecoli_Part_RBS_list = [{"name":"pEcR01","alias":"CY1753"},{"name":"pEcRBS02","alias":"CY1755"},{"name":"pEcRBS03","alias":"CY2005"},{"name":"pEcRBS04","alias":"CY1756"},{"name":"pEcRBS05","alias":"CY1752"}]
# Ecoli_Part_RBS_list = ["CY1753","CY1755","LXY181","CY1756","CY1752"]
Ecoli_Part_RBS_list = ["pEcR01","pEcR02","pEcR03","pEcR04","pEcR05","pEcR06"]

#Ecoli_Part_CDS_list
# Ecoli_Part_CDS_list = [{"name":"pEcC01","alias":"XRHL1-C041"},{"name":"pEcCDS02","alias":"XRHL1-C042"},{"name":"pEcCDS03","alias":"XRHL1-C043"},{"name":"pEcCDS04","alias":"XRHL1-C044"},{"name":"pEcCDS05","alias":"NNN76"},
#                        {"name":"pEcCDS06","alias":"XRHL1-C040"},{"name":"pEcCDS07","alias":"XRHL1-C006"},{"name":"pEcCDS08","alias":"XRHL1-C007"},{"name":"pEcCDS09","alias":"XRHL1-C008"},{"name":"pEcCDS10","alias":"GFW102"},
#                        {"name":"pEcCDS11","alias":"CY1728"},{"name":"pEcCDS12","alias":"CY1702"},{"name":"pEcCDS13","alias":"XRHL1-C039"},{"name":"pEcCDS14","alias":"CY1727"}]
# Ecoli_Part_CDS_list = ["XRHL1-C041","XRHL1-C042","XRHL1-C043","XRHL1-C044","NNN76","XRHL1-C040","XRHL1-C006","XRHL1-C007","XRHL1-C008",
#                        "GFW102","CY1728","CY1702","XRHL1-C039","CY1727"]

Ecoli_Part_CDS_list = ["pEcC01","pEcC02","pEcC03","pEcC04","pEcC05","pEcC06","pEcC07","pEcC08","pEcC09","pEcC10","pEcC11","pEcC12","pEcC13","pEcC14","pEcC15"]

#Ecoli_Part_Terminator_list
Ecoli_Part_Terminator_list = ["pEcT01","pEcT02","pEcT03","pEcT04","pEcT05"]
# Ecoli_Part_Terminator_list = ["ZYX49","ZYX50","ZYX52","ZYX54","ZYX55"]


#Ecoli_Backbone_list
Ecoli_Backbone_list = ["pEcBB01","pEcBB02","pEcBB03","pEcBB04","pEcBB05","pEcBB06","pEcBB07","pEcBB08","pEcBB09","pEcBB10","pEcBB11","pEcBB12","pEcBB13","pEcBB14","pEcBB15",
                        "pEcBB16","pEcBB17","pEcBB18","pEcBB19","pEcBB20","pEcBB21","pEcBB22","pEcBB23","pEcBB27","pEcBB28","pEcBB29","pEcBB30",
                        "pEcBB31","pEcBB32","pEcBB33","pEcBB34","pEcBB35","pEcBB36","pEcBB37","pEcBB38","pEcBB39","pEcBB40"]
# Ecoli_Backbone_list = ["XSYB1","XSYB2","XSYB3","pCQM005","pCQM004","LJQ02","LJQ03","WTZB8","WTZB9","WTZB6","XRHe-B026","XRHe-B015","XRHe-B016",
#                        "XRHe-B017","XRHe-B018","XRHe-B019","XRHe-B020","CWJB04","BZC001","BZC002","BZC003","BZC004","ZYX45","ZYX46","ZYX47",
#                        "ZYX48","GFW76","GFW77","GFW78","GFW79","XRHe-B013","XRHe-B021","XRHe-B022","XRHe-B023","XRHe-B024","YLB13","YLB14",
#                        "YLB15","BZC005","XRHe-B010","XRHe-B011","CWJB35","XRHe-B012","XRHe-B007","CWJB05"]


#Ecoli_Plasmid_list
Ecoli_Plasmid_list = ["pEcint01","pEcint02","pEcint03","pEcint04","pcp20","pEcint05","pEcint06","pEcint07","pEcint08","pEcint09","pEcint10","pEcint11","pEcCas","pEcgRNA"]
# Ecoli_Plasmid_list = ["BZC034","XRHL3-1183","XRHL3-1188","BZC021","pcp20","XSY-attB2","XSY-attB5","XSY-attB7","BZC354","BZC353","BZC355",
#                       "pEcCas9","pEcgRNA"]


#Sc_Part_promoter_list
Sc_Part_promoter_list = ["pScP01","pScP02","pScP06","pScP07","pScP08","pScP12","pScP13","pScP14","pScP15","pScP16","pScP17","pScP18","pScP19","pScP20","pScP21",
                        "pScP22","pScP23","pScP24","pScP26","pScP27","pScP28","pScP29","pScP30","pScP31"]

Sc_Part_CDS_list = ["pScORF01","pScORF02","pScORF03","pScORF04","pScORF05","pScORF06","pScORF07","pScORF08","pScORF09","pScORF10","pScORF11","pScORF12"]

Sc_Part_Terminator_list = ["pScTerm01","pScTerm03","pScTerm04","pScTerm07","pScTerm09","pScTerm10","pScTerm11","pScTerm17","pScTerm21"]
Sc_Backbone_list = ["pScbb01","pScbb02","pScbb03","pScbb04","pScbb05","pScbb06","pScbb07","pScbb08","pScbb09","pScbb10","pScbb11","pScbb12","pScbb13",
                    "pScbb14","pScbb15","pScbb16","pScbb17","pScbb18","pScbb20","pScbb21","pScbb22","pScbb23","pScbb24","pScbb25","pScbb31","pScbb32","pScbb33","pScbb34","pScbb35",
                    "pScbb36","pScbb37","pScbb38","pScbb39","pScbb40","pScbb41","pScbb42","pScbb43","pScbb44","pScbb45","pScbb46","pScbb47","pScbb48","pScCom02"]
Sc_Plasmid_list = ["pScLv001","pScLv002","pScLv003","pScLv005","pScLv007","pScLv008","pScLv013","pCfB2312"]

GG_ENZYME_RULES = {
    "bsai": {
        "site_fwd": "GGTCTC",
        "site_rev": "GAGACC",
        "fwd_cut_after_site": 1,
        "rev_cut_before_site": 5,
        "overhang_len": 4,
    },
    "bsmbi": {
        "site_fwd": "CGTCTC",
        "site_rev": "GAGACG",
        "fwd_cut_after_site": 1,
        "rev_cut_before_site": 5,
        "overhang_len": 4,
    },
    "bbsi": {
        "site_fwd": "GAAGAC",
        "site_rev": "GTCTTC",
        "fwd_cut_after_site": 2,
        "rev_cut_before_site": 6,
        "overhang_len": 4,
    },
}

def __create_session(request):
    login_url = getattr(settings, "API_LOGIN_URL", f"{settings.WEBDATABASE_URL}login")
    username = getattr(settings, "API_LOGIN_USERNAME", None)
    password = getattr(settings, "API_LOGIN_PASSWORD", None)
    username_field = getattr(settings, "API_LOGIN_USERNAME_FIELD", "username")
    password_field = getattr(settings, "API_LOGIN_PASSWORD_FIELD", "password")
    next_value = getattr(settings, "API_LOGIN_NEXT", "")


    
    if not username or not password:
        return None

    login_data = {
        username_field: username,
        password_field: password,
    }
    if next_value:
        login_data["next"] = next_value
    
    session = ApiSession()
    response = session.get(login_url, data=login_data, timeout=_webdb_timeout())
    if(response.status_code == 200):
        token = request.COOKIES.get('csrftoken')
        session.headers.update({
            'User-Agent':'Django-App/1.0',
            'Content-Type':'application/json',
            'X-CSRFToken':token,
        })
        return session
    else:
        return None

def _extract_scar(payload):
    if not isinstance(payload, dict):
        return None
    scar_source = payload.get("scar_info") or payload.get("data")
    if isinstance(scar_source, list) and scar_source:
        scar_source = scar_source[0]
    if not isinstance(scar_source, dict):
        return None
    extracted = {}
    for key in ("bbsi", "bsai"):
        if key in scar_source:
            extracted[key] = scar_source[key]
    if not extracted:
        return None
    return extracted


def _request_scar(session, url):
    if not url:
        return None
    try:
        resp = session.get(url)
    except requests.RequestException:
        return None
    if resp.status_code != 200:
        return None
    json_data = resp.json()
    if isinstance(json_data, dict) and json_data.get("success") is False:
        return None
    return _extract_scar(json_data)


def _webdb_timeout():
    return getattr(settings, "API_REQUEST_TIMEOUT", 20)


def _visitor_cookie_name():
    return getattr(settings, "VISITOR_COOKIE_NAME", "kitapp_visitor_id")


def _set_visitor_cookie(response, visitor_id):
    response.set_cookie(
        _visitor_cookie_name(),
        str(visitor_id),
        max_age=getattr(settings, "VISITOR_COOKIE_MAX_AGE", 60 * 60 * 24 * 365),
        secure=getattr(settings, "VISITOR_COOKIE_SECURE", False),
        httponly=False,
        samesite=getattr(settings, "VISITOR_COOKIE_SAMESITE", "Lax"),
    )
    return response


def _get_client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def _parse_json_body(request):
    try:
        return json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return None


def _post_webdatabase_json(session, endpoint, payload):
    response = session.post(
        f"{settings.WEBDATABASE_URL}{endpoint}",
        json=payload,
        timeout=_webdb_timeout(),
    )
    try:
        data = response.json()
    except ValueError:
        data = {"success": False, "message": response.text}
    return response, data


def _resolve_visitor_id(payload, request):
    payload_visitor_id = None
    if isinstance(payload, dict):
        payload_visitor_id = payload.get("visitor_id")
    return payload_visitor_id or request.COOKIES.get(_visitor_cookie_name())




# Create your views here.
@ensure_csrf_cookie
def index(request):
    return render(request,'index.html')


@ensure_csrf_cookie
def landing_page(request):
    return render(request, "landing.html")


def register_visitor(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "method not allowed"}, status=405, safe=False)

    payload = _parse_json_body(request)
    if payload is None:
        return JsonResponse({"success": False, "message": "invalid json"}, status=400, safe=False)

    institution = (payload.get("institution") or "").strip()
    lab_name = (payload.get("lab_name") or "").strip()
    person_name = (payload.get("person_name") or "").strip()
    if not institution or not lab_name or not person_name:
        return JsonResponse(
            {"success": False, "message": "institution, lab_name and person_name are required"},
            status=400,
            safe=False,
        )

    session = __create_session(request)
    if session is None:
        return JsonResponse({"success": False, "message": "Login Error"}, status=403, safe=False)

    api_payload = {
        "institution": institution,
        "lab_name": lab_name,
        "person_name": person_name,
    }

    try:
        response, data = _post_webdatabase_json(session, "createVisitorProfile", api_payload)
    except requests.RequestException as exc:
        return JsonResponse(
            {"success": False, "message": f"downstream request failed: {str(exc)}"},
            status=502,
            safe=False,
        )

    if response.status_code != 200 or not data.get("success"):
        return JsonResponse(data, status=response.status_code, safe=False)

    visitor_data = data.get("data") or {}
    visitor_id = visitor_data.get("id")
    if not visitor_id:
        return JsonResponse(
            {"success": False, "message": "visitor id missing from WebDatabase response"},
            status=502,
            safe=False,
        )

    kitapp_response = JsonResponse(
        {"success": True, "data": {"visitor_id": visitor_id, "profile": visitor_data}},
        status=200,
        safe=False,
    )
    return _set_visitor_cookie(kitapp_response, visitor_id)


def track_visit(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "method not allowed"}, status=405, safe=False)

    payload = _parse_json_body(request)
    if payload is None:
        return JsonResponse({"success": False, "message": "invalid json"}, status=400, safe=False)

    visitor_id = _resolve_visitor_id(payload, request)
    if not visitor_id:
        return JsonResponse({"success": False, "message": "visitor_id not found in cookies"}, status=400, safe=False)

    session = __create_session(request)
    if session is None:
        return JsonResponse({"success": False, "message": "Login Error"}, status=403, safe=False)

    api_payload = {
        "visitor_id": visitor_id,
        "path": (payload.get("path") or request.path).strip(),
        "method": payload.get("method") or request.method,
        "ip": payload.get("ip") or _get_client_ip(request),
        "user_agent": payload.get("user_agent") or request.headers.get("User-Agent"),
        "referer": payload.get("referer") or request.headers.get("Referer"),
        "cookie_snapshot": { "visitor_id": str(visitor_id) },
    }

    try:
        response, data = _post_webdatabase_json(session, "createVisitorAccessLog", api_payload)
    except requests.RequestException as exc:
        return JsonResponse(
            {"success": False, "message": f"downstream request failed: {str(exc)}"},
            status=502,
            safe=False,
        )

    kitapp_response = JsonResponse(data, status=response.status_code, safe=False)
    return _set_visitor_cookie(kitapp_response, visitor_id)


def submit_feedback(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "method not allowed"}, status=405, safe=False)

    payload = _parse_json_body(request)
    if payload is None:
        return JsonResponse({"success": False, "message": "invalid json"}, status=400, safe=False)

    visitor_id = _resolve_visitor_id(payload, request)
    if not visitor_id:
        return JsonResponse({"success": False, "message": "visitor_id not found in cookies"}, status=400, safe=False)

    feedback_type = (payload.get("feedback_type") or "").strip().lower()
    title = (payload.get("title") or "").strip()
    content = (payload.get("content") or "").strip()
    contact_email = (payload.get("contact_email") or "").strip()
    page_path = (payload.get("page_path") or request.path).strip()

    allowed_types = {"issue", "suggestion"}
    if feedback_type not in allowed_types:
        return JsonResponse({"success": False, "message": "invalid feedback_type"}, status=400, safe=False)

    if not title or not content:
        return JsonResponse({"success": False, "message": "title and content are required"}, status=400, safe=False)

    session = __create_session(request)
    if session is None:
        return JsonResponse({"success": False, "message": "Login Error"}, status=403, safe=False)

    api_payload = {
        "visitor_id": visitor_id,
        "feedback_type": feedback_type,
        "title": title,
        "content": content,
        "contact_email": contact_email,
        "page_path": page_path,
    }

    try:
        response, data = _post_webdatabase_json(session, "createVisitorFeedback", api_payload)
    except requests.RequestException as exc:
        return JsonResponse(
            {"success": False, "message": f"downstream request failed: {str(exc)}"},
            status=502,
            safe=False,
        )

    kitapp_response = JsonResponse(data, status=response.status_code, safe=False)
    return _set_visitor_cookie(kitapp_response, visitor_id)

def InitData(request):
    
    session = __create_session(request)
    
    if session == None:
        return JsonResponse(data={"success":False,"message":"Login Error"},status=403, safe=False)
    
    if request.method != "GET":
        return JsonResponse(data={"success":False, "message":"method not allowed"}, status=405, safe=False)

    currentCategory = request.GET.get("currentCategory")
    currentType = request.GET.get("currentType")
    try:
        if currentCategory == "ecoli":
            if currentType == "part":
                Ecoli_part_promoter_info = []
                Ecoli_part_rbs_info = []
                Ecoli_part_cds_info = []
                Ecoli_part_terminator_info = []
                for each in Ecoli_Part_promoter_List:
                    part_parent_name = ""
                    part_data_response = session.get(f'{settings.WEBDATABASE_URL}PlasmidName?name={each}')
                    
                    # if len(part_data_response.history) > 0:
                    #     return JsonResponse({"success":False,"next_url":f"{settings.WEBDATABASE_URL}login"})
                    if part_data_response.status_code == 200:
                        part_plasmid_id = part_data_response.json()['data']['plasmidid']
                        part_parent_response = session.get(f"{settings.WEBDATABASE_URL}GetPartParent?plasmidid={part_plasmid_id}")
                        if(part_parent_response.json()["success"]):
                            part_parent_name = part_parent_response.json()['data'][0]['name']
                        part_alias = part_data_response.json()['data']['alias']
                        part_length = f"{part_data_response.json()['data']['length']}bp"
                        part_user = part_data_response.json()['data']['user']
                        Ecoli_part_promoter_info.append({"name":each,"status":True,"type":"promoter","alias":part_alias,"length":part_length,"part":part_parent_name,"user":part_user})
                    else:
                        Ecoli_part_promoter_info.append({"name":each,"status":False})
                for each in Ecoli_Part_RBS_list:
                    part_parent_name = ""
                    part_data_response = session.get(f'{settings.WEBDATABASE_URL}PlasmidName?name={each}')
                    
                    # if len(part_data_response.history) > 0:
                    #     return JsonResponse({"success":False,"next_url":f"{settings.WEBDATABASE_URL}login"})
                    if part_data_response.status_code == 200:
                        part_plasmid_id = part_data_response.json()['data']['plasmidid']
                        part_parent_response = session.get(f"{settings.WEBDATABASE_URL}GetPartParent?plasmidid={part_plasmid_id}")
                        if(part_parent_response.json()["success"]):
                            part_parent_name = part_parent_response.json()['data'][0]['name']
                        part_alias = part_data_response.json()['data']['alias']
                        part_length = f"{part_data_response.json()['data']['length']}bp"
                        part_user = part_data_response.json()['data']['user']
                        Ecoli_part_rbs_info.append({"name":each,"status":True,"type":"rbs","alias":part_alias,"length":part_length,"part":part_parent_name,"user":part_user})
                    else:
                        Ecoli_part_rbs_info.append({"name":each,"status":False})
                for each in Ecoli_Part_CDS_list:
                    part_parent_name = ""
                    part_data_response = session.get(f'{settings.WEBDATABASE_URL}PlasmidName?name={each}')
                    
                    # if len(part_data_response.history) > 0:
                    #     return JsonResponse({"success":False,"next_url":f"{settings.WEBDATABASE_URL}login"})
                    if part_data_response.status_code == 200:
                        part_plasmid_id = part_data_response.json()['data']['plasmidid']
                        part_parent_response = session.get(f"{settings.WEBDATABASE_URL}GetPartParent?plasmidid={part_plasmid_id}")
                        if(part_parent_response.json()["success"]):
                            part_parent_name = part_parent_response.json()['data'][0]['name']
                        part_alias = part_data_response.json()['data']['alias']
                        part_length = f"{part_data_response.json()['data']['length']}bp"
                        part_user = part_data_response.json()['data']['user']
                        Ecoli_part_cds_info.append({"name":each,"status":True,"type":"cds","alias":part_alias,"length":part_length,"part":part_parent_name,"user":part_user})
                    else:
                        Ecoli_part_cds_info.append({"name":each,"status":False})
                for each in Ecoli_Part_Terminator_list:
                    part_parent_name = ""
                    part_data_response = session.get(f'{settings.WEBDATABASE_URL}PlasmidName?name={each}')
                    # if len(part_data_response.history) > 0:
                    #     return JsonResponse({"success":False,"next_url":f"{settings.WEBDATABASE_URL}login"})
                    if part_data_response.status_code == 200:
                        part_plasmid_id = part_data_response.json()['data']['plasmidid']
                        part_parent_response = session.get(f"{settings.WEBDATABASE_URL}GetPartParent?plasmidid={part_plasmid_id}")
                        if(part_parent_response.json()["success"]):
                            part_parent_name = part_parent_response.json()['data'][0]['name']
                        part_alias = part_data_response.json()['data']['alias']
                        part_length = f"{part_data_response.json()['data']['length']}bp"
                        part_user = part_data_response.json()['data']['user']
                        Ecoli_part_terminator_info.append({"name":each,"status":True,"type":"terminator","alias":part_alias,"length":part_length,"part":part_parent_name,"user":part_user})
                    else:
                        Ecoli_part_terminator_info.append({"name":each,"status":False})
                result = Ecoli_part_promoter_info + Ecoli_part_rbs_info + Ecoli_part_cds_info + Ecoli_part_terminator_info
                return JsonResponse(data={"success":True, "data":result},status=200, safe=False)
            if currentType == "backbone":
                Ecoli_backbone_info = []
                for each in Ecoli_Backbone_list:
                    backbone_data_response = session.get(f'{settings.WEBDATABASE_URL}BackboneName?name={each}')
                    # if len(backbone_data_response.history) > 0:
                    #     return JsonResponse({"success":False,"next_url":f"{settings.WEBDATABASE_URL}login"})
                    if backbone_data_response.status_code == 200:
                        data = backbone_data_response.json()['data']
                        backbone_alias = data["alias"]
                        backbone_length = f"{data['length']}bp"
                        backbone_marker = data['marker']
                        backbone_ori = data['ori']
                        backbone_user = data['user']
                        backbone_id = data.get('id')
                        scar_value = _request_scar(session, f'{settings.WEBDATABASE_URL}getBackboneScar?id={backbone_id}')
                        Ecoli_backbone_info.append({
                            "name":each,
                            "status":True,
                            "alias":backbone_alias,
                            "length":backbone_length,
                            "marker":backbone_marker,
                            "ori":backbone_ori,
                            "user":backbone_user,
                            "scar": scar_value
                        })
                    else:
                        Ecoli_backbone_info.append({"name":each,"status":False})
                return JsonResponse(data={"success":True, "data":Ecoli_backbone_info}, status=200, safe=False)
            if currentType == "plasmid":
                Ecoli_plasmid_info = []
                for each in Ecoli_Plasmid_list:
                    plasmid_data_response = session.get(f'{settings.WEBDATABASE_URL}PlasmidName?name={each}')
                    # if len(plasmid_data_response.history) > 0:
                    #     return JsonResponse({"success":False,"next_url":f"{settings.WEBDATABASE_URL}login"})
                    if plasmid_data_response.status_code == 200:
                        data = plasmid_data_response.json()['data']
                        plasmid_alias = data['alias']
                        plasmid_length = f"{data['length']}bp"
                        plasmid_ori = data['ori_info']
                        plasmid_marker = data['marker_info']
                        plasmid_user = data['user']
                        plasmid_id = data.get('plasmidid')
                        plasmid_scar = _request_scar(session, f'{settings.WEBDATABASE_URL}getPlasmidScar?plasmidid={plasmid_id}')
                        Ecoli_plasmid_info.append({
                            'name':each,
                            "status":True,
                            "alias":plasmid_alias,
                            'length':plasmid_length,
                            "ori":plasmid_ori,
                            "marker":plasmid_marker,
                            "user":plasmid_user,
                            "scar": plasmid_scar
                        })
                    else:
                        Ecoli_plasmid_info.append({"name":each,"status":False})
                return JsonResponse(data={"success":True,"data":Ecoli_plasmid_info},status=200,safe=False)

        elif currentCategory == "yeast":
            if currentType == "part":
                Sc_part_promoter_info = []
                Sc_part_cds_info = []
                Sc_part_terminator_info = []
                for each in Sc_Part_promoter_list:
                    part_parent_name = ""
                    part_data_response = session.get(f'{settings.WEBDATABASE_URL}PlasmidName?name={each}')
                    
                    # if len(part_data_response.history) > 0:
                    #     return JsonResponse({"success":False,"next_url":f"{settings.WEBDATABASE_URL}login"})
                    if part_data_response.status_code == 200:
                        part_plasmid_id = part_data_response.json()['data']['plasmidid']
                        part_parent_response = session.get(f"{settings.WEBDATABASE_URL}GetPartParent?plasmidid={part_plasmid_id}")
                        if(part_parent_response.json()["success"]):
                            part_parent_name = part_parent_response.json()['data'][0]['name']
                        part_alias = part_data_response.json()['data']['alias']
                        part_length = f"{part_data_response.json()['data']['length']}bp"
                        part_ori = part_data_response.json()['data']['ori_info']
                        part_marker = part_data_response.json()['data']['marker_info']
                        part_user = part_data_response.json()['data']['user']
                        Sc_part_promoter_info.append({"name":each,"status":True,"type":"promoter","alias":part_alias,"length":part_length,"ori":part_ori,"marker":part_marker,"part":part_parent_name,"user":part_user})
                    else:
                        Sc_part_promoter_info.append({"name":each,"status":False})
                for each in Sc_Part_CDS_list:
                    part_parent_name = ""
                    part_data_response = session.get(f'{settings.WEBDATABASE_URL}PlasmidName?name={each}')
                    
                    # if len(part_data_response.history) > 0:
                    #     return JsonResponse({"success":False,"next_url":f"{settings.WEBDATABASE_URL}login"})
                    if part_data_response.status_code == 200:
                        part_plasmid_id = part_data_response.json()['data']['plasmidid']
                        part_parent_response = session.get(f"{settings.WEBDATABASE_URL}GetPartParent?plasmidid={part_plasmid_id}")
                        if(part_parent_response.json()["success"]):
                            part_parent_name = part_parent_response.json()['data'][0]['name']
                        part_alias = part_data_response.json()['data']['alias']
                        part_length = f"{part_data_response.json()['data']['length']}bp"
                        part_ori = part_data_response.json()['data']['ori_info']
                        part_marker = part_data_response.json()['data']['marker_info']
                        part_user = part_data_response.json()['data']['user']
                        Sc_part_cds_info.append({"name":each,"status":True,"type":"cds","alias":part_alias,"length":part_length,"ori":part_ori,"marker":part_marker,"part":part_parent_name,"user":part_user})
                    else:
                        Sc_part_cds_info.append({"name":each,"status":False})
                for each in Sc_Part_Terminator_list:
                    part_parent_name = ""
                    part_data_response = session.get(f'{settings.WEBDATABASE_URL}PlasmidName?name={each}')
                    
                    # if len(part_data_response.history) > 0:
                    #     return JsonResponse({"success":False,"next_url":f"{settings.WEBDATABASE_URL}login"})
                    if part_data_response.status_code == 200:
                        part_plasmid_id = part_data_response.json()['data']['plasmidid']
                        part_parent_response = session.get(f"{settings.WEBDATABASE_URL}GetPartParent?plasmidid={part_plasmid_id}")
                        if(part_parent_response.json()["success"]):
                            part_parent_name = part_parent_response.json()['data'][0]['name']
                        part_alias = part_data_response.json()['data']['alias']
                        part_length = f"{part_data_response.json()['data']['length']}bp"
                        part_ori = part_data_response.json()['data']['ori_info']
                        part_marker = part_data_response.json()['data']['marker_info']
                        part_user = part_data_response.json()['data']['user']
                        Sc_part_terminator_info.append({"name":each,"status":True,"type":"terminator","alias":part_alias,"length":part_length,"ori":part_ori,"marker":part_marker,"part":part_parent_name,"user":part_user})
                    else:
                        Sc_part_terminator_info.append({"name":each,"status":False})
                result = Sc_part_promoter_info + Sc_part_cds_info + Sc_part_terminator_info
                return JsonResponse(data={"success":True,"data":result},status=200, safe=False)
            if currentType == "backbone":
                Sc_backbone_info = []
                for each in Sc_Backbone_list:
                    backbone_data_response = session.get(f'{settings.WEBDATABASE_URL}BackboneName?name={each}')
                    # if len(backbone_data_response.history) > 0:
                    #     return JsonResponse({"success":False,"next_url":f"{settings.WEBDATABASE_URL}login"})
                    if backbone_data_response.status_code == 200:
                        data = backbone_data_response.json()['data']
                        backbone_alias = data["alias"]
                        backbone_length = f"{data['length']}bp"
                        backbone_marker = data['marker']
                        backbone_ori = data['ori']
                        backbone_user = data['user']
                        backbone_id = data.get('id')
                        scar_value = _request_scar(session, f'{settings.WEBDATABASE_URL}getBackboneScar?id={backbone_id}')
                        Sc_backbone_info.append({
                            "name":each,
                            "status":True,
                            "alias":backbone_alias,
                            "length":backbone_length,
                            "marker":backbone_marker,
                            "ori":backbone_ori,
                            "user":backbone_user,
                            "scar": scar_value
                        })
                    else:
                        Sc_backbone_info.append({"name":each,"status":False})
                return JsonResponse(data={"success":True, "data":Sc_backbone_info}, status=200, safe=False)
            if currentType == "plasmid":
                Sc_plasmid_info = []
                for each in Sc_Plasmid_list:
                    plasmid_data_response = session.get(f"{settings.WEBDATABASE_URL}PlasmidName?name={each}")
                    # if len(plasmid_data_response.history) > 0:
                    #     return JsonResponse({"success":False,"next_url":f"{settings.WEBDATABASE_URL}login"})
                    if plasmid_data_response.status_code == 200:
                        data = plasmid_data_response.json()['data']
                        plasmid_alias = data['alias']
                        plasmid_length = f"{data['length']}bp"
                        plasmid_ori = data['ori_info']
                        plasmid_marker = data['marker_info']
                        plasmid_user = data['user']
                        plasmid_id = data.get('plasmidid')
                        plasmid_scar = _request_scar(session, f'{settings.WEBDATABASE_URL}getPlasmidScar?plasmidid={plasmid_id}')
                        
                        Sc_plasmid_info.append({
                            'name':each,
                            "status":True,
                            "alias":plasmid_alias,
                            'length':plasmid_length,
                            "ori":plasmid_ori,
                            "marker":plasmid_marker,
                            "user":plasmid_user,
                            "scar": plasmid_scar
                        })
                    else:
                        Sc_plasmid_info.append({"name":each,"status":False})
                return JsonResponse(data={"success":True, "data":Sc_plasmid_info}, status=200, safe=False)

        return JsonResponse(data={"success":False, "message":"invalid category/type"}, status=400, safe=False)
    except requests.RequestException as exc:
        return JsonResponse(
            data={"success":False, "message":f"downstream request failed: {str(exc)}"},
            status=502,
            safe=False,
        )
            
            
def Assembly(request):
    session = __create_session(request)
    request.session["info"] = {"uid":20,"uname":"webtest"}
    if session == None:
        return JsonResponse(data={"success":False,"message":"Login Error"},status=403, safe=False)
    
    plan_name = str(uuid.uuid4())
    if(request.method == "POST"):
        try:
            data = json.loads(request.body)
            
            
            part_list = data['part']
            backbone_list = data['backbone']
            plasmid_list = data["plasmid"]
            part_id_list = []
            #处理Level1
            if(len(part_list) == 1):
                plasmid_id = (session.get(f"{settings.WEBDATABASE_URL}PlasmidID?name={part_list[0]}",cookies=request.COOKIES)).json()["PlasmidID"]
                plasmid_part_id_response = (session.get(f"{settings.WEBDATABASE_URL}GetPartParent?plasmidid={plasmid_id}",cookies=request.COOKIES))
                if plasmid_part_id_response.status_code == 200:
                    part_id_list.append(plasmid_part_id_response.json()["data"][0]["partid"])
                    request_body = {"uuid":plan_name,"part":part_id_list,"backbone":backbone_list,"plasmid":[]}
            else:
                request_body={"uuid":plan_name,"part":[],"backbone":backbone_list,"plasmid":part_list+plasmid_list}
            response = session.post(f"{settings.LABDATABASE_URL}AssemblyWithoutRepo",json=request_body,cookies=request.COOKIES)
            if(response.status_code == 200):
                result = response.json()
                result["name"] = plan_name
                return JsonResponse(data=result,status=200,safe=False)
            else:
                return JsonResponse(data=response.json(),status=400,safe=False)
        except requests.RequestException as exc:
            return JsonResponse(
                data={"success":False, "message":f"downstream request failed: {str(exc)}"},
                status=502,
                safe=False,
            )
    return JsonResponse(data={"success":False, "message":"method not allowed"}, status=405, safe=False)

def task_status(request, taskID):
    session = __create_session(request)
    
    if session == None:
        return JsonResponse(data={"success":False,"message":"Login Error"},status=403, safe=False)
    
    if(request.method == "GET"):
        try:
            response = (session.get(f"{settings.LABDATABASE_URL}task_status/{taskID}"))
            status_code = response.status_code
            return JsonResponse(data=response.json(), status=status_code)
        except requests.RequestException as exc:
            return JsonResponse(
                data={"success":False, "message":f"downstream request failed: {str(exc)}"},
                status=502,
                safe=False,
            )
    return JsonResponse(data={"success":False, "message":"method not allowed"}, status=405, safe=False)

def getAssembly(request,taskID,name):
    session = __create_session(request)
    if session == None:
        return JsonResponse(data={"success":False,"message":"Login Error"},status=403, safe=False)
    
    if(request.method == "GET"):
        try:
            response = session.get(f"{settings.LABDATABASE_URL}getAssembly/{name}?task_id={taskID}",stream=True)
            if(response.status_code != 200):
                return JsonResponse(data={"success":False},status=400, safe=False)
            stream_response = StreamingHttpResponse(response.iter_content(chunk_size=8192))
            stream_response['Content-Type'] = "application/octet-stream"
            
            stream_response['Content-Disposition'] = 'attachment;filename='+name+".gb"
            return stream_response
        except requests.RequestException as exc:
            return JsonResponse(
                data={"success":False, "message":f"downstream request failed: {str(exc)}"},
                status=502,
                safe=False,
            )
    return JsonResponse(data={"success":False, "message":"method not allowed"}, status=405, safe=False)


def gg_assemble(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "method not allowed"}, status=405)

    files = request.FILES.getlist("files")
    if len(files) < 2:
        return JsonResponse(
            {"success": False, "message": "at least two genbank files are required"},
            status=400,
        )

    enzyme = (request.POST.get("enzyme") or "auto").strip().lower()
    output_name = (request.POST.get("output_name") or "GG_Assembly_Result").strip()
    if not output_name:
        output_name = "GG_Assembly_Result"

    try:
        assembled_record = assemble_genbank_files(files, enzyme=enzyme, output_name=output_name)
    except Exception as exc:
        return JsonResponse({"success": False, "message": str(exc)}, status=400)

    sio = io.StringIO()
    SeqIO.write(assembled_record, sio, "genbank")
    content = sio.getvalue()
    response = StreamingHttpResponse(content, content_type="chemical/seq-na-genbank")
    response["Content-Disposition"] = f'attachment; filename="{output_name}.gb"'
    return response

def _configured_download(request, setting_name):
    if request.method != 'GET':
        return JsonResponse({'success': False, 'message': 'GET required'}, status=405)
    file_address = getattr(settings, setting_name, None)
    if not file_address or not os.path.isfile(file_address):
        raise Http404('Download file is not configured or does not exist')
    try:
        stream = open(file_address, 'rb')
    except FileNotFoundError:
        raise Http404('Download file does not exist') from None
    return FileResponse(stream, as_attachment=True)


def getTutorial(request):
    return _configured_download(request, 'TUTORIAL_ADDRESS')


def getZip(request):
    return _configured_download(request, 'ZIP_ADDRESS')


def getTutorialTest(request, doc_path=""):
    site_root = settings.TUTORIAL_SITE_ROOT
    requested = (doc_path or "").strip("/").replace("\\", "/")

    candidates = []
    if not requested:
        candidates.append(os.path.join(site_root, "index.html"))
    else:
        normalized = os.path.normpath(os.path.join(site_root, requested))
        candidates.append(normalized)
        if not os.path.splitext(normalized)[1]:
            candidates.append(os.path.join(normalized, "index.html"))
            candidates.append(f"{normalized}.html")

    resolved_path = None
    site_root_real = os.path.realpath(site_root)
    for candidate in candidates:
        candidate_real = os.path.realpath(candidate)
        try:
            if os.path.commonpath([candidate_real, site_root_real]) != site_root_real:
                continue
        except ValueError:
            continue
        if os.path.isfile(candidate_real):
            resolved_path = candidate_real
            break

    if resolved_path is None:
        raise Http404("Tutorial document not found")

    content_type, encoding = mimetypes.guess_type(resolved_path)
    response = FileResponse(open(resolved_path, "rb"), content_type=content_type or "application/octet-stream")
    if encoding:
        response["Content-Encoding"] = encoding
    return response
