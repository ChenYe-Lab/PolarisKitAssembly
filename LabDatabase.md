# 文件处理代码

```
def process_excel_async(upload_record,django_request):
    try:
        file_content = upload_record.read()
        excel_data = pd.read_excel(io.BytesIO(file_content))
        print(excel_data.columns)
        if(excel_data.columns.tolist()[0] == "PartName"):
            type = "part"
        elif(excel_data.columns.tolist()[0] == "BackboneName"):
            type = "backbone"
        elif(excel_data.columns.tolist()[0] == "PlasmidName"):
            type = "plasmid"
        print(type)
        result = ExcelProcessor.process_excel_file(django_request,excel_data,type)
    except Exception as e:
        print(e.args)

def UploadFile(request):
    if(request.method == 'POST' and request.FILES):
        file = request.FILES.get('file')
        title = request.POST.get('title', file.name)
        thread = threading.Thread(
            target = process_excel_async,
            args= (file,request)
        )
        thread.daemon = True
        thread.start()
        return JsonResponse(data={'success':True},status = 200, safe=False)
    else:
        return JsonResponse({'success':False,'message':'Upload record is empty'},status = 400, safe = False)
```
# ExcelProcessor.py

```
from django.core.exceptions import ValidationError
import logging
import requests
from .ControllerModule import FittingLabels
from .CaculateModule.ScarIdentify import scarFunction

BASE_URL = 'http://10.30.76.2:8000/WebDatabase'
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

class ExcelProcessor:
    """Excel 文件处理工具类"""
    
    # 预期的列映射（Excel列名 -> 模型字段）
    PART_COLUMN_MAPPING = {
        'PartName': 'name',
        'Alias': 'Alias', 
        'Type': 'Type',
        'LengthOfSequence': 'Lengthinlevel0',
        'Sequence': 'Level0Sequence',
        'Species': 'SourceOrganism',
    }

    BACKBONE_COLUMN_MAPPING = {
        'BackboneName':'name',
        'Alias':'alias',
        'Length of Sequence': 'length',
        'Sequence':'sequence',
        'Species':'species',
        'Note':'Note',
    }

    PLASMID_COLUMN_MAPPING = {
        'PlasmidName':'name',
        'Alias':'alias',
        'Level':'level',
        'Length Of Sequence':'length',
        'Sequence':'sequenceConfirm',
        'ParentPart':'',
        'ParentBackbone':'',
        'ParentSourceNote':'',
    }
    
    PART_REQUIRED_COLUMNS = ['PartName','Alias','Type','Sequence','Species']
    BACKBONE_REQUIRED_COLUMNS = ['BackboneName','Alias','Sequence','Species','Note',]
    PLASMID_REQUIRED_COLUMNS = ['PlasmidName','Alias','Level','Sequence','ParentSourceNote',]
    
    PLASMID_PARENT_COLUMNS = ['ParentPart','ParentBackbone','ParentPlasmid','ParentSourceNote']
    @classmethod
    def validate_excel_structure(cls, df, type):
        """验证 Excel 文件结构"""
        missing_columns = []
        if(type == 'part'):
            for col in cls.PART_REQUIRED_COLUMNS:
                if col not in df.columns:
                    missing_columns.append(col)
        elif(type == 'backbone'):
            for col in cls.BACKBONE_REQUIRED_COLUMNS:
                if col not in df.columns:
                    missing_columns.append(col)
        elif(type == 'plasmid'):
            for col in cls.PLASMID_REQUIRED_COLUMNS:
                if col not in df.columns:
                    missing_columns.append(col)
        if missing_columns:
            raise ValidationError(f"Excel 文件缺少必要的列: {', '.join(missing_columns)}")
        if len(df) == 0:
            raise ValidationError("Excel 文件没有数据")
    
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
    def validate_row_data(cls, row_data, row_index,type):
        """验证单行数据"""
        errors = []
        
        # 检查必填字段
        if(type == 'part'):
            for col in cls.PART_REQUIRED_COLUMNS:
                if not row_data.get(col):
                    errors.append(f'第 {row_index} 行：{col}为必填项')
        elif(type == 'backbone'):
            for col in cls.BACKBONE_REQUIRED_COLUMNS:
                if not row_data.get(col):
                    errors.append(f'第 {row_index} 行：{col}为必填项')
        elif(type == 'plasmid'):
            for col in cls.PLASMID_REQUIRED_COLUMNS:
                if not row_data.get(col):
                    errors.append(f'第 {row_index} 行：{col}为必填项')
            if( not row_data.get(cls.PLASMID_PARENT_COLUMNS[0]) and not row_data.get(cls.PLASMID_PARENT_COLUMNS[1]) and 
                not row_data.get(cls.PLASMID_PARENT_COLUMNS[2]) and not row_data.get(cls.PLASMID_PARENT_COLUMNS[3])):
                errors.append(f'Parent 信息需至少填写一项')
        
        return errors
    
    @classmethod
    def process_excel_file(cls,django_request,upload_record, type):
        """处理 Excel 文件"""
        try:
            # 读取 Excel 文件
            df = upload_record
            
            # 验证文件结构
            cls.validate_excel_structure(df, type)

            # 清理数据
            df = cls.clean_dataframe(df)

            error_rows = []
            session = createSession(django_request)
            # session = requests.Session()
            # token = django_request.COOKIES.get('csrftoken')
            # session.headers.update({
            #     'User-Agent':'Django-App/1.0',
            #     'Content-Type':'application/json',
            #     'X-CSRFToken':token,
            # })
            # GenerateLabels()
            # 处理每一行数据
            if(type == 'part'):
                for index, row in df.iterrows():
                    row_data = row.to_dict()
                    row_errors = cls.validate_row_data(row_data, index + 2,type)  # +2 因为 Excel 从第2行开始数据
                
                    if row_errors:
                        error_rows.extend(row_errors)
                        continue
                    else:
                        # session = createSession(django_request)
                        data_body = {'name':row['PartName'],'alias':row['Alias'],'Level0Sequence':row['Sequence'],'source':row['Species'],'type':row['Type'],'note':""}
                        response = session.post(f'{BASE_URL}/AddPartData',json=data_body,cookies=django_request.COOKIES)
                        scar_result_list = scarFunction(row['Sequence'])
                        scar_data_body = {'name':row['PartName'],'bsmbi':scar_result_list[0],'bsai':scar_result_list[1],'bbsi':scar_result_list[2],'aari':scar_result_list[3],'sapi':scar_result_list[4]}
                        scar_response = session.post(f'{BASE_URL}/setPartScar',json=scar_data_body,cookies=django_request.COOKIES)
                        if(response.status_code == 200 and scar_response.status_code == 200):
                            return True
            elif(type == 'backbone'):
                for index, row in df.iterrows():
                    row_data = row.to_dict()
                    row_errors = cls.validate_row_data(row_data, index + 2,type)  # +2 因为 Excel 从第2行开始数据
                    if row_errors:
                        error_rows.extend(row_errors)
                        continue
                    else:
                        Ori = ""
                        Marker = ""
                        OriAndMarkerLabel = FittingLabels(row['Sequence'])
                        if(OriAndMarkerLabel["Origin"] == ""):
                            Ori = OriAndMarkerLabel["Origin"]
                        if(OriAndMarkerLabel["Marker"] == ""):
                            Marker = OriAndMarkerLabel["Marker"]
                        data_body = {'name':row['BackboneName'],'alias':row['Alias'],'sequence':row['Sequence'],'ori':Ori,'marker':Marker,'species':row['Species'],'note':row['Note'],'copynumber':''}
                        response = session.post(f'{BASE_URL}/AddBackbone',json=data_body,cookies=django_request.COOKIES)
                        print(response.status_code)
                        scar_result_list = scarFunction(row['Sequence'])
                        scar_data_body = {'name':row['BackboneName'],'bsmbi':scar_result_list[0],'bsai':scar_result_list[1],'bbsi':scar_result_list[2],'aari':scar_result_list[3],'sapi':scar_result_list[4]}
                        scar_response = session.post(f'{BASE_URL}/setBackboneScar',json=scar_data_body,cookies=django_request.COOKIES)
                        if(response.status_code == 200):
                            return True
            elif(type == 'plasmid'):
                for index, row in df.iterrows():
                    row_data = row.to_dict()
                    row_errors = cls.validate_row_data(row_data, index + 2,type)  # +2 因为 Excel 从第2行开始数据
                    if row_errors:
                        error_rows.extend(row_errors)
                        continue
                    else:
                        OriClone = "default"
                        OriHost = "default"
                        MarkerClone = "default"
                        MarkerHost = "default"
                        OriAndMarkerLabel = FittingLabels(row['Sequence'])
                        if(len(OriAndMarkerLabel["Origin"]) == 1):
                            OriClone = OriAndMarkerLabel['Origin'][0]
                        elif(len(OriAndMarkerLabel["Origin"]) == 2):
                            OriClone = OriAndMarkerLabel['Origin'][0]
                            OriHost = OriAndMarkerLabel['Marker'][1]
                        if(len(OriAndMarkerLabel["Marker"]) == 1):
                            MarkerClone = OriAndMarkerLabel["Marker"][0]
                        elif(len(OriAndMarkerLabel['Marker']) == 2):
                            MarkerClone = OriAndMarkerLabel['Marker'][0]
                            MarkerHost = OriAndMarkerLabel['Marker'][1]
                        data_body = {'name':row['PlasmidName'],'alias':row['Alias'],'oriclone':OriClone,'orihost':OriHost,'markerclone':MarkerClone,'markerhost':MarkerHost,'level':row['Level'],'sequence':row['Sequence'],'ParentInfo':row['ParentSourceNote']}
                        # print(data_body)
                        response = session.post(f'{BASE_URL}/AddPlasmidData',json=data_body,cookies=django_request.COOKIES)
                        # print(response.status_code)
                        scar_result_list = scarFunction(row['Sequence'])
                        scar_data_body = {'name':row['PlasmidName'],'bsmbi':scar_result_list[0],'bsai':scar_result_list[1],'bbsi':scar_result_list[2],'aari':scar_result_list[3],'sapi':scar_result_list[4]}
                        scar_response = session.post(f'{BASE_URL}/setPlasmidScar',json=scar_data_body,cookies=django_request.COOKIES)
                        if(response.status_code != 200):
                            return False
                        ParentPart = row['ParentPart']
                        ParentBackbone = row['ParentBackbone']
                        ParentPlasmid = row['ParentPlasmid']
                        if(ParentPart != ""):
                            ParentPartList = ParentPart.split(',')
                            for each_part in ParentPartList:
                                request_body = {'SonPlasmidName':row['PlasmidName'],'ParentPartName':each_part}
                                ParentPartResponse = session.post(f'{BASE_URL}/AddPartParent',json=request_body,cookies=django_request.COOKIES)
                                if(ParentPartResponse.status_code != 200):
                                    if(response.status_code == 200):
                                        return {'success':False,'error':'Plasmid upload success, Parent part upload fail'}
                                # return {'success':False,'error':response.json()}
                        if(ParentBackbone != ""):
                            ParentBackboneList = ParentBackbone.split(',')
                            for each_backbone in ParentBackboneList:
                                request_body = {'SonPlasmidName':row['PlasmidName'],'ParentBackboneName':each_backbone}
                                ParentBackboneResponse = session.post(f'{BASE_URL}/AddBackboneParent',json=request_body,cookies=django_request.COOKIES)
                                if(ParentBackboneResponse.status_code != 200):
                                    if(response.status_code == 200):
                                        return {'success':False,'error':'Plasmid upload success, Parent Backbone upload fail'}
                        if(ParentPlasmid != ""):
                            ParentPlasmidList = ParentPlasmid.split(',')
                            for each_plasmid in ParentPlasmidList:
                                request_body = {'SonPlasmidName':row['PlasmidName'],'ParentPlasmidName':each_plasmid}
                                ParentPlasmidResponse = session.post(f'{BASE_URL}/AddPlasmidParent',json=request_body,cookies=django_request.COOKIES)
                                if(ParentPlasmidResponse.status_code != 200):
                                    if(response.status_code == 200):
                                        return {'success':False,'error':'Plasmid upload success, Parent plasmid upload fail'}
            return {'success':True}
        except Exception as e:
            logger.error(f"处理 Excel 文件失败: {str(e)}")
            
            return {
                'success': False,
                'error': str(e)
            }
```
注：分析文件时调用了WebDatabase api -AddPartData，setPartScar, AddBackbone, setBackboneScar, AddPlasmidData, setPlasmidScar, AddPartParent, AddBackboneParent, AddPlasmidParent. 使用了ControllerModule中的FittingLabels，CaculateModule.ScarIdentity中的scarFunction
# 质粒渲染部分代码

```
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>质粒信息 - 基因元件数据库</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        body {
            background-color: #f5f7fa;
            color: #333;
            line-height: 1.6;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }
        
        header {
            background: linear-gradient(135deg, #1a6fc4, #0d4d8a);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        h1 {
            font-size: 2.2rem;
            margin-bottom: 10px;
        }
        
        .plasmid-id {
            font-size: 1.2rem;
            opacity: 0.9;
        }
        
        .content {
            padding: 30px;
        }
        
        .info-section {
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px solid #eee;
        }
        
        h2 {
            color: #1a6fc4;
            margin-bottom: 15px;
            font-size: 1.5rem;
            display: flex;
            align-items: center;
        }
        
        h2 i {
            margin-right: 10px;
        }
        
        .plasmid-name {
            font-size: 1.8rem;
            color: #0d4d8a;
            margin-bottom: 10px;
        }
        
        .sequence-container {
            background-color: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            margin-top: 10px;
            border: 1px solid #e1e5e9;
        }
        
        .sequence {
            font-family: 'Courier New', monospace;
            background-color: #2d3748;
            color: #e2e8f0;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
            white-space: nowrap;
            margin-top: 10px;
            font-size: 0.9rem;
            line-height: 1.4;
        }
        
        .construction-process {
            margin-top: 20px;
        }
        
        .process-step {
            display: flex;
            margin-bottom: 30px;
            position: relative;
        }
        
        .process-step:not(:last-child)::after {
            content: '';
            position: absolute;
            left: 30px;
            bottom: -30px;
            width: 2px;
            height: 30px;
            background-color: #1a6fc4;
        }
        
        .step-number {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background-color: #1a6fc4;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            font-weight: bold;
            margin-right: 20px;
            flex-shrink: 0;
        }
        
        .step-content {
            flex: 1;
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #1a6fc4;
        }
        
        .step-content h3 {
            color: #0d4d8a;
            margin-bottom: 10px;
        }
        
        .step-content p {
            color: #555;
            margin-bottom: 10px;
        }
        
        .step-method {
            display: inline-block;
            background-color: #e3f2fd;
            color: #0d4d8a;
            padding: 5px 10px;
            border-radius: 4px;
            font-size: 0.9rem;
            font-weight: bold;
            margin-top: 10px;
        }
        
        .hierarchy-section {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .hierarchy-card {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-top: 4px solid #1a6fc4;
        }
        
        .hierarchy-card h3 {
            color: #0d4d8a;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
        }
        
        .hierarchy-card h3 i {
            margin-right: 8px;
        }
        
        .hierarchy-list {
            list-style-type: none;
        }
        
        .hierarchy-item {
            background-color: white;
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 6px;
            border-left: 3px solid #1a6fc4;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .hierarchy-item:hover {
            transform: translateX(5px);
            box-shadow: 0 3px 10px rgba(0,0,0,0.1);
        }
        
        .item-name {
            font-weight: bold;
            color: #0d4d8a;
            margin-bottom: 5px;
        }
        
        .item-desc {
            color: #666;
            font-size: 0.9rem;
        }
        
        .map-container {
            background-color: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin-top: 20px;
            text-align: center;
            border: 1px solid #e1e5e9;
        }
        
        .plasmid-map {
            width: 100%;
            max-width: 500px;
            height: 500px;
            margin: 0 auto;
            background: linear-gradient(135deg, #e3f2fd, #bbdefb);
            border-radius: 50%;
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
            border: 2px solid #0d4d8a;
        }
        
        .plasmid-label {
            position: absolute;
            font-size: 0.8rem;
            font-weight: bold;
            color: #0d4d8a;
            transform-origin: center;
            text-align: center;
            width: 80px;
            padding: 2px 5px;
            border-radius: 3px;
            background-color: rgba(255, 255, 255, 0.7);
            transition: all 0.3s ease;
        }
        
        .reference-list {
            list-style-type: none;
        }
        
        .reference-item {
            background-color: #f8f9fa;
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 8px;
            border-left: 4px solid #1a6fc4;
        }
        
        .reference-title {
            font-weight: bold;
            margin-bottom: 5px;
            color: #0d4d8a;
        }
        
        .reference-authors {
            color: #555;
            font-style: italic;
            margin-bottom: 5px;
        }
        
        .reference-journal {
            color: #666;
            margin-bottom: 5px;
        }
        
        .reference-link {
            color: #1a6fc4;
            text-decoration: none;
            font-weight: bold;
        }
        
        .reference-link:hover {
            text-decoration: underline;
        }
        
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .info-card {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-top: 4px solid #1a6fc4;
        }
        
        .info-card h3 {
            color: #0d4d8a;
            margin-bottom: 10px;
        }
        
        .info-card p {
            color: #555;
        }
        
        .download-section {
            display: flex;
            gap: 15px;
            margin-top: 20px;
            flex-wrap: wrap;
        }
        
        .btn {
            padding: 10px 20px;
            border-radius: 5px;
            text-decoration: none;
            font-weight: bold;
            transition: all 0.3s ease;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background-color: #1a6fc4;
            color: white;
            border: none;
            cursor: pointer;
        }
        
        .btn:hover {
            background-color: #0d4d8a;
        }
        
        .btn i {
            margin-right: 8px;
        }
        
        footer {
            text-align: center;
            padding: 20px;
            background-color: #f1f5f9;
            color: #666;
            font-size: 0.9rem;
        }
        
        @media (max-width: 768px) {
            .container {
                border-radius: 0;
            }
            
            .content {
                padding: 20px;
            }
            
            h1 {
                font-size: 1.8rem;
            }
            
            .info-grid, .hierarchy-section {
                grid-template-columns: 1fr;
            }
            
            .plasmid-map {
                height: 300px;
                width: 300px;
            }
            
            .process-step {
                flex-direction: column;
            }
            
            .step-number {
                margin-bottom: 10px;
                margin-right: 0;
            }
            
            .process-step:not(:last-child)::after {
                left: 30px;
                top: 60px;
                width: 2px;
                height: 30px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
 
            <div class="info-section">
                <h2><i>🗺️</i> 质粒图谱</h2>
                <p>{{plasmid.name}}质粒图谱显示主要功能元件的位置和方向：</p>
                <div class="map-container">
                    <div class="plasmid-map">
                        <div class="plasmid-label" style="transform: rotate(0deg) translate(220px) rotate(0deg);">{{plasmid.oricloning}}</div>
                        <div class="plasmid-label" style="transform: rotate(72deg) translate(220px) rotate(-72deg);">{{plasmid.markercloning}}</div>
                        <div class="plasmid-label" style="transform: rotate(144deg) translate(220px) rotate(-144deg);">{{plasmid.orihost}}</div>
                        <div class="plasmid-label" style="transform: rotate(216deg) translate(220px) rotate(-216deg);">{{plasmid.markerhost}}</div>
                    </div>
                </div>
            
            </div>
    </div>

    <script>
        // 质粒图谱交互效果
        document.querySelectorAll('.plasmid-label').forEach(label => {
            label.addEventListener('mouseover', function() {
                this.style.backgroundColor = 'rgba(255,255,255,0.9)';
                this.style.boxShadow = '0 0 5px rgba(0,0,0,0.2)';
                this.style.zIndex = '10';
            });
            
            label.addEventListener('mouseout', function() {
                this.style.backgroundColor = 'rgba(255,255,255,0.7)';
                this.style.boxShadow = 'none';
                this.style.zIndex = '1';
            });
        });
    </script>
</body>
</html>
```