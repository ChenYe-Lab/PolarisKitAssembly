from Bio.Seq import Seq
# import re
import pymysql
import sys
from Bio.SeqIO import parse
sys.path.append(r'C:\Users\admin\Desktop\WebDatabaseBeta\WebDatabase\WebDataWorld\LabDatabase')
# from CaculateModule import ScarIdentify
from ScarIdentify import scarIdentSitePosition
from CaculateModule.KmerIndex import KmerIndex
# from ControllerModule import FittingLabels
seq = "gattatcaaaaaggatcttcacctagatccttttaaattaaaaatgaagttttaaatcaatctaaagtatatatgagtaaacttggtctgacagagttctgaggtcattactggatctatcaacagcagtccgtgttacaaccaattaaccaattctgattagaaaaactcatcgagcatcaaatgaaactgcaatttattcatatcaggattatcaataccatatttttgaaaaagccgtttctgtaatgaaggagaaaactcaccgaggcagttccataggatggcaagatcctggtatcggtctgcgattccgactcgtccaacatcaatacaacctattaatttcccctcgtcaaaaataaggttatcaagtgagaaatcaccatgagtgacgactgaatccggtgagaatggcaaaagcttatgcatttctttccagacttgttcaacaggccagccattacgctcgtcatcaaaatcactcgcatcaaccaaaccgttattcattcgtgattgcgcctgagcgaggcgaaatacgcgatcgctgttaaaaggacaattacaaacaggaatcgaatgcaaccggcgcaggaacactgccagcgcatcaacaatattttcacctgaatcaggatattcttctaatacctggaatgctgttttcccggggatcgcagtggtgagtaaccatgcatcatcaggagtacggataaaatgcttgatggtcggaagaggcataaattccgtcagccagtttagtctgaccatctcatctgtaacatcattggcaacgctacctttgccatgtttcagaaacaactctggcgcatcgggcttcccatacaatcgatagattgtcgcacctgattgcccgacattatcgcgagcccatttatacccatataaatcagcatccatgttggaatttaatcgcggcctggagcaagacgtttcccgttgaatatggctcataacaccccttgtattactgtttatgtaagcagacagttttattgttcatgatgatatatttttatcttgtgcaatgtaacatcagagattttgagacacaacgtggctttgttgaataaatcgaacttttgctgagttgaaggatcagcccgatcaactcgcgcgtttgccacctgacgtctaagaaaaggaatattcagcaatttgcccgtgccgaagaaaggcccacccgtgaaggtgagctccggcaattaaaaaagcggctaaccacgccgctttttttacgtctgcactcggtaccaaattccagaaaagaggcctcccgaaaggggggccttttttcgttttggtccacaatcacctatgaactgtcggtgcggagaccggcttactaaaagccagataacagtatgcatatttgcgcgctgatttttgcggtataagaatatatactgatatgtatacccgaagtatgtcaaaaagaggtatgctatgaagcagcgtattacagtgacagttgacagcgacagctatcagttgctcaaggcatatatgatgtcaatatctccggtctggtaagcacaaccatgcagaatgaagcccgtcgtctgcgtgccgaacgctggaaagcggaaaatcaggaagggatggctgaggtcgcccggtttattgaaatgaacggctcttttgctgacgagaacaggggctggtgaaatgcagtttaaggtttacacctataaaagagagagccgttatcgtctgtttgtggatgtacagagtgatattattgacacgcccgggcgacggatggtgatccccctggccagtgcacgtctgctgtcagataaagtctcccgtgaactttacccggtggtgcatatcggggatgaaagctggcgcatgatgaccaccgatatggccagtgtgccggtttccgttatcggggaagaagtggctgatctcagccaccgcgaaaatgacatcaaaaacgccattaacctgatgttctggggaatataaggtctcgtaaatctttaaaaagaaacctccgcattgcggaggtttcgccttttgatactctgtctgaagtaattcttgccgcagtgaaaaatggcgcccatcggcgccatttttttatgcttccattagaaagcaaaaagcctgctagaaagcaggcttttttgaatttggctcctctgaccctcttatttgatttcaattttgtcccactccccctagaggcatcaaataaaacgaaaggctcagtcgaaagactgggcctttcgttttatctgttgtttgtcggtgaacgctctcctgagtaggacaaatccgccgccctagacctagggtacgggttttgctgcccgcaaacgggctgttctggtgttgctagtttgttatcagaatcgcagatccggcttcagccggtttgccggctgaaagcgctatttcttccagaattgccatgattttttccccacgggaggcgtcactggctcccgtgttgtcggcagctttgattcgataagcagcatcgcctgtttcaggctgtctatgtgtgactgttgagctgtaacaagttgtctcaggtgttcaatttcatgttctagttgctttgttttactggtttcacctgttctattaggtgttacatgctgttcatctgttacattgtcgatctgttcatggtgaacagctttgaatgcaccaaaaactcgtaaaagctctgatgtatctatcttttttacaccgttttcatctgtgcatatggacagttttccctttgatatgtaacggtgaacagttgttctacttttgtttgttagtcttgatgcttcactgatagatacaagagccataagaacctcagatccttccgtatttagccagtatgttctctagtgtggttcgttgtttttgcgtgagccatgagaacgaaccattgagatcatacttactttgcatgtcactcaaaaattttgcctcaaaactggtgagctgaatttttgcagttaaagcatcgtgtagtgtttttcttagtccgttatgtaggtaggaatctgatgtaatggttgttggtattttgtcaccattcatttttatctggttgttctcaagttcggttacgagatccatttgtctatctagttcaacttggaaaatcaacgtatcagtcgggcggcctcgcttatcaaccaccaatttcatattgctgtaagtgtttaaatctttacttattggtttcaaaacccattggttaagccttttaaactcatggtagttattttcaagcattaacatgaacttaaattcatcaaggctaatctctatatttgccttgtgagttttcttttgtgttagttcttttaataaccactcataaatcctcatagagtatttgttttcaaaagacttaacatgttccagattatattttatgaatttttttaactggaaaagataaggcaatatctcttcactaaaaactaattctaatttttcgcttgagaacttggcatagtttgtccactggaaaatctcaaagcctttaaccaaaggattcctgatttccacagttctcgtcatcagctctctggttgctttagctaatacaccataagcattttccctactgatgttcatcatctgagcgtattggttataagtgaacgataccgtccgttctttccttgtagggttttcaatcgtggggttgagtagtgccacacagcataaaattagcttggtttcatgctccgttaagtcatagcgactaatcgctagttcatttgctttgaaaacaactaattcagacatacatctcaattggtctaggtgattttaatcactataccaattgagatgggctagtcaatgataattactagtccttttcctttgagttgtgggtatctgtaaattctgctagacctttgctggaaaacttgtaaattctgctagaccctctgtaaattccgctagacctttgtgtgttttttttgtttatattcaagtggttataatttatagaataaagaaagaataaaaaaagataaaaagaatagatcccagccctgtgtataactcactactttagtcagttccgcagtattacaaaaggatgtcgcaaacgctgtttgctcctctacaaaacagaccttaaaaccctaaaggcttaagtagcaccctcgcaagctcgggcaaatcgctgaatattccttttgtctccgaccatcaggcacctgagtcgctgtctttttcgtgacattcagttcgctgcgctcacggctctggcagtgaatgggggtaaatggcactacaggcgccttttatggattcatgcaaggaaactacccataatacaagaaaagcccgtcacgggcttctcagggcgttttatggcgggtctgctatgtggtgctatctgactttttgctgttcagcagttcctgccctctgattttccagtctgaccacttcggattatcccgtgacaggtcattcagactggctaatgcacccagtaaggcagcggtatcatcaacaggcttacccgtcttactgtc"
print(seq[160:162])
# seq="gcggccgcGAAGACCTGCTTCGAATTTCTTATGATTTATGATTTTTATTATTAAATAAGTTATAAAAAAAATAAGTGTATACAAATTTTAAAGTGACACTTAGGTTTTAAAACGAAAATTCCCTCAGTCATAAGTCTGGGCTAAGCCCACTGATGAGTCGCTGAAATGCGACGAAACTTATGAATGTTTGGGCGGGCCGGGGTGGGATGGAGGCTGGCATGTGTGGGGACATTATGGGGGTAGGTATCCCAGTGCCTGGTGTGGTTAGGGGGCCGGTGCGGAGACCGGCTTACTAAAAGCCAGATAACAGTATGCATATTTGCGCGCTGATTTTTGCGGTATAAGAATATATACTGATATGTATACCCGAAGTATGTCAAAAAGAGGTATGCTATGAAGCAGCGTATTACAGTGACAGTTGACAGCGACAGCTATCAGTTGCTCAAGGCATATATGATGTCAATATCTCCGGTCTGGTAAGCACAACCATGCAGAATGAAGCCCGTCGTCTGCGTGCCGAACGCTGGAAAGCGGAAAATCAGGAAGGGATGGCTGAGGTCGCCCGGTTTATTGAAATGAACGGCTCTTTTGCTGACGAGAACAGGGGCTGGTGAAATGCAGTTTAAGGTTTACACCTATAAAAGAGAGAGCCGTTATCGTCTGTTTGTGGATGTACAGAGTGATATTATTGACACGCCCGGGCGACGGATGGTGATCCCCCTGGCCAGTGCACGTCTGCTGTCAGATAAAGTCTCCCGTGAACTTTACCCGGTGGTGCATATCGGGGATGAAAGCTGGCGCATGATGACCACCGATATGGCCAGTGTGCCGGTTTCCGTTATCGGGGAAGAAGTGGCTGATCTCAGCCACCGCGAAAATGACATCAAAAACGCCATTAACCTGATGTTCTGGGGAATATAAGGTCTCGCCTCCTGAAGGTCTTCGAGCGGTATCAGCTCACTCAAAGGCGGTAATACGGTTATCCACAGAATCaggggcggccgcacggttatccacagaatcaggggataacgcaggaaagaacatgtgagcaaaaggccagcaaaaggccaggaaccgtaaaaaggccgcgttgctggcgtttttccataggctccgcccccctgacgagcatcacaaaaatcgacgctcaagtcagaggtggcgaaacccgacaggactataaagataccaggcgtttccccctggaagctccctcgtgcgctctcctgttccgaccctgccgcttaccggatacctgtccgcctttctcccttcgggaagcgtggcgctttctcatagctcacgctgtaggtatctcagttcggtgtaggtcgttcgctccaagctgggctgtgtgcacgaaccccccgttcagcccgaccgctgcgccttatccggtaactatcgtcttgagtccaacccggtaagacacgacttatcgccactggcagcagccactggtaacaggattagcagagcgaggtatgtaggcggtgctacagagttcttgaagtggtggcctaactacggctacactagaagaacagtatttggtatctgcgctctgctgaagccagttaccttcggaaaaagagttggtagctcttgatccggcaaacaaaccaccgctggtagcggtggtttttttgtttgcaagcagcagattacgcgcagaaaaaaaggatctcaagaagatcctttgatcttttctacggggtctgacgctcagtggaacgaaaactcacgttaagggattttggtcatgactgatccttcaactcagcaaaagttcgatttattcaacaaagccacgttgtgtctcaaaatctctgatgttacattgcacaagataaaaatatatcatcatgaacaataaaactgtctgcttacataaacagtaatacaaggggtgttatgagccatattcaacgggaaacgtcttgctccaggccgcgattaaattccaacatggatgctgatttatatgggtataaatgggctcgcgataatgtcgggcaatcaggtgcgacaatctatcgattgtatgggaagcccgatgcgccagagttgtttctgaaacatggcaaaggtagcgttgccaatgatgttacagatgagatggtcagactaaactggctgacggaatttatgcctcttccgaccatcaagcattttatccgtactcctgatgatgcatggttactcaccactgcgatccccgggaaaacagcattccaggtattagaagaatatcctgattcaggtgaaaatattgttgatgcgctggcagtgttcctgcgccggttgcattcgattcctgtttgtaattgtccttttaacagcgatcgcgtatttcgcctcgctcaggcgcaatcacgaatgaataacggtttggttgatgcgagtgattttgatgacgagcgtaatggctggcctgttgaacaagtctggaaagaaatgcataagcttttgccattctcaccggattcagtcgtcactcatggtgatttctcacttgataaccttatttttgacgaggggaaattaataggttgtattgatgttggacgagtcggaatcgcagaccgataccaggatcttgccatcctatggaactgcctcggtgagttttctccttcattacagaaacggctttttcaaaaatatggtattgataatcctgatatgaataaattgcagtttcatttgatgctcgatgagtttttctaatcagaattggttaattggttgtaacacgcggccgctcgggacggatcgcttgcctgtaacttacacgcgcctcgtatcttttaatgatggaataatttgggaatttactctgtgtttatttatttttatgttttgtatttggattttagaaagtaaataaagaaggtagaagagttacggaatgaagaaaaaaaaataaacaaaggtttaaaaaatttcaacaaaaagcgtactttacatatatatttattagacaagaaaagcagattaaatagatatacattcgattaacgataagtaaaatgtaaaatcacaggattttcgtgtgtggttttctacacagacaagatgaaacaattcggcattaatacctgagagcaggaagagcaagataaaaggtagtatttgttggcgatccccctagagtcttttacatcttcggaaaacaaaaactattttttctttaatttctttttttactttctatttttaatttatatatttatattaaaaaatttaaattataattatttttatagcacgtgatactcctgcctatttaacgccaacgttgcgagatatacactcgaaatgtgtgatgtagatgtaaacagacggctatatgaatgccactagccggttattttactcctagttaatacatatttcctagaattttttacgtgcataagagtagaatagtctaaagagaagggtcctccaggttaagcaaggattttcttaacttcttcggcgacagcatcaccgacttcggtggtactgttggaaccacctaaatcaccagttctgatacctgcatccaaaacctttttaactgcatcttcaatggccttaccttcttcaggcaagttcaatgacaatttcaacatcattgcagcagacaagatagtggcgatagggttgaccttattctttggcaaatctggagcagaaccgtggcatggttcgtacaaaccaaatgcggtgttcttgtctggcaaagaggccaaggacgcagatggcaacaaacccaaggaacctgggataacggaggcttcatcggagatgatatcaccaaacatgttgctggtgattataataccatttaggtgggttgggttcttaactaggatcatggcggcagaatcaatcaattgatgttgaaccttcaatgtaggaaattcgttcttgatggtttcctccacagtttttctccataatcttgaagaggccaaaacattagctttatccaaggaccaaataggcaatggtggctcatgttgtagggccatgaaagcggccattcttgtgattctttgcacttctggaacggtgtattgttcactatcccaagcgacaccatcaccatcgtcctcctttctcttaccaaagtaaatacctcccactaattctctgacaacaacgaagtcagtacctttagcaaattgtggcttgattggagataagtctaaaagagagtcggatgcaaagttacatggtcttaagttggcgtacaattgaagttctttacggatttttagtaaaccttgttcaggtctaacactaccggttccccatttaggaccacccacagcacctaacaaaacggcatcagccttcttggaggcttccagcgcctcatctggaagtggaacacctgtagcatcgatagcagcaccaccaattaaatgattttcgaaatcgaacttgacattggaacgaacatcagaaatagctttaagaaccttaatggcttcggctgtgatttcttgaccaacgtggtcacctggcaaaacgacgatcttcttaggggcagacattagaatggtatatccttgaaatatatatatatatattgctgaaatgtaaaaggtaagaaaagttagaaagtaagacgattgctaaccacctattggaaaaaacaataggtccttaaataatattgtcaacttcaagtattgtgatgcaagcatttagtcatgaacgcttctctattctatatgaaaagccggttccggcgctctcacctttcctttttctcccaatttttcagttgaaaaaggtatatgcgtcaggcgacctctgaaattaacaaaaaatttccagtcatcgaatttgattctgtgcgatagcgcccctgtgtgttctcgttatgttgaggaaaaaaataatggttgctaagagattcgaactcttgcatcttacgatacctgagtattcccacagttaactgcggtcaagatatttcttgaatcaggcgccttagaccgctcggccaaacaaccaattacttgttgagaaatagagtataattatcctataaatataacgtttttgaacacacatgaacaaggaagtacaggacaattgattttgaagagaatgtggattttgatgtaattgttgggattccatttttaataaggcaataatattaggtatgtagatatactagaagttctcctcgatgtaGAAAGGCCCACCCGTGAAGGTGAGCCAGTGA"
# print(ScarIdentify.scarFunction(seq))

# file_address = r"C:\\\\Users\\\\admin\\\\Desktop\\\\WebDatabase\\\\WebDataWorld\\\\LabDatabase\\\\static\\\\LabDatabase\\\\DownloadFile\\\\GenerateFile\\\\\\\\AssemblyFile\\\\backbone-XRHe-B011.gbk"

# records = parse(file_address, "genbank")
# for record in records:
#     print(record.features)

# str = "aggggataacgcaggaaagaacatgtgagcaaaaggccagcaaaaggccaggaaccgtaaaaaggccgcgttgctggcgtttttccataggctccgcccccctgacgagcatcacaaaaatcgacgctcaagtcagaggtggcgaaacccgacaggactataaagataccaggcgtttccccctggaagctccctcgtgcgctctcctgttccgaccctgccgcttaccggatacctgtccgcctttctcccttcgggaagcgtggcgctttctcatagctcacgctgtaggtatctcagttcggtgtaggtcgttcgctccaagctgggctgtgtgcacgaaccccccgttcagcccgaccgctgcgccttatccggtaactatcgtcttgagcccaacccggtaagacacgacttatcgccactggcagcagccactggtaacaggattagcagagcgaggtatgtaggcggtgctacagagttcttgaagtggtggcctaactacggctacactagaagaacagtatttggtatctgcgctctgctgaagccagttaccttcggaaaaagagttggtagctcttgatccggcaaacaaaccaccgctggtagcggtggtttttttgtttgcaagcagcagattacgcgcagaaaaaaaggatctcaagaagatcctttgatcttttctacggggtctgacgctcagtggaacgaaaactcacgttaagggattttggtcatgagattatcaaaaaggatcttcacctagatccttttaaattaaaaatgaagttttaaatcaatctaaagtatatatgagtaaacttggtctgacagttaccaatgcttaatcagtgaggcacctatctcagcgatctgtctatttcgttcatccatagttgcctggctccccgtcgtgtagataactacgatacgggagggcttaccatctggccccagtgctgcaatgataccgcgagagccacgctcaccggctccagatttatcagcaataaaccagccagccggaagggccgagcgcagaagtggtcctgcaactttatccgcctccatccagtctattaattgttgccgggaagctagagtaagtagttcgccagttaatagtttgcgcaacgttgttgccattgctacaggcatcgtggtgtcacgctcgtcgtttggtatggcttcattcagctccggttcccaacgatcaaggcgagttacatgatcccccatgttgtgcaaaaaagcggttagctccttcggtcctccgatcgttgtcagaagtaagttggccgcagtgttatcactcatggttatggcagcactgcataattctcttactgtcatgccatccgtaagatgcttttctgtgactggtgagtactcaaccaagtcattctgagaatagtgtatgcggcgaccgagttgctcttgcccggcgtcaatacgggataataccgcgccacatagcagaactttaaaagtgctcatcattggaaaacgttcttcggggcgaaaactctcaaggatcttaccgctgttgagatccagttcgatgtaacccactcgtgcacccaactgatcttcagcatcttttactttcaccagcgtttctgggtgagcaaaaacaggaaggcaaaatgccgcaaaaaagggaataagggcgacacggaaatgttgaatactcatactcttcctttttcaatattattgaagcatttatcagggttattgtctcatgagcggatacatatttgaatgtatttagaaaaataaacaaataggggttccgcgcacatttccccgaaaagtgccacctgacgtctaagaaaccattattatcatgacattaacctataaaaataggcgtatcacgaggccctttcgtctcgcgcgtttcggtgatgacggtgaaaacctctgacacatgcagctcccggagacggtcacagcttgtctgtaagcggatgccgggagcagacaagcccgtcagggcgcgtcagcgggtgttggcgggtgtcggggctggcttaactatgcggcatcagagcagattgtactgctagcataaccccttggggcctctaaacgggtcttgaggggttttttgggtctcagtgctggtcttcggcttactaaaagccagataacagtatgcatatttgcgcgctgatttttgcggtataagaatatatactgatatgtatacccgaagtatgtcaaaaagaggtatgctatgaagcagcgtattacagtgacagttgacagcgacagctatcagttgctcaaggcatatatgatgtcaatatctccggtctggtaagcacaaccatgcagaatgaagcccgtcgtctgcgtgccgaacgctggaaagcggaaaatcaggaagggatggctgaggtcgcccggtttattgaaatgaacggctcttttgctgacgagaacaggggctggtgaaatgcagtttaaggtttacacctataaaagagagagccgttatcgtctgtttgtggatgtacagagtgatattattgacacgcccgggcgacggatggtgatccccctggccagtgcacgtctgctgtcagataaagtctcccgtgaactttacccggtggtgcatatcggggatgaaagctggcgcatgatgaccaccgatatggccagtgtgccggtttccgttatcggggaagaagtggctgatctcagccaccgcgaaaatgacatcaaaaacgccattaacctgatgttctggggaatataagaagactaatcaagagaccctcggtaccaaattccagaaaagaggcctcccgaaaggggggccttttttcgttttggtccgagcggtatcagctcactcaaaggcggtaatacggttatccacagaatc"
# print(scarIdentSitePosition(str))
# def compare_strings(str1, str2):
#     """
#     比较两个字符串，找出不同的字符及其位置
#     """
#     # 找出最大长度，以便处理不同长度的字符串
#     max_len = max(len(str1), len(str2))
    
#     differences = []
    
#     for i in range(max_len):
#         # 获取当前位置的字符（如果存在）
#         char1 = str1[i] if i < len(str1) else None
#         char2 = str2[i] if i < len(str2) else None
        
#         if char1 != char2:
#             differences.append({
#                 'position': i + 1,  # 位置从1开始计数，更符合人类习惯
#                 'str1_char': char1,
#                 'str2_char': char2,
#                 'str1_index': i,
#                 'str2_index': i
#             })
    
#     return differences


# def display_differences(str1, str2, differences):
#     """
#     显示比对结果
#     """
#     print(f"字符串1: {str1}")
#     print(f"字符串2: {str2}")
#     print(f"字符串长度 - 字符串1: {len(str1)}, 字符串2: {len(str2)}")
#     print("-" * 50)
    
#     if not differences:
#         print("两个字符串完全相同！")
#     else:
#         print(f"发现 {len(differences)} 处不同：")
#         print("-" * 50)
        
#         # 创建可视化标记
#         marker1 = [' '] * len(str1)
#         marker2 = [' '] * len(str2)
        
#         for diff in differences:
#             pos = diff['position'] - 1  # 转换为0-based索引
            
#             if pos < len(str1):
#                 marker1[pos] = '↑'
#             if pos < len(str2):
#                 marker2[pos] = '↑'
            
#             print(f"位置 {diff['position']}:")
#             print(f"  字符串1: '{diff['str1_char']}'" if diff['str1_char'] is not None else "  字符串1: [无字符]")
#             print(f"  字符串2: '{diff['str2_char']}'" if diff['str2_char'] is not None else "  字符串2: [无字符]")
#             print()
        
#         # 显示带标记的字符串
#         print("字符位置标记：")
#         print("字符串1:", str1)
#         print("        ", ''.join(marker1))
#         print("字符串2:", str2)
#         print("        ", ''.join(marker2))


# def detailed_compare(str1, str2):
#     """
#     详细的字符串比对函数
#     """
#     differences = compare_strings(str1, str2)
#     display_differences(str1, str2, differences)
    
#     # 返回差异信息以便进一步处理
#     return differences


# # 示例使用
# if __name__ == "__main__":
#     # 测试用例

#     detailed_compare("ACGGGTTTTGCTGCCCGCAAACGGGCTGTTCTGGTGTTGCTAGTTTGTTATCAGAATCGCAGATCCGGCTTCAGCCGGTTTGCCGGCTGAAAGCGCTATTTCTTCCAGAATTGCCATGATTTTTTCCCCACGGGAGGCGTCACTGGCTCCCGTGTTGTCGGCAGCTTTGATTCGATAAGCAGCATCGCCTGTTTCAGGCTGTCTATGTGTGACTGTTGAGCTGTAACAAGTTGTCTCAGGTGTTCAATTTCATGTTCTAGTTGCTTTGTTTTACTGGTTTCACCTGTTCTATTAGGTGTTACATGCTGTTCATCTGTTACATTGTCGATCTGTTCATGGTGAACAGCTTTgAATGCACCAAAAACTCGTAAAAGCTCTGATGTATCTATCTTTTTTACACCGTTTTCATCTGTGCATATGGACAGTTTTCCCTTTGATATgTAACGGTGAACAGTTGTTCTACTTTTGTTTGTTAGTCTTGATGCTTCACTGATAGATACAAGAGCCATAAGAACCTCAGATCCTTCCGTATTTAGCCAGTATGTTCTCTAGTGTGGTTCGTTGTTTTTGCGTGAGCCATGAGAACGAACCATTGAGATCATaCTTACTTTGCATGTCACTCAAAAATTTTGCCTCAAAACTGGTGAGCTGAATTTTTGCAGTTAAAGCATCGTGTAGTGTTTTTCTTAGTCCGTTAtGTAGGTAGGAATCTGATGTAATGGTTGTTGGTATTTTGTCACCATTCATTTTTATCTGGTTGTTCTCAAGTTCGGTTACGAGATCCATTTGTCTATCTAGTTCAACTTGGAAAATCAACGTATCAGTCGGGCGGCCTCGCTTATCAACCACCAATTTCATATTGCTGTAAGTGTTTAAATCTTTACTTATTGGTTTCAAAACCCATTGGTTAAGCCTTTTAAACTCATGGTAGTTATTTTCAAGCATTAACATGAACTTAAATTCATCAAGGCTAATCTCTATATTTGCCTTGTGAGTTTTCTTTTGTGTTAGTTCTTTTAATAACCACTCATAAATCCTCATAGAGTATTTGTTTTCAAAAGACTTAACATGTTCCAGATTATATTTTATGAATTTTTTTAACTGGAAAAGATAAGGCAATATCTCTTCACTAAAAACTAATTCTAATTTTTCGCTTGAGAACTTGGCATAGTTTGTCCACTGGAAAATCTCAAAGCCTTTAACCAAAGGATTCCTGATTTCCACAGTTCTCGTCATCAGCTCTCTGGTTGCTTTAGCTAATACACCATAAGCATTTTCCCTACTGATGTTCATCATCTGAGCGTATTGGTTATAAGTGAACGATACCGTCCGTTCTTTCCTTGTAGGGTTTTCAATCGTGGGGTTGAGTAGTGCCACACAGCATAAAATTAGCTTGGTTTCATGCTCCGTTAAGTCATAGCGACTAATCGCTAGTTCATTTGCTTTGAAAACAACTAATTCAGACATACATCTCAATTGGTCTAGGTGATTTTAATCACTATACCAATTGAGATGGGCTAGTCAATGATAATTACTAGTCCTTTTCCTTTGAGTTGTGGGTATCTGTAAATTCTGCTAGACCTTTGCTGGAAAACTTGTAAATTCTGCTAGACCCTCTGTAAATTCCGCTAGACCTTTGTGTGTTTTTTTTGTTTATATTCAAGTGGTTATAATTTATAGAATAAAGAAAGAATAAAAAAAGATAAAAAGAATAGATCCCAGCCCTGTGTATAACTCACTACTTTAGTCAGTTCCGCAGTATTACAAAAGGATGTCGCAAACGCTGTTTGCTCCTCTACAAAACAGACCTTAAAACCCTAAAGGCTTAAGTAGCACCCTCGCAAGCTCGGGCAAATCGCTGAATATTCCTTTTGTCTCCGACCATCAGGCACCTGAGTCGCTGTCTTTTTCGTGACATTCAGTTCGCTGCGCTCACGGCTCTGGCAGTGAATGGGGGTAAATGGCACTACAGGCGCCTTTTATGGATTCATGCAAGGAAACTACCCATAATACAAGAAAAGCCCGTCACGGGCTTCTCAGGGCGTTTTATGGCGGGTCTGCTATGTGGTGCTATCTGACTTTTTGCTGTTCAGCAGTTCCTGCCCTCTGATTTTCCAGTCTGACCACTTCGGATTATCCCGTGACAGGTCATTCAGACTGGCTAATGCACCCAGTAAGGCAGCGGTATCATCAACAGGCTTACCCGTCTTACTGTC",
#                      "acgggttttgctgcccgcaaacgggctgttctggtgttgctagtttgttatcagaatcgcagatccggcttcagccggtttgccggctgaaagcgctatttcttccagaattgccatgattttttccccacgggaggcgtcactggctcccgtgttgtcggcagctttgattcgataagcagcatcgcctgtttcaggctgtctatgtgtgactgttgagctgtaacaagttgtctcaggtgttcaatttcatgttctagttgctttgttttactggtttcacctgttctattaggtgttacatgctgttcatctgttacattgtcgatctgttcatggtgaacagctttaaatgcaccaaaaactcgtaaaagctctgatgtatctatcttttttacaccgttttcatctgtgcatatggacagttttccctttgatatctaacggtgaacagttgttctacttttgtttgttagtcttgatgcttcactgatagatacaagagccataagaacctcagatccttccgtatttagccagtatgttctctagtgtggttcgttgtttttgcgtgagccatgagaacgaaccattgagatcatgcttactttgcatgtcactcaaaaattttgcctcaaaactggtgagctgaatttttgcagttaaagcatcgtgtagtgtttttcttagtccgttacgtaggtaggaatctgatgtaatggttgttggtattttgtcaccattcatttttatctggttgttctcaagttcggttacgagatccatttgtctatctagttcaacttggaaaatcaacgtatcagtcgggcggcctcgcttatcaaccaccaatttcatattgctgtaagtgtttaaatctttacttattggtttcaaaacccattggttaagccttttaaactcatggtagttattttcaagcattaacatgaacttaaattcatcaaggctaatctctatatttgccttgtgagttttcttttgtgttagttcttttaataaccactcataaatcctcatagagtatttgttttcaaaagacttaacatgttccagattatattttatgaatttttttaactggaaaagataaggcaatatctcttcactaaaaactaattctaatttttcgcttgagaacttggcatagtttgtccactggaaaatctcaaagcctttaaccaaaggattcctgatttccacagttctcgtcatcagctctctggttgctttagctaatacaccataagcattttccctactgatgttcatcatctgagcgtattggttataagtgaacgataccgtccgttctttccttgtagggttttcaatcgtggggttgagtagtgccacacagcataaaattagcttggtttcatgctccgttaagtcatagcgactaatcgctagttcatttgctttgaaaacaactaattcagacatacatctcaattggtctaggtgattttaatcactataccaattgagatgggctagtcaatgataattactagtccttttcctttgagttgtgggtatctgtaaattctgctagacctttgctggaaaacttgtaaattctgctagaccctctgtaaattccgctagacctttgtgtgttttttttgtttatattcaagtggttataatttatagaataaagaaagaataaaaaaagataaaaagaatagatcccagccctgtgtataactcactactttagtcagttccgcagtattacaaaaggatgtcgcaaacgctgtttgctcctctacaaaacagaccttaaaaccctaaaggcttaagtagcaccctcgcaagctcgggcaaatcgctgaatattccttttgtctccgaccatcaggcacctgagtcgctgtctttttcgtgacattcagttcgctgcgctcacggctctggcagtgaatgggggtaaatggcactacaggcgccttttatggattcatgcaaggaaactacccataatacaagaaaagcccgtcacgggcttctcagggcgttttatggcgggtctgctatgtggtgctatctgactttttgctgttcagcagttcctgccctctgattttccagtctgaccacttcggattatcccgtgacaggtcattcagactggctaatgcacccagtaaggcagcggtatcatcaacaggcttacccgtcttactgtc")
# conn = pymysql.connect(user="root",password="04080117",host="localhost",database="labdnadata")
# cur = conn.cursor()


# sql = "select backboneid, count(backboneid) from Backbonescartable group by backboneid having count(backboneid) > 1;"
# cur.execute(sql)
# result = cur.fetchall()
# # print(result)

# for each in result:
#     sql = f"select BackboneScarID from BackboneScarTable where BackboneID = {each[0]};"
#     cur.execute(sql)
#     partscarResult = cur.fetchall()
#     for index in range(1,len(partscarResult)):
#         sql = f"delete from backbonescartable where backbonescarid = {partscarResult[index][0]}"
#         cur.execute(sql)
#         conn.commit()
# conn.commit()P





# plasmid_id = 1
# sql = f"select sequenceconfirm from plasmidneed where plasmidid = {plasmid_id};"
# cur.execute(sql)
# seqResult = cur.fetchall()[0]
# plasmid_seq = seqResult[0]
# kmer = KmerIndex()
# kmer.add_sequence("pSC101",newPSC101Seq)
# kmerResult = kmer.query(plasmid_seq)
# start = kmerResult['pSC101']['start']
# end = kmerResult["pSC101"]['end']
# newsequence = plasmid_seq[:start] + newPSC101Seq + plasmid_seq[end:]
# print(newsequence)

# sql = "begin;"
# sql = "select backbone_id from backbone_culture_functions where function_content = 'pSC101'"
# cur.execute(sql)
# result = cur.fetchall()
# # print(result)
# newPSC101Seq = "ACGGGTTTTGCTGCCCGCAAACGGGCTGTTCTGGTGTTGCTAGTTTGTTATCAGAATCGCAGATCCGGCTTCAGCCGGTTTGCCGGCTGAAAGCGCTATTTCTTCCAGAATTGCCATGATTTTTTCCCCACGGGAGGCGTCACTGGCTCCCGTGTTGTCGGCAGCTTTGATTCGATAAGCAGCATCGCCTGTTTCAGGCTGTCTATGTGTGACTGTTGAGCTGTAACAAGTTGTCTCAGGTGTTCAATTTCATGTTCTAGTTGCTTTGTTTTACTGGTTTCACCTGTTCTATTAGGTGTTACATGCTGTTCATCTGTTACATTGTCGATCTGTTCATGGTGAACAGCTTTgAATGCACCAAAAACTCGTAAAAGCTCTGATGTATCTATCTTTTTTACACCGTTTTCATCTGTGCATATGGACAGTTTTCCCTTTGATATgTAACGGTGAACAGTTGTTCTACTTTTGTTTGTTAGTCTTGATGCTTCACTGATAGATACAAGAGCCATAAGAACCTCAGATCCTTCCGTATTTAGCCAGTATGTTCTCTAGTGTGGTTCGTTGTTTTTGCGTGAGCCATGAGAACGAACCATTGAGATCATaCTTACTTTGCATGTCACTCAAAAATTTTGCCTCAAAACTGGTGAGCTGAATTTTTGCAGTTAAAGCATCGTGTAGTGTTTTTCTTAGTCCGTTAtGTAGGTAGGAATCTGATGTAATGGTTGTTGGTATTTTGTCACCATTCATTTTTATCTGGTTGTTCTCAAGTTCGGTTACGAGATCCATTTGTCTATCTAGTTCAACTTGGAAAATCAACGTATCAGTCGGGCGGCCTCGCTTATCAACCACCAATTTCATATTGCTGTAAGTGTTTAAATCTTTACTTATTGGTTTCAAAACCCATTGGTTAAGCCTTTTAAACTCATGGTAGTTATTTTCAAGCATTAACATGAACTTAAATTCATCAAGGCTAATCTCTATATTTGCCTTGTGAGTTTTCTTTTGTGTTAGTTCTTTTAATAACCACTCATAAATCCTCATAGAGTATTTGTTTTCAAAAGACTTAACATGTTCCAGATTATATTTTATGAATTTTTTTAACTGGAAAAGATAAGGCAATATCTCTTCACTAAAAACTAATTCTAATTTTTCGCTTGAGAACTTGGCATAGTTTGTCCACTGGAAAATCTCAAAGCCTTTAACCAAAGGATTCCTGATTTCCACAGTTCTCGTCATCAGCTCTCTGGTTGCTTTAGCTAATACACCATAAGCATTTTCCCTACTGATGTTCATCATCTGAGCGTATTGGTTATAAGTGAACGATACCGTCCGTTCTTTCCTTGTAGGGTTTTCAATCGTGGGGTTGAGTAGTGCCACACAGCATAAAATTAGCTTGGTTTCATGCTCCGTTAAGTCATAGCGACTAATCGCTAGTTCATTTGCTTTGAAAACAACTAATTCAGACATACATCTCAATTGGTCTAGGTGATTTTAATCACTATACCAATTGAGATGGGCTAGTCAATGATAATTACTAGTCCTTTTCCTTTGAGTTGTGGGTATCTGTAAATTCTGCTAGACCTTTGCTGGAAAACTTGTAAATTCTGCTAGACCCTCTGTAAATTCCGCTAGACCTTTGTGTGTTTTTTTTGTTTATATTCAAGTGGTTATAATTTATAGAATAAAGAAAGAATAAAAAAAGATAAAAAGAATAGATCCCAGCCCTGTGTATAACTCACTACTTTAGTCAGTTCCGCAGTATTACAAAAGGATGTCGCAAACGCTGTTTGCTCCTCTACAAAACAGACCTTAAAACCCTAAAGGCTTAAGTAGCACCCTCGCAAGCTCGGGCAAATCGCTGAATATTCCTTTTGTCTCCGACCATCAGGCACCTGAGTCGCTGTCTTTTTCGTGACATTCAGTTCGCTGCGCTCACGGCTCTGGCAGTGAATGGGGGTAAATGGCACTACAGGCGCCTTTTATGGATTCATGCAAGGAAACTACCCATAATACAAGAAAAGCCCGTCACGGGCTTCTCAGGGCGTTTTATGGCGGGTCTGCTATGTGGTGCTATCTGACTTTTTGCTGTTCAGCAGTTCCTGCCCTCTGATTTTCCAGTCTGACCACTTCGGATTATCCCGTGACAGGTCATTCAGACTGGCTAATGCACCCAGTAAGGCAGCGGTATCATCAACAGGCTTACCCGTCTTACTGTC"
# kmer = KmerIndex()
# kmer.add_sequence("pSC101",newPSC101Seq)
# for each_plasmid in result:
#     plasmid_id = each_plasmid[0]
#     sql = f"select sequence from backbonetable where id = {plasmid_id};"
#     cur.execute(sql)
#     seqResult = cur.fetchall()[0]
#     plasmid_seq = seqResult[0]
#     try:
#         kmerResult = kmer.query(plasmid_seq)
#         start = kmerResult['pSC101']['start']
#         end = kmerResult["pSC101"]['end']
#         newsequence = plasmid_seq[:start] + newPSC101Seq + plasmid_seq[end:]
#         sql = f"update backbonetable set sequence = '{newsequence}' where id = {plasmid_id};"
#         cur.execute(sql)
#         conn.commit()
#     except Exception as e:
#         print(kmerResult)
#         print(plasmid_id)
# for each in result:
#     # result = ScarIdentify.scarPosition(each[2])
#     # print(result)
#     # noScarSequence = each[1][result[2]['BbsI']['index'][0]+3 : result[2]['BbsI']['index'][1]-1]
#     # print(noScarSequence)
#     try:
#         result = ScarIdentify.scarPosition(each[2])
#         noScarSequence = each[1][result[1]['BsaI']['index'][0]+3 : result[1]['BsaI']['index'][1]-1]
#         # print(noScarSequence)
#         # sql = f"update parttable set level0sequence = '{noScarSequence}' where partid = {each[0]};"
#         # cur.execute(sql)
#     except Exception as e:
#         try:
#             result = ScarIdentify.scarPosition(each[2])
#             noScarSequence = each[1][result[2]['BbsI']['index'][0]+3 : result[2]['BbsI']['index'][1]-1]
#             # print(noScarSequence)
#             # sql = f"update parttable set level0sequence = '{noScarSequence}' where partid = {each[0]};"
#             # cur.execute(sql)
#         except Exception as e:
#             sql = f"update parttable set tag = 'abnormal' where partid = {each[0]}"
#             cur.execute(sql)
# conn.commit()
            
            
#     sql2 = f"update parttable set tag = 'normal' where partid = {each[0]};"
#     cur.execute(sql2)
# sql = "begin;"
# sql = "select plasmidid from plasmidneed;"
# cur.execute(sql)
# result = cur.fetchall()
# for each_id in result:
#     sql_t = f"select pcfid,function_content from plasmid_culture_functions where plasmid_id = {each_id[0]} and function_type = \"marker\";"
#     print(sql_t)
#     cur.execute(sql_t)
#     result_t = cur.fetchall()
#     result_list = set()
#     for each in result_t:
#         if(result_list.__contains__(each[1]) == False):
#             sql_2 = f"delete from plasmid_culture_functions where pcfid = {each[0]};"
#             cur.execute(sql_2)
#         else:
#             result_list.add(each[1])
# cur.execute("rollback;")
# conn.commit()
# from FeatureIdentify import featureIdentify
# # from LabDatabase.CaculateModule.FileGenerator import SequenceAnnotator
# from FileGenerator import SequenceAnnotator
seq_obj = Seq("ggcttactaaaagccagataacagtatgcatatttgcgcgctgatttttgcggtataagaatatatactgatatgtatacccgaagtatgtcaaaaagaggtatgctatgaagcagcgtattacagtgacagttgacagcgacagctatcagttgctcaaggcatatatgatgtcaatatctccggtctggtaagcacaaccatgcagaatgaagcccgtcgtctgcgtgccgaacgctggaaagcggaaaatcaggaagggatggctgaggtcgcccggtttattgaaatgaacggctcttttgctgacgagaacaggggctggtgaaatgcagtttaaggtttacacctataaaagagagagccgttatcgtctgtttgtggatgtacagagtgatattattgacacgcccgggcgacggatggtgatccccctggccagtgcacgtctgctgtcagataaagtctcccgtgaactttacccggtggtgcatatcggggatgaaagctggcgcatgatgaccaccgatatggccagtgtgccggtttccgttatcggggaagaagtggctgatctcagccaccgcgaaaatgacatcaaaaacgccattaacctgatgttctggggaatataa")
print(str(seq_obj.reverse_complement()))
# from ScarIdentify import ScarIdentify, scarFunction, scarPosition

# seq = "TTATGACAACTTGACGGCTACATCATTCACTTTTTCTTCACAACCGGCACGGAACTCGCTCGGGCTGGCCCCGGTGCATTTTTTAAATACCCGCGAGAAATAGAGTTGATCGTCAAAACCAACATTGCGACCGACGGTGGCGATAGGCATCCGGGTGGTGCTCAAAAGCAGCTTCGCCTGGCTGATACGTTGGTCCTCGCGCCAGCTTAAGACGCTAATCCCTAACTGCTGGCGGAAAAGATGTGACAGACGCGACGGCGACAAGCAAACATGCTGTGCGACGCTGGCGATATCAAAATTGCTGTCTGCCAGGTGATCGCTGATGTACTGACAAGCCTCGCGTACCCGATTATCCATCGGTGGATGGAGCGACTCGTTAATCGCTTCCATGCGCCGCAGTAACAATTGCTCAAGCAGATTTATCGCCAGCAGCTCCGAATAGCGCCCTTCCCCTTGCCCGGCGTTAATGATTTGCCCAAACAGGTCGCTGAAATGCGGCTGGTGCGCTTCATCCGGGCGAAAGAACCCCGTATTGGCAAATATTGACGGCCAGTTAAGCCATTCATGCCAGTAGGCGCGCGGACGAAAGTAAACCCACTGGTGATACCATTCGCGAGCCTCCGGATGACGACCGTAGTGATGAATCTCTCCTGGCGGGAACAGCAAAATATCACCCGGTCGGCAAACAAATTCTCGTCCCTGATTTTTCACCACCCCCTGACCGCGAATGGTGAGATTGAGAATATAACCTTTCATTCCCAGCGGTCGGTCGATAAAAAAATCGAGATAACCGTTGGCCTCAATCGGCGTTAAACCCGCCACCAGATGGGCATTAAACGAGTATCCCGGCAGCAGGGGATCATTTTGCGCTTCAGCCAT"
# print(seq.upper())
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

# text = "AAAAAAAAPart(Ptet)Part( BCD2)Part(fluc)Part(DT100)Backbone(CQM007)Plasmid(XJL38)Plasmid(XJL39)Plasmid(XJL40)Plasmid(GFW60)"
# pattern = r'(\w+)\(([ a-zA-z0-9]+)\)'
# matches = re.findall(pattern, text)
# result = {
#     "parts":[],
#     "backbones":[],
#     "plasmid":[],
# }
# for component_type, letter in matches:
#     if(component_type == 'Part'):
#         result
# print(matches)
