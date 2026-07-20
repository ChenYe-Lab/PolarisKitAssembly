import django.core.exceptions
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.core import serializers
from django.db.utils import OperationalError
import math
import json
import uuid
import re
from datetime import datetime, timedelta
from django.db import transaction, IntegrityError
import time
from django.utils import timezone
from django.conf import settings
# from datetime import datetime
# from zoneinfo import ZoneInfo
from django.db.models import Q
from django.utils.deprecation import MiddlewareMixin
from .models import (Backbonetable,Parentplasmidtable,
                    Partrputable,Parttable,Plasmidneed,
                    Straintable,TbBackboneUserfileaddress,
                    TbPartUserfileaddress,TbPlasmidUserfileaddress, Temporaryrepository,
                    Testdatatable,CustomUser,Lbdnrtable,Lbddimertable,Dbdtable,Parentbackbonetable,\
                    Parentparttable, Partscartable, Backbonescartable, Plasmidscartable, \
                    Plasmid_Culture_Functions,Backbone_Culture_Functions,Backbonefeaturetable,
                    Partfeaturetable, Plasmidfeaturetable,
                    VisitorProfile, VisitorAccessLog, VisitorFeedback)
from django.views.decorators.csrf import csrf_exempt
# from .serializers import StraintableSerializer, BackbonetableSerializer, ParentplasmidtableSerializer, \
#     PartrputableSerializer,ParttableSerializer,PlasmidneedSerializer,TbBackboneUserfileaddressSerializer,\
#     TbPartUserfileaddressSerializer,TbPlasmidUserfileaddressSerializer,TestdatatableSerializer
import logging
import pytz
from .logger import request_logger
from .exceptions import WebDatabaseException,WebDatabaseConflictException,WebDatabasePermissionException,\
                        WebDatabaseNotFoundException,WebDatabaseServerException,WebDatabaseValidationException,\
                        WebDatabaseGETMethodException,WebDatabasePOSTMethodException,WebDatabaseTimeoutException

# print(getattr(settings,"TIME_ZONE"))
tz = pytz.timezone(getattr(settings,"TIME_ZONE"))
timezone.activate(tz)
# print(timezone.localtime(timezone.now()))
def _build_or_keyword_query(raw_keywords, fields):
    """
    Build AND fuzzy query from whitespace-separated keywords.
    Each keyword can match any field (OR within keyword, AND across keywords).
    """
    if raw_keywords is None:
        return None

    keywords = [kw for kw in re.split(r"\s+", str(raw_keywords).strip()) if kw]
    if not keywords:
        return None

    keyword_query = None
    for kw in keywords:
        per_keyword_query = Q()
        for field in fields:
            per_keyword_query |= Q(**{f"{field}__icontains": kw})
        if keyword_query is None:
            keyword_query = per_keyword_query
        else:
            keyword_query &= per_keyword_query
    return keyword_query


UPLOAD_RECORD_TABLES = {
    "parttable": {
        "model": Parttable,
        "id_field": "partid",
        "fields": ("partid", "name", "alias", "type", "user", "tag", "uploaddate", "updatedate"),
    },
    "backbonetable": {
        "model": Backbonetable,
        "id_field": "id",
        "fields": ("id", "name", "alias", "species", "copynumber", "user", "tag", "uploaddate", "updatedate"),
    },
    "plasmidneed": {
        "model": Plasmidneed,
        "id_field": "plasmidid",
        "fields": ("plasmidid", "name", "alias", "level", "state", "user", "tag", "uploaddate", "updatedate"),
    },
}


def _parse_upload_date(value):
    value = str(value or "").strip()
    if re.fullmatch(r"\d{4}-\d{2}", value):
        year, month = map(int, value.split("-"))
        start = datetime(year, month, 1)
        next_start = datetime(year + 1, 1, 1) if month == 12 else datetime(year, month + 1, 1)
        return start, next_start
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        start = datetime.strptime(value, "%Y-%m-%d")
        return start, start + timedelta(days=1)
    raise WebDatabaseException(message="date 只支持 YYYY-MM 或 YYYY-MM-DD")


def _build_upload_record_query(filter_expr):
    expression = str(filter_expr or "").strip()
    if not expression:
        return Q()

    query = Q()
    pattern = re.compile(r"^(date|uploaddate)\s*(>=|<=|=|>|<)\s*(.+)$", re.IGNORECASE)
    for clause in (item.strip() for item in expression.split(",") if item.strip()):
        match = pattern.match(clause)
        if not match:
            raise WebDatabaseException(message=f"不支持的 filter 条件: {clause}")
        _, operator, raw_value = match.groups()
        start, next_start = _parse_upload_date(raw_value)
        if operator == ">=":
            query &= Q(uploaddate__gte=start)
        elif operator == ">":
            query &= Q(uploaddate__gte=next_start)
        elif operator == "<":
            query &= Q(uploaddate__lt=start)
        elif operator == "<=":
            query &= Q(uploaddate__lt=next_start)
        else:
            query &= Q(uploaddate__gte=start, uploaddate__lt=next_start)
    return query


#----------------------------------------------------------


class User_auth(MiddlewareMixin):
    
    def process_request(self,request):
        request.start_time = time.time()
        try:
            #鎺掗櫎涓嶉渶瑕佺櫥褰曞氨鑳借闂殑椤甸潰
            if request.path_info == "/WebDatabase/login" or request.path_info == "/WebDatabase/register" or request.path_info == "/WebDatabase/AdminRegister" or request.path_info == "/WebDatabase/reset":
                return
            info = request.session.get('info')
            #temp
            if(info['uname'] == "wang5042"):
                request.session["info"]["uname"] = "optimus_wang"
            user = request.user
            if user:
                return
            else:
                return redirect('/WebDatabase/login')
            # if not info:
            #     return redirect('/WebDatabase/login')
            # else:
            #     return
        except Exception as e:
            return

    def process_response(self,request,response):
        final_time = time.time()
        duration_time = time.time() - request.start_time
        request_logger.request_log(
            request, response, duration_time
        )
        return response
    def process_exception(self,request,exception):
        if(isinstance(exception, WebDatabaseException)):
            return exception.to_response()
        elif(isinstance(exception, Exception)):
            print('777')
            print(str(exception))
            return JsonResponse(data={"success":False, "message":str(exception)},status=400,safe=False)
        return None
    # if not info:
    #     return JsonResponse({'status': 'Not logged in'})




#-----------------------------------------------------------
#Strain Table
#鏂板鏁版嵁鏂规硶
def SearchByStrainName(request):
    """
    閫氳繃鑿屾牚鍚嶇О锛圢ame锛夎幏鍙栨暣浣撴€т俊鎭?
    Args:
        request: django request
    GET Args:
        name: 鑿屾牚鍚嶇О
    Returns:
        JsonResponse: 1. status_code = 200 list data if search successfully,
        2. status_code = 400/404 string data, if search unsuccessfully
    """
    
    if(request.method == "GET"):
        Name = request.GET.get('name')
        if(Name == None or Name == ""):
            raise WebDatabaseValidationException(parameter="name")
            # return JsonResponse(data="Name cannot be empty", status=400,safe=False)
        StrainList = Straintable.objects.filter(strainname=Name)
        if(len(StrainList) > 0):
            return JsonResponse(data=list(StrainList.values()), status=200,safe=False)
            # return JsonResponse({'code':200,'status': 'success', 'data': list(StrainList.values())})
        else:
            raise WebDatabaseNotFoundException()
            # return JsonResponse(data="No such strain", status=404,safe=False)
            # return JsonResponse({'code':204,'status': 'failed', 'data': "Strain Not Found"})
    else:
        raise WebDatabaseGETMethodException()

#-------------------------------------------------------------
#Part Table
#ALL
def PartFields(request):
    """
    鑾峰彇Parttable鎵€鏈夌浉鍏崇瓫閫変俊鎭」锛屼笉鍖呮嫭arentparttable锛宲artrputable锛宲artscartable锛宼bpartuserfileaddress
    
    Args:
        request: django request
    
    Returns:
        JsonResponse: 1. JsonResponse.json()["success"] = True, JsonResponse.json()['data'] = data, JsonResponse.status_code=200 list if successfully search,
        2. JsonResponse.json()["success"] = False, JsonResponse.json()["message"] = Error Information, JsonResponse.status_code = 400, if search unsuccessfully.
    """
    
    fields =[field.name for field in Parttable._meta.get_fields()]
    fields.remove("parentparttable")
    fields.remove("partrputable")
    fields.remove("partscartable")
    fields.remove("tbpartuserfileaddress")
    fields.remove("partfeaturetable")
    return JsonResponse(data={"success":True, "data":fields}, status = 200, safe=False)
    
def PartCount(request):
    """
    鑾峰彇Part table鐨勬暟鎹潯鏁?
    
    Args:
        request: django request
    
    Returns:
        JsonResponse: 1.JsonResponse.json()["success"]=True, JsonResponse.json()["data"]=integer(鏁版嵁鏉℃暟),JsonResponse.status_code=200 if search successfully,
        2.JsonResponse.json()['success'] = False,JsonResponse.json()["message"] = Error Information, JsonResponse.status_code=400/200 if search unsuccessfully.
    """
    
    if(request.method == "GET"):
        count = Parttable.objects.values().count()
        return JsonResponse(data = {'success':True, "data":count}, status = 200, safe = False)
    else:
        raise WebDatabaseGETMethodException()
        # return JsonResponse(data = {"success":False, "message":"Juset GET method"}, status = 200, safe=False)

def PartDataALL(request):
    """
    鑾峰彇part table鐨勬墍鏈夋暟鎹潯鐩紝浠ame鎺掑簭
    
    Args:
        request: django request
    
    Returns:
        JsonResponse: 1.JsonResponse.json()[0] = a data dict, JsonResponse.status_code = 200, if search successfully and Page = 0
        2.JsonResponse.json() = "No such part", if search successfully
        3.JsonResponse.json()["success"] = True, JsonResponse.json()['data'] = a part data dict in one page, JsonResponse.json()["pagination"] = page information, if search successfully and Page != 0
    
    """
    
    if(request.method == "GET"):
        page = int(request.GET.get('page',0))
        if(page == 0):
            PartData = Parttable.objects.all().order_by('name')
            if(len(PartData) > 0):
                return JsonResponse(data=list(PartData.values()), status=200,safe=False)
                # return JsonResponse({'code':200,'data':list(PartData.values())})
            else:
                raise WebDatabaseNotFoundException()
                # return JsonResponse(data="No such part", status=404,safe=False)
                # return JsonResponse({'code':204,'status': 'failed', 'data': []})
        else:
            page_size = int(request.GET.get('page_size',10))
            offset = (page -1)*page_size
            total_count = Parttable.objects.count()
            total_pages = (total_count + page_size -1) // page_size
            query_set = list(Parttable.objects.order_by('name').values('partid','name','alias','type','sourceorganism','reference','tag'))[offset:offset+page_size]
            # query_set = Parttable.objects.only('partid','name','type','sourceorganism','reference').order_by('name')[offset:offset+page_size]
            has_next = page < total_pages
            has_previous = page > 1
            return JsonResponse(data={'success':True,
                                        'data':query_set,
                                        'pagination':{
                                        'current_page' : page,
                                        'total_pages' : total_pages,
                                        'total_count' : total_count,
                                        'has_next':has_next,
                                        'has_previous' : has_previous,
                                        'page_size':page_size,
                                        'offset':offset
                                        }
                                    },status = 200, safe=False
                                )
#PartFilter
def PartFilter(request):
    """
    Part Table Filter Function, Filter selections are type, Enzyme, Scar, name
    
    Args:
        request: django request
    
    Returns:
        JsonResponse: 1.JsonResponse.json()["success"] = True, JsonResponse.json()["data"] = a list of data dict, JsonResponse.json()["pagination"] = a dict of page information, JsonResponse.status_code = 200, if search successfully
        2.JsonResponse.json()["success"] = False, JsonResponse.json()["error"] = error information, if search unsuccessfully
    """
    if(request.method == "POST"):
        data = json.loads(request.body)
        type = data["type"]
        Enzyme = data['Enzyme']
        Scar = data['Scar']
        name = data['name']
        page = data['page']
        page_size = data['page_size']
        offset = (page - 1) * page_size
        if(type != ""):
            if(type.lower() == "promoter"):
                type = 1
            elif(type.lower() == "terminator"):
                type = 3
            elif(type.lower() == "rbs"):
                type = 4
            elif(type.lower() == "cds"):
                type = 2
            elif(type.lower() == "p+r"):
                type = 5
        scarpartid = []
        if(Enzyme == "BsmBI"):
            scarpartid = list(Partscartable.objects.filter(bsmbi = Scar).values('partid'))
        elif(Enzyme == "BsaI"):
            scarpartid = list(Partscartable.objects.filter(bsai = Scar).values('partid'))
        elif(Enzyme == "BbsI"):
            scarpartid = list(Partscartable.objects.filter(bbsi = Scar).values('partid'))
        elif(Enzyme == "AarI"):
            scarpartid = list(Partscartable.objects.filter(aari = Scar).values('partid'))
        elif(Enzyme == "SapI"):
            scarpartid = list(Partscartable.objects.filter(sapi = Scar).values('partid'))
        if(Enzyme != "" and len(scarpartid) == 0):
            raise WebDatabaseNotFoundException()
            # return JsonResponse(data={'success':False,'error':'No data'}, status = 400, safe = False)
        # result = Parttable.objects
        PartResult = []
        if(len(scarpartid) != 0):
            for each_id in scarpartid:
                result = Parttable.objects
                result = result.filter(partid = each_id['partid'])
                if(type != "" and result != None):
                    # 'partid','name','type','sourceorganism','reference'
                    result = result.filter(type = type)
                if(name != "" and result != None):
                    keyword_query = _build_or_keyword_query(name, ["name", "alias"])
                    if keyword_query is not None:
                        result = result.filter(keyword_query)
                if(result != None):
                    PartResult.append(list(result.order_by('name').values('partid','name','alias','type','sourceorganism','reference','tag'))[0])
        else:
            result = Parttable.objects
            if(type != "" and result != None):
            # 'partid','name','type','sourceorganism','reference'
                result = result.filter(type = type)
            if(name != "" and result != None):
                # print(name)
                keyword_query = _build_or_keyword_query(name, ["name", "alias"])
                if keyword_query is not None:
                    result = result.filter(keyword_query)
            if(result != None):
                PartResult = (list(result.order_by('name').values('partid','name','alias','type','sourceorganism','reference','tag')))
        # print(PartResult)
        if(len(PartResult) != 0):
            total_count = len(PartResult)
            total_pages = (total_count + page_size -1) // page_size
            has_next = page < total_pages
            has_previous = page > 1
            if(len(PartResult) > page_size):
                return JsonResponse(data = {'success':True, 'data': list(PartResult[offset:offset+page_size]),
                                        'pagination':{
                                            'current_page' : page,
                                            'total_pages' : total_pages,
                                            'total_count' : total_count,
                                            'has_next' : has_next,
                                            'has_previous' : has_previous,
                                            'page_size' : page_size,
                                            'offset' : offset
                                            }
                                        },status = 200, safe = False)
            else:
                return JsonResponse(data = {'success':True, 'data': list(PartResult[:]),
                                        'pagination':{
                                            'current_page' : page,
                                            'total_pages' : total_pages,
                                            'total_count' : total_count,
                                            'has_next' : has_next,
                                            'has_previous' : has_previous,
                                            'page_size' : page_size,
                                            'offset' : offset
                                            }
                                        },status = 200, safe = False)
        else:
            return JsonResponse(data = {'success':False, 'data': [],
                                        'pagination':{
                                            'current_page' : 0,
                                            'total_pages' : 0,
                                            'total_count' : 0,
                                            'has_next' : 0,
                                            'has_previous' : 0,
                                            'page_size' : 0,
                                            'offset' : 0
                                            }
                                        },status = 200, safe = False)


#Search
def SearchByPartName(request):
    """
    
    Args:
        request: django request
        
    Returns:
        JsonResponse: 1.JsonResponse.json()["success"] = True, JsonResponse.json()["data"] = A dict of data, JsonResponse.status = 200, if search successfully,
        2. JsonResponse.json() = error information, JsonResponse.status_code = 400/404, if search unsuccessfully
    """
    
    
    if(request.method == "GET"):
        Name = request.GET.get('name')
        # print(Name)
        if(Name == None or Name == ""):
            raise WebDatabaseValidationException(parameter="name")
            # return JsonResponse(data="Name cannot be empty", status=400,safe=False)
            # return JsonResponse({'code':204,'status': 'failed', 'data': "Name cannot be empty"})
        PartList = Parttable.objects.filter(name=Name)
        # print(PartList)
        if(PartList != None):
            print(PartList)
            if len(list(PartList.values())) == 0:
                raise WebDatabaseNotFoundException()
            return JsonResponse(data={"success":True, 'data':list(PartList.values())[0]}, status=200,safe=False)
            # return JsonResponse({'code':200,'status': 'success', 'data': list(PartList.values())})
        else:
            raise WebDatabaseNotFoundException()
                # return JsonResponse(data="No such part", status=404,safe=False)
    


def SearchByPartNameFilter(request):
    """
    
    
    Args:
        request: django request
    
    Returns:
        JsonResponse: 1. JsonResponse.json() = Part dict, JsonResponse.status_code = 200, if search successfully,
        2. JsonResponse.json() = error information, JsonResponse.status_code = 400/404, if search unsuccessfully.
    """
    if(request.method == "GET"):
        Name = request.GET.get('keywords')
        Type = request.GET.get('Type')
        if(Name == None or Name == ""):
            raise WebDatabaseValidationException(parameter = "keywords")
            # return JsonResponse(data="Name cannot be empty",status=400,safe=False)
        else:
            try:
                result = Parttable.objects.filter(type=Type)
                keyword_query = _build_or_keyword_query(Name, ["name", "alias"])
                if keyword_query is not None:
                    result = result.filter(keyword_query)
                promoterResult = list(result.values('partid','name','sourceorganism','reference'))
                if(len(promoterResult[0]) > 0):
                    return JsonResponse(data=promoterResult,status=200,safe=False)
                else:
                    return JsonResponse(data = [],status=200,safe=False)
            except Exception as e:
                return JsonResponse(data = str(e),status=404,safe=False)
    else:
        raise WebDatabaseGETMethodException()



def getBackboneOriAndMarker(Backboneid):
    """
    getBackboneOriAndMarker API view.

    Args:
        Backboneid: Input parameter.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    ori_list = []
    marker_list = []
    ori_info = Backbone_Culture_Functions.objects.filter(backbone_id = Backboneid,function_type = 'ori').values('function_content')
    # print(ori_info)
    marker_info = Backbone_Culture_Functions.objects.filter(backbone_id = Backboneid,function_type = 'marker').values('function_content')
    # if(ori_info == None or marker_info == None):
    #     raise WebDatabaseNotFoundException()
    for each_ori in ori_info:
        ori_list.append(each_ori['function_content'])
    for each_marker in marker_info:
        marker_list.append(each_marker['function_content'])
    return [ori_list, marker_list]
        

def SearchByBackboneNameFilter(request):
    """
    SearchByBackboneNameFilter API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        Name = request.GET.get('keywords')
        if(Name == None or Name == ""):
            raise WebDatabaseValidationException(parameter="keywords")
            # return JsonResponse(data="Name cannot be empty",status=400,safe=False)
        else:
            # backboneResult = list(Backbonetable.objects.filter(name__icontains = Name).values('id','name','ori','marker','species'))
                result = Backbonetable.objects
                keyword_query = _build_or_keyword_query(Name, ["name", "alias"])
                if keyword_query is not None:
                    result = result.filter(keyword_query)
                backboneResult = list(result.values('id','name','species'))
                for each in backboneResult:
                    info_list = getBackboneOriAndMarker(each['id'])
                    each['ori'] = info_list[0]
                    each['marker'] = info_list[1]
                if(len(backboneResult) > 0):
                    return JsonResponse(data=backboneResult,status=200,safe=False)
                else:
                    return JsonResponse(data = [],status=200,safe=False)
    else:
        raise WebDatabaseGETMethodException()


def SearchByPlasmidNameFilter(request):
    """
    SearchByPlasmidNameFilter API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    
    if(request.method == 'GET'):
        Name = request.GET.get('keywords')
        if(Name == None or Name == ""):
            raise WebDatabaseValidationException(parameter="keywords")
            # return JsonResponse(data="Name cannot be empty",status=400,safe=False)
        else:
            result = Plasmidneed.objects
            keyword_query = _build_or_keyword_query(Name, ["name", "alias"])
            if keyword_query is not None:
                result = result.filter(keyword_query)
            plasmidResult = list(result.values('plasmidid','name'))
            if(len(plasmidResult) > 0):
                for each in plasmidResult:
                    info_list = getOriAndMarker(each['plasmidid'])
                    each['ori_info'] = info_list[0]
                    each['marker_info'] = info_list[1]
                return JsonResponse(data = plasmidResult,status=200,safe=False)
            else:
                # raise WebDatabaseNotFoundException()
                return JsonResponse(data = [],status=200,safe=False)
    else:
        raise WebDatabaseGETMethodException()
    

def SearchByPartID(request):
    """
    SearchByPartID API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    
    if(request.method == "GET"):
        ID = request.GET.get('ID')
        if(ID == None or ID == ""):
            raise WebDatabaseValidationException(parameter="ID")
            # return JsonResponse(data="ID cannot be empty", status=400,safe=False)
            # return JsonResponse({'code':204,'status': 'failed', 'data': "Name cannot be empty"})
        PartList = Parttable.objects.filter(partid=ID)
        if(len(PartList) > 0):
            return JsonResponse(data=list(PartList.values()), status=200,safe=False)
            # return JsonResponse({'code':200,'status': 'success', 'data': list(PartList.values())})
        else:
            raise WebDatabaseNotFoundException()
            # return JsonResponse(data="No such part", status=404,safe=False)
            # return JsonResponse({'code':204,'status': 'failed', 'data': []})
    else:
        raise WebDatabaseGETMethodException()
        # return JsonResponse(data="Just Get Method", status=400, safe=False)

def SearchByPartAlterName(request):
    """
    SearchByPartAlterName API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        AlterName = request.GET.get('AlterName')
        if(AlterName == None or AlterName == ""):
            raise WebDatabaseValidationException(parameter="AlterName")
            # return JsonResponse(data="AlterName cannot be empty", status=400,safe=False)
            # return JsonResponse({'code':204,'status': 'failed', 'data': "AlterName cannot be empty"})
        PartList = Parttable.objects.filter(alias=AlterName)
        if(len(PartList) > 0):
            return JsonResponse(data=list(PartList.values()), status=200,safe=False)
            # return JsonResponse({'code':200,'status': 'success', 'data': list(PartList.values())})
        else:
            raise WebDatabaseNotFoundException()
            # return JsonResponse(data="No such part", status=404,safe=False)
            # return JsonResponse({'code':204,'status': 'failed', 'data': []})
    else:
        raise WebDatabaseGETMethodException()


def SearchByPartType(request):
    """
    SearchByPartType API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        Type = request.GET.get('type')
        if(Type == None or Type == ""):
            raise WebDatabaseValidationException(parameter="type")
            # return JsonResponse(data="Type cannot be empty", status=400,safe=False)
            # return JsonResponse({'code':204,'status': 'failed', 'data': "Type cannot be empty"})
        if(Type.lower() == "promoter"):
            PartList = Parttable.objects.filter(type=1)
        elif(Type.lower() == "terminator"):
            PartList = Parttable.objects.filter(type=3)
        elif(Type.lower() == "cds"):
            PartList = Parttable.objects.filter(type=2)
        elif(Type.lower() == "rbs"):
            PartList = Parttable.objects.filter(type=4)
        else:
            PartList = Parttable.objects.filter(type=5)
        if(len(PartList) > 0):
            return JsonResponse(data=list(PartList.values()), status=200,safe=False)
            # return JsonResponse({'code':200,'status': 'success', 'data': list(PartList.values())})
        else:
            raise WebDatabaseNotFoundException()
            # return JsonResponse(data="No such part", status=404,safe=False)
            # return JsonResponse({'code':204,'status': 'failed', 'data': "Part Not Found"})
    else:
        raise WebDatabaseGETMethodException()
    
    
    
def SearchPartTypeByName(request):
    """
    SearchPartTypeByName API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        Name = request.GET.get('name')
        if(Name == None or Name == ""):
            raise WebDatabaseValidationException(parameter="name")
            # return JsonResponse(data="Name cannot be empty", status=400,safe=False)
            # return JsonResponse({'code':204,'status': 'failed', 'data': "Name cannot be empty"})
        Type = Parttable.objects.filter(name=Name).first().type
        if(Type != None):
            if(Type == 1):
                return JsonResponse(data={"Type":"Promoter"},status=200)
                # return JsonResponse({'code':200,'status': 'success', 'data': {"Type":"Promoter"}})
            elif(Type == 2):
                return JsonResponse(data={"Type":"CDS"},status=200)
                # return JsonResponse({'code':200,'status':'success','data':{"Type":"Terminator"}})
            elif(Type == 3):
                # return HttpResponse("CDS")
                return JsonResponse(data={"Type":"Terminator"},status=200)
                # return JsonResponse({'code':200,'status': 'success', 'data': {"Type": "CDS"}})
            elif(Type == 4):
                return JsonResponse(data={"Type":"RBS"},status=200)
                # return JsonResponse({'code':200,'status': 'success', 'data': {"Type": "RBS"}})
            else:
                return JsonResponse(data={"Type":"P+R"}, status=200)
                # return JsonResponse({'code':200,'status': 'success', 'data': {"Type": "Carb"}})
        else:
            raise WebDatabaseNotFoundException()
                # return JsonResponse(data="No such part", status=404,safe=False)
                # return JsonResponse({'code':204,'status': 'failed', 'data': "Part Not Found"})
    else:
        raise WebDatabaseGETMethodException()




def SearchPartTypeByID(request):
    """
    SearchPartTypeByID API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        ID = request.GET.get('ID')
        if(ID == None or ID == ""):
            raise WebDatabaseValidationException(parameter="ID")
            # return JsonResponse(data="ID cannot be empty", status=400,safe=False)
            # return JsonResponse({'code':204,'status': 'failed', 'data': "Name cannot be empty"})
        Type = Parttable.objects.filter(partid=ID).first().type
        if(Type != None):
            if(Type == 1):
                return JsonResponse(data={"Type":"Promoter"},status=200)
                # return JsonResponse({'code':200,'status': 'success', 'data': {"Type":"Promoter"}})
            elif(Type == 3):
                return JsonResponse(data={"Type":"Terminator"},status=200)
                # return JsonResponse({'code':200,'status':'success','data':{"Type":"Terminator"}})
            elif(Type == 2):
                # return HttpResponse("CDS")
                return JsonResponse(data={"Type":"CDS"},status=200)
                # return JsonResponse({'code':200,'status': 'success', 'data': {"Type": "CDS"}})
            elif(Type == 4):
                return JsonResponse(data={"Type":"RBS"},status=200)
                # return JsonResponse({'code':200,'status': 'success', 'data': {"Type": "RBS"}})
            else:
                return JsonResponse(data={"Type":"P+R"}, status=200)
                # return JsonResponse({'code':200,'status': 'success', 'data': {"Type": "Carb"}})
        else:
            raise WebDatabaseNotFoundException()
                # return JsonResponse(data="No such part", status=404,safe=False)
                # return JsonResponse({'code':204,'status': 'failed', 'data': "Part Not Found"})
    else:
        raise WebDatabaseGETMethodException()

# def SearchPartByStrength(request):
#     Strength = float(request.GET.get('strength'))
#     StrengthLow = math.ceil(Strength)
#     StrengthHigh = math.floor(Strength)
#     PartList = Parttable.objects.filter(strength_in=[StrengthLow, StrengthHigh])
#     if(len(PartList) > 0):
#         return HttpResponse(PartList)
#     else:
#         return HttpResponse("")


def SearchByRPU(request):
    """
    SearchByRPU API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if (request.method == "GET"):
        RPU = float(request.GET.get('rpu'))
        if (RPU == None or RPU == 0):
            raise WebDatabaseValidationException(parameter="rpu")
            # return JsonResponse({'code': 204, 'status': 'failed', 'data': "RPU cannot be empty"})
        RPULow = math.ceil(RPU)
        RPUHigh = math.floor(RPU)
        PartIDList = Partrputable.objects.filter(rpu__in=[RPULow, RPUHigh])
        if (len(PartIDList) > 0):
            PartList = []
            for obj in PartIDList:
                PartList.append(list(Parttable.objects.filter(partid=obj.partid.partid).values())[0])
                # PartList.append(obj.partid.values())
            if (len(PartList) > 0):
                return JsonResponse(data=PartList, status=200,safe=False)
                # return JsonResponse({'code': 200, 'status': 'success', 'data': list(PartList)})
        raise WebDatabaseNotFoundException()
        # return JsonResponse({'code': 204, 'status': 'failed', 'data': "Part Not Found"})
    raise WebDatabaseGETMethodException()

def GetPartRPU(request):
    """
    GetPartRPU API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        partID = request.GET.get('partID')
        if(partID == None or partID == ""):
            raise WebDatabaseValidationException(parameter="partID")
            # return JsonResponse("PartID cannot be empty", status = 400, safe=False)
        PartRPUList = Partrputable.objects.filter(partid = partID)
        if(len(PartRPUList) > 0):
            return JsonResponse(data=list(PartRPUList.values()),status=200,safe=False)
        else:
            raise WebDatabaseNotFoundException()
    raise WebDatabaseGETMethodException()


def SearchBySeq(request):
    """
    SearchBySeq API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        Seq = request.GET.get('seq')
        if(Seq == None or Seq == ""):
            raise WebDatabaseValidationException(parameter="seq")
            # return JsonResponse(data="Seq cannot be empty", status=400,safe=False)
            # return JsonResponse({'code':204,'status': 'failed', 'data': "Sequence cannot be empty"})
        PartList = Parttable.objects.filter(level0sequence__contains=Seq)
        if len(PartList) > 0:
            # return HttpResponse(PartList)
            return JsonResponse(data=list(PartList.values()), status=200,safe=False)
            # return JsonResponse({'code':200,'status': 'success', 'data': list(PartList.values())})
        else:
            raise WebDatabaseNotFoundException()
            # return JsonResponse(data="No such part", status=404,safe=False)
            # return JsonResponse({'code':204,'status': 'failed', 'data': "Part Not Found"})
    raise WebDatabaseGETMethodException()

def SearchPartFile(request):
    """
    SearchPartFile API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        Name = request.GET.get('name')
        if(Name == None or Name == ""):
            raise WebDatabaseValidationException(parameter="name")
            # return JsonResponse(data="Name cannot be empty", status=400,safe=False)
            # return JsonResponse({'code':204,'status': 'failed', 'data': "Name cannot be empty"})
        PartID = Parttable.objects.filter(name=Name).first()
        if(PartID == None):
            raise WebDatabaseNotFoundException()
            # return JsonResponse(data="No such part", status=404,safe=False)
            # return JsonResponse({'code':204,'status': 'failed', 'data': "Part Not Found"})
        PartID = PartID.id
        userid = request.session.get('info')['uid']
        FilterDict = {"partid":PartID,"userid":userid}
        # Address = TbPartUserfileaddress.objects.filter(**FilterDict).first()
        Obj = TbPartUserfileaddress.objects.filter(**FilterDict).first()
        if(Obj!=None):
            return JsonResponse(data={"FileAddress":Obj.fileaddress}, status=200)
            # return JsonResponse({'code':200,'status': 'success', 'data': {"FileAddress":Address}})
        else:
            raise WebDatabaseNotFoundException()
            # return JsonResponse(data="No such par file address", status=404,safe=False)
            # return JsonResponse({'code':204,'status': 'failed', 'data': "Address Not Found"})
    raise WebDatabaseGETMethodException()

#Add
def AddPartRPU(request):
    """
    AddPartRPU API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "POST"):
        name = request.POST.get('Name')
        if(name == None or name == ""):
            raise WebDatabaseValidationException(parameter="Name")
            # return JsonResponse(data="Name cannot be empty", status=400,safe=False)
            # return JsonResponse({'code':204,'status': 'failed', 'data': "Name cannot be empty"})
        PartID = Parttable.objects.filter(name=name).first()
        if(PartID == None):
            raise WebDatabaseNotFoundException()
            # return JsonResponse({'code':204,'status': 'failed', 'data': 'Part Not Found'})
        rpu = float(request.POST.get('rpu'))
        testStrain = request.POST.get('testStrain')
        Note = request.POST.get('Note')
        Partrputable.objects.create(partid=PartID.partid, rpu=rpu, testStrain=testStrain,note=Note)
        return JsonResponse(data="Added part rpu", status=200)
        # return JsonResponse({'code':200,'status': 'success','data':'Part RPU added'})
    raise WebDatabasePOSTMethodException()

def AddPartData(request):
    """
    AddPartData API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "POST"):
        data = json.loads(request.body)
        # print(data)
        name = data['name']
        alias = data['alias']
        if(data['Level0Sequence'] != ""):
            length = len(data['Level0Sequence'])
            level0Seq = data['Level0Sequence']
        else:
            length = 0
            level0Seq = ""
        ConfirmedSequence = data['ConfirmedSequence'] if'ConfirmedSequence' in data else ""
        InsertSequence = data['InsertSequence'] if 'InsertSequence' in data else ""
        sourceOrganism = data['source'] if 'source' in data else ""
        reference = data['reference']  if 'reference' in data else ""
        note = data['note'] if 'note' in data else ""
        type = data['type']
        if(type == None or type == ""):
            raise WebDatabaseValidationException(parameter = "type")
        if(type.lower() == "promoter"):
            type = 1
        elif(type.lower() == "terminator"):
            type = 3
        elif(type.lower() == "cds"):
            type = 2
        elif(type.lower() == "rbs"):
            type = 4
        elif(type.lower() == "p+r"):
            type = 5
        username = request.session['info']['uname']
        if(name == "" or name == None):
            raise WebDatabaseValidationException(parameter="name")
            # return JsonResponse({'code':204,'status': 'failed', 'data': 'Name or Sequence can not be empty'})
        exist_part = Parttable.objects.filter(name__iexact=name).first()
        if(exist_part != None):
            updateDate = timezone.localtime(timezone.now())
            if(alias != ""):
                exist_part.update(alias=alias)
            if(length != 0):
                exist_part.update(lengthinlevel0=length, level0sequence=level0Seq)
            if(ConfirmedSequence != ""):
                exist_part.update(confirmedsequence = ConfirmedSequence)
            if(InsertSequence != ""):
                exist_part.update(insertsequence = InsertSequence)
            if(sourceOrganism != ""):
                exist_part.update(sourceorganism = sourceOrganism)
            if(reference != ""):
                exist_part.update(reference = reference)
            if(note != ""):
                exist_part.update(note = note)
            if(type != None):
                exist_part.update(type = type)
            exist_part.update(user=username, updatedate = updateDate)
        else:
            uploadDate = timezone.localtime(timezone.now())
            updateDate = timezone.localtime(timezone.now())
            try:
                Parttable.objects.create(name=name, alias=alias, lengthinlevel0=length, level0sequence=level0Seq,
                                    confirmedsequence = ConfirmedSequence, insertsequence = InsertSequence,
                                    sourceorganism = sourceOrganism, reference=reference, note=note, type=type,user=username,
                                    uploaddate = uploadDate, updatedate = updateDate)
            except IntegrityError:
                return JsonResponse(data={"success":False, "message":"Part name already exists"}, status=409, safe=False)
        return JsonResponse(data={"success":True}, status=200,safe=False)
        # return JsonResponse({'code':200,'status': 'success','data':'Part data added'})
    raise WebDatabasePOSTMethodException()


def AddPartFileAddress(request):
    """
    AddPartFileAddress API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "POST"):
    # if(request.method == "GET"):
        userid = request.session.get('info')['uid']
        # userid = 8
        # print(userid)
        partName = request.POST.get('PartName')
        fileAddress = request.POST.get('fileAddress')
        # partName=request.GET.get('name')
        # fileAddress = "TTT"
        if(partName == None or partName == ""):
            raise WebDatabaseValidationException(parameter="PartName")
        if(fileAddress == None or fileAddress == ""):
            raise WebDatabaseValidationException(parameter="fileAddress")
            # return JsonResponse(data="Parameters cannot be empty", status=400,safe=False)
        partID = Parttable.objects.filter(name=partName).first()
        if(partID == None):
            raise WebDatabaseNotFoundException()
            # return JsonResponse({'code':204,'status': 'failed', 'data': 'Part Not Found'})
        # uid = User.objects.get(uid=userid)
        user = CustomUser.objects.filter(uid=userid).first()
        TbPartUserfileaddress.objects.create(userid=user, partid=partID, fileaddress=fileAddress)

        return JsonResponse(data="Added part address", status=200,safe=False)
        # return JsonResponse({'code':200,'status': 'success','data':'Part file address added'})
    raise WebDatabasePOSTMethodException()

#Update
def UpdatePart(request):
    """
    UpdatePart API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "POST"):
        data = json.loads(request.body)
        if('OriginalName' in data):
            OriginalName = data['OriginalName']
            PartID = Parttable.objects.get(name=OriginalName).id
        elif('PartID' in data):
            PartID = data['PartID']
        if(PartID == None):
            raise WebDatabaseNotFoundException()
            # return JsonResponse({'code':204,'status': 'failed', 'data': 'Part Not Found'})
        NewName = data['Name']
        NewAlias = data['Alias']
        NewType = data['Type']
        NewLength = len(data['Level0Sequence'])
        NewLevel0Sequence = data['Level0Sequence']
        NewConfirmedSequence = data['ConfirmedSequence']
        NewInsertSequence = data['InsertSequence']
        NewSourceOrganism = data["source"]
        NewReference = data["reference"]
        NewNote = data["note"]
        if(NewName == None or NewName == ""):
            raise WebDatabaseValidationException(parameter="Name")
            # return JsonResponse(data="Parameters Name cannot be empty", status=400,safe=False)
        if(Parttable.objects.filter(name__iexact=NewName).exclude(partid=PartID).exists()):
            raise WebDatabaseNotFoundException()
            # return JsonResponse(data={"success":False, "message":"Part name already exists"}, status=409, safe=False)
        updateDate = timezone.localtime(timezone.now())
        # print(updateDate)
        try:
            Parttable.objects.filter(partid = PartID).update(name=NewName, alias=NewAlias,type=NewType,lengthinlevel0=NewLength,
                                                               level0sequence=NewLevel0Sequence,confirmedsequence=NewConfirmedSequence,
                                                               insertsequence=NewInsertSequence,sourceorganism = NewSourceOrganism,
                                                               reference=NewReference,note=NewNote, updatedate = updateDate,user=request.session.get('info')['uname'])
        except IntegrityError:
            return JsonResponse(data={"success":False, "message":"Part name already exists"}, status=409, safe=False)
        # print("11111112222")
        return JsonResponse(data="Updated part data", status=200,safe=False)
        # return JsonResponse({'code':200,'status': 'success','data':'Part data updated'})
    raise WebDatabasePOSTMethodException()


def UpdatePartRPU(request):
    """
    UpdatePartRPU API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "POST"):
        Name = request.POST.get('Name')
        rpu = float(request.POST.get('rpu'))
        testStrain = request.POST.get('testStrain')
        note = request.POST.get('note')
        if(Name == None or Name == ""):
            raise WebDatabaseValidationException(parameter = "Name")
        if(rpu == None or rpu == 0):
            raise WebDatabaseValidationException(parameter = "rpu")
        if(testStrain == None or testStrain == ""):
            raise WebDatabaseValidationException(parameter = "testStrain")
            # return JsonResponse(data="Name cannot be empty", status=400,safe=False)
            # return JsonResponse({'code':204,'status': 'failed', 'data': 'Name, rpu, testStrain can not be empty'})
        partID = Parttable.objects.filter(name=Name).first().id
        if(partID == None):
            raise WebDatabaseNotFoundException()
            # return JsonResponse(data="No such part rpu", status=404,safe=False)
            # return JsonResponse({'code':204,'status': 'failed', 'data': 'Part Not Found'})
        filterDict = {"partid":partID,"testStrain":testStrain}
        Partrputable.objects.filter(**filterDict).update(rpu=rpu,note=note)
        return JsonResponse(data="Updated part rpu", status=200)
        # return JsonResponse({'code':200,'status': 'success','data':'Part RPU updated'})
    raise WebDatabasePOSTMethodException()

def UpdatePartFileAddress(request):
    """
    UpdatePartFileAddress API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "POST"):
        PartName = request.POST.get('PartName')
        Address = request.POST.get('Address')
        userid = request.session.get('info')['uid']
        if(PartName == None or PartName == ""):
            raise WebDatabaseValidationException(parameter="PartName")
        if(Address == None or Address == ""):
            raise WebDatabaseValidationException(parameter = "Address")
            # return JsonResponse(data="Name cannot be empty", status=400,safe=False)
            # return JsonResponse({'code':204,'status': 'failed', 'data': 'PartName, Address can not be empty'})
        PartID = Parttable.objects.get(name=PartName).partid
        if(PartID == None):
            raise WebDatabaseNotFoundException()
            # return JsonResponse(data="No such part", status=404,safe=False)
            # return JsonResponse({'code':204,'status': 'failed', 'data': 'Part Not Found'})
        filterDict = {"PartID":PartID,"userid":userid}
        TbPartUserfileaddress.objects.filter(**filterDict).update(userid=userid,partid=PartID,fileaddress=Address)
        return JsonResponse(data="Added part address", status=200)
        # return JsonResponse({'code':200,'status': 'success','data':'Part file address updated'})
    raise WebDatabasePOSTMethodException()
#Delete
def deletePartData(request):
    """
    deletePartData API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        # name = request.GET.get('name')
        # if(name == None or name == ""):
        #     return JsonResponse(data={"success":False, "messsage":"Name cannot be empty"}, status=400,safe=False)
        #     # return JsonResponse({'code':204,'status': 'failed', 'data': 'Name can not be empty'})
        PartID = request.GET.get("partid")
        username = request.user.uname
        partuploaduser = Parttable.objects.get(partid = PartID).user
        if(partuploaduser == "" or partuploaduser == None or (username != partuploaduser and request.user.email != partuploaduser)):
            raise WebDatabasePermissionException()
            # return JsonResponse(data = {"success":False, "message" : "褰撳墠鐢ㄦ埛娌℃湁鍒犻櫎鏉冮檺锛岃鑱旂郴涓婁紶鐢ㄦ埛杩涜鍒犻櫎"},status = 400, safe=False)
        if(PartID == None):
            raise WebDatabaseNotFoundException()
            # return JsonResponse(data={"success":False, "message":"No such part"}, status=404,safe=False)
            # return JsonResponse({'code':204,'status': 'failed', 'data': 'Part Not Found'})
        TbPartUserfileaddress.objects.filter(partid=PartID).delete()
        Partrputable.objects.filter(partid=PartID).delete()
        Partfeaturetable.objects.filter(partid=PartID).delete()
        Parttable.objects.filter(partid = PartID).delete()
        return JsonResponse(data={"success":True}, status=200)
        # return JsonResponse({'code':200,'status': 'success','data':'Part data deleted'})
    raise WebDatabasePOSTMethodException()

def deletePartFile(request):
    """
    deletePartFile API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        userid = request.session.get('info')['uid']
        name = request.GET.get('name')
        if(name == None or name == ""):
            raise WebDatabaseValidationException(parameter="name")
            # return JsonResponse(data="Name cannot be empty", status=400,safe=False)
            # return JsonResponse({'code':204,'status': 'failed', 'data': 'Name can not be empty'})
        PartID = Parttable.objects.get(name=name).id
        if(PartID == None):
            raise WebDatabaseNotFoundException()
            # return JsonResponse(data="No such part", status=404,safe=False)
            # return JsonResponse({'code':204,'status': 'failed', 'data': 'Part Not Found'})
        FilterDict = {"userid":userid,"partid":PartID}
        TbPartUserfileaddress.objects.filter(**FilterDict).delete()
        return JsonResponse(data="Deleted part", status=200)
        # return JsonResponse({'code':200,'status': 'success','data':'Part file address deleted'})
    raise WebDatabaseGETMethodException()
    
def PartListByUser(request,username):
    """
    PartListByUser API view.

    Args:
        request: Django HttpRequest object.
        username: Input parameter.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        if(username == None or username == ""):
            raise WebDatabaseValidationException(parameter = "username")
            # return JsonResponse(data = {"success":False, "message":"Parameter cannot be empty"}, status=400, safe=False)
        else:
            result = list(Parttable.objects.filter(user = username).values())
            return JsonResponse(data={"success":True, "data":result}, status = 200, safe= False)
    else:
        raise WebDatabaseGETMethodException()
        # return JsonResponse(data={"success":False,"message":"Just GET method"},status =400, safe=False)


def GetPartSource(request, partID):
    """
    GetPartSource API view.

    Args:
        request: Django HttpRequest object.
        partID: Input parameter.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        try:
            source = Parttable.objects.get(partid = partID).sourceorganism
            return JsonResponse(data={"success":True,"source":source},status=200,safe=False)
        except Parttable.DoesNotExist:
            raise WebDatabaseNotFoundException()
    else:
        raise WebDatabaseGETMethodException()



#---------------------------------------------------------------
#pladmid need
def PlasmidCount(request):
    """
    PlasmidCount API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        count = Plasmidneed.objects.values().count()
        return JsonResponse(data={"success":True, "data":count}, status = 200, safe=False)
    else:
        raise WebDatabaseGETMethodException()
        # return JsonResponse(data={"success":False, "message":"Just GET method"}, status = 200, safe=False)
def getOriAndMarker(plasmid_id):
    """
    getOriAndMarker API view.

    Args:
        plasmid_id: Input parameter.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    # print("8888888888888888")
    ori_list = []
    marker_list = []
    ori_info = Plasmid_Culture_Functions.objects.filter(plasmid_id = plasmid_id,function_type = 'ori').values('function_content')
    # print(ori_info)
    marker_info = Plasmid_Culture_Functions.objects.filter(plasmid_id = plasmid_id,function_type = 'marker').values('function_content')
    for each_ori in ori_info:
        ori_list.append(each_ori['function_content'])
    for each_marker in marker_info:
        marker_list.append(each_marker['function_content'])
    # print([ori_list, marker_list])
    return [ori_list, marker_list]

def getdefaultplasmidscar(plasmidid):
    """
    getdefaultplasmidscar API view.

    Args:
        plasmidid: Input parameter.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    plasmid_obj = Plasmidscartable.objects.filter(plasmidid = plasmidid).first()
    if plasmid_obj != None:
        return plasmid_obj.bsai+"/"+plasmid_obj.bbsi
    else:
        return "No Sequence"

def PlasmidDataALL(request):
    """
    PlasmidDataALL API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        page = int(request.GET.get('page',0))
        if(page == 0):
            PlasmidData = list(Plasmidneed.objects.all().order_by('name').values())
            if(len(PlasmidData) > 0):
                for each in PlasmidData:
                    info_list = getOriAndMarker(each['plasmidid'])
                    each['ori_info'] = info_list[0]
                    each['marker_info'] = info_list[1]
                    # print(each['plasmidid'])
                    each['scar'] = getdefaultplasmidscar(each['plasmidid'])
                    # print(each)
                return JsonResponse(data=PlasmidData, status=200,safe=False)
                # return JsonResponse({'code':200,'data':list(PartData.values())})
            else:
                raise WebDatabaseNotFoundException()
                # return JsonResponse(data="No plasmid", status=404,safe=False)
                # return JsonResponse({'code':204,'status': 'failed', 'data': []})
        else:
            page_size = int(request.GET.get('page_size',10))
            offset = (page -1)*page_size
            total_count = Plasmidneed.objects.count()
            total_pages = (total_count + page_size -1) // page_size
            # query_set = Plasmidneed.objects.only('plasmidid','name','oricloning','orihost','markercloning','markerhost','level').all().order_by('name')[offset:offset+page_size]
            query_set = list(Plasmidneed.objects.order_by('name').values('plasmidid','name','alias','level','tag'))[offset:offset+page_size]
            for each_plasmid in query_set:
                info_list = getOriAndMarker(each_plasmid['plasmidid'])
                each_plasmid['ori_info'] = info_list[0]
                each_plasmid['marker_info'] = info_list[1]
                each_plasmid['scar'] = getdefaultplasmidscar(each_plasmid['plasmidid'])
                # print(each_plasmid)
            # print(query_set)
            has_next = page < total_pages
            has_previous = page > 1
            return JsonResponse(data={'success':True,
                                      'data':query_set,
                                      'pagination':{
                                          'current_page' : page,
                                          'total_pages' : total_pages,
                                          'total_count' : total_count,
                                          'has_next':has_next,
                                          'has_previous' : has_previous,
                                          'page_size':page_size,
                                          'offset':offset
                                          }
                                        },status = 200, safe=False
                                )

#Plasmid Filter

def PlasmidFilter(request):
    """
    PlasmidFilter API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == 'POST'):
        data = json.loads(request.body)
        Name = data['name']
        Ori = data['ori']
        Marker = data['marker']
        Enzyme = data['Enzyme']
        Scar = data['Scar']
        page = data['page']
        page_size = data['page_size']
        offset = (page -1)*page_size
        scarplasmidid = []
        if(Enzyme == "BsmBI"):
            scarplasmidid = list(Plasmidscartable.objects.filter(bsmbi = Scar).values('plasmidid'))
        elif(Enzyme == "BsaI"):
            scarplasmidid = list(Plasmidscartable.objects.filter(bsai = Scar).values('plasmidid'))
        elif(Enzyme == "BbsI"):
            scarplasmidid = list(Plasmidscartable.objects.filter(bbsi = Scar).values('plasmidid'))
        elif(Enzyme == "AarI"):
            scarplasmidid = list(Plasmidscartable.objects.filter(aari = Scar).values('plasmidid'))
        elif(Enzyme == "SapI"):
            scarplasmidid = list(Plasmidscartable.objects.filter(sapi = Scar).values('plasmidid'))
        if(Enzyme != "" and len(scarplasmidid) == 0):
            raise WebDatabaseNotFoundException()
            # return JsonResponse(data={'success':False,'error':'No data'}, status = 404, safe = False)
        PlasmidResult = []
        if(len(scarplasmidid) != 0):
            for each_id in scarplasmidid:
                result = Plasmidneed.objects
                if(Ori != ""):
                    Ori_result = Plasmid_Culture_Functions.objects.filter(plasmid_id = each_id['plasmidid'], function_content = Ori, function_type="ori").values()
                    if(Ori_result == None):
                        continue
                if(Marker != ""):
                    Marker_result = Plasmid_Culture_Functions.objects.filter(plasmid_id = each_id['plasmidid'],function_content = Marker, function_type="marker").values()
                    if(Marker_result == None):
                        continue
                result = result.filter(plasmidid = each_id['plasmidid'])
                if(Name != '' and result != None):
                    keyword_query = _build_or_keyword_query(Name, ["name", "alias"])
                    if keyword_query is not None:
                        result = result.filter(keyword_query)
                result = result.order_by('name').values('plasmidid','name','alias','level','tag')
                if(result != None and len(list(result)) != 0):
                    temp_result = list(result)[0]
                    # 'plasmidid','name','oricloning','orihost','markercloning','markerhost','level'
                    info_list = getOriAndMarker(temp_result['plasmidid'])
                    temp_result['ori_info'] = info_list[0]
                    temp_result['marker_info'] = info_list[1]
                    temp_result['scar'] = Scar
                    PlasmidResult.append(temp_result)
        else:
            Ori_plasmid_id_list = set()
            Marker_plasmid_id_list = set()
            final_plasmid_id_list = set()
            if(Ori != ""):
                Ori_result = Plasmid_Culture_Functions.objects.filter(function_content = Ori, function_type="ori").values("plasmid_id")
                for each in Ori_result:
                    Ori_plasmid_id_list.add(each['plasmid_id'])
            if(Marker != ""):
                Marker_result = Plasmid_Culture_Functions.objects.filter(function_content = Marker, function_type="marker").values("plasmid_id")
                for each in Marker_result:
                    Marker_plasmid_id_list.add(each['plasmid_id'])
            if(Ori != "" and Marker != ""):
                final_plasmid_id_list = Ori_plasmid_id_list & Marker_plasmid_id_list
            else:
                final_plasmid_id_list = Ori_plasmid_id_list | Marker_plasmid_id_list
            # print(Ori_plasmid_id_list)
            # print(Marker_plasmid_id_list)
            # print(final_plasmid_id_list)
            if(len(final_plasmid_id_list) == 0):
                # if(Name != "" and result != None):
                #     result = result.filter(Q(name__icontains = Name) | Q(alias__icontains = Name))
                # if(result != None):
                if(Ori != "" or Marker != ""):
                    return JsonResponse(data = {'success':False, 'data': [],
                                        'pagination':{
                                            'current_page' : 0,
                                            'total_pages' : 0,
                                            'total_count' : 0,
                                            'has_next' : 0,
                                            'has_previous' : 0,
                                            'page_size' : 0,
                                            'offset' : 0
                                            }
                                        },status = 200, safe = False)
                    # PlasmidResult = (list(result.order_by('name').values('plasmidid','name','alias','oricloning','orihost','markercloning','markerhost','level')))
                else:
                    PlasmidResult = []
                    result = Plasmidneed.objects
                    if(Name != "" and result != None):
                        keyword_query = _build_or_keyword_query(Name, ["name", "alias"])
                        if keyword_query is not None:
                            result = result.filter(keyword_query)
                    if(len(result) != 0):
                        temp_result = list(result.values('plasmidid','name','alias','level','tag'))
                        # print(temp_result)
                        for each in temp_result:
                            try:
                                info_list = getOriAndMarker(each['plasmidid'])
                                each['ori_info'] = info_list[0]
                                each['marker_info'] = info_list[1]
                                # print(info_list)
                                each['scar'] = getdefaultplasmidscar(each['plasmidid'])
                            except Plasmidscartable.DoesNotExist:
                                each['scar'] = "No Sequence"
                            except Plasmid_Culture_Functions.DoesNotExist:
                                each['ori_info'] = ["No Sequence"]
                                each['marker_info'] = ["No Sequence"]
                            PlasmidResult.append(each)
            else:
                PlasmidResult = []
                for each_id in final_plasmid_id_list:
                    result = Plasmidneed.objects.filter(plasmidid = each_id)
                    if(Name != "" and result != None):
                        keyword_query = _build_or_keyword_query(Name, ["name", "alias"])
                        if keyword_query is not None:
                            result = result.filter(keyword_query)
                    if(len(result) != 0):
                        temp_result = (list(result.values('plasmidid','name','alias','level','tag')))[0]
                        info_list = getOriAndMarker(temp_result['plasmidid'])
                        temp_result['ori_info'] = info_list[0]
                        temp_result['marker_info'] = info_list[1]
                        temp_result['scar'] = getdefaultplasmidscar(temp_result['plasmidid'])
                        PlasmidResult.append(temp_result)
        if(len(PlasmidResult) != 0):
            total_count = len(PlasmidResult)
            total_pages = (total_count + page_size -1) // page_size
            has_next = page < total_pages
            has_previous = page > 1
            if(len(PlasmidResult) < page_size):
                return JsonResponse(data = {'success':True, 'data': list(PlasmidResult[:]),
                                        'pagination':{
                                            'current_page' : page,
                                            'total_pages' : total_pages,
                                            'total_count' : total_count,
                                            'has_next' : has_next,
                                            'has_previous' : has_previous,
                                            'page_size' : page_size,
                                            'offset' : offset
                                            }
                                        })
            return JsonResponse(data = {'success':True, 'data': list(PlasmidResult[offset:offset+page_size]),
                                        'pagination':{
                                            'current_page' : page,
                                            'total_pages' : total_pages,
                                            'total_count' : total_count,
                                            'has_next' : has_next,
                                            'has_previous' : has_previous,
                                            'page_size' : page_size,
                                            'offset' : offset
                                            }
                                        })
        else:
            return JsonResponse(data = {'success':False, 'data': [],
                                        'pagination':{
                                            'current_page' : 0,
                                            'total_pages' : 0,
                                            'total_count' : 0,
                                            'has_next' : 0,
                                            'has_previous' : 0,
                                            'page_size' : 0,
                                            'offset' : 0
                                            }
                                        },status = 200, safe = False)
    else:
        raise WebDatabasePOSTMethodException()

#search
def SearchByPlasmidName(request):
    """
    SearchByPlasmidName API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        Name = request.GET.get('name')
        if(Name == None or Name == ""):
            raise WebDatabaseValidationException(parameter="name")
            # return JsonResponse(data="Name cannot be empty", status=400,safe=False)
            # return JsonResponse({'code':204,'status': 'failed', 'data': 'Name can not be empty'})
        PlasmidList = Plasmidneed.objects.filter(name=Name)
        if(PlasmidList != None):
            PlasmidResultList = list(PlasmidList.values())[0]
            culture_function = getOriAndMarker(PlasmidResultList['plasmidid'])
            PlasmidResultList['ori_info'] = culture_function[0]
            PlasmidResultList['marker_info'] = culture_function[1]
            return JsonResponse(data={"success":True, "data":PlasmidResultList}, status=200,safe=False)
            # return JsonResponse({'code':200,'status':'success','data':list(PlasmidList.values())})
        else:
            raise WebDatabaseNotFoundException()
            # return JsonResponse(data="No such Plasmid", status=404,safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':"Plamsid Not Found"})
    else:
        raise WebDatabaseGETMethodException()

def SearchByPlasmidID(request):
    """
    SearchByPlasmidID API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        ID = request.GET.get('ID')
        if(ID == None or ID == ""):
            raise WebDatabaseValidationException(parameter="ID")
            # return JsonResponse(data="ID cannot be empty", status=400,safe=False)
            # return JsonResponse({'code':204,'status': 'failed', 'data': 'Name can not be empty'})
        PlasmidList = list(Plasmidneed.objects.filter(plasmidid=ID).values())
        if(len(PlasmidList) > 0):
            for each in PlasmidList:
                info_list = getOriAndMarker(each['plasmidid'])
                each["ori_info"] = info_list[0]
                each["marker_info"] = info_list[1]
            return JsonResponse(data=PlasmidList, status=200,safe=False)
            # return JsonResponse({'code':200,'status':'success','data':list(PlasmidList.values())})
        else:
            raise WebDatabaseNotFoundException()
            # return JsonResponse(data="No such Plasmid", status=404,safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':"Plamsid Not Found"})
    else:
        raise WebDatabaseGETMethodException()

def SearchByPlasmidAlterName(request):
    """
    SearchByPlasmidAlterName API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        AlterName = request.GET.get('altername')
        if(AlterName == None or AlterName == ""):
            raise WebDatabaseValidationException(parameter="altername")
            # return JsonResponse(data="AlterName cannot be empty", status=400,safe=False)
            # return JsonResponse({'code':204,'status': 'failed', 'data': 'Name can not be empty'})
        PlasmidList = list(Plasmidneed.objects.filter(alter_name=AlterName).values())
        if(len(PlasmidList) > 0):
            for each in PlasmidList:
                info_list = getOriAndMarker(each['plasmidid'])
                each['ori_info'] = info_list[0]
                each['marker_info'] = info_list[0]
            return JsonResponse(data=PlasmidList, status=200)
            # return JsonResponse({'code':200,'status':'success','data':list(PlasmidList.values())})
        else:
            raise WebDatabaseNotFoundException()
            # return JsonResponse(data="No such Plasmid", status=404,safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':[]})
    else:
        raise WebDatabaseGETMethodException()

def SearchByPlasmidSeq(request):
    """
    SearchByPlasmidSeq API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        Seq = request.GET.get('seq')
        if(Seq == None or Seq == ""):
            raise WebDatabaseValidationException(parameter="seq")
            # return JsonResponse(data="Seq cannot be empty", status=400,safe=False)
            # return JsonResponse({'code':204,'status': 'failed', 'data': 'Seq can not be empty'})
        PlasmidList = list(Plasmidneed.objects.filter(sequenceconfirm__contains=Seq).values())
        if(len(PlasmidList) > 0):
            for each in PlasmidList:
                info_list = getOriAndMarker(each['plasmidid'])
                each['ori_info'] = info_list[0]
                each['marker_info'] = info_list[1]
            return JsonResponse(data=PlasmidList, status=200,safe = False)
            # return JsonResponse({'code':200,'status':'success','data':list(PlasmidList.values())})
        else:
            raise WebDatabaseNotFoundException()
            # return JsonResponse(data="No such Plasmid", status=404,safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':[]})
    else:
        raise WebDatabaseGETMethodException()
    
def SearchPlasmidSequenceByName(request):
    """
    SearchPlasmidSequenceByName API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        Name = request.GET.get('name')
        if(Name == None or Name ==""):
            raise WebDatabaseValidationException(parameter="name")
            # return JsonResponse(data="Name cannot be empty", status=400,safe=False)
            # return JsonResponse({'code':204,'status': 'failed', 'data': 'Name can not be empty'})
        PlasmidList = Plasmidneed.objects.filter(name=Name)
        result = []
        if(len(PlasmidList) > 0):
            for obj in PlasmidList:
                temp = {}
                temp["Name"] = obj.name
                temp["Sequence"] = obj.sequenceconfirm
                result.append(temp)
            if(len(result) > 0):
                return JsonResponse(data=result, status=200)
                # return JsonResponse({'code':200,'status':'success','data':result})
            else:
                raise WebDatabaseNotFoundException()
                # return JsonResponse(data="No such Plasmid", status=404,safe=False)
                # return JsonResponse({'code':204,'status':'failed','data':'Plasmid Not Found'})
        else:
            raise WebDatabaseNotFoundException()
            # return JsonResponse(data="No such Plasmid", status=404,safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':'Plasmid Not Found'})
    else:
        raise WebDatabaseGETMethodException()


def SearchPlasmidSequenceByID(request):
    """
    SearchPlasmidSequenceByID API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        id = request.GET.get('plasmidid')
        if(id == None or id == 0):
            raise WebDatabaseValidationException(parameter="plasmidid")
            # return JsonResponse(data="id cannot be empty", status=400,safe=False)
            # return JsonResponse({'code':204,'status': 'failed', 'data': 'Name can not be empty'})
        PlasmidList = list(Plasmidneed.objects.filter(plasmidid = id).values('sequenceconfirm'))
        if(len(PlasmidList) > 0):
            return JsonResponse(data = {'success':True, "data":PlasmidList[0]}, status=200, safe = False)
                # return JsonResponse({'code':200,'status':'success','data':result})
        else:
            raise WebDatabaseNotFoundException()
            # return JsonResponse(data={'success':False, "data":"No such Plasmid"}, status=404,safe=False)
                # return JsonResponse({'code':204,'status':'failed','data':'Plasmid Not Found'})
    else:
        raise WebDatabaseGETMethodException()
        # return JsonResponse(data={"success":False,'data':'Just GET method'}, status=404,safe=False)
        # return JsonResponse({'code':204,'status':'failed','data':'Plasmid Not Found'})

def SearchByOri(request):
    """
    SearchByOri API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        Ori = request.GET.get('oriClone')
        if(Ori == None or Ori == ""):
            raise WebDatabaseValidationException(parameter="oriClone")
            # return JsonResponse(data="OriClone cannot be empty", status=400,safe=False)
            # return JsonResponse({'code':204,'status': 'failed', 'data': 'Ori can not be empty'})
        plasmid_ori_result = list(Plasmid_Culture_Functions.objects.filter(function_content = Ori, function_type = "ori").values("plasmid_id").distinct())
        Plasmid_result = []
        for each in plasmid_ori_result:
            temp_plasmid = list(Plasmidneed.objects.filter(plasmidid = each['plasmid_id']).first())[0]
            info_list = getOriAndMarker(each['plasmid_id'])
            temp_plasmid["ori_info"] = info_list[0]
            temp_plasmid["marker_info"] = info_list[1]
            Plasmid_result.append(temp_plasmid)
        if(len(Plasmid_result) > 0):
            return JsonResponse(data=Plasmid_result, status=200, safe=False)
            # return JsonResponse({'code':200,'status':'success','data':list(PlasmidList.values())})
        else:
            raise WebDatabaseNotFoundException()
    else:
        raise WebDatabaseGETMethodException()
            # return JsonResponse(data="No such Plasmid", status=404,safe=False)
            # return JsonResponse({'code':200,'status':'failed','data':'Plasmid Not Found'})


def SearchByMarker(request):
    """
    SearchByMarker API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        Marker = request.GET.get('markerHost')
        if(Marker == None or Marker == ""):
            raise WebDatabaseValidationException(parameter="markerHost")
            # return JsonResponse(data="Marker cannot be empty", status=400,safe=False)
            # return JsonResponse({'code':204,'status': 'failed', 'data': 'Marker can not be empty'})
        plasmid_marker_result = list(Plasmid_Culture_Functions.objects.filter(function_content = Marker, function_type = "marker").values("plasmid_id").distinct())
        Plasmid_result = []
        for each in plasmid_marker_result:
            temp_plasmid = list(Plasmidneed.objects.filter(plasmidid = each['plasmid_id']).first())[0]
            info_list = getOriAndMarker(each['plasmid_id'])
            temp_plasmid["ori_info"] = info_list[0]
            temp_plasmid["marker_info"] = info_list[1]
            Plasmid_result.append(temp_plasmid)
        if(len(Plasmid_result) > 0):
            return JsonResponse(data=Plasmid_result, status=200, safe=False)
            # return JsonResponse({'code':200,'status':'success','data':list(PlasmidList.values())})
        else:
            raise WebDatabaseNotFoundException()
            # return JsonResponse(data="No such Plasmid", status=404,safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':"Plasmid Not Found"})
    else:
        raise WebDatabaseGETMethodException()


def SearchByLevel(request):
    """
    SearchByLevel API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        Level = request.GET.get('level')
        if(Level == None or Level == ""):
            raise WebDatabaseValidationException(parameter="level")
            # return JsonResponse(data="Level cannot be empty", status=400,safe=False)
            # return JsonResponse({'code':204,'status': 'failed', 'data': 'Level can not be empty'})
        PlasmidList = list(Plasmidneed.objects.filter(level=Level).values())
        if(len(PlasmidList) > 0):
            for each in PlasmidList:
                info_list = getOriAndMarker(each['plasmidid'])
                each['ori_info'] = info_list[0]
                each['marker_info'] = info_list[1]
            return JsonResponse(data=PlasmidList, status=200, safe = False)
            # return JsonResponse({'code':200,'status':'success','data':list(PlasmidList.values())})
        else:
            raise WebDatabaseNotFoundException()
    else:
        raise WebDatabaseGETMethodException()
            # return JsonResponse(data="No such Plasmid", status=404,safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':"Plasmid Not Found"})


def SearchByPlate(request):
    """
    SearchByPlate API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        Plate = request.GET.get('plate')
        if(Plate == None or Plate == ""):
            raise WebDatabaseValidationException(parameter="plate")
            # return JsonResponse(data="Plate cannot be empty", status=400,safe=False)
            # return JsonResponse({'code':204,'status': 'failed', 'data': 'Plate can not be empty'})
        PlasmidList = list(Plasmidneed.objects.filter(plate=Plate).values())
        if(len(PlasmidList) > 0):
            for each in PlasmidList:
                info_list = getOriAndMarker(each['plasmidid'])
                each['ori_info'] = info_list[0]
                each['marker_info'] = info_list[1]
            return JsonResponse(data=PlasmidList, status=200, safe=False)
            # return JsonResponse({'code':200,'status':'success','data':list(PlasmidList.values())})
        else:
            raise WebDatabaseNotFoundException()
            # return JsonResponse(data="No such Plasmid", status=404,safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':"Plasmid Not Found"})
    else:
        raise WebDatabaseGETMethodException()


def SearchPlasmidParent(request):
    """
    SearchPlasmidParent API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        plasmidName = request.GET.get('plasmidName')
        if(plasmidName == None or plasmidName == ""):
            raise WebDatabaseValidationException(parameter="plasmidName")
            # return JsonResponse(data="PlasmidName cannot be empty", status=400,safe=False)
            # return JsonResponse({'code':204,'status': 'failed', 'data': 'Plasmid Name can not be empty'})
        plasmidid = Plasmidneed.objects.filter(name = plasmidName).first().plasmidid
        PlasmidList = Parentplasmidtable.objects.filter(sonplasmidid=plasmidid)
        if(len(PlasmidList) == 0):
            raise WebDatabaseNotFoundException()
            # return JsonResponse(data="No such Plasmid", status=404,safe=False)
            # return JsonResponse({'code':204,'status': 'failed', 'data': 'Plasmid Parent not Found'})
        plasmidNameList = []
        for obj in PlasmidList:
            name = Plasmidneed.objects.get(plasmidid=obj.parentplasmidid).name
            plasmidNameList.append(name)
        if(len(plasmidNameList) > 0):
            return JsonResponse(data=PlasmidList,status=200,safe=False)
            # return JsonResponse({'code':200,'status':'success','data':PlasmidList})
        else:
            raise WebDatabaseNotFoundException()
    else:
        raise WebDatabaseGETMethodException()
            # return JsonResponse(data="No such Plasmid", status=404,safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':"Plasmid Parent not Found"})

def SearchPlasmidParentByID(request):
    """
    SearchPlasmidParentByID API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        plasmidID = request.GET.get('plasmidID')
        if(plasmidID == None or plasmidID == ""):
            raise WebDatabaseValidationException(parameter="plasmidID")
            # return JsonResponse(data="PlasmidID cannot be empty",status = 400, safe=False)
        ParentList = Parentplasmidtable.objects.filter(sonplasmidid=plasmidID)
        if(len(ParentList) == 0):
            raise WebDatabaseNotFoundException()
            # return JsonResponse(data = "No Parent Plasmid", status = 404, safe=False)
        PlasmidNameList = []
        for obj in ParentList:
            name = Plasmidneed.objects.get(plasmidid=obj.parentplasmidid).name
            PlasmidNameList.append(name)
        if(len(PlasmidNameList) > 0):
            return JsonResponse(data=PlasmidNameList,status=200,safe=False)
        else:
            raise WebDatabaseNotFoundException()
            # return JsonResponse(data = "No such plasmid",status=404,safe=False)
    raise WebDatabaseGETMethodException()
    
    
def GetParentID(request):
    """
    GetParentID API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        plasmidID = request.GET.get('plasmidID')
        if(plasmidID == None or plasmidID == ""):
            raise WebDatabaseValidationException(parameter="plasmidID")
            # return JsonResponse(data="PlasmidID cannot be empty",status = 400, safe=False)
        ParentList = Parentplasmidtable.objects.filter(sonplasmidid=plasmidID)
        if(len(ParentList) == 0):
            raise WebDatabaseNotFoundException()
            # return JsonResponse(data = "No Parent Plasmid", status = 404, safe=False)
        ParentIDList = []
        for obj in ParentList:
            ParentIDList.append(obj.parentplasmidid)
        if(len(ParentIDList) > 0):
            return JsonResponse(data=ParentIDList,status=200,safe=False)
        else:
            raise WebDatabaseNotFoundException()
    raise WebDatabaseGETMethodException()
            # return JsonResponse(data = "No such plasmid",status=404,safe=False)
        



def SearchPlasmidFileAddress(request):
    """
    SearchPlasmidFileAddress API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        Name = request.GET.get('name')
        if(Name == None or Name == ""):
            raise WebDatabaseValidationException(parameter="name")
            # return JsonResponse(data="Name cannot be empty", status=400,safe=False)
            # return JsonResponse({'code':204,'status': 'failed', 'data': 'Name can not be empty'})
        PlasmidID = Plasmidneed.objects.filter(name=Name).first().plasmidid
        if(PlasmidID == None):
            raise WebDatabaseNotFoundException()
            # return JsonResponse(data="No such Plasmid", status=404,safe=False)
            # return JsonResponse({'code':204,'status': 'failed', 'data': 'Plasmid Not Found'})
        userid = request.session.get('info')['uid']
        FilterDict = {"userid": userid,"plasmidid": PlasmidID}
        Address = TbPlasmidUserfileaddress.objects.filter(FilterDict).first().fileaddress
        if(Address != ""):
            return JsonResponse(data=Address, status=200, safe=False)
            # return JsonResponse({'code':200,'status':'success','data':Address})
        else:
            raise WebDatabaseNotFoundException()
    else:
        raise WebDatabaseGETMethodException()
            # return JsonResponse(data="No such Plasmid", status=404,safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':'Address Not Found'})

#Add
#TODO:鐢ㄦ埛绠＄悊
def AddPlasmidFileAddress(request):
    """
    AddPlasmidFileAddress API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "POST"):
        name = request.POST.get('name')
        Address = request.POST.get('address')
        if(name == None or name == ""):
            raise WebDatabaseValidationException(parameter="name")
        if(Address == None or Address == ""):
            raise WebDatabaseValidationException(parameter="address")
            # return JsonResponse(data="Name cannot be empty", status=400,safe=False)
            # return JsonResponse({'code':204,'status': 'failed', 'data': 'Name,Address can not be empty'})
        PlasmidID = Plasmidneed.objects.filter(name=name).first().plasmidid
        if(PlasmidID == None):
            raise WebDatabaseNotFoundException()
            # return JsonResponse(data="No such Plasmid", status=404,safe=False)
            # return JsonResponse({'code':204,'status': 'failed', 'data': 'Plasmid Not Found'})
        userid = request.session.get('info')['uid']
        TbPlasmidUserfileaddress.objects.create(plasmidid=PlasmidID, fileaddress=Address, userid=userid)
        return JsonResponse(data="Plasmid Address Added", status=200)
        # return JsonResponse({'code':200,'status':'success','data':'Plasmid Address Added'})
    else:
        raise WebDatabasePOSTMethodException()
    
    
def AddPlasmidData(request):
    """
    AddPlasmidData API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "POST"):
        data = json.loads(request.body)
        # print(data)
        name = data['name']
        # oriclone = data['oriclone']
        # orihost = data['orihost']
        # markerclone = data['markerclone']
        # markerhost = data['markerhost']
        level = data['level'] if "level" in data else 0
        length = len(data['sequence']) if data['sequence']!="" else 0
        sequence = data['sequence']
        plate = data['plate'] if 'plate' in data else ""
        state = data['state'] if 'state' in data else -1
        note = data['note'] if 'note' in data else ""
        alias = data['alias']
        #TODO: 鏇存敼杩欓噷
        try:
            username = request.session['info']['uname']
        except:
            username = "webtest"
        print(username)
        ParentInfo = data['ParentInfo'] if 'ParentInfo' in data else ""
        # username = request.session.get('info')['uname']
        tag = data['tag'] if "tag" in data else "normal"
        if(name == None or name == ""):
            raise WebDatabaseValidationException(parameter = "name")
        if(level == None or level == ""):
            raise WebDatabaseValidationException(parameter = "level")
            # return JsonResponse(data="Required parameter cannot be empty", status=400,safe=False)
            # return JsonResponse({'code':204,'status': 'failed', 'data': 'Name,Level,Sequence,ori,marker information can not be empty'})
        exist_plasmid = Plasmidneed.objects.filter(name__iexact=name).first()
        if(exist_plasmid == None):
            try:
                Plasmidneed.objects.create(name=name, level = level, length = length, sequenceconfirm=sequence,
                                   plate=plate, state = state, note=note, alias=alias,customparentinformation = ParentInfo,
                                   uploaddate = timezone.localtime(timezone.now()), updatedate = timezone.localtime(timezone.now()), user = username)
            except Exception as e:
                # print(e.args)
                raise e
        else:
            try:
                with transaction.atomic():
                    plasmid_obj = Plasmidneed.objects.select_for_update().get(plasmidid=exist_plasmid.plasmidid)
                    # plasmid_obj.name = name
                    if level != 0:
                        plasmid_obj.level = level
                    if length != 0:
                        plasmid_obj.length = length
                        plasmid_obj.sequenceconfirm = sequence
                    if plate != 0:
                        plasmid_obj.plate = plate
                    if state != -1:
                        plasmid_obj.state = state
                    if note != "":
                        plasmid_obj.note = note
                    if alias != "":
                        plasmid_obj.alias = alias
                    if ParentInfo != "":
                        plasmid_obj.customparentinformation = ParentInfo
                    plasmid_obj.user = username
                    plasmid_obj.updatedate = timezone.localtime(timezone.now())
                    # plasmid_obj.level = level
                    # plasmid_obj.length = length
                    # plasmid_obj.sequenceconfirm = sequence
                    # plasmid_obj.plate = plate
                    # plasmid_obj.state = state
                    # plasmid_obj.note = note
                    # plasmid_obj.alias = alias
                    # plasmid_obj.customparentinformation = ParentInfo
                    # plasmid_obj.user = username
                    # plasmid_obj.tag = tag
                    # plasmid_obj.updatedate = timezone.localtime(timezone.now())
                    plasmid_obj.save()
                return JsonResponse(data={"success":True}, status=200,safe=False)
            except Exception as e:
                raise e
        # return JsonResponse({'code':200,'status':'success','data':'Plasmid Data Added'})
        return JsonResponse({"success":True})
    
    
    
def AddParentPlasmid(request):
    """
    AddParentPlasmid API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "POST"):
        data = json.loads(request.body)
        if('SonPlasmidName' in data):
            sonPlasmidid = Plasmidneed.objects.filter(name = data['SonPlasmidName']).first().plasmidid
        if('SonPlasmidId' in data):
            sonPlasmidid = data['SonPlasmidId']
        ParentPlasmidName = data['ParentPlasmidName']
        if(sonPlasmidid == None or sonPlasmidid == 0):
            raise WebDatabaseValidationException(parameter = "SonPlasmidId")
        if(ParentPlasmidName == None or ParentPlasmidName == ""):
            raise WebDatabaseValidationException(parameter = "ParentPlasmidName")
            # return JsonResponse(data="SonPlasmidName cannot be empty", status=400,safe=False)
            # return JsonResponse({'code':204,'status': 'failed', 'data': 'Plasmid Name can not be empty'})
        start_time = time.time()
        max_wait_time = 5
        while time.time() - start_time < max_wait_time:
            try:
                with transaction.atomic():
                    sonPlasmidObj = Plasmidneed.objects.get(plasmidid = sonPlasmidid)
                    parentPlasmidObj = Plasmidneed.objects.filter(name = ParentPlasmidName).first()
                    if(parentPlasmidObj == None):
                        raise WebDatabaseNotFoundException()
                    if(Parentplasmidtable.objects.filter(sonplasmidid = sonPlasmidObj,parentplasmidid = parentPlasmidObj).count() == 0):
                        Parentplasmidtable.objects.create(sonplasmidid=sonPlasmidObj,parentplasmidid = parentPlasmidObj)
                    return JsonResponse(data={"success":True},status=200,safe=False)
            except Plasmidneed.DoesNotExist:
                time.sleep(0.5)
                continue
            except OperationalError as e:
                if 'lock' in str(e).lower():
                    time.sleep(0.5)
                    continue
                raise e
        raise WebDatabaseTimeoutException()
        # return JsonResponse(data={'success':False,'error':'time out'},status = 400, safe = False)
        # return JsonResponse({'code':200,'status':'success','data':'Parent Plasmid Added'})

def AddPlasmidParentByID(request):
    """
    AddPlasmidParentByID API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "POST"):
        data = json.loads(request.body)
        sonPlasmidName = data['SonPlasmidName']
        ParentPlasmidID = data['ParentPlasmidID']
        if(sonPlasmidName == None or sonPlasmidName == ""):
            raise WebDatabaseValidationException(parameter="SonPlasmidName")
        if(ParentPlasmidID == None or ParentPlasmidID == ""):
            raise WebDatabaseValidationException(parameter="ParentPlasmidID")
            # return JsonResponse(data="SonPlasmidName cannot be empty", status=400,safe=False)
            # return JsonResponse({'code':204,'status': 'failed', 'data': 'Plasmid Name can not be empty'})
        start_time = time.time()
        max_wait_time = 5
        while time.time() - start_time < max_wait_time:
            try:
                with transaction.atomic():
                    sonPlasmidObj = Plasmidneed.objects.select_for_update().get(name = sonPlasmidName)
                    parentPlasmidObj = Plasmidneed.objects.filter(plasmidid = ParentPlasmidID).first()
                    if(parentPlasmidObj == None):
                        return JsonResponse(data={"success":False},status=404,safe=False)
                    if(Parentplasmidtable.objects.filter(sonplasmidid = sonPlasmidObj.plasmidid,parentplasmidid = parentPlasmidObj.plasmidid).count() == 0):
                        Parentplasmidtable.objects.create(sonplasmidid=sonPlasmidObj,parentplasmidid = parentPlasmidObj)
                    return JsonResponse(data={"success":True},status=200,safe=False)
            except Plasmidneed.DoesNotExist:
                time.sleep(0.5)
                continue
            except OperationalError as e:
                if 'lock' in str(e).lower():
                    time.sleep(0.5)
                    continue
                raise e
        raise WebDatabaseTimeoutException()
        # return JsonResponse(data={'success':False,'error':'time out'},status = 400, safe = False)
    raise WebDatabasePOSTMethodException()


def GetParentPart(request):
    """
    GetParentPart API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == 'GET'):
        sonPlasmidid = Plasmidneed.objects.filter(plasmidid = request.GET.get('plasmidid')).first()
        ppResult = Parentparttable.objects.filter(sonplasmidid = sonPlasmidid).values('parentpartid')
        pplist = []
        for each_id in ppResult:
            pplist.append(list(Parttable.objects.filter(partid = each_id['parentpartid']).values('name','alias','partid'))[0])
        return JsonResponse(data={'success':True,'data':pplist},status = 200, safe = False)
    else:
        raise WebDatabaseGETMethodException()
        # return JsonResponse(data={'success':False,"message":str(e.args)},status=400,safe=False)



def GetParentBackbone(request):
    """
    GetParentBackbone API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == 'GET'):
        sonPlasmidid = Plasmidneed.objects.filter(plasmidid = request.GET.get('plasmidid')).first()
        pbResult = list(Parentbackbonetable.objects.filter(sonplasmidid = sonPlasmidid).values('parentbackboneid'))
        pblist = []
        for each_id in pbResult:
            pblist.append(list(Backbonetable.objects.filter(id = each_id['parentbackboneid']).values('name','alias','id'))[0])
        
        return JsonResponse(data={'success':True, 'data':pblist},status = 200, safe = False)
        
            # return JsonResponse(data={"success":False,"message":"Empty"}, status=200, safe=False)
    else:
        raise WebDatabaseGETMethodException()

def GetParentPlasmid(request):
    """
    GetParentPlasmid API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == 'GET'):
        sonPlasmidid = Plasmidneed.objects.filter(plasmidid = request.GET.get('plasmidid')).first()
        ppResult = list(Parentplasmidtable.objects.filter(sonplasmidid = sonPlasmidid).values('parentplasmidid'))
        pplist = []
        for each_id in ppResult:
            pplist.append(list(Plasmidneed.objects.filter(plasmidid = each_id['parentplasmidid']).values('name','alias',"plasmidid"))[0])
        return JsonResponse(data = {'success':True,'data':pplist},status = 200, safe = False)
    else:
        raise WebDatabaseGETMethodException()


def GetSonPlasmid(request):
    """
    GetSonPlasmid API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        parentPlasmidid = Plasmidneed.objects.filter(plasmidid = request.GET.get('plasmidid')).first()
        spResult = list(Parentplasmidtable.objects.filter(parentplasmidid = parentPlasmidid).values('sonplasmidid'))
        splist = []
        for each_id in spResult:
            splist.append(list(Plasmidneed.objects.filter(plasmidid = each_id['sonplasmidid']).values('name','alias'))[0])
        return JsonResponse(data = {'success':True, 'data':splist},status = 200, safe = False)
    else:
        raise WebDatabaseGETMethodException()


def GetPlasmidRelations(request):
    """Return plasmid parent relationships and IDs matching a related keyword."""
    if request.method != "GET":
        raise WebDatabaseGETMethodException()

    raw_ids = str(request.GET.get("plasmidids", ""))
    try:
        plasmid_ids = list(dict.fromkeys(
            int(item.strip()) for item in raw_ids.split(",") if item.strip()
        ))
    except ValueError:
        raise WebDatabaseException(message="plasmidids 必须是逗号分隔的整数")

    keyword = str(request.GET.get("keyword", "")).strip()
    matched_ids = []
    if keyword:
        plasmid_query = _build_or_keyword_query(keyword, ["name", "alias"])
        part_query = _build_or_keyword_query(keyword, ["parentpartid__name", "parentpartid__alias"])
        backbone_query = _build_or_keyword_query(keyword, ["parentbackboneid__name", "parentbackboneid__alias"])
        parent_plasmid_query = _build_or_keyword_query(keyword, ["parentplasmidid__name", "parentplasmidid__alias"])
        matched_ids.extend(Plasmidneed.objects.filter(plasmid_query).values_list("plasmidid", flat=True))
        matched_ids.extend(Parentparttable.objects.filter(part_query).values_list("sonplasmidid_id", flat=True))
        matched_ids.extend(Parentbackbonetable.objects.filter(backbone_query).values_list("sonplasmidid_id", flat=True))
        matched_ids.extend(Parentplasmidtable.objects.filter(parent_plasmid_query).values_list("sonplasmidid_id", flat=True))
        matched_ids = list(dict.fromkeys(item for item in matched_ids if item))

    relation_ids = list(dict.fromkeys(plasmid_ids + matched_ids))
    relations = {
        str(plasmid_id): {
            "related_parts": [],
            "related_backbones": [],
            "related_plasmids": [],
        }
        for plasmid_id in relation_ids
    }
    for son_id, name in Parentparttable.objects.filter(
        sonplasmidid_id__in=relation_ids
    ).values_list("sonplasmidid_id", "parentpartid__name"):
        relations[str(son_id)]["related_parts"].append(name)
    for son_id, name in Parentbackbonetable.objects.filter(
        sonplasmidid_id__in=relation_ids
    ).values_list("sonplasmidid_id", "parentbackboneid__name"):
        relations[str(son_id)]["related_backbones"].append(name)
    for son_id, name in Parentplasmidtable.objects.filter(
        sonplasmidid_id__in=relation_ids
    ).values_list("sonplasmidid_id", "parentplasmidid__name"):
        relations[str(son_id)]["related_plasmids"].append(name)

    return JsonResponse({"success": True, "data": relations, "plasmid_ids": matched_ids})


def GetUploadRecords(request):
    """Query upload records without exposing WebDatabase models to other apps."""
    if request.method != "GET":
        raise WebDatabaseGETMethodException()

    table_name = request.GET.get("table", "")
    if table_name not in UPLOAD_RECORD_TABLES:
        raise WebDatabaseException(message="table 只支持 parttable、backbonetable、plasmidneed")
    try:
        page = max(int(request.GET.get("page", 1)), 1)
        page_size = min(max(int(request.GET.get("pagesize", 100)), 1), 5000)
    except (TypeError, ValueError):
        raise WebDatabaseException(message="page 和 pagesize 必须为整数")

    config = UPLOAD_RECORD_TABLES[table_name]
    filter_expr = request.GET.get("filter", "")
    queryset = config["model"].objects.filter(_build_upload_record_query(filter_expr))
    total = queryset.count()
    start = (page - 1) * page_size
    records = list(
        queryset.order_by("-uploaddate", f"-{config['id_field']}")
        .values(*config["fields"])[start:start + page_size]
    )
    for record in records:
        record["table"] = table_name
        record["record_id"] = record.get(config["id_field"])
        for field in ("uploaddate", "updatedate"):
            if record.get(field):
                record[field] = timezone.localtime(record[field]).isoformat()

    return JsonResponse({
        "success": True,
        "table": table_name,
        "filter": filter_expr,
        "page": page,
        "pagesize": page_size,
        "count": total,
        "data": records,
    })

#Update
def UpdatePlasmidData(request):
    """
    UpdatePlasmidData API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "POST"):
        data = json.loads(request.body)
        if("OriginName" in data):
            OriginName = data['OriginName']
            if(OriginName == None or OriginName == ""):
                raise WebDatabaseValidationException(parameter="OriginName")
                # return JsonResponse(data="OriginName cannot be empty", status=400,safe=False)
            PlasmidID = Plasmidneed.objects.get(name=OriginName).plasmidid
        elif("id" in data):
            PlasmidID = data['id']
            # return JsonResponse({'code':204,'status': 'failed', 'data': 'OriginName can not be empty'})
        if(PlasmidID == None):
            raise WebDatabaseNotFoundException()
            # return JsonResponse(data="No such OriginName", status=404,safe=False)
            # return JsonResponse({'code':204,'status': 'failed', 'data': 'OriginName Not Found'})

        newName = data['newName']
        newOri = data['newOri']
        newMarker = data['newMarker']
        newLevel = data['newLevel'] if data['newLevel'] != "" else 1
        newLength = len(data['newSequence']) if data['newSequence'] != "" else 0
        newSequence = data['newSequence']
        newPlate = data['newPlate'] if 'newPlate' in data else ""
        newState = data['newState'] if 'newState' in data else 1
        newUser = request.session.get('info')['uname']
        newNote = data['newNote']
        newAlias = data['newAlias']
        tag = "abnormal" if(len(newOri) > 1 or len(newMarker) > 1) else "normal"
        if(newName == None or newName == ""):
            raise WebDatabaseValidationException(parameter="newName")
            # return JsonResponse(data="New Name cannot be empty", status=400,safe=False)
        if(Plasmidneed.objects.filter(name__iexact=newName).exclude(plasmidid=PlasmidID).exists()):
            return JsonResponse(data={"success":False, "message":"Plasmid name already exists"}, status=409, safe=False)
            # return JsonResponse({'code':204,'status': 'failed', 'data': 'Name,Ori,Marker,Sequence can not be empty'})
        try:
            with transaction.atomic():
                plasmid_obj = Plasmidneed.objects.select_for_update().get(plasmidid = PlasmidID)
                plasmid_obj.name = newName
                plasmid_obj.level = newLevel
                plasmid_obj.length = newLength
                plasmid_obj.sequenceconfirm = newSequence
                plasmid_obj.plate = newPlate
                plasmid_obj.alias = newAlias
                plasmid_obj.state = newState
                plasmid_obj.user = newUser
                plasmid_obj.note = newNote
                plasmid_obj.tag = tag
                plasmid_obj.updatedate = timezone.localtime(timezone.now())
                plasmid_obj.save()
        except IntegrityError:
            return JsonResponse(data={"success":False, "message":"Plasmid name already exists"}, status=409, safe=False)
        Plasmid_Culture_Functions.objects.filter(plasmid_id = PlasmidID).delete()
        plasmidOBJ = Plasmidneed.objects.get(plasmidid = PlasmidID)
        for each in newOri:
            Plasmid_Culture_Functions.objects.create(plasmid_id = plasmidOBJ, function_content = each, function_type = "ori")
        for each in newMarker:
            Plasmid_Culture_Functions.objects.create(plasmid_id = plasmidOBJ, function_content = each, function_type = "marker")

        return JsonResponse(data="Plasmid Data Updated", status=200, safe = False)
        # return JsonResponse({'code':200,'status':'success','data':'Plasmid Data Updated'})


def UpdatePlasmidFileAddress(request):
    """
    UpdatePlasmidFileAddress API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "POST"):
        PlasmidName = request.POST.get('name')
        Address = request.POST.get('address')
        if(PlasmidName == None or PlasmidName == ""):
            raise WebDatabaseValidationException(parameter = "name")
        if(Address == None or Address == ""):
            raise WebDatabaseValidationException(parameter = "address")
            # return JsonResponse(data="PlasmidName cannot be empty", status=400,safe=False)
            # return JsonResponse({'code':204,'status':'failed', 'data': 'Plasmid Name, Address can not be empty'})
        plasmidID = Plasmidneed.objects.filter(name=PlasmidName).first().plasmidid
        if(plasmidID == None):
            raise WebDatabaseNotFoundException()
            # return JsonResponse(data="No such Plasmid", status=404,safe=False)
            # return JsonResponse({'code':204,'status': 'failed', 'data': 'Plasmid Not Found'})
        userID = request.session.get('info')['uid']
        FilterDict = {"userid": userID,"plasmidid": plasmidID}
        TbPlasmidUserfileaddress.objects.filter(FilterDict).update(userid=userID,plasmidid=plasmidID,fileaddress=Address)
        return JsonResponse(data="Plasmid File Address Updated", status=200)
        # return JsonResponse({'code':200,'status':'success','data':'Plasmid Address Updated'})
    else:
        raise WebDatabasePOSTMethodException()

#delete
def deletePlasmidData(request):
    """
    deletePlasmidData API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        print("deletePlasmidData")
        # name = request.GET.get('name')
        # if(name == None or name == ""):
        #     return JsonResponse(data={"success":False, "message":"Name cannot be empty"}, status=400,safe=False)
        #     # return JsonResponse({'code':204,'status':'failed', 'data': 'Plasmid Name can not be empty'})
        PlasmidID = request.GET.get("plasmidid")
        print(PlasmidID)
        if(PlasmidID == None):
            raise WebDatabaseValidationException(parameter="plasmidid")
            # return JsonResponse(data={"success":False, "message":"No such Plasmid"}, status=404,safe=False)
            # return JsonResponse({'code':204,'status': 'failed', 'data': 'Plasmid Not Found'})
        plasmid_user = Plasmidneed.objects.get(plasmidid = PlasmidID).user
        print("99999999999999999999999999999999999999")
        print(plasmid_user == request.user.uname)
        if(plasmid_user != request.user.uname and plasmid_user != request.user.email):
            
            raise WebDatabasePermissionException()
            # return JsonResponse(data = {"success":False, "message":"褰撳墠鐢ㄦ埛娌℃湁鍒犻櫎鏉冮檺锛岃鑱旂郴涓婁紶鐢ㄦ埛杩涜鍒犻櫎"}, status = 400, safe=False)
        try:
            Parentplasmidtable.objects.filter(sonplasmidid=PlasmidID).delete()
            Parentplasmidtable.objects.filter(parentplasmidid=PlasmidID).delete()
            Parentparttable.objects.filter(sonplasmidid = PlasmidID).delete()
            Parentbackbonetable.objects.filter(sonplasmidid = PlasmidID).delete()
            Plasmidscartable.objects.filter(plasmidid = PlasmidID).delete()
            Plasmid_Culture_Functions.objects.filter(plasmid_id = PlasmidID).delete()
            Plasmidfeaturetable.objects.filter(plasmidid=PlasmidID).delete()
            TbPlasmidUserfileaddress.objects.filter(plasmidid=PlasmidID).delete()
            Plasmidneed.objects.filter(plasmidid = PlasmidID).delete()
            return JsonResponse(data={"success":True}, status=200, safe=False)
        except Exception as e:
            print(e.args)
            return JsonResponse(data = {"success":False,"message":str(e)},status = 400, safe= False)
        # return JsonResponse({'code':200,'status':'success','data':'Plasmid Data Deleted'})

def deletePlasmidFileAddress(request):
    """
    deletePlasmidFileAddress API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        PlasmidName = request.GET.get('PlasmidName')
        if(PlasmidName == None or PlasmidName == ""):
            raise WebDatabaseValidationException(parameter="PlasmidName")
            # return JsonResponse(data="PlasmidName cannot be empty", status=400,safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':'Plasmid Name can not be empty'})
        PlasmidID = Plasmidneed.objects.filter(name=PlasmidName).first().plasmidid
        if(PlasmidID == None):
            raise WebDatabaseNotFoundException()
            # return JsonResponse(data="No such Plasmid", status=404,safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':'Plasmid Not Found'})
        userid = request.session.get('info')['uid']
        FilterDict = {"userid": userid,"plasmidid": PlasmidID}
        TbPlasmidUserfileaddress.objects.filter(**FilterDict).delete()
        return JsonResponse(data="Plasmid File Address Deleted", status=200)
        # return JsonResponse({'code':200,'status':'success','data':'Plasmid Address Deleted'})
    else:
        raise WebDatabaseGETMethodException()

def DeleteParentPlasmid(request):
    """
    DeleteParentPlasmid API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        ParentPlasmidName = request.GET.get('plasmidName')
        if(ParentPlasmidName == None or ParentPlasmidName == ""):
            raise WebDatabaseValidationException(parameter = "plasmidName")
            # return JsonResponse(data="ParentPlasmidName cannot be empty", status=400,safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':'Plasmid Name can not be empty'})
        ParentPlasmidID = Plasmidneed.objects.filter(name=ParentPlasmidName).first().plasmidid
        if(ParentPlasmidID == None):
            raise WebDatabaseNotFoundException()
            # return JsonResponse(data="No such ParentPlasmid", status=404,safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':'Plasmid Not Found'})
        Parentplasmidtable.objects.get(parentplasmidid=ParentPlasmidID).delete()
        return JsonResponse(data="ParentPlasmid Deleted", status=200)
        # return JsonResponse({'code':200,'status':'success','data':'Parent Plasmid Deleted'})
    else:
        raise WebDatabaseGETMethodException()

def setPlasmidCulture(request):
    """
    setPlasmidCulture API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "POST"):
        data = json.loads(request.body)
        plasmidName = data["name"]
        Ori_list = data["ori"]
        Marker_list = data["marker"]
        if(plasmidName == None or plasmidName == ""):
            raise WebDatabaseValidationException(parameter = "name")
        start_time = time.time()
        max_wait_time = 5
        while time.time() - start_time < max_wait_time:
            try:
                with transaction.atomic():
                    # plasmidid = Plasmidneed.objects.filter(name=plasmidName).first()
                    plasmidid = Plasmidneed.objects.select_for_update().get(name = plasmidName)
                   
                    Plasmid_culture_exist = Plasmid_Culture_Functions.objects.filter(plasmid_id = plasmidid).values()
                    if(len(Plasmid_culture_exist) != 0):
                        Plasmid_Culture_Functions.objects.filter(plasmid_id = plasmidid).delete()
                    for each_ori in Ori_list:
                        Plasmid_Culture_Functions.objects.create(plasmid_id = plasmidid,function_content = each_ori, function_type = "ori")
                    for each_marker in Marker_list:
                        Plasmid_Culture_Functions.objects.create(plasmid_id = plasmidid,function_content = each_marker, function_type="marker")
                    plasmidid.updatedate = timezone.localtime(timezone.now())
                    plasmidid.tag = "abnormal" if len(Ori_list) > 1 or len(Marker_list) > 1 or len(Ori_list) == 0 or len(Marker_list) == 0 else "normal"
                    plasmidid.save()
                    return JsonResponse(data = {"success":True,"data":"success upload"},status=200, safe=False)
            except Plasmidneed.DoesNotExist:
                time.sleep(0.5)
                continue
            except OperationalError as e:
                if 'lock' in str(e).lower():
                    time.sleep(0.5)
                    continue
                raise e
        raise WebDatabaseTimeoutException()
    else:
        raise WebDatabasePOSTMethodException()

def getPlasmidCulture(request):
    """
    getPlasmidCulture API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        plasmidid = request.GET.get("plasmidId");
        if(plasmidid == None or plasmidid == ""):
            raise WebDatabaseValidationException(parameter = "plasmidId")
        try:
            CustomInfo = Plasmidneed.objects.get(plasmidid = plasmidid).customparentinformation
            return JsonResponse(data = {"success":True,"customInfo":CustomInfo},status = 200, safe=False)
        except Plasmidneed.DoesNotExist:
            raise WebDatabaseNotFoundException()
    else:
        raise WebDatabaseGETMethodException()
            

def PlasmidFields(request):
    """
    PlasmidFields API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    fields =[field.name for field in Plasmidneed._meta.get_fields()]
    fields.remove("parentparttable")
    fields.remove("parentplasmidtable")
    fields.remove("parentbackbonetable")
    fields.remove("parentplasmidtable_parentplasmidid_set")
    fields.remove("plasmid_culture_functions")
    fields.remove("plasmidscartable")
    fields.remove("plasmidunessential")
    fields.remove("tbplasmiduserfileaddress")
    fields.remove("plasmidfeaturetable")
    return JsonResponse(data={"success":True, "data":fields}, status = 200, safe=False)

def PlasmidListByUser(request,username):
    """
    PlasmidListByUser API view.

    Args:
        request: Django HttpRequest object.
        username: Input parameter.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        if(username == None or username == ""):
            raise WebDatabaseValidationException(parameter = "username")
            # return JsonResponse(data = {"success":False, "message":"Parameter cannot be empty"}, status=400, safe=False)
        else:
            result = list(Plasmidneed.objects.filter(user = username).values())
            return JsonResponse(data={"success":True, "data":result}, status = 200, safe= False)
    else:
        raise WebDatabaseGETMethodException()
        # return JsonResponse(data={"success":False,"message":"Just GET method"},status =400, safe=False)








#----------------------------------------------------------
#Backbone table
def BackboneCount(request):
    """
    BackboneCount API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        count = Backbonetable.objects.values().count()
        return JsonResponse(data={"success":True, "data":count}, status = 200, safe=False)
    else:
        raise WebDatabaseGETMethodException()
        # return JsonResponse(data={"success":False, "message":"Just GET method"}, status = 200, safe=False)
    
    
def getdefaultbackbonescar(backboneid):
    """
    getdefaultbackbonescar API view.

    Args:
        backboneid: Input parameter.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    backbone_obj = Backbonescartable.objects.filter(backboneid = backboneid).first()
    if backbone_obj != None:
        return backbone_obj.bsai + "/" + backbone_obj.bbsi
    else:
        return "No Sequence"
#Search
def BackboneDataALL(request):
    """
    BackboneDataALL API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        page = int(request.GET.get('page',0))
        if(page == 0):
            BackboneData = Backbonetable.objects.all().order_by('name').values()
            if(len(BackboneData) > 0):
                BackboneData = list(BackboneData)
                for each in BackboneData:
                    info_list = getBackboneOriAndMarker(each['id'])
                    each['ori'] = info_list[0]
                    each['marker'] = info_list[1]
                    each['scar'] = getdefaultbackbonescar(each['id'])
                return JsonResponse(data={'success': True, 'data':BackboneData}, status=200,safe=False)
                # return JsonResponse({'code':200,'data':list(PartData.values())})
            else:
                raise WebDatabaseNotFoundException()
                # return JsonResponse(data={'success':False, 'error':"No such backbone"}, status=404,safe=False)
                # return JsonResponse({'code':204,'status': 'failed', 'data': []})
        else:
            page_size = int(request.GET.get('page_size',10))
            offset = (page -1)*page_size
            total_count = Backbonetable.objects.count()
            total_pages = (total_count + page_size -1) // page_size
            query_set = Backbonetable.objects.order_by('name').values('id','name','alias','species','tag')[offset:offset+page_size]
            # query_set = Backbonetable.objects.only('id','name','marker','ori','species').all().order_by('name')[offset:offset+page_size]
            query_set = list(query_set)
            for each in query_set:
                info_list = getBackboneOriAndMarker(each['id'])
                each['ori'] = info_list[0]
                each['marker'] = info_list[1]
                each['scar'] = getdefaultbackbonescar(each['id'])
            has_next = page < total_pages
            has_previous = page > 1
            return JsonResponse(data={'success':True,
                                      'data':query_set,
                                      'pagination':{
                                          'current_page' : page,
                                          'total_pages' : total_pages,
                                          'total_count' : total_count,
                                          'has_next':has_next,
                                          'has_previous' : has_previous,
                                          'page_size':page_size,
                                          'offset':offset
                                          }
                                        },status = 200, safe=False
                                )
    else:
        raise WebDatabaseGETMethodException()
#Backbone filter

def BackboneFilter(request):
    """
    BackboneFilter API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "POST"):
        data = json.loads(request.body)
        # print(data)
        ori = data['ori']
        marker = data['marker']
        Enzyme = data['Enzyme']
        Scar = data['Scar']
        Name = data['name']
        page = data['page']
        page_size = data['page_size']
        offset = (page -1)*page_size
        scarBackboneid = []
        if(Enzyme == "BsmBI"):
            scarBackboneid = list(Backbonescartable.objects.filter(bsmbi = Scar).values('backboneid'))
        elif(Enzyme == "BsaI"):
            scarBackboneid = list(Backbonescartable.objects.filter(bsai = Scar).values('backboneid'))
        elif(Enzyme == "BbsI"):
            scarBackboneid = list(Backbonescartable.objects.filter(bbsi = Scar).values('backboneid'))
        elif(Enzyme == "AarI"):
            scarBackboneid = list(Backbonescartable.objects.filter(aari = Scar).values('backboneid'))
        elif(Enzyme == "SapI"):
            scarBackboneid = list(Backbonescartable.objects.filter(sapi = Scar).values('backboneid'))
        if(Enzyme != "" and len(scarBackboneid) == 0):
            raise WebDatabaseNotFoundException()
            # return JsonResponse(data={'success':False,'error':'No data'}, status = 404, safe = False)

        BackboneResult = []
        if(len(scarBackboneid) != 0):
            for each_id in scarBackboneid:
                result = Backbonetable.objects
                result = result.filter(id = each_id['backboneid'])
                if(ori != ""):
                    ori_result = Backbone_Culture_Functions.objects.filter(backbone_id =each_id['backboneid']).values()
                    if(len(ori_result) == 0):
                        continue
                if(marker != ""):
                    marker_result = Backbone_Culture_Functions.objects.filter(backbone_id = each_id['backboneid'].values())
                    
                    print(marker_result)
                    if(len(marker_result) == 0):
                        continue
                
                # if(ori != "" and result != None):
                #     # 'partid','name','type','sourceorganism','reference'
                #     result = result.filter(ori = ori)
                #    
                # if(marker != "" and result != None):
                #     result = result.filter(marker = marker)
                if(Name != "" and result != None):
                    keyword_query = _build_or_keyword_query(Name, ["name", "alias"])
                    if keyword_query is not None:
                        result = result.filter(keyword_query)
                if(len(result) != 0):
                    
                    # PartResult.append(result.order_by('name').values('partid','name','type','sourceorganism','reference'))
                    temp_result = list(result.order_by('name').values('id','name','alias','species','tag'))[0]
                    info_list = getBackboneOriAndMarker(temp_result['id'])
                    temp_result['ori'] = info_list[0]
                    temp_result['marker'] = info_list[1]
                    temp_result['scar'] = Scar
                    BackboneResult.append(temp_result)
        else:
            Ori_backbone_id_list = set()
            Marker_backbone_id_list = set()
            final_backbone_id_list = set()
            if(ori != ""):
                Ori_result = Backbone_Culture_Functions.objects.filter(function_content = ori, function_type="ori").values("backbone_id")
                for each in Ori_result:
                    Ori_backbone_id_list.add(each['backbone_id'])
            if(marker != ""):
                Marker_result = Backbone_Culture_Functions.objects.filter(function_content = marker, function_type="marker").values("backbone_id")
                for each in Marker_result:
                    Marker_backbone_id_list.add(each['backbone_id'])
            if(ori != "" and marker != ""):
                final_backbone_id_list = Ori_backbone_id_list & Marker_backbone_id_list
            else:
                final_backbone_id_list = Ori_backbone_id_list | Marker_backbone_id_list
            print(final_backbone_id_list)
            if(len(final_backbone_id_list) == 0):
                # if(Name != "" and result != None):
                #     result = result.filter(Q(name__icontains = Name) | Q(alias__icontains = Name))
                # if(result != None):
                if(ori != "" or marker != ""):
                    return JsonResponse(data = {'success':False, 'data': [],
                                        'pagination':{
                                            'current_page' : 0,
                                            'total_pages' : 0,
                                            'total_count' : 0,
                                            'has_next' : 0,
                                            'has_previous' : 0,
                                            'page_size' : 0,
                                            'offset' : 0
                                            }
                                        },status = 200, safe = False)
                else:
                    BackboneResult = []
                    result = Backbonetable.objects
                    if(Name != "" and result != None):
                        keyword_query = _build_or_keyword_query(Name, ["name", "alias"])
                        if keyword_query is not None:
                            result = result.filter(keyword_query)
                    if(len(result) != 0):
                        temp_result = list(result.values('id','name','alias','species','tag'))
                        for each in temp_result:
                            try:
                                info_list = getBackboneOriAndMarker(each['id'])
                                each['ori'] = info_list[0]
                                each['marker'] = info_list[1]
                                each['scar'] = getdefaultbackbonescar(each['id'])
                            except Backbonescartable.DoesNotExist:
                                each['scar'] = "No sequence"
                            except Backbone_Culture_Functions.DoesNotExist:
                                each['ori'] = "No sequence"
                                each['marker'] = "No sequence"
                            BackboneResult.append(each)
                    # PlasmidResult = (list(result.order_by('name').values('plasmidid','name','alias','oricloning','orihost','markercloning','markerhost','level')))
            else:
                BackboneResult = []
                for each_id in final_backbone_id_list:
                    result = Backbonetable.objects.filter(id = each_id)
                    if(Name != "" and result != None):
                        keyword_query = _build_or_keyword_query(Name, ["name", "alias"])
                        if keyword_query is not None:
                            result = result.filter(keyword_query)
                    if(len(result) != 0):
                        temp_result = (list(result.values('id','name','alias','species','tag')))[0]
                        info_list = getBackboneOriAndMarker(temp_result['id'])
                        temp_result['ori'] = info_list[0]
                        temp_result['marker'] = info_list[1]
                        temp_result['scar'] = getdefaultbackbonescar(temp_result['id'])
                        BackboneResult.append(temp_result)
        
        if(len(BackboneResult) != 0):
            total_count = len(BackboneResult)
            total_pages = (total_count + page_size -1) // page_size
            has_next = page < total_pages
            has_previous = page > 1

            # data={'success':True,
            #                           'data':list(query_set.values()),
            #                           'pagination':{
            #                               'current_page' : page,
            #                               'total_pages' : total_pages,
            #                               'total_count' : total_count,
            #                               'has_next':has_next,
            #                               'has_previous' : has_previous,
            #                               'page_size':page_size,
            #                               'offset':offset
            #                               }
            #                             },status = 200, safe=False
            if(len(BackboneResult) < page_size):
                return JsonResponse(data = {'success':True, 'data': list(BackboneResult[:]),
                                        'pagination':{
                                            'current_page' : page,
                                            'total_pages' : total_pages,
                                            'total_count' : total_count,
                                            'has_next' : has_next,
                                            'has_previous' : has_previous,
                                            'page_size' : page_size,
                                            'offset' : offset
                                            }
                                        })
            else:
                return JsonResponse(data = {'success':True, 'data': list(BackboneResult[offset:offset+page_size]),
                                        'pagination':{
                                            'current_page' : page,
                                            'total_pages' : total_pages,
                                            'total_count' : total_count,
                                            'has_next' : has_next,
                                            'has_previous' : has_previous,
                                            'page_size' : page_size,
                                            'offset' : offset
                                            }
                                        })
            
        else:
            # return JsonResponse(data = {'success':False, 'error':'No data'},status = 404, safe = False)
            return JsonResponse(data = {'success':False, 'data': [],
                                        'pagination':{
                                            'current_page' : 0,
                                            'total_pages' : 0,
                                            'total_count' : 0,
                                            'has_next' : 0,
                                            'has_previous' : 0,
                                            'page_size' : 0,
                                            'offset' : 0
                                            }
                                        },status = 200, safe = False)



def SearchByBackboneName(request):
    """
    SearchByBackboneName API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        Name = request.GET.get('name')
        if(Name == None or Name == ""):
            raise WebDatabaseValidationException(parameter="name")
            # return JsonResponse(data="Name cannot be empty", status=400,safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':'Name can not be empty'})
        BackboneList = Backbonetable.objects.filter(name=Name)
        if(BackboneList != None):
            BackboneList = list(BackboneList.values())[0]
            info_list = getBackboneOriAndMarker(BackboneList["id"])
            BackboneList['ori'] = info_list[0]
            BackboneList['marker'] = info_list[1]
            return JsonResponse(data={"success":True,"data":BackboneList}, status=200,safe=False)
            # return JsonResponse({'code':200,'status':'success','data':list(BackboneList.values())})
        else:
            raise WebDatabaseNotFoundException()
            # return JsonResponse(data="No such Name", status=404,safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':'No Backbone Found'})

def SearchByBackboneID(request):
    """
    SearchByBackboneID API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        ID = request.GET.get('ID')
        if(ID == None or ID == ""):
            raise WebDatabaseValidationException(parameter = "ID")
            # return JsonResponse(data="Name cannot be empty", status=400,safe=False)
            # return JsonResponse({'code':204,'status': 'failed', 'data': 'Name can not be empty'})
        BackboneList = list(Backbonetable.objects.filter(id=ID).values())
        if(len(BackboneList) > 0):
            for each in BackboneList:
                info_list = getBackboneOriAndMarker(each['id'])
                each['ori'] = info_list[0]
                each['marker'] = info_list[1]
            return JsonResponse(data=BackboneList, status=200,safe=False)
            # return JsonResponse({'code':200,'status':'success','data':list(PlasmidList.values())})
        else:
            raise WebDatabaseNotFoundException()
            # return JsonResponse(data="No such Plasmid", status=404,safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':"Plamsid Not Found"})
    else:
        raise WebDatabaseGETMethodException()

def  SearchByBackboneSeq(request):
    """
    SearchByBackboneSeq API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        Seq = request.GET.get('seq')
        if(Seq == None or Seq == ""):
            raise WebDatabaseValidationException(parameter = "seq")
            # return JsonResponse(data="Seq cannot be empty", status=400,safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':'Sequence can not be empty'})
        BackboneList = list(Backbonetable.objects.filter(sequence=Seq).values())
        if(len(BackboneList) > 0):
            for each in BackboneList:
                info_list = getBackboneOriAndMarker(each['id'])
                each['ori'] = info_list[0]
                each['marker'] = info_list[1]
            return JsonResponse(data=BackboneList, status=200,safe=False)
            # return JsonResponse({'code':200,'status':'success','data':list(BackboneList.values())})
        else:
            raise WebDatabaseNotFoundException()
            # return JsonResponse(data="No such backbone", status=404,safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':'No Backbone Found'})
    else:
        raise WebDatabaseGETMethodException()

def GetBackboneSeqByID(request):
    """
    GetBackboneSeqByID API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        ID = request.GET.get('backboneid')
        if(ID ==None or ID == 0):
            raise WebDatabaseValidationException(parameter="backboneid")
            # return JsonResponse(data = {'success':False,'data':"Parameter is empty"},status=404, safe = False)
        else:
            BackboneSeq = list(Backbonetable.objects.filter(id=ID).values('sequence'))
            print(BackboneSeq)
            if(len(BackboneSeq) > 0):
                return JsonResponse(data = {'success':True, 'data':BackboneSeq[0]},status = 200, safe = False)
            else:
                raise WebDatabaseNotFoundException()
                # return JsonResponse(data = {'success':False,'data':"No such backbone"},status = 404, safe=False)
    else:
        raise WebDatabaseGETMethodException()
        # return JsonResponse(data = {'success':False,'data':'Only Get method'},status = 400, safe = False)


def SearchByBackboneSpecies(request):
    """
    SearchByBackboneSpecies API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        Species = request.GET.get('species')
        if(Species == None or Species == ""):
            raise WebDatabaseValidationException(parameter="species")
            # return JsonResponse(data="Species cannot be empty", status=400,safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':'Species can not be empty'})
        BackboneList = list(Backbonetable.objects.filter(species=Species).values())
        if(len(BackboneList) > 0):
            for each in BackboneList:
                info_list = getBackboneOriAndMarker(each['id'])
                each['ori'] = info_list[0]
                each['marker'] = info_list[1]
            return JsonResponse(data=BackboneList, status=200,safe=False)
            # return JsonResponse({'code':200,'status':'success','data':list(BackboneList.values())})
        else:
            raise WebDatabaseNotFoundException()
            # return JsonResponse(data="No such Species", status=404,safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':'No Backbone Found'})
    else:
        raise WebDatabaseGETMethodException()

def SearchByBackboneMarker(request):
    """
    SearchByBackboneMarker API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        Marker = request.GET.get('marker')
        if(Marker == None or Marker == ""):
            raise WebDatabaseValidationException(parameter = "marker")
            # return JsonResponse(data="Marker cannot be empty", status=400,safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':'Marker can not be empty'})
        backbone_result = list(Backbone_Culture_Functions.objects.filter(function_content = Marker, function_type = "marker").values('backbone_id').distinct())
        if(len(backbone_result) > 0):
            BackboneList = []
            for each in backbone_result:
                backbone_each_result = list(Backbonetable.objects.filter(id = each['backbone_id']).values())[0]
                info_list = getBackboneOriAndMarker(backbone_each_result['id'])
                backbone_each_result['ori'] = info_list[0]
                backbone_each_result['marker'] = info_list[1]
                BackboneList.append(backbone_each_result)
            return JsonResponse(data=BackboneList, status=200,safe=False)
            # return JsonResponse({'code':200,'status':'success','data':list(BackboneList.values())})
        else:
            raise WebDatabaseNotFoundException()
            # return JsonResponse(data="No such Marker", status=404,safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':'No Backbone Found'})
    else:
        raise WebDatabaseGETMethodException()


def SearchByBackboneOri(request):
    """
    SearchByBackboneOri API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        Ori = request.GET.get('ori')
        if(Ori == None or Ori == ""):
            return WebDatabaseValidationException(parameter="ori")
            # return JsonResponse(data="Ori cannot be empty", status=400,safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':'Ori can not be empty'})
        backbone_result = list(Backbone_Culture_Functions.objects.filter(function_content = Ori, function_type = "ori").values('backbone_id').distinct())
        if(len(backbone_result) > 0):
            BackboneList = []
            for each in backbone_result:
                backbone_each_result = list(Backbonetable.objects.filter(id = each['backbone_id']).values())[0]
                info_list = getBackboneOriAndMarker(backbone_each_result['id'])
                backbone_each_result['ori'] = info_list[0]
                backbone_each_result['marker'] = info_list[1]
                BackboneList.append(backbone_each_result)
            return JsonResponse(data=BackboneList, status=200,safe=False)
        else:
            raise WebDatabaseNotFoundException()
            # return JsonResponse(data="No such Ori", status=404,safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':'No Backbone Found'})

def SearchByCopyNumber(request):
    """
    SearchByCopyNumber API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == 'GET'):
        CopyNumber = request.GET.get('copynumber')
        if(CopyNumber == None or CopyNumber == ""):
            raise WebDatabaseValidationException(parameter="copynumber")
            # return JsonResponse(data="CopyNumber cannot be empty", status=400,safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':'CopyNumber can not be empty'})
        BackboneList = list(Backbonetable.objects.filter(copynumber = CopyNumber).values())
        if(len(BackboneList) > 0):
            for each in BackboneList:
                info_list = getBackboneOriAndMarker(each['id'])
                each['ori'] = info_list[0]
                each['marker'] = info_list[1]
            return JsonResponse(data=BackboneList, status=200,safe=False)
            # return JsonResponse({'code':200,'status':'success','data':list(BackboneList.values())})
        else:
            raise WebDatabaseNotFoundException()
            # return JsonResponse(data="No such CopyNumber", status=404,safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':'No Backbone Found'})

def SearchBackboneFileAddress(request):
    """
    SearchBackboneFileAddress API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        name = request.GET.get('name')
        if(name == None or name == ""):
            raise WebDatabaseValidationException(parameter="name")
            # return JsonResponse(data="Name cannot be empty", status=400,safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':'name can not be empty'})
        BackboneID = Backbonetable.objects.filter(name=name).first().id
        if(BackboneID == None):
            raise WebDatabaseNotFoundException()
            # return JsonResponse(data="No such Backbone", status=404,safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':'Backbone Not Found'})
        userid = request.session.get('info')['uid']
        FilterDict = {"userid": userid,"backboneid":BackboneID}
        BackboneAddress = TbBackboneUserfileaddress.objects.filter(**FilterDict).first().fileaddress
        if(BackboneAddress != ""):
            return JsonResponse(data=BackboneAddress, status=200,safe=False)
            # return JsonResponse({'code':200,'status':'success','data':BackboneAddress})
        else:
            raise WebDatabaseNotFoundException()
            # return JsonResponse(data="No such Backbone Address", status=404,safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':'No Backbone Address Found'})
#Add
def AddBackboneData(request):
    """
    AddBackboneData API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "POST"):
        data = json.loads(request.body)
        name = data['name']
        length = len(data['sequence']) if data['sequence'] != "" else 0
        sequence = data['sequence']
        species = data['species'] if "species" in data else ""
        copynumber = data['copynumber'] if 'copynumber' in data else ""
        note = data['note'] if 'note' in data else ""
        alias = data['alias'] if 'alias' in data else ""
        username = request.session['info']['uname']
        tag = data['tag'] if 'tag' in data else "normal"
        if(name == None or name == ""):
            raise WebDatabaseValidationException(parameter="name")
            # return JsonResponse(data="Name cannot be empty", status=400,safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':'name, sequence can not be empty'})
        # tag = "abnormal" if (len(ori) > 1 or len(marker) > 1) else "normal"
        exist_backbone = Backbonetable.objects.filter(name__iexact=name).first()
        if(exist_backbone != None):
            with transaction.atomic():
                backbone_obj = Backbonetable.objects.select_for_update().get(id=exist_backbone.id)
                if length != 0:
                    backbone_obj.length = length
                    backbone_obj.sequence = sequence
                if species != "":
                    backbone_obj.species = species
                if copynumber != "":
                    backbone_obj.copynumber = copynumber
                if note != "":
                    backbone_obj.notes = note
                if alias != "":
                    backbone_obj.alias = alias
                # backbone_obj.name = name
                # # backbone_obj.length = length
                # backbone_obj.sequence = sequence
                # backbone_obj.species = species
                # backbone_obj.copynumber = copynumber
                # backbone_obj.notes = note
                # backbone_obj.alias = alias
                backbone_obj.user = username
                backbone_obj.tag = tag
                backbone_obj.updatedate = timezone.localtime(timezone.now())
                backbone_obj.save()
        else:
            uploadDate = timezone.localtime(timezone.now())
            updateDate = timezone.localtime(timezone.now())
            try:
                Backbonetable.objects.create(name=name, length=length, sequence=sequence,
                                        species = species,copynumber=copynumber, notes=note, alias=alias,user=username, tag=tag,
                                        uploaddate = uploadDate, updatedate = updateDate)
            except IntegrityError:
                return JsonResponse(data={"success":False, "message":"Backbone name already exists"}, status=409, safe=False)
        return JsonResponse(data={"success":True}, status=200,safe=False)
        # return JsonResponse({'code':200,'status':'success','data':'Backbone Data Added'})

#TODO:鐢ㄦ埛绠＄悊
def AddBackboneFileAddress(request):
    """
    AddBackboneFileAddress API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "POST"):
        Backbonename = request.POST.get('name')
        Address = request.POST.get('address')
        if(Backbonename == None or Backbonename == "" or Address == None or Address == ""):
            raise WebDatabaseValidationException(parameter="name")
            # return JsonResponse(data="Name cannot be empty", status=400,safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':'name,address can not be empty'})
        BackboneID = Backbonetable.objects.filter(name = Backbonename).first().id
        if(BackboneID == None):
            raise WebDatabaseNotFoundException()
            # return JsonResponse(data="No such BackboneID", status=404,safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':'Backbone Not Found'})
        userid = request.session.get('info')['uid']
        TbBackboneUserfileaddress.objects.create(userid=userid, backboneid=BackboneID, fileaddress=Address)
        return JsonResponse(data="Added backbone data", status=200,safe=False)
        # return JsonResponse({'code':200,'status':'success','data':'Backbone Address Added'})

#Update
def UpdateBackboneData(request):
    """
    UpdateBackboneData API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "POST"):
        data = json.loads(request.body)
        if("OriginalName" in data):
            OriginalName = data['OriginalName']
            if(OriginalName == None or OriginalName == ""):
                raise WebDatabaseValidationException(parameter="OriginalName")
                # return JsonResponse(data="OriginalName cannot be empty", status=400,safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':'Original name can not be empty'})
            BackboneID = Backbonetable.objects.filter(name = OriginalName).first().id
        elif("BackboneID" in data):
            BackboneID = data['BackboneID']
        if(BackboneID == None):
            raise WebDatabaseNotFoundException()
            # return JsonResponse(data="No such BackboneID", status=404,safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':'Backbone Not Found'})
        newName = data['newName']
        
        newLength = len(data['sequence']) if data['sequence'] != "" else 0
        newSequence = data['sequence'] if data['sequence'] != None else ""
        
        newSpecies = data['species']
        newCopynumber = data['copynumber']
        newNote = data['note']
        newAlias = data['alias']
        newTag = data['tag'] if 'tag' in data else "normal"
        newUser = request.session.get('info')['uname']
        # tag = "abnormal" if (len(newOri) >1 or len(newMarker) > 1) else "normal"
        if(newName == None or newName == ""):
            raise WebDatabaseValidationException(parameter="newName")
            # return JsonResponse(data="Name cannot be empty", status=400,safe=False)
        if(Backbonetable.objects.filter(name__iexact=newName).exclude(id=BackboneID).exists()):
            return JsonResponse(data={"success":False, "message":"Backbone name already exists"}, status=409, safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':'name, Sequence can not be empty'})
        try:
            with transaction.atomic():
                backbone_obj = Backbonetable.objects.select_for_update().get(id = BackboneID)
                
                backbone_obj.name = newName
                backbone_obj.length = newLength
                backbone_obj.sequence = newSequence
                backbone_obj.species = newSpecies
                backbone_obj.copynumber = newCopynumber
                backbone_obj.notes = newNote
                backbone_obj.alias = newAlias
                backbone_obj.user = newUser
                backbone_obj.tag = newTag
                backbone_obj.updatedate = timezone.localtime(timezone.now())
                backbone_obj.save()
        except IntegrityError:
            return JsonResponse(data={"success":False, "message":"Backbone name already exists"}, status=409, safe=False)
        return JsonResponse(data="Added backbone data", status=200,safe=False)
        # return JsonResponse({'code':200,'status':'success','data':'Backbone Data Updated'})


def UpdateBackboneFileAddress(request):
    """
    UpdateBackboneFileAddress API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == 'POST'):
        data = json.load(request.body)
        Name = data['name']
        Address = data['address']
        if(Name == None or Name == "" or Address == None or Address == ""):
            raise WebDatabaseValidationException(parameter="name")
            # return JsonResponse(data="Name cannot be empty", status=400,safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':'name can not be empty'})
        BackboneID = Backbonetable.objects.filter(name = Name).first().id
        if(BackboneID == None):
            raise WebDatabaseNotFoundException()
            # return JsonResponse(data="No such BackboneID", status=404,safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':'Backbone Not Found'})
        userID = request.session.get('info')['uid']
        FilterDict = {"backboneid": BackboneID,"userid": userID}
        TbBackboneUserfileaddress.objects.filter(**FilterDict).update(userid=userID, backboneid=BackboneID,fileaddress=Address)
        return JsonResponse(data="Added backbone data", status=200,safe=False)
        # return JsonResponse({'code':200,'status':'success','data':'Backbone Address Updated'})

#Delete
def DeleteBackboneData(request):
    """
    DeleteBackboneData API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        # Name = request.GET.get('name')
        # if(Name == None or Name == ""):
        #     return JsonResponse(data={"success":False, "message":"Name cannot be empty"}, status=400,safe=False)
        #     # return JsonResponse({'code':204,'status':'failed','data':'name can not be empty'})
        print(request.user)
        username = request.user.uname
        email = request.user.email
        print(username)
        BackboneID = request.GET.get('backboneid')
        Backbone_obj = Backbonetable.objects.get(id=BackboneID)
        if(Backbone_obj.user == None or Backbone_obj.user == "" or (Backbone_obj.user != username and Backbone_obj.user != email) ):
            raise WebDatabasePermissionException()
            # return JsonResponse(data ={"success" : False, "message":"褰撳墠鐢ㄦ埛娌℃湁鍒犻櫎鏉冮檺锛岃鑱旂郴涓婁紶鐢ㄦ埛杩涜鍒犻櫎"} , status = 400, safe = False)
        if(BackboneID == None):
            raise WebDatabaseNotFoundException()
            # return JsonResponse(data={"success":False, "message":"No such BackboneID"}, status=404,safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':'Backbone Not Found'})
        Backbonefeaturetable.objects.filter(backboneid=BackboneID).delete()
        TbBackboneUserfileaddress.objects.filter(backboneid=BackboneID).delete()
        Parentbackbonetable.objects.filter(parentbackboneid = BackboneID).delete()
        Backbonescartable.objects.filter(backboneid = BackboneID).delete()
        Backbone_Culture_Functions.objects.filter(backbone_id = BackboneID).delete()
        Backbonetable.objects.filter(id=BackboneID).delete()
        return JsonResponse(data={"success": True}, status=200,safe=False)
        # return JsonResponse({'code':200,'status':'success','data':'Backbone Data Deleted'})

def DeleteBackboneFileAddress(request):
    """
    DeleteBackboneFileAddress API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        name = request.GET.get('name')
        if(name == None or name == ""):
            raise WebDatabaseValidationException()
            # return JsonResponse(data="Name cannot be empty", status=400,safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':'name can not be empty'})
        BackboneID = Backbonetable.objects.filter(name = name).first().id
        if(BackboneID == None):
            raise WebDatabaseNotFoundException()
            # return JsonResponse(data="No such BackboneID", status=404,safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':'Backbone Not Found'})
        userid = request.session.get('info')['uid']
        FilterDict = {"userid": userid,"backboneid": BackboneID}
        TbBackboneUserfileaddress.objects.filter(**FilterDict).delete()
        return JsonResponse(data="Deleted backbone data", status=200,safe=False)
        # return JsonResponse({'code':200,'status':'success','data':'Backbone Address Deleted'})


def setBackboneCulture(request):
    """
    setBackboneCulture API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "POST"):
        data = json.loads(request.body)
        if("id" in data):
            backboneid = data['id']
        elif("name" in data):
            BackboneName = data["name"]
        Ori_list = data["ori"]
        Marker_list = data["marker"]
        start_time = time.time()
        max_wait_time = 5
        while time.time() - start_time < max_wait_time:
            try:
                with transaction.atomic():
                    if("name" in data):
                        backboneid = Backbonetable.objects.filter(name=BackboneName).first().id
                    Backbone_culture_exist = Backbone_Culture_Functions.objects.filter(backbone_id = backboneid).values()
                    if(len(Backbone_culture_exist) != 0):
                        Backbone_Culture_Functions.objects.filter(backbone_id = backboneid).delete()
                    backbone_id_obj = Backbonetable.objects.get(id = backboneid)
                    for each_ori in Ori_list:
                        Backbone_Culture_Functions.objects.create(backbone_id = backbone_id_obj,function_content = each_ori, function_type = "ori")
                    for each_marker in Marker_list:
                        Backbone_Culture_Functions.objects.create(backbone_id = backbone_id_obj,function_content = each_marker, function_type="marker")
                    backbone_obj = Backbonetable.objects.select_for_update().get(id=backboneid)
                    backbone_obj.tag = "abnormal" if len(Ori_list) > 1 or len(Marker_list) > 1 or len(Ori_list) == 0 or len(Marker_list) == 0 else "normal"
                    backbone_obj.updatedata = timezone.localtime(timezone.now())
                    backbone_obj.save()
                    return JsonResponse(data = {"success":True,"data":"success upload"},status=200, safe=False)
            except Plasmidneed.DoesNotExist:
                time.sleep(0.5)
                continue
            except OperationalError as e:
                if 'lock' in str(e).lower():
                    time.sleep(0.5)
                    continue
                raise e
        return JsonResponse(data={'success':False,'error':'time out'},status = 400, safe = False)


def BackboneFields(request):
    """
    BackboneFields API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    fields =[field.name for field in Backbonetable._meta.get_fields()]
    fields.remove("backbone_culture_functions")
    fields.remove("backbonescartable")
    fields.remove("tbbackboneuserfileaddress")
    fields.remove("parentbackbonetable")
    fields.remove("backbonefeaturetable")
    return JsonResponse(data={"success":True, "data":fields}, status = 200, safe=False)

def BackboneListByUser(request,username):
    """
    BackboneListByUser API view.

    Args:
        request: Django HttpRequest object.
        username: Input parameter.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        if(username == None or username == ""):
            raise WebDatabaseValidationException(parameter="username")
            # return JsonResponse(data = {"success":False, "message":"Parameter cannot be empty"}, status=400, safe=False)
        else:
            result = list(Backbonetable.objects.filter(user = username).values())
            return JsonResponse(data={"success":True, "data":result}, status = 200, safe= False)
    else:
        raise WebDatabaseGETMethodException()
        # return JsonResponse(data={"success":False,"message":"Just GET method"},status =400, safe=False)
        
        
def deleteBackboneFeature(request):
    """
    deleteBackboneFeature API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if request.method == "GET":
        try:
            name = request.GET.get("name")
            bid=Backbonetable.objects.filter(name=name).first().id
            with transaction.atomic():
                Backbonefeaturetable.objects.select_for_update().filter(backboneid=bid).delete()
            return JsonResponse(data={"success":True},status=200,safe=False)
        except Exception as e:
            return JsonResponse(data={"success":False,"message":str(e.args)},status=400,safe=False)
                
                
                
                
                
def AddBackboneFeature(request, BackboneName):
    """
    AddBackboneFeature API view.

    Args:
        request: Django HttpRequest object.
        BackboneName: Input parameter.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "POST"):
        data = json.loads(request.body)
        start_position = data['start_position']
        end_position = data['end_position']
        label = data['label']
        type = data['feature_type']
        color = data['color']
        ape_info = data['ape_info']
        max_wait_time = 5
        start_time = time.time()
        while time.time() - start_time < max_wait_time:
            with transaction.atomic():
                try:
                    backbone_obj = Backbonetable.objects.get(name = BackboneName)
                        # backbone_obj = Backbonetable.objects.get(name = BackboneName)
                except Backbonetable.DoesNotExist:
                    time.sleep(0.5)
                    continue
                Backbonefeaturetable.objects.create(backboneid = backbone_obj, feature_start = start_position, feature_end  = end_position,
                                            feature_type = type, feature_label = label, feature_color = color, feature_apeinfo = ape_info)
                return JsonResponse(data={'success':True}, status = 200 , safe=False)
        raise WebDatabaseException(f"Backbone {BackboneName} 不存在")
    else:
        raise WebDatabasePOSTMethodException()
        # return JsonResponse(data={'success':False,'message':"Just POST Method"}, status = 200, safe=False)

def GetBackboneFeature(request, BackboneID):
    """
    GetBackboneFeature API view.

    Args:
        request: Django HttpRequest object.
        BackboneID: Input parameter.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        try:
            result = Backbonefeaturetable.objects.filter(backboneid=BackboneID).values()
            return JsonResponse(data={"success":True,"data":list(result)},status = 200, safe=False)
        except Backbonefeaturetable.DoesNotExist:
            raise WebDatabaseNotFoundException()
            # return JsonResponse(data={"success":False,"message":"BackboneFeatureTable Does Not Exist"}, status=400, safe=False)
        except Exception as e:
            raise e
    else:
        raise WebDatabaseGETMethodException()
        # return JsonResponse(data={"successs":False,"message":"Just Get Method"},status=400,safe=False)


def _get_feature_payload(data):
    return {
        "feature_start": data.get("feature_start", data.get("start_position")),
        "feature_end": data.get("feature_end", data.get("end_position")),
        "feature_type": data.get("feature_type"),
        "feature_label": data.get("feature_label", data.get("label")),
        "feature_color": data.get("feature_color", data.get("color")),
        "feature_apeinfo": data.get("feature_apeinfo", data.get("ape_info")),
    }


def _validate_feature_payload(payload, partial=False):
    required_fields = ["feature_start", "feature_end", "feature_type", "feature_label", "feature_color", "feature_apeinfo"]
    if payload["feature_color"] in [None, ""]:
        payload["feature_color"] = payload["feature_apeinfo"]
    if partial:
        payload = {key: value for key, value in payload.items() if value is not None}
        if not payload:
            return False, "No feature fields to update", payload
    missing_fields = [field for field in required_fields if not partial and payload.get(field) in [None, ""]]
    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}", payload
    return True, "", payload


def _add_feature(request, parent_model, feature_model, parent_lookup, parent_id_field, parent_obj_field, parent_name):
    if request.method != "POST":
        return JsonResponse(data={"success": False, "message": "Just POST Method"}, status=405, safe=False)

    try:
        data = json.loads(request.body)
        payload = _get_feature_payload(data)
        valid, message, payload = _validate_feature_payload(payload)
        # print(data)
        # print(valid)
        # print(message)
        # print(payload)
        if not valid:
            
            return JsonResponse(data={"success": False, "message": message}, status=400, safe=False)
        
        parent_obj = parent_model.objects.get(**{parent_lookup: parent_name})
        feature_obj = feature_model.objects.create(**{parent_obj_field: parent_obj}, **payload)
        return JsonResponse(data={"success": True, "data": list(feature_model.objects.filter(pfid=feature_obj.pfid).values())[0]}, status=200, safe=False)
    except parent_model.DoesNotExist:
        raise WebDatabaseNotFoundException()
        # return JsonResponse(data={"success": False, "message": f"No such {parent_id_field}"}, status=404, safe=False)
    except Exception as e:
        raise e
        # return JsonResponse(data={"success": False, "message": str(e.args)}, status=400, safe=False)


def _get_feature(request, feature_model, parent_obj_field, parent_id):
    if request.method != "GET":
        raise WebDatabaseGETMethodException()
        # return JsonResponse(data={"success": False, "message": "Just GET Method"}, status=405, safe=False)

    try:
        result = feature_model.objects.filter(**{parent_obj_field: parent_id}).values()
        return JsonResponse(data={"success": True, "data": list(result)}, status=200, safe=False)
    except Exception as e:
        raise e
        # return JsonResponse(data={"success": False, "message": str(e.args)}, status=400, safe=False)


def _update_feature(request, feature_model):
    if request.method != "POST":
        raise WebDatabasePOSTMethodException()
        # return JsonResponse(data={"success": False, "message": "Just POST Method"}, status=405, safe=False)

    try:
        data = json.loads(request.body)
        pfid = data.get("pfid")
        if pfid in [None, ""]:
            raise WebDatabaseValidationException(parameter="pfid")
            # return JsonResponse(data={"success": False, "message": "pfid cannot be empty"}, status=400, safe=False)
        payload = _get_feature_payload(data)
        valid, message, payload = _validate_feature_payload(payload, partial=True)
        if not valid:
            raise WebDatabasePermissionException()
            # return JsonResponse(data={"success": False, "message": message}, status=400, safe=False)

        with transaction.atomic():
            feature_obj = feature_model.objects.select_for_update().get(pfid=pfid)
            for field, value in payload.items():
                setattr(feature_obj, field, value)
            feature_obj.save()
        return JsonResponse(data={"success": True, "data": list(feature_model.objects.filter(pfid=pfid).values())[0]}, status=200, safe=False)
    except feature_model.DoesNotExist:
        return WebDatabaseNotFoundException()
        # return JsonResponse(data={"success": False, "message": "Feature does not exist"}, status=404, safe=False)
    except Exception as e:
        raise e
        # return JsonResponse(data={"success": False, "message": str(e.args)}, status=400, safe=False)


def _delete_feature(request, feature_model, parent_model, parent_lookup, parent_obj_field):
    if request.method != "GET":
        raise WebDatabaseGETMethodException()
        # return JsonResponse(data={"success": False, "message": "Just GET Method"}, status=405, safe=False)

    try:
        pfid = request.GET.get("pfid")
        parent_id = request.GET.get("id")
        parent_name = request.GET.get("name")
        if pfid:
            deleted_count, _ = feature_model.objects.filter(pfid=pfid).delete()
        elif parent_id:
            deleted_count, _ = feature_model.objects.filter(**{parent_obj_field: parent_id}).delete()
        elif parent_name:
            parent_obj = parent_model.objects.get(**{parent_lookup: parent_name})
            deleted_count, _ = feature_model.objects.filter(**{parent_obj_field: parent_obj.pk}).delete()
        else:
            raise WebDatabaseValidationException(parameter="pfid or name")
            # return JsonResponse(data={"success": False, "message": "pfid or id or name cannot be empty"}, status=400, safe=False)
        return JsonResponse(data={"success": True, "deleted_count": deleted_count}, status=200, safe=False)
    except parent_model.DoesNotExist:
        raise WebDatabaseNotFoundException()
        # return JsonResponse(data={"success": False, "message": "Parent data does not exist"}, status=404, safe=False)
    except Exception as e:
        raise e
        # return JsonResponse(data={"success": False, "message": str(e.args)}, status=400, safe=False)


def AddPartFeature(request, PartName):
    return _add_feature(request, Parttable, Partfeaturetable, "name", "part", "partid", PartName)


def GetPartFeature(request, PartID):
    return _get_feature(request, Partfeaturetable, "partid", PartID)


def UpdatePartFeature(request):
    return _update_feature(request, Partfeaturetable)


def deletePartFeature(request):
    return _delete_feature(request, Partfeaturetable, Parttable, "name", "partid")


def AddPlasmidFeature(request, PlasmidName):
    return _add_feature(request, Plasmidneed, Plasmidfeaturetable, "name", "plasmid", "plasmidid", PlasmidName)


def GetPlasmidFeature(request, PlasmidID):
    return _get_feature(request, Plasmidfeaturetable, "plasmidid", PlasmidID)


def UpdatePlasmidFeature(request):
    return _update_feature(request, Plasmidfeaturetable)


def deletePlasmidFeature(request):
    return _delete_feature(request, Plasmidfeaturetable, Plasmidneed, "name", "plasmidid")
            


#=========================================================================================
#TestData
def SearchByTestdataName(request):
    """
    SearchByTestdataName API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        name = request.GET.get('name')
        if(name == None or name == ""):
            return JsonResponse(data="Name cannot be empty", status=400,safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':'name can not be empty'})
        TestData = Testdatatable.objects.filter(name = name)
        if(len(TestData) > 0):
            return JsonResponse(data=list(TestData.values()), status=200,safe=False)
            # return JsonResponse({'code':200,'status':'success','data':list(TestData.values())})
        else:
            return JsonResponse(data="No such TestData", status=404,safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':'No Test Data Found'})







#=============================================================================================
#DBD
def GetDBDList(request):
    """
    GetDBDList API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        DBDList = Dbdtable.objects.all()
        DBDDict = []
        if(len(DBDList) > 0):
            for DBD in DBDList:
                PartObj = Parttable.objects.filter(name = DBD.name).first()
                # DBDDict[DBD.name] = [PartObj.alias,PartObj.level0sequence,PartObj.sourceorganism,PartObj.reference,PartObj.note,PartObj.confirmedsequence,PartObj.insertsequence,DBD.i0,DBD.kd]
                DBDDict.append({"Name":DBD.name,"Alias": PartObj.alias,"Level0Sequence":PartObj.level0sequence,"SourceOrganism":PartObj.sourceorganism,"Reference":PartObj.reference,"Note":PartObj.note,"ConfirmedSequence":PartObj.confirmedsequence,"InsertSequence":PartObj.insertsequence,"I0": DBD.i0,"kd": DBD.kd})
                # DBDDict.append([DBD.name,PartObj.alias,PartObj.level0sequence,PartObj.sourceorganism,PartObj.reference,PartObj.note,PartObj.confirmedsequence,PartObj.insertsequence,DBD.i0,DBD.kd])
            return JsonResponse(data=DBDDict, status=200,safe=False)
            # return JsonResponse({'code':200,'status':'success','data':list(DBDList)})
        else:
            return JsonResponse(data="No such DBDList", status=404,safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':'No DB Data Found'})

def GetDBDNameList(request):
    """
    GetDBDNameList API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        DBDNameList = Dbdtable.objects.all()
        Namelist = []
        if(len(DBDNameList) > 0):
            for obj in DBDNameList:
                Namelist.append(obj.name)
            return JsonResponse(data=Namelist, status=200,safe=False)
            # return JsonResponse({'code':200,'status':'success','data':Namelist})
        else:
            return JsonResponse(data="No DBD List", status=404,safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':'No DB Data Found'})

def GetDBDKdList(request):
    """
    GetDBDKdList API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        DBDKdList = Dbdtable.objects.all()
        KdList = []
        if(len(DBDKdList) > 0):
            for obj in DBDKdList:
                KdList.append(obj.kd)
            return JsonResponse(data=KdList, status=200,safe=False)
            # return JsonResponse({'code':200,'status':'success','data':KdList})
        else:
            return JsonResponse(data="No DBD List", status=404,safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':'No DB Data Found'})

def GetDBD(request):
    """
    GetDBD API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        name = request.GET.get('name')
        if(name == None or name == ""):
            return JsonResponse(data="Name cannot be empty", status=400,safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':"name can not be empty"})
        DBD = Dbdtable.objects.filter(name = name)
        if(DBD != None):
            return JsonResponse(data=list(DBD.values()), status=200,safe=False)
            # return JsonResponse({'code':200,'status':'success','data':list(DBD)})
        else:
            return JsonResponse(data="No such DBD", status=404,safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':'No DB Data Found'})

def GetDBDAllByName(request):
    """
    GetDBDAllByName API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        name = request.GET.get('name')
        if(name == None or name == ""):
            return JsonResponse(data="Name cannot be empty", status=400,safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':"name can not be empty"})
        DBD = Dbdtable.objects.filter(name = name).first()
        if(DBD != None):
            part_obj = Parttable.objects.filter(name = name).first()
            DBD_list = {"Name":DBD.name,"Alias": part_obj.alias,"Level0Sequence":part_obj.level0sequence,"SourceOrganism":part_obj.sourceorganism,"Reference":part_obj.reference,"Note":part_obj.note,"ConfirmedSequence":part_obj.confirmedsequence,"InsertSequence":part_obj.insertsequence,"I0": DBD.i0,"kd": DBD.kd}
            # DBD_list = [DBD.name,part_obj.alias,part_obj.level0sequence,part_obj.sourceorganism,part_obj.reference,part_obj.note,part_obj.confirmedsequence,part_obj.insertsequence,DBD.i0,DBD.kd]
            return JsonResponse(data = DBD_list, status=200,safe=False)
            # return JsonResponse({'code':200,'status':'success','data':list(DBD)})
        else:
            return JsonResponse(data="No such DBD", status=404,safe=False)

def GetDBDMenu(request):
    """
    GetDBDMenu API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        DBDList = Dbdtable.objects.all()
        DBDMenu = []
        if(len(DBDMenu) > 0):
            for obj in DBDMenu:
                DBDMenu.append({"name":"obj.name","i0":obj.i0,"kd":obj.kd})
                # DBDMenu[obj.name] = [obj.i0,obj.kd]
            return JsonResponse(data=DBDMenu, status=200,safe=False)
            # return JsonResponse({'code':200,'status':'success','data':DBDMenu})
        else:
            return JsonResponse(data="No DBD Menu", status=404,safe=False)

def GetDBDKd(request):
    """
    GetDBDKd API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        name = request.GET.get('name')
        if(name == None or name == ""):
            return JsonResponse(data="Name cannot be empty", status=400,safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':'name can not be empty'})
        DBDKd = Dbdtable.objects.filter(name=name).first().kd
        if(DBDKd != None):
            return JsonResponse(data={'Kd':DBDKd}, status=200)
            # return JsonResponse({'code':200,'status':'success','data':DBDKd})
        else:
            return JsonResponse(data="No such DBD", status=404,safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':'No DB Data Found'})

def AddDBD(request):
    """
    AddDBD API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "POST"):
        Name = request.POST.get('name')
        I0 = float(request.POST.get('i0'))
        kd = float(request.POST.get('kd'))
        if(Name == None or I0 == None or kd == None or Name == "" or I0 == 0 or kd == 0):
            return JsonResponse(data="Name,I0,Kd cannot be empty", status=400,safe=False)
        else:
            Dbdtable.objects.create(name=Name, i0=I0, kd=kd)
            return JsonResponse(data="Added DBD", status=200,safe=False)

def UpdateDBD(request):
    """
    UpdateDBD API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "POST"):
        Name = request.POST.get('name')
        I0 = float(request.POST.get('i0'))
        kd = float(request.POST.get('kd'))
        if (Name == None or I0 == None or kd == None or Name == "" or I0 == 0 or kd == 0):
            return JsonResponse(data="Name,I0,Kd cannot be empty", status=400, safe=False)
        else:
            dbdobj = Dbdtable.objects.filter(name=Name)
            if(len(dbdobj)>0):
                dbdobj.update(i0=I0, kd=kd)
                return JsonResponse(data="Updated DBD", status=200, safe=False)
            else:
                return JsonResponse(data="No such DBD",status=404,safe=False)




#===================================================================================================
#LBD Dimer
def GetLBDDimer(request):
    """
    GetLBDDimer API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        LBDDimerList = Lbddimertable.objects.all()
        LBDDimerDict = []
        if(len(LBDDimerList) > 0):
            for obj in LBDDimerList:
                PartObj = Parttable.objects.filter(name = obj.name).first()
                # LBDDimerDict[obj.name] = [PartObj.alias,PartObj.level0sequence,PartObj.sourceorganism,PartObj.reference,PartObj.note,PartObj.confirmedsequence,PartObj.insertsequence,obj.k1,obj.k2,obj.k3,obj.i]
                LBDDimerDict.append({"name":obj.name,"alias":PartObj.alias,"level0sequence":PartObj.level0sequence,"sourceorganism":PartObj.sourceorganism,"reference":PartObj.reference,"note":PartObj.note,"confirmedsequence":PartObj.confirmedsequence,"insertsequence":PartObj.insertsequence,"k1":obj.k1,"k2":obj.k2,"k3":obj.k3,"i":obj.i})
            return JsonResponse(data=LBDDimerDict, status=200)
            # return JsonResponse({'code':200,'status':'success','data':list(LBDDimerList)})
        else:
            return JsonResponse(data="No such LBDDimer", status=404,safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':'No LBD Dimer Data Found'})


def GetLBDDimerMenu(request):
    """
    GetLBDDimerMenu API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        LBDDimerList = Lbddimertable.objects.all()
        LBDMenu = []
        if(len(LBDDimerList) > 0):
            for obj in LBDDimerList:
                LBDMenu.append({"name":obj.name,'k1':obj.k1,'k2':obj.k2,'k3':obj.k3,'i':obj.i})
                # LBDMenu[obj.name] = [obj.k1,obj.k2,obj.k3,obj.i]
            return JsonResponse(data=LBDMenu, status=200,safe=False)
            # return JsonResponse({'code':200,'status':'success','data':LBDMenu})
        else:
            return JsonResponse(data="No such LBDDimer", status=404,safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':'No LBD Dimer Data Found'})

def GetLBDDimerAllByName(request):
    """
    GetLBDDimerAllByName API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        name = request.GET.get('name')
        if(name == None or name == ""):
            return JsonResponse(data="Name cannot be empty", status=400,safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':"name can not be empty"})
        LBD = Lbddimertable.objects.filter(name = name).first()
        if(LBD != None):
            part_obj = Parttable.objects.filter(name = name).first()
            LBD_list = {"name":LBD.name,"alias":part_obj.alias,"level0sequence":part_obj.level0sequence,"sourceorganism":part_obj.sourceorganism,"reference":part_obj.reference,"note":part_obj.note,"confirmedsequence":part_obj.confirmedsequence,"insertsequence":part_obj.insertsequence,"k1":LBD.k1,"k2":LBD.k2,"k3":LBD.k3,"i":LBD.i}
            # LBD_list = [LBD.name,part_obj.alias,part_obj.level0sequence,part_obj.sourceorganism,part_obj.reference,part_obj.note,part_obj.confirmedsequence,part_obj.insertsequence,LBD.k1,LBD.k2,LBD.k3,LBD.i]
            return JsonResponse(data = LBD_list, status=200,safe=False)
            # return JsonResponse({'code':200,'status':'success','data':list(DBD)})
        else:
            return JsonResponse(data="No such LBD Dimer", status=404,safe=False)


def GetLBDDimerNameList(request):
    """
    GetLBDDimerNameList API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        LBDDimerList = Lbddimertable.objects.all()
        NameList = []
        if(len(LBDDimerList) > 0):
            for obj in LBDDimerList:
                NameList.append(obj.name)
            return JsonResponse(data=NameList, status=200, safe=False)
            # return JsonResponse({'code':200,'status':'success','data':NameList})
        else:
            return JsonResponse(data="No such LBDDimer", status=404,safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':'No LBD Dimer Data Found'})

def AddLBDDimer(request):
    """
    AddLBDDimer API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "POST"):
        Name = request.POST.get('name')
        k1 = float(request.POST.get('k1'))
        k2 = float(request.POST.get('k2'))
        k3 = float(request.POST.get('k3'))
        I = float(request.POST.get('i'))
        if(Name == None or Name == "" or k1 == None or k1 == 0 or k2 == None
                or k2 == 0 or k3 == None or k3 == 0 or I == None or I == 0):
            return JsonResponse(data="Name,k1,k2,k3,I cannot be empty", status=400,safe=False)
        else:
            Lbddimertable.objects.create(name=Name, k1=k1, k2=k2, k3=k3, I=I)
            return JsonResponse(data="Added LBDDimer", status=200,safe=False)

def UpdateLbdDimer(request):
    """
    UpdateLbdDimer API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "POST"):
        Name = request.POST.get('name')
        k1 = float(request.POST.get('k1'))
        k2 = float(request.POST.get('k2'))
        k3 = float(request.POST.get('k3'))
        I = float(request.POST.get('i'))
        if (Name == None or Name == "" or k1 == None or k1 == 0 or k2 == None
                or k2 == 0 or k3 == None or k3 == 0 or I == None or I == 0):
            return JsonResponse(data="Name,k1,k2,k3,I cannot be empty", status=400, safe=False)
        else:
            LBDObj = Lbddimertable.objects.filter(name=Name)
            if(len(LBDObj)>0):
                LBDObj.update(k1=k1, k2=k2, k3=k3, I=I)
                return JsonResponse(data="Updated LBD Dimer", status=200, safe=False)
            else:
                return JsonResponse(data="No such LBD Dimer", status=404, safe=False)



#===================================================================================================
#LBD NR
def GetLBDNr(request):
    """
    GetLBDNr API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        LBDNrList = Lbdnrtable.objects.all()
        LBDList = []
        if(len(LBDNrList) > 0):
            for obj in LBDNrList:
                PartObj = Parttable.objects.filter(name=obj.name).first()
                LBDList.append({"name":obj.name,"alias":PartObj.alias,"level0sequence":PartObj.level0sequence,"sourceorganism":PartObj.sourceorganism,"reference":PartObj.reference,"note":PartObj.note,"confirmedsequence":PartObj.confirmedsequence,"insertsequence":PartObj.insertsequence,"k1":obj.k1,"k2":obj.k2,"k3":obj.k3,"kx1":obj.kx1,"kx2":obj.kx2})
                # LBDList[obj.name] = [PartObj.alias,PartObj.level0sequence,PartObj.sourceorganism,PartObj.reference,PartObj.note,PartObj.confirmedsequence,PartObj.insertsequence,obj.k1,obj.k2,obj.k3,obj.kx1,obj.kx2]
            return JsonResponse(data=LBDList, status=200)
            # return JsonResponse({'code':200,'status':'success','data':list(LBDList)})
        else:
            return JsonResponse(data="No such LBDNr", status=404,safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':'No LBDNr Data Found'})




def GetLBDNRMenu(request):
    """
    GetLBDNRMenu API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        LBDNrList = Lbdnrtable.objects.all()
        LBDNRMenu = []
        if(len(LBDNrList) > 0):
            for obj in LBDNrList:
                # LBDNRMenu[obj.name] = [obj.k1,obj.k2,obj.k3,obj.kx1,obj.kx2]
                LBDNRMenu.append({"name":obj.name,"k1":obj.k1,"k2":obj.k2,"k3":obj.k3,"kx1":obj.kx1,"kx2":obj.kx2})
            return JsonResponse(data=LBDNRMenu, status=200)
            # return JsonResponse({'code':200,'status':'success','data':LBDNRMenu})
        else:
            return JsonResponse(data="No such LBDNr", status=404,safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':'No LBDNR Data Found'})

def GetLBDNRAllByName(request):
    """
    GetLBDNRAllByName API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        name = request.GET.get('name')
        if(name == None or name == ""):
            return JsonResponse(data="Name cannot be empty", status=400,safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':"name can not be empty"})
        LBD = Lbdnrtable.objects.filter(name = name).first()
        if(LBD != None):
            part_obj = Parttable.objects.filter(name = name).first()
            LBD_list = {"name":LBD.name,"alias":part_obj.alias,"level0sequence":part_obj.level0sequence,"sourceorganism":part_obj.sourceorganism,"reference":part_obj.reference,"note":part_obj.note,"confirmedsequence":part_obj.confirmedsequence,"insertsequence":part_obj.insertsequence,"k1":LBD.k1,"k2":LBD.k2,"k3":LBD.k3,"kx1":LBD.kx1,"kx2":LBD.kx2}
            # LBD_list = [LBD.name,part_obj.alias,part_obj.level0sequence,part_obj.sourceorganism,part_obj.reference,part_obj.note,part_obj.confirmedsequence,part_obj.insertsequence,LBD.k1,LBD.k2,LBD.k3,LBD.i]
            return JsonResponse(data = LBD_list, status=200,safe=False)
            # return JsonResponse({'code':200,'status':'success','data':list(DBD)})
        else:
            return JsonResponse(data="No such LBD Dimer", status=404,safe=False)


def GetLBDNRNameList(request):
    """
    GetLBDNRNameList API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        LBDNRList = Lbdnrtable.objects.all()
        LBDNameList = []
        if(len(LBDNRList) > 0):
            for obj in LBDNRList:
                LBDNameList.append(obj.name)
            return JsonResponse(data=LBDNameList, status=200,safe=False)
            # return JsonResponse({'code':200,'status':'success','data':LBDNRMenu})
        else:
            return JsonResponse(data="No such LBDNR", status=404,safe=False)
            # return JsonResponse({'code':204,'status':'failed','data':'No LBDNR Data Found'})


def AddLbdnr(request):
    """
    AddLbdnr API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "POST"):
        Name = request.POST.get('name')
        k1 = float(request.POST.get('k1'))
        k2 = float(request.POST.get('k2'))
        k3 = float(request.POST.get('k3'))
        kx1 = float(request.POST.get('kx1'))
        kx2 = float(request.POST.get('kx2'))
        if(Name == None or Name == "" or k1 == None or k1 == 0 or k2 == None or k2 == 0 or k3 == None
        or k3 == 0 or kx1 == None or kx1 == 0 or kx2 == None or kx2 == 0):
            return JsonResponse(data="Name,k1,k2,k3,kx1,kx2 cannot be empty", status=400,safe=False)
        else:
            Lbdnrtable.objects.create(name=Name,k1=k1,k2=k2,k3=k3,kx1=kx1,kx2=kx2)
            return JsonResponse(data="Added LBD NR", status=200,safe=False)

def UpdateLBDnr(request):
    """
    UpdateLBDnr API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "POST"):
        Name = request.POST.get('name')
        k1 = float(request.POST.get('k1'))
        k2 = float(request.POST.get('k2'))
        k3 = float(request.POST.get('k3'))
        kx1 = float(request.POST.get('kx1'))
        kx2 = float(request.POST.get('kx2'))
        if (Name == None or Name == "" or k1 == None or k1 == 0 or k2 == None or k2 == 0 or k3 == None
                or k3 == 0 or kx1 == None or kx1 == 0 or kx2 == None or kx2 == 0):
            return JsonResponse(data="Name,k1,k2,k3,kx1,kx2 cannot be empty", status=400, safe=False)
        else:
            Lbdnrtable.objects.filter(name=Name).update(k1 = k1,k2=k2,k3=k3,kx1=kx1,kx2=kx2)
            return JsonResponse(data="Updated LBD NR", status=200, safe=False)

def GetPartIDByName(request):
    """
    GetPartIDByName API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        Name = request.GET.get('name')
        if(Name != None and Name != ""):
            ID = Parttable.objects.filter(name = Name).first()
            if(ID != None):
                return JsonResponse(data = {"PartID":ID.partid},status=200,safe=False)
            else:
                raise WebDatabaseNotFoundException()
                # return JsonResponse(data = "No such part",status=404, safe=False)
        else:
            raise WebDatabaseValidationException(parameter="name")
            # return JsonResponse(data = "Name cannot be empty",status=400,safe=False)


def GetPartNameByID(request):
    """
    GetPartNameByID API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        ID = request.GET.get('ID')
        if(ID != None and ID != ""):
            Name = Parttable.objects.filter(partid = ID).first()
            if(Name != None):
                return JsonResponse(data = {"PartName":Name.name},status=200,safe=False)
            else:
                raise WebDatabaseNotFoundException()
                # return JsonResponse(data = "No such part",status=404, safe=False)
        else:
            raise WebDatabaseValidationException(parameter="ID")
            # return JsonResponse(data = "ID cannot be empty",status=400,safe=False)

def GetPartAliasByID(request):
    if(request.method == "GET"):
        ID = request.GET.get('ID')
        if(ID != None and ID != ""):
            Name = Parttable.objects.filter(partid = ID).first()
            if(Name != None):
                return JsonResponse(data = {"PartAlias":Name.alias},status=200,safe=False)
            else:
                raise WebDatabaseNotFoundException()
                # return JsonResponse(data = "No such part",status=404, safe=False)
        else:
            raise WebDatabaseValidationException(parameter="ID")
            # return JsonResponse(data = "ID cannot be empty",status=400,safe=False)


def GetPartSeqByID(request):
    """
    GetPartSeqByID API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        ID = request.GET.get('partid')
        if(ID == None or ID == 0):
            raise WebDatabaseValidationException(parameter="partid")
            # return JsonResponse(data = {"success":False,"data":"Parameter is empty"}, status = 400, safe = False)
        else:
            sequence = list(Parttable.objects.filter(partid = ID).values('level0sequence'))
            if(len(sequence) > 0):
                return JsonResponse(data = {'success':True,'data':sequence[0]}, status = 200, safe = False)
            else:
                raise WebDatabaseNotFoundException()
                # return JsonResponse(data = {'success':False, "data":"No such part"},status = 404, safe = False)
    else:
        raise WebDatabaseGETMethodException()
        # return JsonResponse(data = {'success':False,'data':'Only GET method'},status = 404, safe = False)




def GetBackboneIDByName(request):
    """
    GetBackboneIDByName API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == 'GET'):
        Name = request.GET.get('name')
        if(Name != None and Name != ''):
            ID = Backbonetable.objects.filter(name=Name).first()
            if(ID != None):
                return JsonResponse(data={"BackboneID":ID.id},status=200,safe=False)
            else:
                raise WebDatabaseNotFoundException()
                # return JsonResponse(data = "No such Backbone",status=404, safe=False)
        else:
            raise WebDatabaseValidationException(parameter="name")
            # return JsonResponse(data="Name cannot be empty",status=400,safe=False)
        
        
def GetBackboneNameByID(request):
    """
    GetBackboneNameByID API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == 'GET'):
        ID = request.GET.get('ID')
        if(ID != None and ID != ''):
            Name = Backbonetable.objects.filter(id=ID).first()
            if(Name != None):
                return JsonResponse(data={"BackboneName":Name.name},status=200,safe=False)
            else:
                raise WebDatabaseNotFoundException()
                # return JsonResponse(data = "No such Backbone",status=404, safe=False)
        else:
            raise WebDatabaseValidationException(parameter="ID")
            # return JsonResponse(data="ID cannot be empty",status=400,safe=False)

def GetBackboneAliasByID(request):
    if(request.method == 'GET'):
        ID = request.GET.get('ID')
        if(ID != None and ID != ''):
            Name = Backbonetable.objects.filter(id=ID).first()
            if(Name != None):
                return JsonResponse(data={"BackboneAlias":Name.alias},status=200,safe=False)
            else:
                raise WebDatabaseNotFoundException()
                # return JsonResponse(data = "No such Backbone",status=404, safe=False)
        else:
            raise WebDatabaseValidationException(parameter="ID")
            # return JsonResponse(data="ID cannot be empty",status=400,safe=False)



def GetPlasmidIDByName(request):
    """
    GetPlasmidIDByName API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method=='GET'):
        Name = request.GET.get('name')
        if(Name != None and Name != ""):
            ID = Plasmidneed.objects.filter(name = Name).first()
            if(ID != None):
                return JsonResponse(data = {"PlasmidID":ID.plasmidid},status=200,safe=False)
            else:
                raise WebDatabaseNotFoundException()
                # return JsonResponse(data = "No such Plasmid",status=400, safe=False)
        else:
            raise WebDatabaseValidationException(parameter="name")
            # return JsonResponse(data = "Name cannot be empty",status=400,safe=False)
        
        
def GetPlasmidNameByID(request):
    """
    GetPlasmidNameByID API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    
    if(request.method=='GET'):
        ID = request.GET.get('ID')
        if(ID != None and ID != ""):
            Name = Plasmidneed.objects.filter(plasmidid = ID).first()
            if(Name != None):
                return JsonResponse(data = {"PlasmidName":Name.name},status=200,safe=False)
            else:
                raise WebDatabaseNotFoundException()
                # return JsonResponse(data = "No such Plasmid",status=400, safe=False)
        else:
            raise WebDatabaseValidationException(parameter="ID")
            # return JsonResponse(data = "ID cannot be empty",status=400,safe=False)

def GetPlasmidAliasByID(request):
    if(request.method=='GET'):
        ID = request.GET.get('ID')
        if(ID != None and ID != ""):
            Name = Plasmidneed.objects.filter(plasmidid = ID).first()
            if(Name != None):
                return JsonResponse(data = {"PlasmidAlias":Name.alias},status=200,safe=False)
            else:
                raise WebDatabaseNotFoundException()
                # return JsonResponse(data = "No such Plasmid",status=400, safe=False)
        else:
            raise WebDatabaseValidationException(parameter="ID")
            # return JsonResponse(data = "ID cannot be empty",status=400,safe=False)

def AddPlasmidParentInfo(request):
    """
    AddPlasmidParentInfo API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "POST"):
        data = json.loads(request.body)
        if("PlasmidName" in data):
            plasmidName = data["PlasmidName"]
            plasmidID = Plasmidneed.objects.filter(name = plasmidName).first().plasmidid
        if("PlasmidID" in data):
            plasmidID = data['PlasmidID']
        ParentInfo = data["PlasmidParentInfo"]
        if(plasmidID == "" or plasmidID == 0):
            raise WebDatabaseValidationException(parameter = "plasmidID")
            # return JsonResponse(data = {"success":False,"data":"Parameter is empty"},status = 400, safe=False)
        start_time = time.time()
        max_wait_time = 5
        while time.time() - start_time < max_wait_time:
            try:
                with transaction.atomic():
                    Plasmidneed.objects.filter(plasmidid = plasmidID).update(customparentinformation = ParentInfo)
                    return JsonResponse(data = {"success":True,"data":"success upload"},status=200, safe=False)
            except Plasmidneed.DoesNotExist:
                time.sleep(0.5)
                continue
            except OperationalError as e:
                if 'lock' in str(e).lower():
                    time.sleep(0.5)
                    continue
                raise e
        raise WebDatabaseTimeoutException()



    
def AddParentPart(request):
    """
    AddParentPart API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "POST"):
        data = json.loads(request.body)
        if('SonPlasmidName' in data):
            sonPlasmidid = Plasmidneed.objects.filter(name = data['SonPlasmidName']).first().plasmidid
        if('SonPlasmidId' in data):
            sonPlasmidid = data['SonPlasmidId']
        ParentPartName = data['ParentPartName']
        if(sonPlasmidid == None or sonPlasmidid == 0 or sonPlasmidid == ""):
            raise WebDatabaseValidationException(parameter="SonPlasmidId")
        if(ParentPartName == None or ParentPartName == ""):
            raise WebDatabaseValidationException(parameter="ParentPartName")
            
            # return JsonResponse(data="PlasmidName or PartName cannot be empty", status=400,safe=False)
            # return JsonResponse({'code':204,'status': 'failed', 'data': 'Plasmid Name can not be empty'})
        start_time = time.time()
        max_wait_time = 5
        while time.time() - start_time < max_wait_time:
            try:
                with transaction.atomic():
                    sonPlasmidObj = Plasmidneed.objects.get(plasmidid = sonPlasmidid)
                    parentPartObj = Parttable.objects.filter(name = ParentPartName).first()
                    if(parentPartObj == None):
                        raise WebDatabaseNotFoundException()
                        # return JsonResponse(data={"success":False},status=404,safe=False)
                    if(Parentparttable.objects.filter(sonplasmidid = sonPlasmidObj,parentpartid = parentPartObj).count() == 0):
                        Parentparttable.objects.create(sonplasmidid=sonPlasmidObj,parentpartid = parentPartObj)
                    return JsonResponse(data={"success":True},status=200,safe=False)
            except Plasmidneed.DoesNotExist:
                time.sleep(0.5)
                continue
            except Parttable.DoesNotExist:
                time.sleep(0.5)
                continue
            except OperationalError as e:
                if 'lock' in str(e).lower():
                    time.sleep(0.5)
                    continue
                raise e
        raise WebDatabaseTimeoutException()

def AddParentPartByID(request):
    """
    AddParentPartByID API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "POST"):
        data = json.loads(request.body)
        sonPlasmidName = data['SonPlasmidName']
        ParentPartID = data['ParentPartID']
        if(sonPlasmidName == None or sonPlasmidName == ""):
            raise WebDatabaseValidationException(parameter="SonPlasmidName")
        if(ParentPartID == None or ParentPartID == ""):
            raise WebDatabaseValidationException(parameter="ParentPartID")
            # return JsonResponse(data="PlasmidName or PartName cannot be empty", status=400,safe=False)
            # return JsonResponse({'code':204,'status': 'failed', 'data': 'Plasmid Name can not be empty'})
        start_time = time.time()
        max_wait_time = 5
        while time.time() - start_time < max_wait_time:
            try:
                with transaction.atomic():
                    sonPlasmidObj = Plasmidneed.objects.get(name = sonPlasmidName)
                    parentPartObj = Parttable.objects.filter(partid = ParentPartID).first()
                    if(parentPartObj == None):
                        raise WebDatabaseNotFoundException()
                        # return JsonResponse(data={"success":False,"message":"No Such Part Data"},status=404,safe=False)
                    if(Parentparttable.objects.filter(sonplasmidid = sonPlasmidObj.plasmidid,parentpartid = parentPartObj.partid).count() == 0):
                        Parentparttable.objects.create(sonplasmidid=sonPlasmidObj,parentpartid = parentPartObj)
                    return JsonResponse(data={"success":True},status=200,safe=False)
            except Plasmidneed.DoesNotExist:
                time.sleep(0.5)
                continue
            except Parttable.DoesNotExist:
                time.sleep(0.5)
                continue
            except OperationalError as e:
                if 'lock' in str(e).lower():
                    time.sleep(0.5)
                    continue
                raise e
        raise WebDatabaseTimeoutException()
        # return JsonResponse(data={'success':False,'error':'time out'},status = 400, safe = False)

def AddParentBackbone(request):
    """
    AddParentBackbone API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "POST"):
        data = json.loads(request.body)
        if('SonPlasmidName' in data):
            sonPlasmidid = Plasmidneed.objects.filter(name = data['SonPlasmidName']).first().plasmidid
        if('SonPlasmidId' in data):
            sonPlasmidid = data['SonPlasmidId']
        ParentBackboneName = data['ParentBackboneName']
        if(sonPlasmidid == None or sonPlasmidid == 0 or ParentBackboneName == None or ParentBackboneName == ""):
            raise WebDatabaseValidationException()
            # return JsonResponse(data="PlasmidName or BackboneName cannot be empty", status=400,safe=False)
            # return JsonResponse({'code':204,'status': 'failed', 'data': 'Plasmid Name can not be empty'})
        start_time = time.time()
        max_wait_time = 5
        while time.time() - start_time < max_wait_time:
            try:
                with transaction.atomic():
                    sonPlasmidObj = Plasmidneed.objects.get(plasmidid = sonPlasmidid)
                    parentBackboneObj = Backbonetable.objects.filter(name = ParentBackboneName).first()
                    
                    if(parentBackboneObj == None):
                        raise WebDatabaseNotFoundException()
                        # return JsonResponse(data={"success":False},status=404,safe=False)
                    if(Parentbackbonetable.objects.filter(sonplasmidid = sonPlasmidObj,parentbackboneid = parentBackboneObj).count() == 0):
                        Parentbackbonetable.objects.create(sonplasmidid=sonPlasmidObj,parentbackboneid = parentBackboneObj)
                    return JsonResponse(data={"success":True},status=200,safe=False)
            except Plasmidneed.DoesNotExist:
                time.sleep(0.5)
                continue
            except Backbonetable.DoesNotExist:
                time.sleep(0.5)
                continue
            except OperationalError as e:
                if 'lock' in str(e).lower():
                    time.sleep(0.5)
                    continue
                raise e
        raise WebDatabaseTimeoutException()
        # return JsonResponse(data={'success':False,'error':'time out'},status = 400, safe = False)


def AddBackboneParentByID(request):
    """
    AddBackboneParentByID API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "POST"):
        data = json.loads(request.body)
        sonPlasmidName = data['SonPlasmidName']
        ParentBackboneID = data['ParentBackboneID']
        if(sonPlasmidName == None or sonPlasmidName == ""):
            raise WebDatabaseValidationException(parameter="SonPlasmidName")
        if(ParentBackboneID == None or ParentBackboneID == ""):
            raise WebDatabaseValidationException(parameter="ParentBackboneID")
            # return JsonResponse(data="PlasmidName or BackboneName cannot be empty", status=400,safe=False)
            # return JsonResponse({'code':204,'status': 'failed', 'data': 'Plasmid Name can not be empty'})
        start_time = time.time()
        max_wait_time = 5
        while time.time() - start_time < max_wait_time:
            try:
                with transaction.atomic():
                    sonPlasmidObj = Plasmidneed.objects.get(name = sonPlasmidName)
                    parentBackboneObj = Backbonetable.objects.filter(id = ParentBackboneID).first()
                    if(parentBackboneObj == None):
                        raise WebDatabaseNotFoundException()
                        # return JsonResponse(data={"success":False},status=404,safe=False)
                    if(Parentbackbonetable.objects.filter(sonplasmidid = sonPlasmidObj.plasmidid,parentbackboneid = parentBackboneObj.id).count() == 0):
                        Parentbackbonetable.objects.create(sonplasmidid=sonPlasmidObj,parentbackboneid = parentBackboneObj)
                    return JsonResponse(data={"success":True},status=200,safe=False)
            except Plasmidneed.DoesNotExist:
                time.sleep(0.5)
                continue
            except Backbonetable.DoesNotExist:
                time.sleep(0.5)
                continue
            except OperationalError as e:
                if 'lock' in str(e).lower():
                    time.sleep(0.5)
                    continue
                raise e
        raise WebDatabaseTimeoutException()
        # return JsonResponse(data={'success':False,'error':'time out'},status = 400, safe = False)


def DeletePlasmidParent(request):
    """
    DeletePlasmidParent API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        plasmidID = request.GET.get("plasmidid")
        
        Parentparttable.objects.filter(sonplasmidid = plasmidID).delete()
        Parentbackbonetable.objects.filter(sonplasmidid = plasmidID).delete()
        Parentplasmidtable.objects.filter(sonplasmidid = plasmidID).delete()
        return JsonResponse({"success":True}, status=200,safe=False)
    else:
        raise WebDatabaseGETMethodException()

def getPartValueList(request,column):
    """
    getPartValueList API view.

    Args:
        request: Django HttpRequest object.
        column: Input parameter.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == 'GET'):
        if(column != None and column != ""):
            categories = Parttable.objects.values_list(column,flat=True).distinct()
            categories_list = list(categories)
            for each_cate in categories_list:
                if(each_cate == "_" or each_cate == ""):
                    categories_list.remove(each_cate)
            return JsonResponse(data={'success':True,'data':categories_list}, status = 200, safe=False)
        else:
            raise WebDatabaseValidationException(parameter="column")
            # return JsonResponse(data="column cannot be empty",status=400, safe=False)
        
def getBackboneValueList(request,column):
    """
    getBackboneValueList API view.

    Args:
        request: Django HttpRequest object.
        column: Input parameter.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == 'GET'):
        if(column != None and column != ""):
            if(column == "ori"):
                categories = Backbone_Culture_Functions.objects.filter(function_type = "ori").values_list("function_content").distinct()
                categories_list = list(categories)
            elif(column == "marker"):
                categories = Backbone_Culture_Functions.objects.filter(function_type = "marker").values_list("function_content").distinct()
                categories_list = list(categories)
            else:
                categories = Backbonetable.objects.values_list(column,flat=True).distinct()
                categories_list = list(categories)
            for each_cate in categories_list:
                if(each_cate == "_" or each_cate == ""):
                    categories_list.remove(each_cate)
            return JsonResponse(data={'success':True,'data':categories_list}, status = 200, safe=False)
        else:
            raise WebDatabaseValidationException(parameter="column")
            # return JsonResponse(data="column cannot be empty",status=400, safe=False)
    else:
        raise WebDatabaseGETMethodException()
    
    
def getPlasmidValueList(request,column):
    """
    getPlasmidValueList API view.

    Args:
        request: Django HttpRequest object.
        column: Input parameter.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == 'GET'):
        if(column != None and column != ""):
            if(column == "ori" or column == "marker"):
                categories = list(Plasmid_Culture_Functions.objects.filter(function_type = column).values("function_content").distinct())
                categories_list = []
                for each_cate in categories:
                    categories_list.append(each_cate['function_content'])
                return JsonResponse(data={'success':True,'data':categories_list}, status = 200, safe=False)
            else:
                categories = Plasmidneed.objects.values_list(column,flat=True).distinct()
                categories_list = list(categories)
                for each_cate in categories_list:
                    if(each_cate == "_" or each_cate == ""):
                        categories_list.remove(each_cate)
                return JsonResponse(data={'success':True,'data':categories_list}, status = 200, safe=False)
        else:
            raise WebDatabaseValidationException(parameter="column")
    else:
        raise WebDatabaseGETMethodException()
            # return JsonResponse(data="column cannot be empty",status=400, safe=False)

#======================================================================
#Part Scar Operation
def getPartScar(request):
    """
    getPartScar API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == 'GET'):
        id = request.GET.get('id')
        if(id != None and id != ""):
            scar_info = Partscartable.objects.filter(part_id = id).values()
            if(scar_info != None):
                return JsonResponse(data = {'success':True,'scar_info':list(scar_info)},status = 200, safe = False)
            else:
                raise WebDatabaseNotFoundException()
                    # return JsonResponse(data = {'success': False,'error':"No such scar information"},status = 400, safe = False)
        else:
            raise WebDatabaseValidationException(parameter="id")
                # return JsonResponse(data={'success':False, 'error':"Name cannot be empty"},status = 400,safe=False)
    else:
        raise WebDatabaseGETMethodException()
    
    
    
    
def setPartScar(request):
    """
    setPartScar API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == 'POST'):
        data = json.loads(request.body)
        name = data['name']
        bsmbi = data['bsmbi']
        bsai = data['bsai']
        bbsi = data['bbsi']
        aari = data['aari']
        sapi = data['sapi']
        if(name != None and name != ""):
            start_time = time.time()
            max_wait_time = 5
            while time.time() - start_time < max_wait_time:
                try:
                    with transaction.atomic():
                        # part_obj = Parttable.objects.filter(name = name).first()
                        # part_obj = Parttable.objects.filter(name = name).first()
                        part_obj = Parttable.objects.select_for_update().get(name = name)
                        if(part_obj != None):
                            part_scar_obj = Partscartable.objects.select_for_update().get(part_id = part_obj.partid)
                            if(part_scar_obj != None):
                            # Partscartable.objects.filter(partid = part_obj).update(bsmbi = bsmbi, bsai = bsai, bbsi = bbsi,aari = aari, sapi = sapi)
                                part_scar_obj.bsmbi = bsmbi
                                part_scar_obj.bsai = bsai
                                part_scar_obj.bbsi = bbsi
                                part_scar_obj.aari = aari
                                part_scar_obj.sapi = sapi
                                part_scar_obj.save()
                                part_obj.updatedate = timezone.localtime(timezone.now())
                                part_obj.save()
                            else:
                                Partscartable.objects.create(partid = part_obj, bsmbi = bsmbi, bsai = bsai, bbsi = bbsi,aari = aari, sapi = sapi)
                        # else:
                            # Partscartable.objects.create(partid = part_obj, bsmbi = bsmbi, bsai = bsai, bbsi = bbsi,aari = aari, sapi = sapi)
                            return JsonResponse(data = {'success':True}, status = 200, safe = False)
                except Parttable.DoesNotExist:
                    time.sleep(0.5)
                    continue
                except OperationalError as e:
                    if 'lock' in str(e).lower():
                        time.sleep(0.5)
                        continue
                    raise e
            raise WebDatabaseTimeoutException()
            # return JsonResponse(data={'success':False,'error':'time out'},stauts = 400, safe = False)
        else:
            raise WebDatabaseValidationException(parameter="name")
            # return JsonResponse(data={'success':False,'error':'Name cannot be empty'},stauts = 400, safe = False)
    else:
        raise WebDatabasePOSTMethodException()
        # return JsonResponse(data = {'success' : False,'error' : 'Just Post request'},status = 400, safe=False)

#==================================================================================
#Backbone Scar Operation
def getBackboneScar(request):
    """
    getBackboneScar API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == 'GET'):
        id = request.GET.get('id')
        if(id != None and id != ""):
            # backbone_object = Backbonetable.objects.filter(name = ).first()
            scar_info = Backbonescartable.objects.filter(backboneid = id).values("bsmbi", "bsai", "bbsi", "aari", "sapi")
            if(len(scar_info) != 0):
                return JsonResponse(data = {'success':True,'scar_info':list(scar_info)},status = 200, safe = False)
            else:
                raise WebDatabaseNotFoundException()
                # return JsonResponse(data = {'success': False,'error':"No such scar information"},status = 200, safe = False)
        else:
            raise WebDatabaseValidationException(parameter="id")
            # return JsonResponse(data={'success':False, 'error':"id cannot be empty"},status = 400,safe=False)
    else:
        raise WebDatabaseGETMethodException()
    
    
    
        # return JsonResponse(data = {'success':False, 'error':'Just GET method'},status = 400, safe=False)

def setBackboneScar(request):
    """
    setBackboneScar API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == 'POST'):
        data = json.loads(request.body)
        if("name" in data):
            name = data['name']
        elif("backboneid" in data):
            id = data['backboneid']
        bsmbi = data['bsmbi']
        bsai = data['bsai']
        bbsi = data['bbsi']
        aari = data['aari']
        sapi = data['sapi']
        if(("name" in data and name != None and name != "") or ("backboneid" in data and id != None and id != "")):
            start_time = time.time()
            max_wait_time = 5
            while time.time() - start_time < max_wait_time:
                try:
                    with transaction.atomic():
                        # backbone_obj = Backbonetable.objects.filter(name = name).first()
                        if("name" in data):
                            id = Backbonetable.objects.get(name = name).id
                        try:
                            backbone_scar_obj = Backbonescartable.objects.select_for_update().get(backboneid = id)
                            backbone_scar_obj.bsmbi = bsmbi
                            backbone_scar_obj.bsai = bsai
                            backbone_scar_obj.bbsi = bbsi
                            backbone_scar_obj.aari = aari
                            backbone_scar_obj.sapi = sapi
                            backbone_scar_obj.save()
                        except Backbonescartable.DoesNotExist:
                            backbone_obj = Backbonetable.objects.get(id = id)
                            Backbonescartable.objects.create(backboneid = backbone_obj, bsmbi = bsmbi, bsai = bsai, bbsi = bbsi,aari = aari, sapi = sapi)
                            # Backbonescartable.objects.filter(backboneid = backbone_obj).update(bsmbi = bsmbi, bsai = bsai, bbsi = bbsi,aari = aari, sapi = sapi)
                        return JsonResponse(data = {'success':True}, status = 200, safe = False)
                except Backbonetable.DoesNotExist:
                    time.sleep(0.5)
                    continue
                except OperationalError as e:
                    if 'lock' in str(e).lower():
                        time.sleep(0.5)
                        continue
                    raise e
            raise WebDatabaseTimeoutException()
            # return JsonResponse(data={'success':False,'error':'time out'},stauts = 400, safe = False)
        else:
            raise WebDatabaseValidationException(parameter="name")
            # return JsonResponse(data={'success':False,'error':'Name cannot be empty'},status = 400, safe = False)
    else:
        raise WebDatabasePOSTMethodException()
        # return JsonResponse(data = {'success' : False,'error' : 'Just Post request'},status = 400, safe=False)
    


#=====================================================================================
#Plasmid Scar Operation
def getPlasmidScar(request):
    """
    getPlasmidScar API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == 'GET'):
        plasmidid = request.GET.get('plasmidid')
        if(plasmidid != None and plasmidid != ""):
            scar_info = Plasmidscartable.objects.filter(plasmidid = plasmidid).values()
            if(len(scar_info) != 0):
                return JsonResponse(data = {'success':True,'scar_info':list(scar_info)},status = 200, safe = False)
            else:
                raise WebDatabaseNotFoundException()
                # return JsonResponse(data = {'success': False,'error':"No such scar information"},status = 200, safe = False)
        else:
            # return JsonResponse(data="Name cannot be empty",status = 400,safe=False)
            raise WebDatabaseValidationException(parameter="plasmidid")
def setPlasmidScar(request):
    """
    setPlasmidScar API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == 'POST'):
        data = json.loads(request.body)
        if("name" in data):
            name = data['name']
        elif("plasmidid" in data):
            id = data['plasmidid']
        bsmbi = data['bsmbi']
        bsai = data['bsai']
        bbsi = data['bbsi']
        aari = data['aari']
        sapi = data['sapi']
        if(("name" in data and name != None and name != "") or ("plasmidid" in data and id != None and id != "")):
            start_time = time.time()
            max_wait_time = 5
            while time.time() - start_time < max_wait_time:
                try:
                    with transaction.atomic():
                        # plasmid_obj = Plasmidneed.objects.filter(name = name).first()
                        if("name" in data):
                            id = Plasmidneed.objects.get(name = name).plasmidid
                        plasmid_obj = Plasmidneed.objects.get(plasmidid = id)
                        try:
                            plasmid_scar_obj = Plasmidscartable.objects.select_for_update().get(plasmidid = id)
                            plasmid_scar_obj.bsmbi = bsmbi
                            plasmid_scar_obj.bsai = bsai
                            plasmid_scar_obj.bbsi = bbsi
                            plasmid_scar_obj.aari = aari
                            plasmid_scar_obj.sapi = sapi
                            plasmid_scar_obj.save()
                            # Plasmidscartable.objects.filter(plasmidid = plasmid_obj).update(bsmbi = bsmbi, bsai = bsai, bbsi = bbsi,aari = aari, sapi = sapi)
                        except Plasmidscartable.DoesNotExist:
                            Plasmidscartable.objects.create(plasmidid = plasmid_obj, bsmbi = bsmbi, bsai = bsai, bbsi = bbsi,aari = aari, sapi = sapi)
                        plasmid_obj.updatedate = timezone.localtime(timezone.now())
                        plasmid_obj.save()
                    return JsonResponse(data = {'success':True}, status = 200, safe = False)
                except Plasmidneed.DoesNotExist:
                    time.sleep(0.5)
                    continue
                except OperationalError as e:
                    if 'lock' in str(e).lower():
                        time.sleep(0.5)
                        continue
                    raise e
            raise WebDatabaseTimeoutException()
            # return JsonResponse(data={'success':False,'error':'time out'},stauts = 400, safe = False)

        else:
            return JsonResponse(data={'success':False,'error':'Name cannot be empty'},stauts = 400, safe = False)
    else:
        return JsonResponse(data = {'success' : False,'error' : 'Just Post request'},status = 400, safe=False)
    

def getPartScarList(request):
    """
    getPartScarList API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        # bsmbi = request.POST.get('bsmbi')
        # bsai = request.POST.get('bsai')
        # bbsi = request.POST.get('bbsi')
        # aari = request.POST.get('aari')
        # sapi = request.POST.get('sapi')
        categories1 = list(Partscartable.objects.values_list('bsmbi',flat = True).distinct())
        categories2 = list(Partscartable.objects.values_list('bsai',flat = True).distinct())
        categories3 = list(Partscartable.objects.values_list('bbsi',flat = True).distinct())
        categories4 = list(Partscartable.objects.values_list('aari',flat = True).distinct())
        categories5 = list(Partscartable.objects.values_list('sapi',flat = True).distinct())
        categories_list = []
        for each_cate in categories1:
            if(each_cate != "_" and each_cate != ""):
                categories_list.append(each_cate)
        for each_cate in categories2:
            if(categories_list.__contains__(each_cate) == False and each_cate != "_" and each_cate != ""):
                categories_list.append(each_cate)
        for each_cate in categories3:
            if(categories_list.__contains__(each_cate) == False and each_cate != "_" and each_cate != ""):
                categories_list.append(each_cate)
        for each_cate in categories4:
            if(categories_list.__contains__(each_cate) == False and each_cate != "_" and each_cate != ""):
                categories_list.append(each_cate)
        for each_cate in categories5:
            if(categories_list.__contains__(each_cate) == False and each_cate != "_" and each_cate != ""):
                categories_list.append(each_cate)
        return JsonResponse(data = {'success':True,'data':categories_list}, status=200,safe=False)

def getBackboneScarList(request):
    """
    getBackboneScarList API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        # bsmbi = request.POST.get('bsmbi')
        # bsai = request.POST.get('bsai')
        # bbsi = request.POST.get('bbsi')
        # aari = request.POST.get('aari')
        # sapi = request.POST.get('sapi')
        categories1 = list(Backbonescartable.objects.values_list('bsmbi',flat = True).distinct())
        categories2 = list(Backbonescartable.objects.values_list('bsai',flat = True).distinct())
        categories3 = list(Backbonescartable.objects.values_list('bbsi',flat = True).distinct())
        categories4 = list(Backbonescartable.objects.values_list('aari',flat = True).distinct())
        categories5 = list(Backbonescartable.objects.values_list('sapi',flat = True).distinct())
        categories_list = []
        for each_cate in categories1:
            if(each_cate != "_" and each_cate != ""):
                categories_list.append(each_cate)
        for each_cate in categories2:
            if(categories_list.__contains__(each_cate) == False and each_cate != "_" and each_cate != ""):
                categories_list.append(each_cate)
        for each_cate in categories3:
            if(categories_list.__contains__(each_cate) == False and each_cate != "_" and each_cate != ""):
                categories_list.append(each_cate)
        for each_cate in categories4:
            if(categories_list.__contains__(each_cate) == False and each_cate != "_" and each_cate != ""):
                categories_list.append(each_cate)
        for each_cate in categories5:
            if(categories_list.__contains__(each_cate) == False and each_cate != "_" and each_cate != ""):
                categories_list.append(each_cate)
        return JsonResponse(data = {'success':True,'data':categories_list}, status=200,safe=False)

def getPlasmidScarList(request):
    """
    getPlasmidScarList API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        # bsmbi = request.POST.get('bsmbi')
        # bsai = request.POST.get('bsai')
        # bbsi = request.POST.get('bbsi')
        # aari = request.POST.get('aari')
        # sapi = request.POST.get('sapi')
        categories1 = list(Plasmidscartable.objects.values_list('bsmbi',flat = True).distinct())
        categories2 = list(Plasmidscartable.objects.values_list('bsai',flat = True).distinct())
        categories3 = list(Plasmidscartable.objects.values_list('bbsi',flat = True).distinct())
        categories4 = list(Plasmidscartable.objects.values_list('aari',flat = True).distinct())
        categories5 = list(Plasmidscartable.objects.values_list('sapi',flat = True).distinct())
        categories_list = []
        for each_cate in categories1:
            if(each_cate != '_' and each_cate != ""):
                categories_list.append(each_cate)
        for each_cate in categories2:
            if(categories_list.__contains__(each_cate) == False and each_cate != '_' and each_cate != ""):
                categories_list.append(each_cate)
        for each_cate in categories3:
            if(categories_list.__contains__(each_cate) == False and each_cate != '_' and each_cate != ""):
                categories_list.append(each_cate)
        for each_cate in categories4:
            if(categories_list.__contains__(each_cate) == False and each_cate != '_' and each_cate != ""):
                categories_list.append(each_cate)
        for each_cate in categories5:
            if(categories_list.__contains__(each_cate) == False and each_cate != '_' and each_cate != ""):
                categories_list.append(each_cate)
        return JsonResponse(data = {'success':True,'data':categories_list}, status=200,safe=False)


def UpdatePartSequence(request):
    """
    UpdatePartSequence API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "POST"):
        data = json.loads(request.body)
        name = data['name']
        sequence = data['Level0Sequence']
        # NewLength = len(request.POST.get('Level0Sequence'))
        # NewLevel0Sequence = request.POST.get('Level0Sequence')
        with transaction.atomic():
            try:
                part_obj = Parttable.objects.select_for_update().get(name = name)
                # Parttable.objects.filter(name = part_obj.name).update(lengthinlevel0 = len(sequence), Level0Sequence = sequence)
                part_obj.lengthinlevel0 = len(sequence)
                part_obj.level0sequence = sequence
                part_obj.updatedate = timezone.localtime(timezone.now())
                part_obj.save()
                return JsonResponse(data = {'success': True}, status = 200, safe = False)
            except Parttable.DoesNotExist:
                raise WebDatabaseNotFoundException()
                # return JsonResponse(data = {'success':False, 'message':"Part Does Not Exist"}, status = 404, safe = False)
            except Exception as e:
                raise e
                # return JsonResponse(data = {'success':False, 'message' : e.args}, status = 500, safe = False)
    else:
        raise WebDatabasePOSTMethodException()
        # return JsonResponse(data = {'success':False, 'message' : "just POST method"}, status = 500, safe = False)

def UpdateBackboneSequence(request):
    """
    UpdateBackboneSequence API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "POST"):
        data = json.loads(request.body)
        name = data['name']
        sequence = data['sequence']
        with transaction.atomic():
            try:
                backbone_obj = Backbonetable.objects.select_for_update().get(name = name)
                # Backbonetable.objects.filter(id = backboneid).update(length = len(sequence), sequence = sequence)
                # Backbonetable.objects.filter(name = backbone_obj.name).update(length = len(sequence), sequence = sequence)
                backbone_obj.sequence = sequence
                backbone_obj.length = len(sequence)
                backbone_obj.updatedate = timezone.localtime(timezone.now())
                backbone_obj.save()
                return JsonResponse(data = {'success': True}, status = 200, safe = False)
            except Backbonetable.DoesNotExist:
                raise WebDatabaseNotFoundException()
                # return JsonResponse(data = {'success':False, 'message':"Backbone Does Not Exist"}, status = 404, safe = False)
    else:
        raise WebDatabaseNotFoundException()
        # return JsonResponse(data = {'success':False, 'message' : "just POST method"}, status = 500, safe = False)
    
def UpdatePlasmidSequence(request):
    """
    UpdatePlasmidSequence API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "POST"):
        data = json.loads(request.body)
        name = data['name']
        sequence = data['sequence']
        try:
            with transaction.atomic():
                # sonPlasmidObj = Plasmidneed.objects.select_for_update().get(name = sonPlasmidName)
                plasmid_obj = Plasmidneed.objects.select_for_update().get(name = name)
                plasmid_obj.sequenceconfirm = sequence
                plasmid_obj.length = len(sequence)
                plasmid_obj.updatedate = timezone.localtime(timezone.now())
                # Plasmidneed.objects.filter(name = plasmid_obj.name).update(length = len(sequence), sequenceconfirm = sequence)
                plasmid_obj.save()
                return JsonResponse(data = {'success': True}, status = 200, safe = False)
        except Plasmidneed.DoesNotExist:
            print("Not Found")
            raise WebDatabaseNotFoundException()
            # return JsonResponse(data = {'success':False, 'message':"Plasmid Does Not Exist"}, status = 404, safe = False)
    else:
        raise WebDatabasePOSTMethodException()
        # return JsonResponse(data = {'success':False, 'message' : "just POST method"}, status = 500, safe = False)
    

def getuserlist(request):
    """
    getuserlist API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        userlist = list(CustomUser.objects.values('uname').distinct())
        return JsonResponse(data = {'success':True, "data":userlist}, status = 200, safe = False)
    else:
        raise WebDatabaseGETMethodException()
        # return JsonResponse(data = {"success":False, "message":"Just GET method"}, status = 400, safe=False)

def getAllUserUploadList(request):
    """
    getAllUserUploadList API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        userlist = list(CustomUser.objects.values('uname').distinct())
        result = []
        for each_user in userlist:
            part_count = Parttable.objects.filter(user = each_user['uname']).count()
            backbone_count = Backbonetable.objects.filter(user = each_user['uname']).count()
            plasmid_count = Plasmidneed.objects.filter(user = each_user['uname']).count()
            result.append({"uname":each_user['uname'],"part_count":part_count, "backbone_count":backbone_count, "plasmid_count":plasmid_count})
        return JsonResponse(data = {"success":True, "data":result}, status = 200, safe = False)
    else:
        raise WebDatabaseGETMethodException()
        # return JsonResponse(data = {"success":False, "message":"Just GET method"},status = 200, safe = False)

def getUserPartCount(request,uname):
    """
    getUserPartCount API view.

    Args:
        request: Django HttpRequest object.
        uname: Input parameter.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        count = Parttable.objects.filter(user = uname).count()
        return JsonResponse({"success":True,"count":count},status=200, safe=False)
    else:
        raise WebDatabaseGETMethodException()
        # return JsonResponse({"success":False,"message":"Just Get Method"},status=400,safe=False)
    
def getUserBackboneCount(request,uname):
    """
    getUserBackboneCount API view.

    Args:
        request: Django HttpRequest object.
        uname: Input parameter.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        count = Backbonetable.objects.filter(user = uname).count()
        return JsonResponse({"success":True,"count":count},status=200, safe=False)
    else:
        raise WebDatabaseGETMethodException()
        # return JsonResponse({"success":False,"message":"Just Get Method"},status=400,safe=False)

def getUserPlasmidCount(request,uname):
    """
    getUserPlasmidCount API view.

    Args:
        request: Django HttpRequest object.
        uname: Input parameter.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        count = Plasmidneed.objects.filter(user = uname).count()
        return JsonResponse({"success":True,"count":count},status=200, safe=False)
    else:
        raise WebDatabaseGETMethodException()
        # return JsonResponse({"success":False,"message":"Just Get Method"},status=400,safe=False)

def getUserrepositoryCount(request,uid):
    """
    getUserrepositoryCount API view.

    Args:
        request: Django HttpRequest object.
        uid: Input parameter.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        count = 0
        repositoryList = Temporaryrepository.objects.filter(userid = uid)
        for each in repositoryList:
            if(each.is_expired() == False):
                count +=1
        return JsonResponse(data={"success":True,"count":count},status=200,safe=False)
    else:
        raise WebDatabaseGETMethodException()
                
    
@csrf_exempt
def create_repository(request):
    """
    create_repository API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "POST"):
        
        data = json.loads(request.body)
        print(data)
        Name = data.get("Name")
        Note = data.get("note")
        Alias = data.get("alias")
        Level = data.get("level")
        if(Name != None and Name != ""):
            try:
                repository_id = str(uuid.uuid1())
                ttl_hours = 24*30
                
                expires_at = timezone.localtime(timezone.now())+timezone.timedelta(hours = ttl_hours)
                user = request.user
                default_data = {"parts":[],"plasmids":[],"backbones":[],"part_before_scar":[],"part_end_scar":[],"total_parts":0,"total_plasmids":0,"total_backbones":0};
                with transaction.atomic():
                    if(Temporaryrepository.objects.filter(userid = user,name=Name).exists()):
                        Temporaryrepository.objects.filter(userid=user, name=Name).delete()
                    Temporaryrepository.objects.create(id=repository_id,name=Name,userid=user,repositorycreate_time = timezone.localtime(timezone.now()),repositoryupdate_time = timezone.localtime(timezone.now()),repositoryexpire_time = expires_at,note=Note,data=default_data, alias = Alias, level=Level)
                return JsonResponse(data={'success':True,'repository_id':repository_id,'repository_name':Name,'url':f'/repository/{repository_id}','expires_at':expires_at},status=200,safe=False)
            except Exception as e:
                raise e
                # return JsonResponse(data=str(e.args),status = 400, safe=False)
        else:
            raise WebDatabaseValidationException(parameter="Name")
            # return JsonResponse(data="Name cannot be empty",status=400,safe=False)
    else:
        raise WebDatabasePOSTMethodException()
    
    
@csrf_exempt
#Get Repositories of the user
def get_repositories(request):
    """
    get_repositories API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "GET"):
        try:
            user = CustomUser.objects.get(uid=request.session['info']['uid'])
            repositories = list(Temporaryrepository.objects.only('id','name').filter(userid=user).values())
            # repositories = list(Temporaryrepository.objects.filter(userid=user).values())
            if(len(repositories) > 0):
                return JsonResponse(data={'success':True,'repo':repositories},status=200,safe=False)
            else:
                raise WebDatabaseNotFoundException()
                # return JsonResponse(data="No repository, Please create Repository firstly",status=400,safe=False)
        except Exception as e:
            raise e
            # return JsonResponse(data=str(e),status=404,safe=False)
    else:
        raise WebDatabaseGETMethodException()

@csrf_exempt
#Get a repository of the user
def get_repository(request):
    """
    get_repository API view.

    Args:
        request: Django HttpRequest object.

    Returns:
        JsonResponse | Any: View response or computed result.
    """
    if(request.method == "POST"):
        userid = request.session['info']['uid']
        data = json.loads(request.body)
        Name = data.get("Name")
        try:
            user = request.session['info']['uid']
            repository = Temporaryrepository.objects.filter(userid=user,name=Name).first()
            if(repository != None):
                if(repository.is_expired()):
                    repository.delete()
                    return JsonResponse({'success':False,'message':'Repository expired'},status = 410)
                return JsonResponse(data={'success':True,'repository':repository.id,'data':repository.data,'name':repository.name,"created_time":repository.repositorycreate_time,"expired_time":repository.repositoryexpire_time,"note":repository.note,"alias":repository.alias,"level":repository.level,"part_start_scar":repository.part_start_scar,"part_end_scar":repository.part_end_scar}, status = 200, safe = False)
            else:
                raise WebDatabaseNotFoundException()
                # return JsonResponse(data={'error':'Repository not found'},status = 404,safe=False)
        except Temporaryrepository.DoesNotExist:
            raise WebDatabaseNotFoundException()
            # return JsonResponse(data={'error':'Repository not found'},status = 404,safe=False)
    else:
        raise WebDatabasePOSTMethodException()
        # return JsonResponse(data={"success":False,"message":"Just POST method"},status=400,safe=False)


@csrf_exempt
def add_part_to_repository(request):
    """
    添加part到仓库
    """
    if request.method != 'POST':
        raise WebDatabasePOSTMethodException()
        # return JsonResponse({'error': 'Only POST method allowed'}, status=405)
    
    try:
        if 'info' not in request.session or 'uid' not in request.session['info']:
            raise WebDatabasePermissionException()
            # return JsonResponse({'error': 'User not logged in'}, status=401)
        
        user_id = request.session['info']['uid']
        user = CustomUser.objects.get(uid=user_id)

        try:
            request_data = json.loads(request.body)
            repositoryName = request_data.get('RepoName')
        except json.JSONDecodeError:
            raise WebDatabaseValidationException(parameter="RepoName")
            # return JsonResponse({'error': 'Invalid JSON format'}, status=400)
        # 鑾峰彇鎴栧垱寤虹敤鎴风殑涓存椂浠撳簱
        try:
            repository = Temporaryrepository.objects.get(userid=user,name=repositoryName)
        except Temporaryrepository.DoesNotExist:
            # 鍒涘缓鏂扮殑涓存椂浠撳簱,璇㈤棶鍚嶇О
            repository_id = uuid.uuid4()
            ttl_hours = 24
            expires_at = timezone.localtime(timezone.now()) + timezone.timedelta(hours=ttl_hours)
            user = CustomUser.objects.filter(uid=user_id).first()
            
            if not user:
                return JsonResponse({'error': 'User not found'}, status=404)
            
            repository = Temporaryrepository.objects.create(
                id=repository_id,
                name=repositoryName,
                userid=user,
                repositorycreate_time=timezone.localtime(timezone.now()),
                repositoryupdate_time=timezone.localtime(timezone.now()),
                repositoryexpire_time=expires_at,
                data={}
            )
        
        # 妫€鏌ヤ粨搴撴槸鍚﹁繃鏈?
        if repository.is_expired():
            repositoryID = repository.id
            repository.delete()
            return JsonResponse(data = {'error': f'Repository {repositoryID} expired'}, status=410)
        
        # 鑾峰彇璇锋眰鏁版嵁
        
        # 楠岃瘉蹇呴渶瀛楁
        if 'part_ids' not in request_data:
            return JsonResponse({'error': 'part_ids field is required'}, status=400)
        
        part_ids = request_data['part_ids']
        scar_before_list = request_data['part_start_scar']
        scar_end_list = request_data['part_end_scar']
        
        #
        if not isinstance(part_ids, list):
            part_ids = [part_ids]
        
        if not isinstance(scar_before_list,list):
            scar_before_list = [scar_before_list]
        
        if not isinstance(scar_end_list,list):
            scar_end_list = [scar_end_list]
        
        for part_id in part_ids:
            if not isinstance(part_id, (int, str)) or not str(part_id).strip():
                return JsonResponse({'error': f'Invalid part_id: {part_id}'}, status=400)
        
        
        current_data = repository.data if repository.data else {}
        
        
        if 'parts' not in current_data:
            current_data['parts'] = []
        
        # 娣诲姞鏂扮殑鍏冧欢ID锛堥伩鍏嶉噸澶嶏級
        existing_part_ids = set(str(pid) for pid in current_data['parts'])
        new_parts = []
        
        for part_id in part_ids:
            part_id_str = str(part_id)
            if part_id_str not in existing_part_ids:
                new_parts.append(part_id)
                existing_part_ids.add(part_id_str)
        
        # 鏇存柊鏁版嵁
        current_data['parts'].extend(new_parts)
        current_data['part_start_scar'] = scar_before_list
        current_data['part_end_scar'] = scar_end_list
        # current_data['last_updated'] = timezone.now().isoformat()
        current_data['total_parts'] = len(current_data['parts'])
        # 淇濆瓨鍒版暟鎹簱
        repository.data = current_data
        repository.repositoryupdate_time = timezone.localtime(timezone.now())
        repository.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully added {len(new_parts)} parts to repository',
            'added_parts': new_parts,
            'total_parts': current_data['total_parts'],
            'repository_id': str(repository.id),
            'expires_at': repository.repositoryexpire_time.isoformat()
        })
        
    except Exception as e:
        raise WebDatabaseServerException()
        # return JsonResponse({'error': f'Internal server error: {str(e)}'}, status=500)




@csrf_exempt
def add_backbone_to_repository(request):
    """
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method allowed'}, status=405)
    
    try:
        # 妫€鏌ョ敤鎴锋槸鍚﹀凡鐧诲綍
        if 'info' not in request.session or 'uid' not in request.session['info']:
            return JsonResponse({'error': 'User not logged in'}, status=401)
        
        user_id = request.session['info']['uid']
        user = CustomUser.objects.get(uid=user_id)

        try:
            request_data = json.loads(request.body.decode('utf-8'))
            repositoryName = request_data.get('RepoName')
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
        # 鑾峰彇鎴栧垱寤虹敤鎴风殑涓存椂浠撳簱
        try:
            repository = Temporaryrepository.objects.get(userid=user,name=repositoryName)
        except Temporaryrepository.DoesNotExist:
            # 鍒涘缓鏂扮殑涓存椂浠撳簱,璇㈤棶鍚嶇О
            repository_id = uuid.uuid4()
            ttl_hours = 24
            expires_at = timezone.localtime(timezone.now()) + timezone.timedelta(hours=ttl_hours)
            user = CustomUser.objects.filter(uid=user_id).first()
            
            if not user:
                return JsonResponse({'error': 'User not found'}, status=404)
            
            repository = Temporaryrepository.objects.create(
                id=repository_id,
                name=repositoryName,
                userid=user,
                repositorycreate_time=timezone.localtime(timezone.now()),
                repositoryupdate_time=timezone.localtime(timezone.now()),
                repositoryexpire_time=expires_at,
                data={}
            )
        
        # 妫€鏌ヤ粨搴撴槸鍚﹁繃鏈?
        if repository.is_expired():
            repositoryID = repository.id
            repository.delete()
            return JsonResponse(data = {'error': f'Repository {repositoryID} expired'}, status=410)
        
        # 鑾峰彇璇锋眰鏁版嵁
        
        # 楠岃瘉蹇呴渶瀛楁
        if 'backbone_ids' not in request_data:
            return JsonResponse({'error': 'backbone_ids field is required'}, status=400)
        
        backbone_ids = request_data['backbone_ids']
        
        # 纭繚part_ids鏄垪琛ㄦ牸寮?
        if not isinstance(backbone_ids, list):
            backbone_ids = [backbone_ids]
        
        # 楠岃瘉鍏冧欢ID鏍煎紡
        for backbone_id in backbone_ids:
            if not isinstance(backbone_id, (int, str)) or not str(backbone_id).strip():
                return JsonResponse({'error': f'Invalid backbone_id: {backbone_id}'}, status=400)
        
        # 鑾峰彇鐜版湁鏁版嵁
        current_data = repository.data if repository.data else {}
        
        # 纭繚parts鍒楄〃瀛樺湪
        if 'backbones' not in current_data:
            current_data['backbones'] = []
        
        # 娣诲姞鏂扮殑鍏冧欢ID锛堥伩鍏嶉噸澶嶏級
        existing_backbone_ids = set(str(bid) for bid in current_data['backbones'])
        new_backbones = []
        
        for backbone_id in backbone_ids:
            backbone_id_str = str(backbone_id)
            if backbone_id_str not in existing_backbone_ids:
                new_backbones.append(backbone_id)
                existing_backbone_ids.add(backbone_id_str)
        
        # 鏇存柊鏁版嵁
        current_data['backbones'].extend(new_backbones)
        # current_data['last_updated'] = timezone.now().isoformat()
        current_data['total_backbones'] = len(current_data['backbones'])
        
        # 淇濆瓨鍒版暟鎹簱
        repository.data = current_data
        repository.repositoryupdate_time = timezone.localtime(timezone.now())
        repository.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully added {len(new_backbones)} backbones to repository',
            'added_backbones': new_backbones,
            'total_backbones': current_data['total_backbones'],
            'repository_id': str(repository.id),
            'expires_at': repository.repositoryexpire_time.isoformat()
        })
        
    except Exception as e:
        return JsonResponse({'error': f'Internal server error: {str(e)}'}, status=500)

@csrf_exempt
def add_plasmid_to_repository(request):
    """
    灏嗗厓浠禝D娣诲姞鍒扮敤鎴风殑涓存椂浠撳簱涓?
    鏀寔鍗曚釜鍏冧欢ID鎴栧厓浠禝D鍒楄〃
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method allowed'}, status=405)
    
    try:
        # 妫€鏌ョ敤鎴锋槸鍚﹀凡鐧诲綍
        if 'info' not in request.session or 'uid' not in request.session['info']:
            return JsonResponse({'error': 'User not logged in'}, status=401)
        
        user_id = request.session['info']['uid']
        user = CustomUser.objects.get(uid=user_id)

        try:
            request_data = json.loads(request.body.decode('utf-8'))
            repositoryName = request_data.get('RepoName')
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
        # 鑾峰彇鎴栧垱寤虹敤鎴风殑涓存椂浠撳簱
        try:
            repository = Temporaryrepository.objects.get(userid=user,name=repositoryName)
        except Temporaryrepository.DoesNotExist:
            # 鍒涘缓鏂扮殑涓存椂浠撳簱,璇㈤棶鍚嶇О
            repository_id = uuid.uuid4()
            ttl_hours = 24
            expires_at = timezone.localtime(timezone.now()) + timezone.timedelta(hours=ttl_hours)
            user = CustomUser.objects.filter(uid=user_id).first()
            
            if not user:
                return JsonResponse({'error': 'User not found'}, status=404)
            
            repository = Temporaryrepository.objects.create(
                id=repository_id,
                name=repositoryName,
                userid=user,
                repositorycreate_time=timezone.localtime(timezone.now()),
                repositoryupdate_time=timezone.localtime(timezone.now()),
                repositoryexpire_time=expires_at,
                data={}
            )
        
        # 妫€鏌ヤ粨搴撴槸鍚﹁繃鏈?
        if repository.is_expired():
            repositoryID = repository.id
            repository.delete()
            return JsonResponse(data = {'error': f'Repository {repositoryID} expired'}, status=410)
        
        # 鑾峰彇璇锋眰鏁版嵁
        
        # 楠岃瘉蹇呴渶瀛楁
        if 'plasmid_ids' not in request_data:
            return JsonResponse({'error': 'plasmid_ids field is required'}, status=400)
        
        plasmid_ids = request_data['plasmid_ids']
        
        # 纭繚part_ids鏄垪琛ㄦ牸寮?
        if not isinstance(plasmid_ids, list):
            plasmid_ids = [plasmid_ids]
        
        # 楠岃瘉鍏冧欢ID鏍煎紡
        for plasmid_id in plasmid_ids:
            if not isinstance(plasmid_id, (int, str)) or not str(plasmid_id).strip():
                return JsonResponse({'error': f'Invalid plasmid_id: {plasmid_id}'}, status=400)
        
        # 鑾峰彇鐜版湁鏁版嵁
        current_data = repository.data if repository.data else {}
        
        # 纭繚parts鍒楄〃瀛樺湪
        if 'plasmids' not in current_data:
            current_data['plasmids'] = []
        
        # 娣诲姞鏂扮殑鍏冧欢ID锛堥伩鍏嶉噸澶嶏級
        existing_plasmid_ids = set(str(pid) for pid in current_data['plasmids'])
        new_plasmids = []
        
        for plasmid_id in plasmid_ids:
            plasmid_id_str = str(plasmid_id)
            if plasmid_id_str not in existing_plasmid_ids:
                new_plasmids.append(plasmid_id)
                existing_plasmid_ids.add(plasmid_id_str)
        
        # 鏇存柊鏁版嵁
        current_data['plasmids'].extend(new_plasmids)
        # current_data['last_updated'] = timezone.now().isoformat()
        current_data['total_plasmids'] = len(current_data['plasmids'])
        
        # 淇濆瓨鍒版暟鎹簱
        repository.data = current_data
        repository.repositoryupdate_time = timezone.localtime(timezone.now())
        repository.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully added {len(new_plasmids)} plasmids to repository',
            'added_plasmids': new_plasmids,
            'total_plasmids': current_data['total_plasmids'],
            'repository_id': str(repository.id),
            'expires_at': repository.repositoryexpire_time.isoformat()
        })
        
    except Exception as e:
        raise WebDatabaseServerException()
        # return JsonResponse({'error': f'Internal server error: {str(e)}'}, status=500)
    
    

@csrf_exempt
def remove_part_from_repository(request):
    """
    浠庣敤鎴风殑涓存椂浠撳簱涓Щ闄ゅ厓浠禝D
    """
    if request.method != 'POST':
        raise WebDatabasePOSTMethodException()
        # return JsonResponse({'error': 'Only POST method allowed'}, status=405)
    
    try:
        # 妫€鏌ョ敤鎴锋槸鍚﹀凡鐧诲綍
        if 'info' not in request.session or 'uid' not in request.session['info']:
            raise WebDatabasePermissionException()
            # return JsonResponse({'error': 'User not logged in'}, status=401)
        
        user_id = request.session['info']['uid']
        user = CustomUser.objects.get(uid=user_id)
        repositoryName = request.POST.get('RepoName')
        
        try:
            repository = Temporaryrepository.objects.get(userid_id=user,name=repositoryName)
        except Temporaryrepository.DoesNotExist:
            raise WebDatabaseNotFoundException()
            # return JsonResponse({'error': 'Repository not found'}, status=404)
        
        
        if repository.is_expired():
            repository.delete()
            return JsonResponse({'error': 'Repository expired'}, status=410)
        
        
        import json
        try:
            request_data = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
        
        
        if 'part_ids' not in request_data:
            raise WebDatabaseValidationException(parameter="part_ids")
            # return JsonResponse({'error': 'part_ids field is required'}, status=400)
        
        part_ids = request_data['part_ids']
        
        # 纭繚part_ids鏄垪琛ㄦ牸寮?
        if not isinstance(part_ids, list):
            part_ids = [part_ids]
        
        # 鑾峰彇鐜版湁鏁版嵁
        current_data = repository.data if repository.data else {}
        
        if 'parts' not in current_data:
            return JsonResponse({'error': 'No parts in repository'}, status=404)
        
        # 绉婚櫎鎸囧畾鐨勫厓浠禝D
        original_count = len(current_data['parts'])
        current_data['parts'] = [pid for pid in current_data['parts'] 
                                if str(pid) not in [str(part_id) for part_id in part_ids]]
        removed_count = original_count - len(current_data['parts'])
        
        # 鏇存柊鏁版嵁
        # current_data['last_updated'] = timezone.now().isoformat()
        current_data['total_parts'] = len(current_data['parts'])
        
        # 淇濆瓨鍒版暟鎹簱
        repository.data = current_data
        repository.repositoryupdate_time = timezone.localtime(timezone.now())
        repository.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully removed {removed_count} parts from repository',
            'removed_parts': part_ids,
            'total_parts': current_data['total_parts'],
            'repository_id': str(repository.id)
        })
        
    except Exception as e:
        return JsonResponse({'error': f'Internal server error: {str(e)}'}, status=500)


@csrf_exempt
def get_repository_parts(request):
    """
    鑾峰彇鐢ㄦ埛涓存椂浠撳簱涓殑鎵€鏈夊厓浠禝D
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Only GET method allowed'}, status=405)
    
    try:
        # 妫€鏌ョ敤鎴锋槸鍚﹀凡鐧诲綍
        if 'info' not in request.session or 'uid' not in request.session['info']:
            return JsonResponse({'error': 'User not logged in'}, status=401)
        
        user_id = request.session['info']['uid']
        
        # 鑾峰彇鐢ㄦ埛鐨勪复鏃朵粨搴?
        try:
            repository = Temporaryrepository.objects.get(userid_id=user_id)
        except Temporaryrepository.DoesNotExist:
            return JsonResponse({
                'success': True,
                'parts': [],
                'total_parts': 0,
                'message': 'Repository not found or empty'
            })
        
        # 妫€鏌ヤ粨搴撴槸鍚﹁繃鏈?
        if repository.is_expired():
            repository.delete()
            return JsonResponse({
                'success': True,
                'parts': [],
                'total_parts': 0,
                'message': 'Repository expired'
            })
        
        # 鑾峰彇鍏冧欢鏁版嵁
        current_data = repository.data if repository.data else {}
        parts = current_data.get('parts', [])
        
        return JsonResponse({
            'success': True,
            'parts': parts,
            'total_parts': len(parts),
            'repository_id': str(repository.id),
            'created_at': repository.repositorycreate_time.isoformat() if repository.repositorycreate_time else None,
            'updated_at': repository.repositoryupdate_time.isoformat() if repository.repositoryupdate_time else None,
            'expires_at': repository.repositoryexpire_time.isoformat() if repository.repositoryexpire_time else None,
            'last_updated': current_data.get('last_updated')
        })
    except Exception as e:
        return JsonResponse({'error': f'Internal server error: {str(e)}'}, status=500)


def _serialize_visitor_profile(profile):
    return {
        "id": profile.id,
        "visitor_uuid": profile.visitor_uuid,
        "institution": profile.institution,
        "lab_name": profile.lab_name,
        "person_name": profile.person_name,
        "cookie_key": profile.cookie_key,
        "visit_count": profile.visit_count,
        "first_seen_at": profile.first_seen_at.isoformat() if profile.first_seen_at else None,
        "last_seen_at": profile.last_seen_at.isoformat() if profile.last_seen_at else None,
        "last_path": profile.last_path,
        "last_ip": profile.last_ip,
        "last_user_agent": profile.last_user_agent,
        "created_by_user_id": profile.created_by_user_id,
        "created_at": profile.created_at.isoformat() if profile.created_at else None,
        "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
    }


def _serialize_visitor_access_log(log):
    return {
        "id": log.id,
        "visitor_id": log.visitor_id,
        "visited_at": log.visited_at.isoformat() if log.visited_at else None,
        "path": log.path,
        "method": log.method,
        "ip": log.ip,
        "user_agent": log.user_agent,
        "referer": log.referer,
        "cookie_snapshot": log.cookie_snapshot,
    }
def _serialize_visitor_feedback(feedback):
    return {
        "id": feedback.id,
        "visitor_id": feedback.visitor_profile_id,
        "feedback_type": feedback.feedback_type,
        "title": feedback.title,
        "content": feedback.content,
        "contact_email": feedback.contact_email,
        "page_path": feedback.page_path,
        "status": feedback.status,
        "created_at": feedback.created_at.isoformat() if feedback.created_at else None,
        "updated_at": feedback.updated_at.isoformat() if feedback.updated_at else None,
    }



def _get_request_json(request):
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return None


def _get_session_user_id(request):
    try:
        return request.session.get("info", {}).get("uid")
    except Exception:
        return None


@csrf_exempt
def createVisitorProfile(request):
    if request.method != "POST":
        raise WebDatabasePOSTMethodException()
        # return JsonResponse({"success": False, "message": "Just POST method"}, status=405, safe=False)

    request_data = _get_request_json(request)
    if request_data is None:
        return JsonResponse({"success": False, "message": "Invalid JSON format"}, status=400, safe=False)

    visitor_uuid = str(request_data.get("visitor_uuid") or uuid.uuid4())
    institution = (request_data.get("institution") or "").strip()
    lab_name = (request_data.get("lab_name") or "").strip()
    person_name = (request_data.get("person_name") or "").strip()
    cookie_key = request_data.get("cookie_key")
    created_by_user_id = request_data.get("created_by_user_id") or _get_session_user_id(request)

    if not institution or not lab_name or not person_name:
        return JsonResponse(
            {"success": False, "message": "institution, lab_name and person_name cannot be empty"},
            status=400,
            safe=False,
        )

    create_kwargs = {
        "visitor_uuid": visitor_uuid,
        "institution": institution,
        "lab_name": lab_name,
        "person_name": person_name,
        "cookie_key": cookie_key,
        "created_by_user_id": created_by_user_id,
    }

    try:
        with transaction.atomic():
            profile = VisitorProfile.objects.create(**create_kwargs)
        return JsonResponse({"success": True, "data": _serialize_visitor_profile(profile)}, status=200, safe=False)
    except IntegrityError as exc:
        return JsonResponse({"success": False, "message": str(exc)}, status=409, safe=False)
    except Exception as exc:
        return JsonResponse({"success": False, "message": str(exc)}, status=400, safe=False)


def getVisitorProfile(request):
    if request.method != "GET":
        return JsonResponse({"success": False, "message": "Just GET method"}, status=405, safe=False)

    visitor_id = request.GET.get("id")
    visitor_uuid = request.GET.get("visitor_uuid")
    cookie_key = request.GET.get("cookie_key")

    if not any([visitor_id, visitor_uuid, cookie_key]):
        return JsonResponse({"success": False, "message": "id or visitor_uuid or cookie_key cannot be empty"}, status=400, safe=False)

    try:
        queryset = VisitorProfile.objects.all()
        if visitor_id:
            profile = queryset.get(id=visitor_id)
        elif visitor_uuid:
            profile = queryset.get(visitor_uuid=visitor_uuid)
        else:
            profile = queryset.get(cookie_key=cookie_key)
        return JsonResponse({"success": True, "data": _serialize_visitor_profile(profile)}, status=200, safe=False)
    except VisitorProfile.DoesNotExist:
        return JsonResponse({"success": False, "message": "No such visitor profile"}, status=404, safe=False)
    except Exception as exc:
        return JsonResponse({"success": False, "message": str(exc)}, status=400, safe=False)


def listVisitorProfiles(request):
    if request.method != "GET":
        return JsonResponse({"success": False, "message": "Just GET method"}, status=405, safe=False)

    try:
        queryset = VisitorProfile.objects.all().order_by("-last_seen_at", "-id")
        institution = request.GET.get("institution")
        lab_name = request.GET.get("lab_name")
        person_name = request.GET.get("person_name")
        keyword = request.GET.get("keyword")
        created_by_user_id = request.GET.get("created_by_user_id")

        if institution:
            queryset = queryset.filter(institution__icontains=institution)
        if lab_name:
            queryset = queryset.filter(lab_name__icontains=lab_name)
        if person_name:
            queryset = queryset.filter(person_name__icontains=person_name)
        if created_by_user_id:
            queryset = queryset.filter(created_by_user_id=created_by_user_id)
        keyword_query = _build_or_keyword_query(keyword, ["institution", "lab_name", "person_name", "cookie_key", "visitor_uuid"])
        if keyword_query is not None:
            queryset = queryset.filter(keyword_query)

        data = [_serialize_visitor_profile(profile) for profile in queryset[:200]]
        return JsonResponse({"success": True, "data": data, "count": len(data)}, status=200, safe=False)
    except Exception as exc:
        return JsonResponse({"success": False, "message": str(exc)}, status=400, safe=False)


@csrf_exempt
def updateVisitorProfile(request):
    if request.method != "POST":
        raise WebDatabasePOSTMethodException()
        # return JsonResponse({"success": False, "message": "Just POST method"}, status=405, safe=False)

    request_data = _get_request_json(request)
    if request_data is None:
        return JsonResponse({"success": False, "message": "Invalid JSON format"}, status=400, safe=False)

    visitor_id = request_data.get("id")
    visitor_uuid = request_data.get("visitor_uuid")
    if not visitor_id and not visitor_uuid:
        return JsonResponse({"success": False, "message": "id or visitor_uuid cannot be empty"}, status=400, safe=False)

    try:
        if visitor_id:
            profile = VisitorProfile.objects.get(id=visitor_id)
        else:
            profile = VisitorProfile.objects.get(visitor_uuid=visitor_uuid)

        for field in [
            "institution", "lab_name", "person_name", "cookie_key",
            "visit_count", "last_path", "last_ip", "last_user_agent", "created_by_user_id"
        ]:
            if field in request_data:
                setattr(profile, field, request_data.get(field))

        if "last_seen_at" in request_data and request_data.get("last_seen_at"):
            profile.last_seen_at = request_data.get("last_seen_at")

        profile.save()
        return JsonResponse({"success": True, "data": _serialize_visitor_profile(profile)}, status=200, safe=False)
    except VisitorProfile.DoesNotExist:
        return JsonResponse({"success": False, "message": "No such visitor profile"}, status=404, safe=False)
    except IntegrityError as exc:
        return JsonResponse({"success": False, "message": str(exc)}, status=409, safe=False)
    except Exception as exc:
        return JsonResponse({"success": False, "message": str(exc)}, status=400, safe=False)


@csrf_exempt
def deleteVisitorProfile(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Just POST method"}, status=405, safe=False)

    request_data = _get_request_json(request)
    if request_data is None:
        return JsonResponse({"success": False, "message": "Invalid JSON format"}, status=400, safe=False)

    visitor_id = request_data.get("id")
    visitor_uuid = request_data.get("visitor_uuid")
    if not visitor_id and not visitor_uuid:
        return JsonResponse({"success": False, "message": "id or visitor_uuid cannot be empty"}, status=400, safe=False)

    try:
        if visitor_id:
            profile = VisitorProfile.objects.get(id=visitor_id)
        else:
            profile = VisitorProfile.objects.get(visitor_uuid=visitor_uuid)
        profile.delete()
        return JsonResponse({"success": True}, status=200, safe=False)
    except VisitorProfile.DoesNotExist:
        return JsonResponse({"success": False, "message": "No such visitor profile"}, status=404, safe=False)
    except Exception as exc:
        return JsonResponse({"success": False, "message": str(exc)}, status=400, safe=False)


@csrf_exempt
def createVisitorAccessLog(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Just POST method"}, status=405, safe=False)

    request_data = _get_request_json(request)
    if request_data is None:
        return JsonResponse({"success": False, "message": "Invalid JSON format"}, status=400, safe=False)

    visitor_id = request_data.get("visitor_id")
    visitor_uuid = request_data.get("visitor_uuid")
    path = (request_data.get("path") or "").strip()
    method = (request_data.get("method") or request.method or "POST").upper()
    ip = request_data.get("ip") or request.META.get("REMOTE_ADDR")
    user_agent = request_data.get("user_agent") or request.META.get("HTTP_USER_AGENT")
    referer = request_data.get("referer") or request.META.get("HTTP_REFERER")
    cookie_snapshot = request_data.get("cookie_snapshot")

    if not path:
        return JsonResponse({"success": False, "message": "path cannot be empty"}, status=400, safe=False)

    try:
        if visitor_id:
            profile = VisitorProfile.objects.get(id=visitor_id)
        elif visitor_uuid:
            profile = VisitorProfile.objects.get(visitor_uuid=visitor_uuid)
        else:
            return JsonResponse({"success": False, "message": "visitor_id or visitor_uuid cannot be empty"}, status=400, safe=False)

        with transaction.atomic():
            access_log = VisitorAccessLog.objects.create(
                visitor=profile,
                path=path,
                method=method,
                ip=ip,
                user_agent=user_agent,
                referer=referer,
                cookie_snapshot=cookie_snapshot,
            )
            profile.visit_count = (profile.visit_count or 0) + 1
            profile.last_seen_at = access_log.visited_at
            profile.last_path = path
            profile.last_ip = ip
            profile.last_user_agent = user_agent
            profile.save(update_fields=["visit_count", "last_seen_at", "last_path", "last_ip", "last_user_agent", "updated_at"])

        return JsonResponse(
            {
                "success": True,
                "data": _serialize_visitor_access_log(access_log),
                "visitor_profile": _serialize_visitor_profile(profile),
            },
            status=200,
            safe=False,
        )
    except VisitorProfile.DoesNotExist:
        return JsonResponse({"success": False, "message": "No such visitor profile"}, status=404, safe=False)
    except Exception as exc:
        return JsonResponse({"success": False, "message": str(exc)}, status=400, safe=False)


@csrf_exempt
def createVisitorFeedback(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Just POST method"}, status=405, safe=False)

    request_data = _get_request_json(request)
    print(request_data)
    if request_data is None:
        return JsonResponse({"success": False, "message": "Invalid JSON format"}, status=400, safe=False)

    visitor_id = request_data.get("visitor_id")
    visitor_uuid = request_data.get("visitor_uuid") if "visitor_uuid" in request_data else None
    feedback_type = (request_data.get("feedback_type") or "").strip().lower()
    title = (request_data.get("title") or "").strip()
    content = (request_data.get("content") or "").strip()
    contact_email = (request_data.get("contact_email") or "").strip()
    page_path = (request_data.get("page_path") or "").strip()
    status_value = (request_data.get("status") or VisitorFeedback.STATUS_PENDING).strip().lower()

    if not visitor_id and not visitor_uuid:
        return JsonResponse({"success": False, "message": "visitor_id or visitor_uuid cannot be empty"}, status=400, safe=False)

    if feedback_type not in {VisitorFeedback.FEEDBACK_TYPE_ISSUE, VisitorFeedback.FEEDBACK_TYPE_SUGGESTION}:
        return JsonResponse({"success": False, "message": "invalid feedback_type"}, status=400, safe=False)

    if not title or not content:
        return JsonResponse({"success": False, "message": "title and content cannot be empty"}, status=400, safe=False)

    if status_value not in {VisitorFeedback.STATUS_PENDING, VisitorFeedback.STATUS_REVIEWED, VisitorFeedback.STATUS_RESOLVED}:
        return JsonResponse({"success": False, "message": "invalid status"}, status=400, safe=False)

    try:
        if visitor_id:
            profile = VisitorProfile.objects.get(id=visitor_id)
        else:
            profile = VisitorProfile.objects.get(visitor_uuid=visitor_uuid)

        print(profile)
        feedback = VisitorFeedback.objects.create(
            visitor_profile=profile,
            feedback_type=feedback_type,
            title=title,
            content=content,
            contact_email=contact_email,
            page_path=page_path,
            status=status_value,
        )
        print(feedback)
        return JsonResponse({"success": True, "data": _serialize_visitor_feedback(feedback)}, status=201, safe=False)
    except VisitorProfile.DoesNotExist:
        return JsonResponse({"success": False, "message": "No such visitor profile"}, status=404, safe=False)
    except IntegrityError as exc:
        return JsonResponse({"success": False, "message": str(exc)}, status=409, safe=False)
    except Exception as exc:
        print(str(exc.args))
        return JsonResponse({"success": False, "message": str(exc)}, status=400, safe=False)

def getVisitorAccessLog(request):
    if request.method != "GET":
        return JsonResponse({"success": False, "message": "Just GET method"}, status=405, safe=False)

    log_id = request.GET.get("id")
    if not log_id:
        return JsonResponse({"success": False, "message": "id cannot be empty"}, status=400, safe=False)

    try:
        access_log = VisitorAccessLog.objects.get(id=log_id)
        return JsonResponse({"success": True, "data": _serialize_visitor_access_log(access_log)}, status=200, safe=False)
    except VisitorAccessLog.DoesNotExist:
        return JsonResponse({"success": False, "message": "No such visitor access log"}, status=404, safe=False)
    except Exception as exc:
        return JsonResponse({"success": False, "message": str(exc)}, status=400, safe=False)


def listVisitorAccessLogs(request):
    if request.method != "GET":
        return JsonResponse({"success": False, "message": "Just GET method"}, status=405, safe=False)

    try:
        queryset = VisitorAccessLog.objects.all().order_by("-visited_at", "-id")
        visitor_id = request.GET.get("visitor_id")
        visitor_uuid = request.GET.get("visitor_uuid")
        path = request.GET.get("path")
        method = request.GET.get("method")

        if visitor_id:
            queryset = queryset.filter(visitor_id=visitor_id)
        if visitor_uuid:
            queryset = queryset.filter(visitor__visitor_uuid=visitor_uuid)
        if path:
            queryset = queryset.filter(path__icontains=path)
        if method:
            queryset = queryset.filter(method__iexact=method)

        data = [_serialize_visitor_access_log(log) for log in queryset[:500]]
        return JsonResponse({"success": True, "data": data, "count": len(data)}, status=200, safe=False)
    except Exception as exc:
        return JsonResponse({"success": False, "message": str(exc)}, status=400, safe=False)


@csrf_exempt
def updateVisitorAccessLog(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Just POST method"}, status=405, safe=False)

    request_data = _get_request_json(request)
    if request_data is None:
        return JsonResponse({"success": False, "message": "Invalid JSON format"}, status=400, safe=False)

    log_id = request_data.get("id")
    if not log_id:
        return JsonResponse({"success": False, "message": "id cannot be empty"}, status=400, safe=False)

    try:
        access_log = VisitorAccessLog.objects.get(id=log_id)
        for field in ["path", "method", "ip", "user_agent", "referer", "cookie_snapshot"]:
            if field in request_data:
                setattr(access_log, field, request_data.get(field))
        if "visitor_id" in request_data and request_data.get("visitor_id"):
            access_log.visitor_id = request_data.get("visitor_id")
        access_log.save()
        return JsonResponse({"success": True, "data": _serialize_visitor_access_log(access_log)}, status=200, safe=False)
    except VisitorAccessLog.DoesNotExist:
        return JsonResponse({"success": False, "message": "No such visitor access log"}, status=404, safe=False)
    except Exception as exc:
        return JsonResponse({"success": False, "message": str(exc)}, status=400, safe=False)


@csrf_exempt
def deleteVisitorAccessLog(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Just POST method"}, status=405, safe=False)

    request_data = _get_request_json(request)
    if request_data is None:
        return JsonResponse({"success": False, "message": "Invalid JSON format"}, status=400, safe=False)

    log_id = request_data.get("id")
    if not log_id:
        return JsonResponse({"success": False, "message": "id cannot be empty"}, status=400, safe=False)

    try:
        access_log = VisitorAccessLog.objects.get(id=log_id)
        access_log.delete()
        return JsonResponse({"success": True}, status=200, safe=False)
    except VisitorAccessLog.DoesNotExist:
        return JsonResponse({"success": False, "message": "No such visitor access log"}, status=404, safe=False)
    except Exception as exc:
        return JsonResponse({"success": False, "message": str(exc)}, status=400, safe=False)
    



