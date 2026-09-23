from WebDataWorld.runtime import ServiceSession, service_url
import logging
from django.shortcuts import render
import requests

logger = logging.getLogger(__name__)


def is_superuser(user):
    return user.is_authenticated and user.is_staff


def AdminDashbordView(request):
    Base_URL = service_url('WEBDATABASE_API_BASE_URL')
    if(is_superuser(request.user)):
        #用户名统计
        session = ServiceSession()
        session.headers.update({
            'User-Agent':'Django-App/1.0',
            'Content-Type':'application/json',
        })
        part_count_response = session.get(f"{Base_URL}partcount",cookies=request.COOKIES)
        if(part_count_response.status_code == 200):
            part_count = part_count_response.json()['data']
        else:
            return render(request,'error.html',{'error':"获取用户数据错误"})
        backbone_count_response = session.get(f"{Base_URL}backbonecount",cookies=request.COOKIES)
        if(backbone_count_response.status_code == 200):
            backbone_count = backbone_count_response.json()['data']
        else:
            return render(request,'error.html',{'error':"获取用户数据错误"})
        plasmid_count_response = session.get(f"{Base_URL}plasmidcount",cookies=request.COOKIES)
        if(plasmid_count_response.status_code == 200):
            plasmid_count = plasmid_count_response.json()['data']
        else:
            return render(request,'error.html',{'error':"获取用户数据错误"})
        # user_add_upload_response = session.get(f"{Base_URL}getalluseruploadlist",cookies=request.COOKIES)
        # if(user_add_upload_response.status_code == 200):
        #     user_add_upload_result = user_add_upload_response.json()['data']
        #     print(user_add_upload_result)
        return render(request,"dashboard.html",{"part_count":part_count, "backbone_count":backbone_count, "plasmid_count":plasmid_count})
        # else:
        #     return render(request,'error.html',{'error':"获取用户数据错误"})
