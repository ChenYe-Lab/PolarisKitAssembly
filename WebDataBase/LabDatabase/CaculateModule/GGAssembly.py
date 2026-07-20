import json
import logging
import requests
from django.forms import ValidationError
import os
from Bio.Seq import Seq
from GGModule import SupportGG
from .FeatureIdentify import featureIdentify
from .FileGenerator import SequenceAnnotator
from .ScarIdentify import scarPosition, scarFunction
from Bio.SeqIO import parse
from ControllerModule import FittingLabels
from urllib.parse import urlencode
from LabDatabaseException import LabDatabaseException


logger = logging.getLogger(__name__)



def createSession(django_request):
    session = requests.Session()
    # token = django_request.COOKIES.get('csrftoken')
            # session.headers.update({
            #     'User-Agent':'Django-App/1.0',
            #     'Content-Type':'application/json',
            #     'X-CSRFToken':token,
            # })
    token = django_request.COOKIES.get('csrftoken')
    session.headers.update({
        'User-Agent':'Django-App/1.0',
        'Content-Type':'application/json',
        'X-CSRFToken':token,
    })
    return session


class FileProcessorException(Exception):
    
    def __init__(self, error_rows):
        self.error_rows = error_rows
    



class GGFileProcessor:
    """Excel 文件处理工具类"""
    
    # 预期的列映射（Excel列名 -> 模型字段）
    ASSEMBLY_REQUIRED_COLUMNS = ['AssemblyName']
    @classmethod
    def validate_excel_structure(cls, df):
        """验证 Excel 文件结构"""
        missing_columns = []
        for col in cls.ASSEMBLY_REQUIRED_COLUMNS:
            if col not in df.columns:
                missing_columns.append(col)
        if missing_columns:
            raise LabDatabaseException(message = f"Excel 文件缺少必要的列：{', '.join(missing_columns)}")
            # raise ValidationError(f"Excel 文件缺少必要的列: {', '.join(missing_columns)}")
        if len(df) == 0:
            raise LabDatabaseException(message = "Excel 文件无数据")
            # raise ValidationError("Excel 文件没有数据")
    
    @classmethod
    def clean_dataframe(cls, df):
        """清理 DataFrame 数据"""
        # 删除完全为空的行
        df = df.dropna(how='all')
        # 填充空值
        df = df.fillna('')
        # 去除字符串字段的空白
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str).str.strip()
        return df
    
    @classmethod
    def validate_row_data(cls, row_data, row_index):
        """验证单行数据"""
        errors = []
        # 检查必填字段
        for col in cls.ASSEMBLY_REQUIRED_COLUMNS:
            if not row_data.get(col):
                errors.append(f'第 {row_index} 行：{col}为必填项\n')
        return errors
    
    @classmethod
    def createTemporaryRepo(cls,django_request,upload_record, BASE_URL):
        print(upload_record)
        """处理 Excel 文件"""
        logger.info('处理上传文件请求：%s',django_request.path)
        try:
            error_rows = []
            session = createSession(django_request)
            for each_plan in upload_record:
            # 读取 Excel 文件
                assembly_name = each_plan['name']
                df = each_plan['data']
            
                # 验证文件结构
                cls.validate_excel_structure(df)

                # 清理数据
                df = cls.clean_dataframe(df)
            
            # session = requests.Session()
            # token = django_request.COOKIES.get('csrftoken')
            # session.headers.update({
            #     'User-Agent':'Django-App/1.0',
            #     'Content-Type':'application/json',
            #     'X-CSRFToken':token,
            # })
            # GenerateLabels()
            # 处理每一行数据
                part_list = []
                backbone_list = []
                plasmid_list = []
                scar_before_list = []
                scar_end_list = []
                Alias = ""
                Note = ""
                Level = 0
                for index, row in df.iterrows():
                    row_data = row.to_dict()
                    row_errors = cls.validate_row_data(row_data, index+2)
                    if row_errors:
                        error_rows.extend(row_errors)
                        continue
                    else:
                        if(row["Alias"] != None):
                            Alias = row["Alias"]
                        if(row["Note"] != None):
                            Note = row["Note"]
                        if(row["Level"] != None):
                            Level = row["Level"]
                        # part_list.add(row["Part"])
                        # backbone_list.add(row["Backbone"])
                        # plasmid_list.add(row["Plasmid"])
                        part_list.append(row["Part"])
                        backbone_list.append(row["Backbone"])
                        plasmid_list.append(row["Plasmid"])
                        scar_before_list.append(row["Part Start Scar"])
                        scar_end_list.append(row["Part End Scar"])
                try:
                    # Assembly_Plan_Name = row["AssemblyName"]
                    # request_body = {"Name":Assembly_Plan_Name, "note":row["Note"] if row["Note"] != None else "","alias":row["Alias"],"level":row["Level"],"part_start_scar":row["Part Start Scar"] if row["Part Start Scar"] != None else "","part_end_start":row["Part End Scar"] if row["Part End Scar"] != None else ""}
                    # print(request)
                    request_body = {"Name":assembly_name,"note":Note,"alias":Alias,"level":Level}
                    tempRepo_response = session.post(f"{BASE_URL}createRepo",json=request_body,cookies=django_request.COOKIES)
                    if(tempRepo_response.json()["success"] == False):
                        error_message = tempRepo_response.json()['message']
                        error_rows.append(f"{assembly_name} 创建仓库失败，{error_message}")
                    else:
                        part_ids = []
                        print(part_list)
                        for each_part in part_list:
                            if each_part != "":
                                query = urlencode({"name":each_part.strip()})

                                part_obj = session.get(f"{BASE_URL}PartName?{query}",cookies=django_request.COOKIES)
                                if(part_obj.status_code == 200):
                                    part_ids.append(part_obj.json()['data']['partid'])
                                else:
                                    raise LabDatabaseException(message=f"{assembly_name} Part {each_part} 不存在")
                                    # error_rows.append(f"第{index}行 Part {query["name"]} 不存在")
                                    # raise FileProcessorException(error_rows=error_rows)
                        backbone_ids = []
                        for each_backbone in backbone_list:
                            if each_backbone != "":
                                backbone_obj = session.get(f"{BASE_URL}BackboneName?name={each_backbone.strip()}",cookies=django_request.COOKIES)
                                if(backbone_obj.status_code == 200):
                                    backbone_ids.append(backbone_obj.json()['data']['id'])
                                else:
                                    raise LabDatabaseException(f"{assembly_name} Backbone {each_backbone.strip()} 不存在")
                                    # error_rows.append(f"第{index}行 Backbone {each_backbone.strip()} 不存在")
                                    # raise FileProcessorException(error_rows=error_rows)
                        plasmid_ids = []
                        for each_plasmid in plasmid_list:
                            if each_plasmid != "":
                                if ',' in each_plasmid:
                                    each_plasmid_list = each_plasmid.split(',')
                                    for each_plasmid_after_split in each_plasmid_list:
                                        plasmid_obj = session.get(f"{BASE_URL}PlasmidName?name={each_plasmid_after_split.strip()}",cookies=django_request.COOKIES)
                                        if(plasmid_obj.status_code == 200):
                                            plasmid_ids.append(plasmid_obj.json()["data"]['plasmidid'])
                                        else:
                                            raise LabDatabaseException(f"{assembly_name} Plasmid {each_plasmid_after_split.strip()} 不存在")
                                else:
                                    plasmid_obj = session.get(f"{BASE_URL}PlasmidName?name={each_plasmid.strip()}",cookies=django_request.COOKIES)
                                    if(plasmid_obj.status_code == 200):
                                        plasmid_ids.append(plasmid_obj.json()["data"]['plasmidid'])
                                    else:
                                        raise LabDatabaseException(f"{assembly_name} Plasmid {each_plasmid.strip()} 不存在")
                                    # error_rows.append(f"第{index}行 Plasmid {each_plasmid.strip()} 不存在")
                                    # raise ValueError
                        request_part_body = {"RepoName":row["AssemblyName"],'part_ids':part_ids,"part_start_scar":scar_before_list,"part_end_scar":scar_end_list}
                        request_backbone_body = {"RepoName":row["AssemblyName"],"backbone_ids":backbone_ids}
                        request_plasmid_body = {"RepoName":row["AssemblyName"],"plasmid_ids":plasmid_ids}
                        
                        add_part_response = session.post(f"{BASE_URL}addparts",json=request_part_body,cookies=django_request.COOKIES)
                        add_backbone_response = session.post(f"{BASE_URL}addbackbones",json=request_backbone_body,cookies=django_request.COOKIES)
                        add_plasmid_response = session.post(f"{BASE_URL}addplasmids",json=request_plasmid_body, cookies=django_request.COOKIES)
                        if(add_part_response.status_code != 200):
                            raise LabDatabaseException(message = f"第{index}行，加入元件失败")
                            # error_rows.append(f"第{index}行，加入元件失败")
                            # raise FileProcessorException(error_rows=error_rows)
                        if(add_backbone_response.status_code != 200):
                            raise LabDatabaseException(message = f"第{index}行，加入载体失败")
                            # error_rows.append(f"第{index}行，加入载体失败")
                            # raise FileProcessorException(error_rows=error_rows)
                        if(add_plasmid_response.status_code != 200):
                            raise LabDatabaseException(message = f"第{index}行，加入质粒失败")
                            # error_rows.append(f"第{index}行，加入质粒失败")
                            # raise FileProcessorException(error_rows=error_rows)
                    # except FileProcessorException as exc:
                    #     logger.error(f"处理Excel文件失败: {str(exc.error_rows)}")
                    #     error_rows.extend(error_rows)
                    #     continue
                except LabDatabaseException as exc:
                    error_rows.append(f"第{index}行, {exc.message}")
                    continue
                except Exception as e:
                    logger.error(f"第{index} 行,处理Excel失败: {str(e.args)}")
                    error_rows.append(f"第{index} 行,处理Excel失败")
                    continue
            if error_rows:
                return {"success":False,"error_row":str(error_rows)}
            return {"success":True}
        except Exception as e:
            return {
                'success':False,
                'error': str(e),
                }
            
            
            
            
def AssemblyResultUpload(django_request,Name, Sequence, partList, BackboneList, PlasmidList, Base_URL):
    try:
        session = requests.Session()
        token = django_request.COOKIES.get('csrftoken')
        session.headers.update({
            'User-Agent':'Django-App/1.0',
            'Content-Type':'application/json',
            'X-CSRFToken':token,
        })
        if(len(partList) != 0):
            level = 2
        else:
            level = 3
        data_body = {'name':Name,'alias':Name,'level':level,'sequence':Sequence,'note':"",'ParentInfo':""}
        response = session.post(f'{Base_URL}AddPlasmidData',json=data_body,cookies=django_request.COOKIES)
        if(response.status_code != 200):
            raise LabDatabaseException(message = f"Plasmid {Name} 添加错误，{response.json()['message']}")
            # return {"success":False, "message":"添加质粒错误"}
        Ori_list = []
        Marker_list = []
        OriAndMarkerLabel = FittingLabels(Sequence)
        for each_ori in OriAndMarkerLabel['Origin']:
            Ori_list.append(each_ori['Name'])
        for each_marker in OriAndMarkerLabel['Marker']:
            Marker_list.append(each_marker['Name'])
        plasmid_culture_body = {"name":Name, "ori":Ori_list,"marker":Marker_list}
        plasmid_culture_response = session.post(f"{Base_URL}setPlasmidCulture",json = plasmid_culture_body, cookies=django_request.COOKIES)
        if(plasmid_culture_response.status_code != 200):
            raise LabDatabaseException(message=f"Plasmid {Name} 添加培养信息失败，{plasmid_culture_response.json()['message']}")
            # return {"success":False, "message":"质粒培养信息添加错误"}
        scar_result_list = scarFunction(Sequence)
        scar_data_body = {'name':Name,'bsmbi':scar_result_list[0],'bsai':scar_result_list[1],'bbsi':scar_result_list[2],'aari':scar_result_list[3],'sapi':scar_result_list[4]}
        scar_response = session.post(f'{Base_URL}setPlasmidScar',json=scar_data_body,cookies=django_request.COOKIES)
        if(scar_response.status_code != 200):
            raise LabDatabaseException(message = f"Plasmid {Name} 添加Scar信息失败,{scar_response.json()['message']}")
            # return {"success":False, "message":"质粒scar信息添加错误"}
        parent_error_info = ""
        for each_part in partList:
            request_body = {"SonPlasmidName":Name,"ParentPartID":each_part}
            part_response = session.post(f"{Base_URL}AddPartParentByID",json=request_body,cookies=django_request.COOKIES)
            if(part_response.status_code != 200):
                parent_error_info += f"Plasmid {Name} 添加Parent Part 信息失败\n"
                # return {"success":False,"message":"Parent Part 添加失败"}
        for each_backbone in BackboneList:
            request_body = {"SonPlasmidName":Name,"ParentBackboneID":each_backbone}
            backbone_response = session.post(f"{Base_URL}AddBackboneParentByID",json=request_body,cookies=django_request.COOKIES)
            if(backbone_response.status_code != 200):
                parent_error_info += f"Plasmid {Name} 添加Parent Backbone 信息失败\n"
            #     return {"success":False,"message":"Parent Backbone 添加失败"}
        for each_plasmid in PlasmidList:
            request_body = {"SonPlasmidName":Name,"ParentPlasmidID":each_plasmid}
            plasmid_response = session.post(f"{Base_URL}AddPlasmidParentByID",json=request_body,cookies=django_request.COOKIES)
            if(plasmid_response.status_code != 200):
                parent_error_info += f"Plasmid {Name} 添加Parent Plasmid 信息失败"
            #     return {"success":False,"message":"Parent Plasmid 添加失败"}
        if(parent_error_info != ""):
            return {"success":True,"error_info":""}
        return {"success":True}
    except LabDatabaseException as exc:
        return {"success":False,"message":exc.message}
    except Exception as exc:
        return {"success":False,"message":str(exc)}
