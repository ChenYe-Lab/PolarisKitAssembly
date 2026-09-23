from WebDataWorld.runtime import ServiceSession
from Bio.SeqIO import parse, write
from Bio.Seq import Seq
import requests
import traceback
from Bio.Restriction import BsaI,BbsI

# from .snapgene_readersnapgene_reader import snapgene_to_dict
from .CaculateModule import snapgene_reader
from LabDatabase.ControllerModule import FittingLabels
from LabDatabase.CaculateModule.ScarIdentify import scarPosition,scarFunction
from LabDatabase.LabDatabaseException import LabDatabaseException,LabDatabaseGETMethodException,LabDatabasePOSTMethodException


def _unique_nonempty_items(items):
    unique_items = []
    seen = set()
    for item in items or []:
        if item in [None, ""]:
            continue
        if item in seen:
            continue
        seen.add(item)
        unique_items.append(item)
    return unique_items


def _crop_feature_payload(request_body, crop_interval, source_start=None, source_end=None):
    if crop_interval is None:
        return request_body

    crop_start, crop_end = crop_interval
    source_start = source_start if source_start is not None else request_body["start_position"]
    source_end = source_end if source_end is not None else request_body["end_position"]

    if source_start > source_end or source_start < crop_start or source_end > crop_end:
        return None

    cropped_body = request_body.copy()
    cropped_body["start_position"] = source_start - crop_start + 1
    cropped_body["end_position"] = source_end - crop_start + 1
    return cropped_body


def _save_features(session, django_request, Base_URL, name, file_type, feature_list, feature_api, crop_interval=None):
    from copy import deepcopy
    from Bio.SeqFeature import SeqFeature, SimpleLocation
    from Bio.SeqRecord import SeqRecord
    from .feature_records import feature_rows, apply_feature_color
    record = SeqRecord(Seq(''), id=name)
    for feature in feature_list:
        if file_type == 'dna':
            item = SeqFeature(SimpleLocation(int(feature['start']), int(feature['end']),
                strand={'+': 1, '-': -1}.get(feature.get('strand'))),
                type=feature['type'], qualifiers={'label': [feature.get('name', '')],
                                                 'color': [feature.get('color', '')]})
        else:
            item = deepcopy(feature)
        if item.location is None:
            continue
        if crop_interval is not None:
            start, end = crop_interval
            if any(int(p.start) < start - 1 or int(p.end) > end for p in item.location.parts):
                continue
            item.location = item.location - (start - 1)
        apply_feature_color(item)
        record.features.append(item)
    response = session.get(f'{Base_URL}delete{feature_api}Feature?name={name}', cookies=django_request.COOKIES)
    response.raise_for_status()
    if not response.json().get('success'):
        raise ValueError('Failed to replace imported features')
    for row in feature_rows(record):
        response = session.post(f'{Base_URL}Add{feature_api}Feature/{name}', json=row, cookies=django_request.COOKIES)
        response.raise_for_status()
        if not response.json().get('success'):
            raise ValueError('Failed to save imported feature: ' + row['feature_label'])

def _extract_color_from_note(note):
    if(note != None and note != ""):
        note_list = note.split(';')
        for each in note_list:
            if('color' in each):
                color = "#"+each.split('#')[-1]
                return color

def process_map_file(upload_map, file_name, upload_type, django_request,Base_URL, save_feature=False):
    try:
        FeatureList = []
        if (file_name[1] == "fasta"):
            records = parse(upload_map, "fasta")
            # upload_map.seek(0)
            for record in records:
                Sequence = str(record.seq)
                break
        elif(file_name[1] == "gb" or file_name[1] == "gbk" or file_name[1] == "ape" or file_name[1] == "str"):
            # try:
            records = parse(upload_map, "genbank")
            for record in records:
                Sequence = str(record.seq)
                FeatureList = record.features
                break
            # except Exception as e:
                # traceback.print_exc()
                # return False
        elif(file_name[1] == "dna"):
            # try:
            record = snapgene_reader.snapgene_to_dict(upload_map)
            FeatureList = record['features']
            Sequence = record['seq']
            # except Exception as e:
            #     return False
        else:
            raise LabDatabaseException(message = "上传文件种类无法处理")
        
        if(Sequence != ""):
            session = ServiceSession()
            token = django_request.COOKIES.get('csrftoken')
            session.headers.update({
                'User-Agent':'Django-App/1.0',
                'Content-Type':'application/json',
                'X-CSRFToken':token,
            })
            name = file_name[0][:20]
            if(upload_type == "plasmid"):
                AddSequenceUpdateResponse = None
                Ori_list = []
                Marker_list = []
                OriAndMarkerLabel = FittingLabels(sequence= Sequence)
                for each_ori in OriAndMarkerLabel['Origin']:
                    Ori_list.append(each_ori['Name'])
                for each_marker in OriAndMarkerLabel['Marker']:
                    Marker_list.append(each_marker['Name'])
                Ori_list = _unique_nonempty_items(Ori_list)
                Marker_list = _unique_nonempty_items(Marker_list)
                scar_data_body = scarFunction(Sequence)
                request_body = {"name":name, "sequence":Sequence}
                print(request_body)
                SequenceUpdateResponse = session.post(f"{Base_URL}UpdatePlasmidSequence",json=request_body,cookies=django_request.COOKIES)
                print(SequenceUpdateResponse.json())
                if(SequenceUpdateResponse.json()['success'] == False and SequenceUpdateResponse.json()["error_code"] == "not_found"):
                    add_request_body = {"name":name,"sequence":Sequence,"alias":""}
                    AddSequenceUpdateResponse = session.post(f"{Base_URL}AddPlasmidData",json=add_request_body,cookies=django_request.COOKIES)
                    print(AddSequenceUpdateResponse.json())
                    # if(AddSequenceUpdateResponse.json()["success"] == False):
                    if(AddSequenceUpdateResponse.status_code != 200):
                        raise LabDatabaseException(message = f"新建 Plasmid {name} 失败")
                
                Culture_request_body = {"name":name,"ori" : Ori_list,"marker":Marker_list}
                print(Culture_request_body)
                CultureResponseResponse = session.post(f"{Base_URL}setPlasmidCulture",json = Culture_request_body, cookies = django_request.COOKIES)
                scar_request_body = {"name":name,"bsmbi":scar_data_body[0],"bsai":scar_data_body[1],"bbsi":scar_data_body[2],"aari":scar_data_body[3],"sapi":scar_data_body[4]}
                ScarUpdateResponse = session.post(f"{Base_URL}setPlasmidScar",json = scar_request_body,cookies=django_request.COOKIES)
                if(save_feature and (SequenceUpdateResponse.status_code == 200 or (AddSequenceUpdateResponse is not None and AddSequenceUpdateResponse.status_code == 200))):
                    _save_features(session, django_request, Base_URL, name, file_name[1], FeatureList, "Plasmid")
                print(SequenceUpdateResponse.status_code)
                if((SequenceUpdateResponse.status_code == 200 or (AddSequenceUpdateResponse is not None and AddSequenceUpdateResponse.status_code == 200)) and CultureResponseResponse.status_code == 200 and ScarUpdateResponse.status_code == 200):
                    return True
                else:
                    if(SequenceUpdateResponse.status_code != 200):
                        raise LabDatabaseException(message=f"Plasmid {name} 序列更新失败")
                    if(AddSequenceUpdateResponse == None or AddSequenceUpdateResponse.status_code != 200):
                        raise LabDatabaseException(message=f"新建 Plasmid {name} 失败")
                    if(CultureResponseResponse.status_code != 200):
                        raise LabDatabaseException(message = f"Plasmid {name} 保存培养信息失败")
                    if(ScarUpdateResponse.status_code != 200):
                        raise LabDatabaseException(message = f"Plasmid {name} 保存Scar信息失败")
            elif(upload_type == "backbone"):
                Ori_list = []
                Marker_list = []
                OriAndMarkerLabel = FittingLabels(sequence= Sequence)
                for each_ori in OriAndMarkerLabel['Origin']:
                    Ori_list.append(each_ori['Name'])
                for each_marker in OriAndMarkerLabel['Marker']:
                    Marker_list.append(each_marker['Name'])
                Ori_list = _unique_nonempty_items(Ori_list)
                Marker_list = _unique_nonempty_items(Marker_list)
                scar_data_body = scarFunction(Sequence)
                request_body = {"name":name, "sequence":Sequence}
                SequenceUpdateResponse = session.post(f"{Base_URL}UpdateBackboneSequence",json=request_body,cookies=django_request.COOKIES)
                print("SequenceUpdateResponse")
                print(SequenceUpdateResponse.json())
                if(SequenceUpdateResponse.json()['success'] == False and SequenceUpdateResponse.json()['error_code'] == "not_found"):
                    print("新建backbone")
                    add_request_body = {"name":name,"sequence":Sequence}
                    AddBackboneResponse = session.post(f"{Base_URL}AddBackbone",json=add_request_body,cookies=django_request.COOKIES)
                    if(AddBackboneResponse.status_code != 200):
                        raise LabDatabaseException(message=f"新建 Backbone {name} 失败")
                _save_features(session, django_request, Base_URL, name, file_name[1], FeatureList, "Backbone")
                Culture_request_body = {"name":name,"ori" : Ori_list,"marker":Marker_list}
                CultureResponseResponse = session.post(f"{Base_URL}setBackboneCulture",json = Culture_request_body, cookies = django_request.COOKIES)
                scar_request_body = {"name":name,"bsmbi":scar_data_body[0],"bsai":scar_data_body[1],"bbsi":scar_data_body[2],"aari":scar_data_body[3],"sapi":scar_data_body[4]}
                ScarUpdateResponse = session.post(f"{Base_URL}setBackboneScar",json = scar_request_body,cookies=django_request.COOKIES)
                if((SequenceUpdateResponse.status_code == 200 or AddBackboneResponse.status_code == 200) and CultureResponseResponse.status_code == 200 and ScarUpdateResponse.status_code == 200):
                    return True
                else:
                    if(SequenceUpdateResponse.status_code != 200):
                        raise LabDatabaseException(message=f"Backbone {name} 序列更新失败")
                    if(AddBackboneResponse.status_code != 200):
                        raise LabDatabaseException(message=f"新建 Backbone {name} 失败")
                    if(CultureResponseResponse.status_code != 200):
                        raise LabDatabaseException(message = f"Backbone {name} 保存培养信息失败")
                    if(ScarUpdateResponse.status_code != 200):
                        raise LabDatabaseException(message = f"Backbone {name} 保存scar信息失败")
            elif(upload_type == "part"):
                target_seq = ""
                target_start = 1
                target_end = len(Sequence)
                # Enzyme_result = BsaI.catalyse(Seq(Sequence),linear=False)
                # for each_result in Enzyme_result:
                #     if((BsaI.site in str(each_result)) == False):
                #         target_seq = str(each_result)
                #         # print(target_seq)
                #         break
                Enzyme_result = BsaI.search(Seq(Sequence))
                BbsI_Enzyme_result = BbsI.search(Seq(Sequence))
                target_seq = Sequence
                if(len(Enzyme_result) == 2):
                    target_seq = Sequence[Enzyme_result[0]-1:Enzyme_result[1] - 1]
                    target_start = Enzyme_result[0]
                    target_end = Enzyme_result[1]
                else:
                    if(len(BbsI_Enzyme_result) == 2):
                        target_seq = Sequence[BbsI_Enzyme_result[0]-1 : BbsI_Enzyme_result[1] - 1]
                        target_start = BbsI_Enzyme_result[0]
                        target_end = BbsI_Enzyme_result[1]
                    else:
                        target_seq = Sequence
                # print(f"target_start:{target_start}")
                # print(f"target_end:{target_end}")
                if(len(Enzyme_result) == 2 or len(BbsI_Enzyme_result) == 2):
                    if(target_seq[:4].upper() == "GTGC" or target_seq[:4].upper() == "GCAC" or target_seq[:4].upper() == "ATCA"
                        or target_seq[:4].upper() == "TGAT" or target_seq[:4].upper() == "AATG" or target_seq[:4].upper() == "CATT"
                        or target_seq[:4].upper() == "TAAA" or target_seq[:4].upper() == "TTTA" or target_seq[:4].upper() == "CCTC"
                        or target_seq[:4].upper() == "GAGG"):
                        target_seq = target_seq[4:]
                        target_start += 4
                    if(target_seq[-4:].upper() == "GTGC" or target_seq[-4:].upper() == "GCAC" or target_seq[-4:].upper() == "ATCA"
                        or target_seq[-4:].upper() == "TGAT" or target_seq[-4:].upper() == "AATG" or target_seq[-4:].upper() == "CATT"
                        or target_seq[-4:].upper() == "TAAA" or target_seq[-4:].upper() == "TTTA" or target_seq[-4:].upper() == "CCTC"
                        or target_seq[-4:].upper() == "GAGG"):
                        target_seq = target_seq[:-4]
                        target_end -= 4
                print(target_seq)
                request_body = {"name":name, "Level0Sequence":target_seq}
                SequenceUpdateResponse = session.post(f"{Base_URL}UpdatePartSequence",json=request_body,cookies=django_request.COOKIES)
                # if(SequenceUpdateResponse.status_code == 200):
                #     return True
                if(SequenceUpdateResponse.json()['success'] == False and SequenceUpdateResponse.json()["error_code"] == "not_found"):
                    add_request_body = {"name":name,"alias":"","Level0Sequence":target_seq,"type":"promoter"}
                    SequenceAddResponse = session.post(f"{Base_URL}AddPartData",json=add_request_body,cookies=django_request.COOKIES)
                    if(SequenceAddResponse.status_code != 200):
                        raise LabDatabaseException(message=f"新建 Part {name} 失败")
                else:
                    raise LabDatabaseException(message = f"Part {name} 序列更新失败")
                if(save_feature):
                    _save_features(session, django_request, Base_URL, name, file_name[1], FeatureList, "Part", crop_interval=(target_start, target_end))
                return True
            else:
                raise LabDatabaseException(message=f"上传种类未知")
        else:
            raise LabDatabaseException(message=f"上传文件中无序列信息,请检查文件后重新上传")
    except LabDatabaseException as exc:
        raise exc
    except Exception as exc:
        raise exc
        
                
                
            
            
# def AnalysisFeature(file_obj, type, name, session, django_request, Base_URL):
#     print("AnalysisFeature")
#     if (type == "fasta"):
#         records = parse(file_obj, "fasta")
#         for record in records:
#             Sequence = str(record.seq)
#             break
#     elif(type == "gb" or type == "gbk" or type == "ape" or type == "str"):
#         records = parse(file_obj, "genbank")
#         for record in records:
#             FeartureList = record.features
#             for each_feature in FeartureList:
#                 try:
#                     start_position = each_feature.location.start
#                     end_position = each_feature.location.end
#                     label = each_feature.qualifiers['label'][0] if "label" in each_feature.qualifiers else ""
#                     feature_type = each_feature.type
#                     color = each_feature.qualifiers['color'][0] if 'color' in each_feature.qualifiers else ""
#                     ape_info = each_feature.qualifiers['ApEinfo_fwdcolor'][0] if 'ApEinfo_fwdcolor' in each_feature.qualifiers else ""
#                     request_body = {"start_position":start_position,"end_position":end_position,"label":label,"feature_type":feature_type,"color":color,"ape_info":ape_info}
#                     add_feature_response = session.post(f"{Base_URL}AddBackboneFeature/{name}",json=request_body,cookies = django_request.COOKIES)
#                 except Exception as e:
#                     continue
#             break
#     elif(type == "dna"):
#         print("process_map_file")
#         print(file_obj.closed)
#         print(str(file_obj))
#         if file_obj.closed:
#             file_obj = open(str(file_obj),"rb")
#         record = snapgene_to_dict(file_obj)
#         FeatureList = record['features']
#         print(FeatureList)
#         for each_feature in FeatureList:
#             try:
#                 start_position = each_feature['start']
#                 end_position = each_feature['end']
#                 label = each_feature['name']
#                 feature_type = each_feature['type']
#                 color = each_feature['color']
#                 ape_info = each_feature['color']
#                 request_body = {"start_position":start_position,"end_position":end_position,"label":label,"feature_type":feature_type,"color":color,"ape_info":ape_info}
#                 add_feature_response = session.post(f"{Base_URL}AddBackboneFeature/{name}",json=request_body,cookies = django_request.COOKIES)
#                 print(add_feature_response.json())
#             except Exception as e:
#                 continue

    

if __name__ == "__main__":
    # import io

    # upload_map_temp = open(file_address)
    # upload_map_temp = upload_map_temp.decode("utf-8")
    # upload_map = io.StringIO(upload_map_temp)
    Sequence = "GGTCTCAGTGCggttgcttcctataaaaaacTTGACTctatatctactagaggtttTCTAATgatggcatccggggaaaaccttgtcaatgaagagcgatctatgatcaagagacc"
    Enzyme_result = BsaI.search(Seq(Sequence))
    if(len(Enzyme_result) == 2):
        target_seq = Sequence[Enzyme_result[0]-1:Enzyme_result[1]]
        target_start = Enzyme_result[0]
        target_end = Enzyme_result[1]
    if(target_seq[:4].upper() == "GTGC" or target_seq[:4].upper() == "GCAC" or target_seq[:4].upper() == "ATCA"
        or target_seq[:4].upper() == "TGAT" or target_seq[:4].upper() == "AATG" or target_seq[:4].upper() == "CATT"
        or target_seq[:4].upper() == "TAAA" or target_seq[:4].upper() == "TTTA" or target_seq[:4].upper() == "CCTC"
        or target_seq[:4].upper() == "GAGG"):
        target_seq = target_seq[4:]
        target_start += 4
    if(target_seq[-4:].upper() == "GTGC" or target_seq[-4:].upper() == "GCAC" or target_seq[-4:].upper() == "ATCA"
        or target_seq[-4:].upper() == "TGAT" or target_seq[-4:].upper() == "AATG" or target_seq[-4:].upper() == "CATT"
        or target_seq[-4:].upper() == "TAAA" or target_seq[-4:].upper() == "TTTA" or target_seq[-4:].upper() == "CCTC"
        or target_seq[-4:].upper() == "GAGG"):
        target_seq = target_seq[:-4]
        target_end -= 4
        
    print(target_seq)
