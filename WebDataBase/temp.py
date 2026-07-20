from Bio.Seq import Seq
from Bio.SeqIO import parse
from LabDatabase.CaculateModule.FeatureIdentify import featureIdentify
# from LabDatabase.CaculateModule.FileGenerator import SequenceAnnotator
from LabDatabase.CaculateModule.FileGenerator import SequenceAnnotator
# # seq_obj = Seq("cattggaaaacgttcttcggggcgaaaactctcaaggatcttaccgctgttgagatccagttcgatgtaacccactcgtgcacccaactgatcttcagcatcttttactttcaccagcgtttctgggtgagcaaaaacaggaaggcaaaatgccgcaaaaaagggaataagggcgacacggaaatgttgaatactcatactcttcctttttcaatattattgaagcatttatcagggttattgtctcatgagcggatacatatttgaatgtatttagaaaaataaacaaataggggttccgcgcacatttccccgaaaagtgccacct")
# # print(str(seq_obj.reverse_complement()))
from LabDatabase.CaculateModule.ScarIdentify import ScarIdentify, scarFunction, scarPosition
import traceback
from Bio.Restriction import BsaI

# seq = "GAAGACCTCTGACAATCACCTATGAACTGTCGGTGCGGAGACCGGCTTACTAAAAGCCAGATAACAGTATGCATATTTGCGCGCTGATTTTTGCGGTATAAGAATATATACTGATATGTATACCCGAAGTATGTCAAAAAGAGGTATGCTATGAAGCAGCGTATTACAGTGACAGTTGACAGCGACAGCTATCAGTTGCTCAAGGCATATATGATGTCAATATCTCCGGTCTGGTAAGCACAACCATGCAGAATGAAGCCCGTCGTCTGCGTGCCGAACGCTGGAAAGCGGAAAATCAGGAAGGGATGGCTGAGGTCGCCCGGTTTATTGAAATGAACGGCTCTTTTGCTGACGAGAACAGGGGCTGGTGAAATGCAGTTTAAGGTTTACACCTATAAAAGAGAGAGCCGTTATCGTCTGTTTGTGGATGTACAGAGTGATATTATTGACACGCCCGGGCGACGGATGGTGATCCCCCTGGCCAGTGCACGTCTGCTGTCAGATAAAGTCTCCCGTGAACTTTACCCGGTGGTGCATATCGGGGATGAAAGCTGGCGCATGATGACCACCGATATGGCCAGTGTGCCGGTTTCCGTTATCGGGGAAGAAGTGGCTGATCTCAGCCACCGCGAAAATGACATCAAAAACGCCATTAACCTGATGTTCTGGGGAATATAAGGTCTCCCCTCTACGGAGTCTTCGAGCGGTATCAGCTCACTCAAAGGCGGTAATACGGTTATCCACAGAATCAGGGGATAACGCAGGAAAGAACATGTGAGCAAAAGGCCAGCAAAAGGCCAGGAACCGTAAAAAGGCCGCGTTGCTGGCGTTTTTCCATAGGCTCCGCCCCCCTGACGAGCATCACAAAAATCGACGCTCAAGTCAGAGGTGGCGAAACCCGACAGGACTATAAAGATACCAGGCGTTTCCCCCTGGAAGCTCCCTCGTGCGCTCTCCTGTTCCGACCCTGCCGCTTACCGGATACCTGTCCGCCTTTCTCCCTTCGGGAAGCGTGGCGCTTTCTCATAGCTCACGCTGTAGGTATCTCAGTTCGGTGTAGGTCGTTCGCTCCAAGCTGGGCTGTGTGCACGAACCCCCCGTTCAGCCCGACCGCTGCGCCTTATCCGGTAACTATCGTCTTGAGCCCAACCCGGTAAGACACGACTTATCGCCACTGGCAGCAGCCACTGGTAACAGGATTAGCAGAGCGAGGTATGTAGGCGGTGCTACAGAGTTCTTGAAGTGGTGGCCTAACTACGGCTACACTAGAAGAACAGTATTTGGTATCTGCGCTCTGCTGAAGCCAGTTACCTTCGGAAAAAGAGTTGGTAGCTCTTGATCCGGCAAACAAACCACCGCTGGTAGCGGTGGTTTTTTTGTTTGCAAGCAGCAGATTACGCGCAGAAAAAAAGGATCTCAAGAAGATCCTTTGATCTTTTCTACGGGGTCTGACGCTCAGTGGAACGAAAACTCACGTTAAGGGATTTTGGTCATGAGATTATCAAAAAGGATCTTCACCTAGATCCTTTTAAATTAAAAATGAAGTTTTAAATCAATCTAAAGTATATATGAGTAAACTTGGTCTGACAGAGTTCTGAGGTCATTACTGGATCTATCAACAGCAGTCCAAGCGAGCTCGATATCAAATTACGCCCCGCCCTGCCACTCATCGCAGTACTGTTGTAATTCATTAAGCATTCTGCCGACATGGAAGCCATCACAAACGGCATGATGAACCTGAATCGCCAGCGGCATCAGCACCTTGTCGCCTTGCGTATAATATTTGCCCATGGTGAAAACGGGGGCGAAGAAGTTGTCCATATTGGCCACGTTTAAATCAAAACTGGTGAAACTCACCCAGGGATTGGCTGAGACGAAAAACATATTCTCAATAAACCCTTTAGGGAAATAGGCCAGGTTTTCACCGTAACACGCCACATCTTGCGAATATATGTGTAGAAACTGCCGGAAATCGTCGTGGTATTCACTCCAGAGCGATGAAAACGTTTCAGTTTGCTCATGGAAAACGGTGTAACAAGGGTGAACACTATCCCATATCACCAGCTCACCGTCTTTCATTGCCATACGAAATTCCGGATGAGCATTCATCAGGCGGGCAAGAATGTGAATAAAGGCCGGATAAAACTTGTGCTTATTTTTCTTTACGGTCTTTAAAAAGGCCGTAATATCCAGCTGAACGGTCTGGTTATAGGTACATTGAGCAACTGACTGAAATGCCTCAAAATGTTCTTTACGATGCCATTGGGATATATCAACGGTGGTATATCCAGTGATTTTTTTCTCCATTTTAGCTTCCTTAGCTCCTGAAAATCTCGATAACTCAAAAAATACGCCCGGTAGTGATCTTATTTCATTATGGTGAAAGTTGGAACCTCTTACGTGCCCGATCAACTCGCGCGTTTGCCACCTGACGTCTAAGAAAAGGAATATTCAGCAATTTGCCCGTGCCGAAGAAAGGCCCACCCGTGAAGGTGAGC"
# seq_obj = Seq(seq)
# seq_reverse = str(seq_obj.reverse_complement())
# fi = featureIdentify()
# feature_list = fi.featureMatch(seq)
# reverse_feature_list = fi.featureMatch(seq_reverse)
# scar_list = scarPosition(seq)
# sa = SequenceAnnotator(seq,feature_list,reverse_feature_list,scar_list)
# sa.GenerateGBKFile()



# print(scar_list)
# for eachfeature in scar_list:
#     EnzymeName = next(iter(eachfeature.keys()))
#     EnzymeInfo = eachfeature[EnzymeName]
#     # 通过scar位置判断酶切位点位置
#     for each_index in EnzymeInfo['index']:
#         print(seq[each_index-8:each_index-2].upper())
#         print(seq[each_index+4:each_index+10].upper())
        # if(seq[each_index-7:each_index-1].upper() == "CGTCTC"):
                




# for each_feature in feature_list.keys():
#     seq_id = 
#     start = each_feature
# print(feature_list)
# print(reverse_feature_list)


# obj = "aacgaagcatctgtgcttcattttgtagaacaaaaatgcaacgcgagagcgctaatttttcaaacaaagaatctgagctgcatttttacagaacagaaatgcaacgcgaaagcgctattttaccaacgaagaatctgtgcttcatttttgtaaaacaaaaatgcaacgcgagagcgctaatttttcaaacaaagaatctgagctgcatttttacagaacagaaatgcaacgcgagagcgctattttaccaacaaagaatctatacttcttttttgttctacaaaaatgcatcccgagagcgctatttttctaacaaagcatcttagattactttttttctcctttgtgcgctctataatgcagtctcttgataactttttgcactgtaggtccgttaaggttagaagaaggctactttggtgtctattttctcttccataaaaaaagcctgactccacttcccgcgtttactgattactagcgaagctgcgggtgcattttttcaagataaaggcatccccgattatattctataccgatgtggattgcgcatactttgtgaacagaaagtgatagcgttgatgattcttcattggtcagaaaattatgaacggtttcttctattttgtctctatatactacgtataggaaatgtttacattttcgtattgttttcgattcactctatgaatagttcttactacaatttttttgtctaaagagtaatactagagataaacataaaaaatgtagaggtcgagtttagatgcaagttcaaggagcgaaaggtggatgggtaggttatatagggatatagcacagagatatatagcaaagagatacttttgagcaatgtttgtggaagcggtattcgcaatattttagtagctcgttacagtccggtgcgtttttggttttttgaaagtgcgtcttcagagcgcttttggttttcaaaagcgctctgaagttcctatactttctagctagagaataggaacttcggaataggaacttcaaagcgtttccgaaaacgagcgcttccgaaaatgcaacgcgagctgcgcacatacagctcactgttcacgtcgcacctatatctgcgtgttgcctgtatatatatatacatgagaagaacggcatagtgcgtgtttatgcttaaatgcgtacttatatgcgtctatttatgtaggatgaaaggtagtctagtacctcctgtgatattatcccattccatgcggggtatcgtatgcttccttcagcactaccctttagctgttctatatgctgccactcctcaattggattagtctcatccttcaatgctatcatttcctttgatattggatc"
# print(obj.lower())

# fileaddress = r'c:\Users\admin\Nutstore\1\元件标准化数据库\大肠杆菌和酵母Kit相关文档\Main text-Figure-SI\图谱文件\E.coli\pEcint07.gb'
# try:
#         records = parse(fileaddress,"genbank")
#         for each in records:
#                 print(77)
#         print(111)
# except Exception as e:
#         print(111)
#         print(e)
#         traceback.print_exc()
import pymysql
conn = pymysql.connect(user="root",password="04080117",host="localhost",database="labdnadata")
cur = conn.cursor()
sql = "select partid,name,level0sequence from parttable;"
cur.execute(sql)
result = cur.fetchall()
for each in result:
        target_seq = each[2]
        if(target_seq[:4].upper() == "GTGC" or target_seq[:4].upper() == "GCAC" or target_seq[:4].upper() == "ATCA"
                or target_seq[:4].upper() == "TGAT" or target_seq[:4].upper() == "AATG" or target_seq[:4].upper() == "CATT"
                or target_seq[:4].upper() == "TAAA" or target_seq[:4].upper() == "TTTA" or target_seq[:4].upper() == "CCTC"
                or target_seq[:4].upper() == "GAGG"):
                target_seq = target_seq[4:]
        if(target_seq[-4:].upper() == "GTGC" or target_seq[-4:].upper() == "GCAC" or target_seq[-4:].upper() == "ATCA"
        or target_seq[-4:].upper() == "TGAT" or target_seq[-4:].upper() == "AATG" or target_seq[-4:].upper() == "CATT"
        or target_seq[-4:].upper() == "TAAA" or target_seq[-4:].upper() == "TTTA" or target_seq[-4:].upper() == "CCTC"
        or target_seq[-4:].upper() == "GAGG"):
                target_seq = target_seq[:-4]
        if(target_seq != each[2]):
                sql = f"update parttable set level0sequence = '{target_seq}' where partid={each[0]};"
                cur.execute(sql)
        else:
                continue
                        
                