from Bio import Restriction
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord


'''
Scar  标识
GTGC   A
GCAC

ATCA   A2
TGAT

AATG   B
CATT

TAAA   C
TTTA

CCTC   D
GAGG

GCTT   E
AAGC

CTGA   F
TCAG

TACG   G
CGTA

TTCC   H
GGAA

AGGT   I
ACCT

CACC   J
GGTG

TGTC   K
GACA

CGCT   L
AGCG

CCGT   M
ACGG

TTTT   T
AAAA

CGAG   Y
CTCG

TAAC   Z
ATTG

'''

type2s_enzymes = ["BsmBI","BsaI","BbsI","AarI","SapI"]


def _normalize_circular_index(index, seq_len):
    if seq_len <= 0:
        return index
    return index % seq_len


def _circular_slice(seq, start, end):
    seq_len = len(seq)
    if seq_len == 0:
        return ""

    normalized_start = start % seq_len
    normalized_end = end % seq_len
    slice_len = end - start
    if slice_len <= 0:
        return ""

    if slice_len >= seq_len:
        repeats = (slice_len // seq_len) + 2
        expanded_seq = seq * repeats
        return expanded_seq[normalized_start:normalized_start + slice_len]

    if normalized_start < normalized_end:
        return seq[normalized_start:normalized_end]
    return seq[normalized_start:] + seq[:normalized_end]
class ScarIdentify:
    def __init__(self, Sequence):
        self.Sequence = Sequence
        self.Part = SeqRecord(Seq(self.Sequence),id="test",name="test",description="test")
    
    def number_of_site(self,enzyme):
        linear = False
        return enzyme.search(self.Part.seq,linear=linear)

    def enzyme_fit_score(self,enzyme_name):
        enzyme = Restriction.__dict__[enzyme_name]
        Site = self.number_of_site(enzyme)
        if(len(Site) == 2):
            scar = {"start":self.Part.seq[Site[0]-1:Site[0]+3],"end":self.Part.seq[Site[1]-1:Site[1]+3]}
        else:
            scar = {"start":"","end":""}
        return {"enzyme_name":enzyme, "site_number":len(Site),"Scar":scar}
        # return self.number_of_site(enzyme)
    def enzyme_position_fit(self,enzyme_name):
        enzyme = Restriction.__dict__[enzyme_name]
        Site = self.number_of_site(enzyme)
        if(len(Site) % 2 == 0):
            return Site
        else:
            return []

def scarPosition(seq):
    SI = ScarIdentify(seq)
    scar_list = []
    for enzyme in type2s_enzymes:
        scar = SI.enzyme_position_fit(enzyme)
        
        scar_name_list = []
        for each_position in scar:
            each_str = scarName(seq[each_position-1:each_position+3])
            scar_name_list.append(each_str)
        scar_list.append({enzyme:{"index":scar,"name":scar_name_list}})
    print(scar_list)
    return scar_list

def scarIdentSitePosition(seq):
    
    SI = ScarIdentify(seq)
    scar_list = []
    seq_len = len(seq)
    for enzyme in type2s_enzymes:
        scar = SI.enzyme_position_fit(enzyme)
        print(scar)
        scar_position_list = []
        scar_name_list = []
        for each_position in scar:
            print(seq[each_position-1:each_position+3])
            each_str = scarName(seq[each_position-1:each_position+3])
            print(each_str)
            before_index = -1
            if(str(enzyme) == "BsaI"):
                scar_before_start_index = each_position - 8
                scar_before_end_index = each_position - 2
                if(_circular_slice(seq, scar_before_start_index, scar_before_end_index).upper() == "GGTCTC"):
                    before_index = _normalize_circular_index(scar_before_start_index, seq_len)
                scar_front_start_index = each_position + 4
                scar_front_end_index = each_position + 10
                if(_circular_slice(seq, scar_front_start_index, scar_front_end_index).upper() == "GAGACC"):
                    before_index = _normalize_circular_index(scar_front_start_index, seq_len)
            elif(enzyme == "BbsI"):
                scar_before_start_index = each_position - 9
                scar_before_end_index = each_position - 3
                print(f"before:{_circular_slice(seq, scar_before_start_index, scar_before_end_index)}")
                if(_circular_slice(seq, scar_before_start_index, scar_before_end_index).upper() == "GAAGAC"):
                    before_index = _normalize_circular_index(scar_before_start_index, seq_len)
                scar_front_start_index = each_position + 5
                scar_front_end_index = each_position + 11
                if(_circular_slice(seq, scar_front_start_index, scar_front_end_index).upper() == "GTCTTC"):
                    before_index = _normalize_circular_index(scar_front_start_index, seq_len)
            elif(enzyme == "BsmBI"):
                scar_before_start_index = each_position - 8
                scar_before_end_index = each_position - 2
                if(_circular_slice(seq, scar_before_start_index, scar_before_end_index).upper() == "CGTCTC"):
                    before_index = _normalize_circular_index(scar_before_start_index, seq_len)
                scar_front_start_index = each_position + 4
                scar_front_end_index = each_position + 10
                if(_circular_slice(seq, scar_front_start_index, scar_front_end_index).upper() == "GAGACG"):
                    before_index = _normalize_circular_index(scar_front_start_index, seq_len)
            elif(enzyme == "AarI"):
                scar_before_start_index = each_position - 12
                scar_before_end_index = each_position - 5
                if(_circular_slice(seq, scar_before_start_index, scar_before_end_index).upper() == "CACCTGC"):
                    before_index = _normalize_circular_index(scar_before_start_index, seq_len)
                scar_front_start_index = each_position + 7
                scar_front_end_index = each_position + 14
                if(_circular_slice(seq, scar_front_start_index, scar_front_end_index).upper() == "GCAGGTG"):
                    before_index = _normalize_circular_index(scar_front_start_index, seq_len)
            elif(enzyme == "SapI"):
                scar_before_start_index = each_position - 9
                scar_before_end_index = each_position - 2
                if(_circular_slice(seq, scar_before_start_index, scar_before_end_index).upper() == "GCTCTTC"):
                    before_index = _normalize_circular_index(scar_before_start_index, seq_len)
                scar_front_start_index = each_position + 3
                scar_front_end_index = each_position + 10
                if(_circular_slice(seq, scar_front_start_index, scar_front_end_index).upper() == "GAAGAGC"):
                    before_index = _normalize_circular_index(scar_front_start_index, seq_len)
            if(before_index != -1):
                scar_name_list.append(each_str)
                scar_position_list.append(before_index)
        scar_list.append({enzyme:{"index":scar_position_list,"name":scar_name_list}})
    return scar_list

    
    

def scarName(seq):
    scar_str = ""
    if(seq.upper() == "GCTT"):
        scar_str = "E"
    elif(seq.upper() == "CTGA"):
        scar_str += "F"
    elif(seq.upper() == "TACG"):
        scar_str = "G"
    elif(seq.upper() == "TTCC"):
        scar_str += "H"
    elif(seq.upper() == "GTGC"):
        scar_str += "A"
    elif(seq.upper() == "ATCA"):
        scar_str += "A2"
    elif(seq.upper() == "AATG"):
        scar_str += "B"
    elif(seq.upper() == "TAAA"):
        scar_str += "C"
    elif(seq.upper() == "CCTC"):
        scar_str += "D"
    elif(seq.upper() == "AGGT"):
        scar_str += "I"
    elif(seq.upper() == "CACC"):
        scar_str += "J"
    elif(seq.upper() == "TGTC"):
        scar_str += "K"
    elif(seq.upper() == "CGCT"):
        scar_str += "L"
    elif(seq.upper() == "CCGT"):
        scar_str += "M"
    elif(seq.upper() == "TTTT"):
        scar_str += "T"
    elif(seq.upper() == "CGAG"):
        scar_str += "Y"
    elif(seq.upper() == "GTTA"):
        scar_str += "Z"
    elif(seq.upper() == "TAAC"):
        scar_str += "Z"
    elif(seq.upper() == "GCAC"):
        scar_str += "A"
    elif(seq.upper() == "TGAT"):
        scar_str += "A2"
    elif(seq.upper() == "CATT"):
        scar_str += "B"
    elif(seq.upper() == "TTTA"):
        scar_str += "C"
    elif(seq.upper() == "GAGG"):
        scar_str += "D"
    elif(seq.upper() == "AAGC"):
        scar_str += "E"
    elif(seq.upper() == "TCAG"):
        scar_str += "F"
    elif(seq.upper() == "CGTA"):
        scar_str += "G"
    elif(seq.upper() == "TTCC"):
        scar_str += "H"
    elif(seq.upper() == "ACCT"):
        scar_str += "I"
    elif(seq.upper() == "GGTG"):
        scar_str += "J"
    elif(seq.upper() == "GACA"):
        scar_str += "K"
    elif(seq.upper() == "AGCG"):
        scar_str += "L"
    elif(seq.upper() == "ACGG"):
        scar_str += "M"
    elif(seq.upper() == "AAAA"):
        scar_str += "T"
    elif(seq.upper() == "CTCG"):
        scar_str += "Y"
    elif(seq.upper() == "ATTG"):
        scar_str += "Z"
    else:
        scar_str = "undefine"
    return scar_str

def scarFunction(seq):

    SI = ScarIdentify(seq)
    scar_list = []
    for enzyme in type2s_enzymes:
        NoSite = SI.enzyme_fit_score(enzyme)
        scar_str = ""
        if(NoSite['site_number'] == 2):
            if(NoSite["Scar"]["start"].upper() == "GCTT"):
                scar_str += "E"
            elif(NoSite["Scar"]["start"].upper() == "CTGA"):
                scar_str += "F"
            elif(NoSite["Scar"]["start"].upper() == "TACG"):
                scar_str += "G"
            elif(NoSite["Scar"]["start"].upper() == "TTCC"):
                scar_str += "H"
            elif(NoSite["Scar"]["start"].upper() == "GTGC"):
                scar_str += "A"
            elif(NoSite["Scar"]["start"].upper() == "ATCA"):
                scar_str += "A2"
            elif(NoSite["Scar"]["start"].upper() == "AATG"):
                scar_str += "B"
            elif(NoSite["Scar"]["start"].upper() == "TAAA"):
                scar_str += "C"
            elif(NoSite["Scar"]["start"].upper() == "CCTC"):
                scar_str += "D"
            elif(NoSite["Scar"]["start"].upper() == "AGGT"):
                scar_str += "I"
            elif(NoSite['Scar']["start"].upper() == "CACC"):
                scar_str += "J"
            elif(NoSite['Scar']["start"].upper() == "TGTC"):
                scar_str += "K"
            elif(NoSite['Scar']["start"].upper() == "CGCT"):
                scar_str += "L"
            elif(NoSite['Scar']["start"].upper() == "CCGT"):
                scar_str += "M"
            elif(NoSite['Scar']["start"].upper() == "TTTT"):
                scar_str += "T"
            elif(NoSite['Scar']["start"].upper() == "CGAG"):
                scar_str += "Y"
            elif(NoSite['Scar']["start"].upper() == "TAAC"):
                scar_str += "Z"
            
            elif(NoSite['Scar']["start"].upper() == "GCAC"):
                scar_str += "A"
            elif(NoSite['Scar']["start"].upper() == "TGAT"):
                scar_str += "A2"
            elif(NoSite['Scar']["start"].upper() == "CATT"):
                scar_str += "B"
            elif(NoSite['Scar']["start"].upper() == "TTTA"):
                scar_str += "C"
            elif(NoSite['Scar']["start"].upper() == "GAGG"):
                scar_str += "D"
            elif(NoSite['Scar']["start"].upper() == "AAGC"):
                scar_str += "E"
            elif(NoSite['Scar']["start"].upper() == "TCAG"):
                scar_str += "F"
            elif(NoSite['Scar']["start"].upper() == "CGTA"):
                scar_str += "G"
            elif(NoSite['Scar']["start"].upper() == "TTCC"):
                scar_str += "H"
            elif(NoSite['Scar']["start"].upper() == "ACCT"):
                scar_str += "I"
            elif(NoSite['Scar']["start"].upper() == "GGTG"):
                scar_str += "J"
            elif(NoSite['Scar']["start"].upper() == "GACA"):
                scar_str += "K"
            elif(NoSite['Scar']["start"].upper() == "AGCG"):
                scar_str += "L"
            elif(NoSite['Scar']["start"].upper() == "ACGG"):
                scar_str += "M"
            elif(NoSite['Scar']["start"].upper() == "AAAA"):
                scar_str += "T"
            elif(NoSite['Scar']["start"].upper() == "CTCG"):
                scar_str += "Y"
            elif(NoSite['Scar']["start"].upper() == "ATTG"):
                scar_str += "Z"
                
                
                
            if(NoSite["Scar"]["end"].upper() == "CTGA"):
                scar_str += "F"
            elif(NoSite["Scar"]["end"].upper() == "TACG"):
                scar_str += "G"
            elif(NoSite["Scar"]["end"].upper() == "TTCC"):
                scar_str += "H"
            elif(NoSite["Scar"]["end"].upper() == "AGGT"):
                scar_str += "I"
            elif(NoSite["Scar"]["end"].upper() == "TGTC"):
                scar_str += "K"
            elif(NoSite["Scar"]["end"].upper() == "CCTC"):
                scar_str += "D"
            elif(NoSite["Scar"]["end"].upper() == "GTGC"):
                scar_str += "A"
            elif(NoSite["Scar"]["end"].upper() == "ATCA"):
                scar_str += "A2"
            elif(NoSite["Scar"]["end"].upper() == "AATG"):
                scar_str += "B"
            elif(NoSite["Scar"]["end"].upper() == "TAAA"):
                scar_str += "C"
            elif(NoSite["Scar"]["end"].upper() == "CCTC"):
                scar_str += "D"
            elif(NoSite["Scar"]["end"].upper() == "GCTT"):
                scar_str += "E"
            elif(NoSite["Scar"]["end"].upper() == "AGGT"):
                scar_str += "I"
            elif(NoSite['Scar']["end"].upper() == "CACC"):
                scar_str += "J"
            elif(NoSite['Scar']["end"].upper() == "TGTC"):
                scar_str += "K"
            elif(NoSite['Scar']["end"].upper() == "CGCT"):
                scar_str += "L"
            elif(NoSite['Scar']["end"].upper() == "CCGT"):
                scar_str += "M"
            elif(NoSite['Scar']['end'].upper() == "TTTT"):
                scar_str += "T"
            elif(NoSite['Scar']["end"].upper() == "CGAG"):
                scar_str += "Y"
            elif(NoSite['Scar']["end"].upper() == "TAAC"):
                scar_str += "Z"
            
            elif(NoSite['Scar']["end"].upper() == "GCAC"):
                scar_str += "A"
            elif(NoSite['Scar']["end"].upper() == "TGAT"):
                scar_str += "A2"
            elif(NoSite['Scar']["end"].upper() == "CATT"):
                scar_str += "B"
            elif(NoSite['Scar']["end"].upper() == "TTTA"):
                scar_str += "C"
            elif(NoSite['Scar']["end"].upper() == "GAGG"):
                scar_str += "D"
            elif(NoSite['Scar']["end"].upper() == "AAGC"):
                scar_str += "E"
            elif(NoSite['Scar']["end"].upper() == "TCAG"):
                scar_str += "F"
            elif(NoSite['Scar']["end"].upper() == "CGTA"):
                scar_str += "G"
            elif(NoSite['Scar']["end"].upper() == "TTCC"):
                scar_str += "H"
            elif(NoSite['Scar']["end"].upper() == "ACCT"):
                scar_str += "I"
            elif(NoSite['Scar']["end"].upper() == "GGTG"):
                scar_str += "J"
            elif(NoSite['Scar']["end"].upper() == "GACA"):
                scar_str += "K"
            elif(NoSite['Scar']["end"].upper() == "AGCG"):
                scar_str += "L"
            elif(NoSite['Scar']["end"].upper() == "ACGG"):
                scar_str += "M"
            elif(NoSite['Scar']["end"].upper() == "AAAA"):
                scar_str += "T"
            elif(NoSite['Scar']["end"].upper() == "CTCG"):
                scar_str += "Y"
            elif(NoSite['Scar']["end"].upper() == "ATTG"):
                scar_str += "Z"
        if(scar_str == ""):
            scar_list.append("-")
        else:
            scar_list.append(scar_str)
    return scar_list



if __name__ == "__main__":
    print(scarPosition("cctcctgagaaatctgctcgtcagtggtgctcacactgacgaatcatgtacagatcataccgatgactgcctggcgactcacaactaagcaagacagccggaaccagcgccggcgaacaccactgcatatatggcatatcacaacagtccacgtctcaagcagttacagagatgttacgaaccactagtgcactgcagtacaagcttgccttgtccccgccgggtcacccggccagcgacatggaggcccagaataccctccttgacagtcttgacgtgcgcagctcaggggcatgatgtgactgtcgcccgtacatttagcccatacatccccatgtataatcatttgcatccatacattttgatggccgcacggcgcgaagcaaaaattacggctcctcgctgcagacctgcgagcagggaaacgctcccctcacagacgcgttgaattgtccccacgccgcgcccctgtagagaaatataaaaggttaggatttgccactgaggttcttctttcatatacttccttttaaaatcttgctaggatacagttctcacatcacatccgaacataaacaacaatgacagtcaacactaagacctatagtgagagagcagaaactcatgcctcaccagtagcacaacgattatttcgattaatggaactgaagaaaaccaatttatgtgcatcaattgatgttgataccactaaggaattccttgaattaattgataaattgggtccttatgtatgcttaatcaagacacatattgatataatcaatgatttttcctatgaatccactattgaaccattattagaactttcacgtaaacatcaatttatgatttttgaagatagaaaatttgctgatattggtaataccgtgaagaaacaatatattggtggagtttataaaattagtagttgggcagatattactaatgctcatggtgtcactgggaatggagtagttgaaggattaaaacagggagctaaagaaaccaccaccaaccaagagccaagagggttattgatgttagctgaattatcatcagtgggatcattagcatatggagaatattctcaaaaaactgttgaaattgctaaatccgataaggaatttgttattggatttattgcccaacgtgatatgggtggacaagaagaaggatttgattggcttattatgacacctggagttggattagatgataaaggtgatggattaggacaacaatatagaactgttgatgaagttgttagcactggaactgatattatcattgttggtagaggattgtttggtaaaggaagagatccagatattgaaggtaaaaggtatagagatgctggttggaatgcttatttgaaaaagactggccaattataaacagtactgacaataaaaagattcttgttttcaagaacttgtcatttgtatagtttttttatattgtagttgttctattttaatcaaatgttagcgtgatttatattttttttcgcctcgacatcatctgcccagatgcgaagttaagtgcgcagaaagtaatatcatgcgtcaatcgtatgtgaatgctggtcgctatactgctgtcgattcgatactaacgccgccatccagtgtcgagagtagagcacttgaatccactgccccgggaatctcggtcgtaatgatttctataatgacgaaaaaaaaaaaattggaaagaaaaagcttcatggcctttataaaaaggaactatccaatacctcgccagaaccaagtaacagtattttacggggcacaaatcaagaacaataagacaggactgtaaagatggacgcattgaactccaaagaacaacaagagttccaaaaagtagtggaacaaaagcaaatgaaggatttcatgcgtttgtactctaatctggtagaaagatgtttcacagactgtgtcaatgacttcacaacatcaaagctaaccaataaggaacaaacatgcatcatgaagtgctcagaaaagttcttgaagcatagcgaacgtgtagggcagcgtttccaagaacaaaacgctgccttgggacaaggcttgggccgataaggtgtactggcgtatatatatctaattatgtatctctggtgtagcccatttttagcatgtaaatataaagaagagacctatcagctcactcaaaggcggtaatacggttatccacagaatcaggggataacgcaggaaagaacatgtgagcaaaaggccagcaaaaggccaggaaccgtaaaaaggccgcgttgctggcgtttttccataggctccgcccccctgacgagcatcacaaaaatcgacgctcaagtcagaggtggcgaaacccgacaggactataaagataccaggcgtttccccctggaagctccctcgtgcgctctcctgttccgaccctgccgcttaccggatacctgtccgcctttctcccttcgggaagcgtggcgctttctcatagctcacgctgtaggtatctcagttcggtgtaggtcgttcgctccaagctgggctgtgtgcacgaaccccccgttcagcccgaccgctgcgccttatccggtaactatcgtcttgagcccaacccggtaagacacgacttatcgccactggcagcagccactggtaacaggattagcagagcgaggtatgtaggcggtgctacagagttcttgaagtggtggcctaactacggctacactagaagaacagtatttggtatctgcgctctgctgaagccagttaccttcggaaaaagagttggtagctcttgatccggcaaacaaaccaccgctggtagcggtggtttttttgtttgcaagcagcagattacgcgcagaaaaaaaggatctcaagaagatcctttgatcttttctacggggtctgacgctcagtggaacgaaaactcacgttaagggattttggtcatgagattatcaaaaagtatcttcacctagatccttttaaattaaaaatgaagttttaaatcaatctaaagtatatatgagtaaacttggtctgacagagttctgaggtcattactggatctatcaacagcagtccaagcgagctcgatatcaaattacgccccgccctgccactcatcgcagtactgttgtaattcattaagcattctgccgacatggaagccatcacaaacggcatgatgaacctgaatcgccagcggcatcagcaccttgtcgccttgcgtataatatttgcccatggtgaaaacgggggcgaagaagttgtccatattggccacgtttaaatcaaaactggtgaaactcacccagggattggctgagacgaaaaacatattctcaataaaccctttagggaaataggccaggttttcaccgtaacacgccacatcttgcgaatatatgtgtagaaactgccggaaatcgtcgtggtattcactccagagcgatgaaaacgtttcagtttgctcatggaaaacggtgtaacaagggtgaacactatcccatatcaccagctcaccgtctttcattgccatacgaaattccggatgagcattcatcaggcgggcaagaatgtgaataaaggccggataaaacttgtgcttatttttctttacggtctttaaaaaggccgtaatatccagctgaacggtctggttataggtacattgagcaactgactgaaatgcctcaaaatgttctttacgatgccattgggatatatcaacggtggtatatccagtgatttttttctccattttagcttccttagctcctgaaaatctcgataactcaaaaaatacgcccggtagtgatcttatttcattatggtgaaagttggaacctcttacgtgcccgatcaactcgcgcgtttgccacctgacgtctaagaaaaggaatattcagcaatttgcccgtgccgaagaaaggcccacccgtgaaggtgagccggtctcggctaaattcgagtgaaacacaggaagatcagaaaatcctcatttcatccatattaacaataatttcaaatgtttatttgcattatttgaaactaggcaagacaagcaacgaaacgtttttgaaaattttgagtattttcaataaatttgtagaggactcagatattgaaaaaaagctacagcaattaatacttgataagaagagtattgagaagggcaacggttcatcatctcatggatctgcacatgaacaaacaccagagtcaaacgacgttgaaattgaggctactgcgccaattgatgacaatacagacgatgataacaaaccgaagttatctgatgtagaaaaggattaaagatgctaagagatagtgatgatatttcataaataatgtaattctatatatgttaattaccttttttgcgaggcatatttatggtgaaggataagttttgaccatcaaagaaggttaatgtggctgtggtttcagggtccataaagcccacatggataacattacgcttgctatgtcgtcggaggagatatttattacttttattattctagttttttacagttatttattaattaattatttttatatgcatgcgaataaaaagtctatatttaagttcttttatttattaatacattttcctctacgagctgtcaccggatgtgctttccggtctgatgagtccgtgaggacgaaacagcctctacaaataattttgtttaagagcaggttgttcatggccgtgcgtatgatgtggggggctcgggcgttgaaaccggggttcggagcgccaggggggtgcttttttattttgttttttttttgcagtataaaaagttagtttgtttaaacaacaaacttttttcatttcttttgtttccccttctcttcttttagttagtttgtttaaacaacaaactagaatatcaagctacaaaaataaataaaaaatgtctaaaggtgaagaattattcactggtgttgtcccaattttggttgaattagatggtgatgttaatggtcacaaattttctgtctccggtgaaggtgaaggtgatgctacttacggtaaattgaccttaaaatttatttgtactactggtaaattgccagttccatggccaaccttagtcactactttaggttatggtttgatgtgttttgctagatacccagatcatatgaaacaacatgactttttcaagtctgccatgccagaaggttatgttcaagaaagaactatttttttcaaagatgacggtaactacaagaccagagctgaagtcaagtttgaaggtgataccttagttaatagaatcgaattaaaaggtattgattttaaagaagatggtaacattttaggtcacaaattggaatacaactataactctcacaatgtttacatcatggctgacaaacaaaagaatggtatcaaagttaacttcaaaattagacacaacattgaagatggttctgttcaattagctgaccattatcaacaaaatactccaattggtgatggtccagtcttgttaccagacaaccattacttatcctatcaatctagattatccaaagatccaaacgaaaagagggatcacatggtcttgttagaatttgttactgctgctggtattacccatggtatggatgaattgtacaaataataaatggtcttcggcttactaaaagccagataacagtatgcatatttgcgcgctgatttttgcggtataagaatatatactgatatgtatacccgaagtatgtcaaaaagaggtatgctatgaagcagcgtattacagtgacagttgacagcgacagctatcagttgctcaaggcatatatgatgtcaatatctccggtctggtaagcacaaccatgcagaatgaagcccgtcgtctgcgtgccgaacgctggaaagcggaaaatcaggaagggatggctgaggtcgcccggtttattgaaatgaacggctcttttgctgacgagaacaggggctggtgaaatgcagtttaaggtttacacctataaaagagagagccgttatcgtctgtttgtggatgtacagagtgatattattgacacgcccgggcgacggatggtgatccccctggccagtgcacgtctgctgtcagataaagtctcccgtgaactttacccggtggtgcatatcggggatgaaagctggcgcatgatgaccaccgatatggccagtgtgccggtttccgttatcggggaagaagtggctgatctcagccaccgcgaaaatgacatcaaaaacgccattaacctgatgttctggggaatataagaagacta"))
    print(scarIdentSitePosition("cctcctgagaaatctgctcgtcagtggtgctcacactgacgaatcatgtacagatcataccgatgactgcctggcgactcacaactaagcaagacagccggaaccagcgccggcgaacaccactgcatatatggcatatcacaacagtccacgtctcaagcagttacagagatgttacgaaccactagtgcactgcagtacaagcttgccttgtccccgccgggtcacccggccagcgacatggaggcccagaataccctccttgacagtcttgacgtgcgcagctcaggggcatgatgtgactgtcgcccgtacatttagcccatacatccccatgtataatcatttgcatccatacattttgatggccgcacggcgcgaagcaaaaattacggctcctcgctgcagacctgcgagcagggaaacgctcccctcacagacgcgttgaattgtccccacgccgcgcccctgtagagaaatataaaaggttaggatttgccactgaggttcttctttcatatacttccttttaaaatcttgctaggatacagttctcacatcacatccgaacataaacaacaatgacagtcaacactaagacctatagtgagagagcagaaactcatgcctcaccagtagcacaacgattatttcgattaatggaactgaagaaaaccaatttatgtgcatcaattgatgttgataccactaaggaattccttgaattaattgataaattgggtccttatgtatgcttaatcaagacacatattgatataatcaatgatttttcctatgaatccactattgaaccattattagaactttcacgtaaacatcaatttatgatttttgaagatagaaaatttgctgatattggtaataccgtgaagaaacaatatattggtggagtttataaaattagtagttgggcagatattactaatgctcatggtgtcactgggaatggagtagttgaaggattaaaacagggagctaaagaaaccaccaccaaccaagagccaagagggttattgatgttagctgaattatcatcagtgggatcattagcatatggagaatattctcaaaaaactgttgaaattgctaaatccgataaggaatttgttattggatttattgcccaacgtgatatgggtggacaagaagaaggatttgattggcttattatgacacctggagttggattagatgataaaggtgatggattaggacaacaatatagaactgttgatgaagttgttagcactggaactgatattatcattgttggtagaggattgtttggtaaaggaagagatccagatattgaaggtaaaaggtatagagatgctggttggaatgcttatttgaaaaagactggccaattataaacagtactgacaataaaaagattcttgttttcaagaacttgtcatttgtatagtttttttatattgtagttgttctattttaatcaaatgttagcgtgatttatattttttttcgcctcgacatcatctgcccagatgcgaagttaagtgcgcagaaagtaatatcatgcgtcaatcgtatgtgaatgctggtcgctatactgctgtcgattcgatactaacgccgccatccagtgtcgagagtagagcacttgaatccactgccccgggaatctcggtcgtaatgatttctataatgacgaaaaaaaaaaaattggaaagaaaaagcttcatggcctttataaaaaggaactatccaatacctcgccagaaccaagtaacagtattttacggggcacaaatcaagaacaataagacaggactgtaaagatggacgcattgaactccaaagaacaacaagagttccaaaaagtagtggaacaaaagcaaatgaaggatttcatgcgtttgtactctaatctggtagaaagatgtttcacagactgtgtcaatgacttcacaacatcaaagctaaccaataaggaacaaacatgcatcatgaagtgctcagaaaagttcttgaagcatagcgaacgtgtagggcagcgtttccaagaacaaaacgctgccttgggacaaggcttgggccgataaggtgtactggcgtatatatatctaattatgtatctctggtgtagcccatttttagcatgtaaatataaagaagagacctatcagctcactcaaaggcggtaatacggttatccacagaatcaggggataacgcaggaaagaacatgtgagcaaaaggccagcaaaaggccaggaaccgtaaaaaggccgcgttgctggcgtttttccataggctccgcccccctgacgagcatcacaaaaatcgacgctcaagtcagaggtggcgaaacccgacaggactataaagataccaggcgtttccccctggaagctccctcgtgcgctctcctgttccgaccctgccgcttaccggatacctgtccgcctttctcccttcgggaagcgtggcgctttctcatagctcacgctgtaggtatctcagttcggtgtaggtcgttcgctccaagctgggctgtgtgcacgaaccccccgttcagcccgaccgctgcgccttatccggtaactatcgtcttgagcccaacccggtaagacacgacttatcgccactggcagcagccactggtaacaggattagcagagcgaggtatgtaggcggtgctacagagttcttgaagtggtggcctaactacggctacactagaagaacagtatttggtatctgcgctctgctgaagccagttaccttcggaaaaagagttggtagctcttgatccggcaaacaaaccaccgctggtagcggtggtttttttgtttgcaagcagcagattacgcgcagaaaaaaaggatctcaagaagatcctttgatcttttctacggggtctgacgctcagtggaacgaaaactcacgttaagggattttggtcatgagattatcaaaaagtatcttcacctagatccttttaaattaaaaatgaagttttaaatcaatctaaagtatatatgagtaaacttggtctgacagagttctgaggtcattactggatctatcaacagcagtccaagcgagctcgatatcaaattacgccccgccctgccactcatcgcagtactgttgtaattcattaagcattctgccgacatggaagccatcacaaacggcatgatgaacctgaatcgccagcggcatcagcaccttgtcgccttgcgtataatatttgcccatggtgaaaacgggggcgaagaagttgtccatattggccacgtttaaatcaaaactggtgaaactcacccagggattggctgagacgaaaaacatattctcaataaaccctttagggaaataggccaggttttcaccgtaacacgccacatcttgcgaatatatgtgtagaaactgccggaaatcgtcgtggtattcactccagagcgatgaaaacgtttcagtttgctcatggaaaacggtgtaacaagggtgaacactatcccatatcaccagctcaccgtctttcattgccatacgaaattccggatgagcattcatcaggcgggcaagaatgtgaataaaggccggataaaacttgtgcttatttttctttacggtctttaaaaaggccgtaatatccagctgaacggtctggttataggtacattgagcaactgactgaaatgcctcaaaatgttctttacgatgccattgggatatatcaacggtggtatatccagtgatttttttctccattttagcttccttagctcctgaaaatctcgataactcaaaaaatacgcccggtagtgatcttatttcattatggtgaaagttggaacctcttacgtgcccgatcaactcgcgcgtttgccacctgacgtctaagaaaaggaatattcagcaatttgcccgtgccgaagaaaggcccacccgtgaaggtgagccggtctcggctaaattcgagtgaaacacaggaagatcagaaaatcctcatttcatccatattaacaataatttcaaatgtttatttgcattatttgaaactaggcaagacaagcaacgaaacgtttttgaaaattttgagtattttcaataaatttgtagaggactcagatattgaaaaaaagctacagcaattaatacttgataagaagagtattgagaagggcaacggttcatcatctcatggatctgcacatgaacaaacaccagagtcaaacgacgttgaaattgaggctactgcgccaattgatgacaatacagacgatgataacaaaccgaagttatctgatgtagaaaaggattaaagatgctaagagatagtgatgatatttcataaataatgtaattctatatatgttaattaccttttttgcgaggcatatttatggtgaaggataagttttgaccatcaaagaaggttaatgtggctgtggtttcagggtccataaagcccacatggataacattacgcttgctatgtcgtcggaggagatatttattacttttattattctagttttttacagttatttattaattaattatttttatatgcatgcgaataaaaagtctatatttaagttcttttatttattaatacattttcctctacgagctgtcaccggatgtgctttccggtctgatgagtccgtgaggacgaaacagcctctacaaataattttgtttaagagcaggttgttcatggccgtgcgtatgatgtggggggctcgggcgttgaaaccggggttcggagcgccaggggggtgcttttttattttgttttttttttgcagtataaaaagttagtttgtttaaacaacaaacttttttcatttcttttgtttccccttctcttcttttagttagtttgtttaaacaacaaactagaatatcaagctacaaaaataaataaaaaatgtctaaaggtgaagaattattcactggtgttgtcccaattttggttgaattagatggtgatgttaatggtcacaaattttctgtctccggtgaaggtgaaggtgatgctacttacggtaaattgaccttaaaatttatttgtactactggtaaattgccagttccatggccaaccttagtcactactttaggttatggtttgatgtgttttgctagatacccagatcatatgaaacaacatgactttttcaagtctgccatgccagaaggttatgttcaagaaagaactatttttttcaaagatgacggtaactacaagaccagagctgaagtcaagtttgaaggtgataccttagttaatagaatcgaattaaaaggtattgattttaaagaagatggtaacattttaggtcacaaattggaatacaactataactctcacaatgtttacatcatggctgacaaacaaaagaatggtatcaaagttaacttcaaaattagacacaacattgaagatggttctgttcaattagctgaccattatcaacaaaatactccaattggtgatggtccagtcttgttaccagacaaccattacttatcctatcaatctagattatccaaagatccaaacgaaaagagggatcacatggtcttgttagaatttgttactgctgctggtattacccatggtatggatgaattgtacaaataataaatggtcttcggcttactaaaagccagataacagtatgcatatttgcgcgctgatttttgcggtataagaatatatactgatatgtatacccgaagtatgtcaaaaagaggtatgctatgaagcagcgtattacagtgacagttgacagcgacagctatcagttgctcaaggcatatatgatgtcaatatctccggtctggtaagcacaaccatgcagaatgaagcccgtcgtctgcgtgccgaacgctggaaagcggaaaatcaggaagggatggctgaggtcgcccggtttattgaaatgaacggctcttttgctgacgagaacaggggctggtgaaatgcagtttaaggtttacacctataaaagagagagccgttatcgtctgtttgtggatgtacagagtgatattattgacacgcccgggcgacggatggtgatccccctggccagtgcacgtctgctgtcagataaagtctcccgtgaactttacccggtggtgcatatcggggatgaaagctggcgcatgatgaccaccgatatggccagtgtgccggtttccgttatcggggaagaagtggctgatctcagccaccgcgaaaatgacatcaaaaacgccattaacctgatgttctggggaatataagaagacta"))
    # import pymysql
    # conn = pymysql.connect(user="root",password="04080117",host="localhost",database="labdnadata")
    # cur = conn.cursor()
    # sql = "select id,sequence from backbonetable where name like '%pecbb%';"
    # cur.execute(sql)
    # result = cur.fetchall()
    # for each in result:
    #     print(each[0])
    #     sequence = each[1]
    #     print(scarIdentSitePosition(sequence))
    # # sequence = "CTGATCCTTCAACTCAGCAAAAGTTCGATTTATTCAACAAAGCCACGTTGTGTCTCAAAATCTCTGATGTTACATTGCACAAGATAAAAATATATCATCATGAACAATAAAACTGTCTGCTTACATAAACAGTAATACAAGGGGTGTTATGAGCCATATTCAACGGGAAACGTCTTGCTCCAGGCCGCGATTAAATTCCAACATGGATGCTGATTTATATGGGTATAAATGGGCTCGCGATAATGTCGGGCAATCAGGTGCGACAATCTATCGATTGTATGGGAAGCCCGATGCGCCAGAGTTGTTTCTGAAACATGGCAAAGGTAGCGTTGCCAATGATGTTACAGATGAGATGGTCAGACTAAACTGGCTGACGGAATTTATGCCTCTTCCGACCATCAAGCATTTTATCCGTACTCCTGATGATGCATGGTTACTCACCACTGCGATCCCCGGGAAAACAGCATTCCAGGTATTAGAAGAATATCCTGATTCAGGTGAAAATATTGTTGATGCGCTGGCAGTGTTCCTGCGCCGGTTGCATTCGATTCCTGTTTGTAATTGTCCTTTTAACAGCGATCGCGTATTTCGCCTCGCTCAGGCGCAATCACGAATGAATAACGGTTTGGTTGATGCGAGTGATTTTGATGACGAGCGTAATGGCTGGCCTGTTGAACAAGTCTGGAAAGAAATGCATAAGCTTTTGCCATTCTCACCGGATTCAGTCGTCACTCATGGTGATTTCTCACTTGATAACCTTATTTTTGACGAGGGGAAATTAATAGGTTGTATTGATGTTGGACGAGTCGGAATCGCAGACCGATACCAGGATCTTGCCATCCTATGGAACTGCCTCGGTGAGTTTTCTCCTTCATTACAGAAACGGCTTTTTCAAAAATATGGTATTGATAATCCTGATATGAATAAATTGCAGTTTCATTTGATGCTCGATGAGTTTTTCTAATCAGAATTGGTTAATTGGTTGTAACACGCGGCCGCTGAAGTTCCTATTCTCTAGAAAGTATAGGAACTTCCCCGATCAACTCGCGCGTTTGCCACCTGACGTCTAAGAAAAGGAATATTCAGCAATTTGCCCGTGCCGAAGAAAGGCCCACCCGTGAAGGTGAGCCTAACAGGTCTTCGGCTTACTAAAAGCCAGATAACAGTATGCATATTTGCGCGCTGATTTTTGCGGTATAAGAATATATACTGATATGTATACCCGAAGTATGTCAAAAAGAGGTATGCTATGAAGCAGCGTATTACAGTGACAGTTGACAGCGACAGCTATCAGTTGCTCAAGGCATATATGATGTCAATATCTCCGGTCTGGTAAGCACAACCATGCAGAATGAAGCCCGTCGTCTGCGTGCCGAACGCTGGAAAGCGGAAAATCAGGAAGGGATGGCTGAGGTCGCCCGGTTTATTGAAATGAACGGCTCTTTTGCTGACGAGAACAGGGGCTGGTGAAATGCAGTTTAAGGTTTACACCTATAAAAGAGAGAGCCGTTATCGTCTGTTTGTGGATGTACAGAGTGATATTATTGACACGCCCGGGCGACGGATGGTGATCCCCCTGGCCAGTGCACGTCTGCTGTCAGATAAAGTCTCCCGTGAACTTTACCCGGTGGTGCATATCGGGGATGAAAGCTGGCGCATGATGACCACCGATATGGCCAGTGTGCCGGTTTCCGTTATCGGGGAAGAAGTGGCTGATCTCAGCCACCGCGAAAATGACATCAAAAACGCCATTAACCTGATGTTCTGGGGAATATAAGAAGACCTCTGAAAAAATCACCTTGCGCTAATGCTCTGTTACAGGTCACTAATACCATCTAAGTAGTTGATTCATAGTGACTGCATATGTTGTGTTTTACAGTATTATGTAGTCTGTTTTTTATGCAAAATCTAATTTAATATATTGATATTTATATCATTTTACGTTTCTCGTTCAGCTTTTTTATACTAAGTTGGCATTATAAAAAAGCATTGCTTATCAATTTGTTGCAACGAACAGGTCACTATCAGTCAAAATAAAATCATTATTTGATTTCAATTTTGTCCCACTCCCCCTAGAGGCATCAAATAAAACGAAAGGCTCAGTCGAAAGACTGGGCCTTTCGTTTTATCTGTTGTTTGTCGGTGAACGCTCTCCTGAGTAGGACAAATCCGCCGCCCTAGACCTAGGGTAGAGACCACGGGTTTTGCTGCCCGCAAACGGGCTGTTCTGGTGTTGCTAGTTTGTTATCAGAATCGCAGATCCGGCTTCAGCCGGTTTGCCGGCTGAAAGCGCTATTTCTTCCAGAATTGCCATGATTTTTTCCCCACGGGAGGCGTCACTGGCTCCCGTGTTGTCGGCAGCTTTGATTCGATAAGCAGCATCGCCTGTTTCAGGCTGTCTATGTGTGACTGTTGAGCTGTAACAAGTTGTCTCAGGTGTTCAATTTCATGTTCTAGTTGCTTTGTTTTACTGGTTTCACCTGTTCTATTAGGTGTTACATGCTGTTCATCTGTTACATTGTCGATCTGTTCATGGTGAACAGCTTTGAATGCACCAAAAACTCGTAAAAGCTCTGATGTATCTATCTTTTTTACACCGTTTTCATCTGTGCATATGGACAGTTTTCCCTTTGATATGTAACGGTGAACAGTTGTTCTACTTTTGTTTGTTAGTCTTGATGCTTCACTGATAGATACAAGAGCCATAAGAACCTCAGATCCTTCCGTATTTAGCCAGTATGTTCTCTAGTGTGGTTCGTTGTTTTTGCGTGAGCCATGAGAACGAACCATTGAGATCATACTTACTTTGCATGTCACTCAAAAATTTTGCCTCAAAACTGGTGAGCTGAATTTTTGCAGTTAAAGCATCGTGTAGTGTTTTTCTTAGTCCGTTATGTAGGTAGGAATCTGATGTAATGGTTGTTGGTATTTTGTCACCATTCATTTTTATCTGGTTGTTCTCAAGTTCGGTTACGAGATCCATTTGTCTATCTAGTTCAACTTGGAAAATCAACGTATCAGTCGGGCGGCCTCGCTTATCAACCACCAATTTCATATTGCTGTAAGTGTTTAAATCTTTACTTATTGGTTTCAAAACCCATTGGTTAAGCCTTTTAAACTCATGGTAGTTATTTTCAAGCATTAACATGAACTTAAATTCATCAAGGCTAATCTCTATATTTGCCTTGTGAGTTTTCTTTTGTGTTAGTTCTTTTAATAACCACTCATAAATCCTCATAGAGTATTTGTTTTCAAAAGACTTAACATGTTCCAGATTATATTTTATGAATTTTTTTAACTGGAAAAGATAAGGCAATATCTCTTCACTAAAAACTAATTCTAATTTTTCGCTTGAGAACTTGGCATAGTTTGTCCACTGGAAAATCTCAAAGCCTTTAACCAAAGGATTCCTGATTTCCACAGTTCTCGTCATCAGCTCTCTGGTTGCTTTAGCTAATACACCATAAGCATTTTCCCTACTGATGTTCATCATCTGAGCGTATTGGTTATAAGTGAACGATACCGTCCGTTCTTTCCTTGTAGGGTTTTCAATCGTGGGGTTGAGTAGTGCCACACAGCATAAAATTAGCTTGGTTTCATGCTCCGTTAAGTCATAGCGACTAATCGCTAGTTCATTTGCTTTGAAAACAACTAATTCAGACATACATCTCAATTGGTCTAGGTGATTTTAATCACTATACCAATTGAGATGGGCTAGTCAATGATAATTACTAGTCCTTTTCCTTTGAGTTGTGGGTATCTGTAAATTCTGCTAGACCTTTGCTGGAAAACTTGTAAATTCTGCTAGACCCTCTGTAAATTCCGCTAGACCTTTGTGTGTTTTTTTTGTTTATATTCAAGTGGTTATAATTTATAGAATAAAGAAAGAATAAAAAAAGATAAAAAGAATAGATCCCAGCCCTGTGTATAACTCACTACTTTAGTCAGTTCCGCAGTATTACAAAAGGATGTCGCAAACGCTGTTTGCTCCTCTACAAAACAGACCTTAAAACCCTAAAGGCTTAAGTAGCACCCTCGCAAGCTCGGGCAAATCGCTGAATATTCCTTTTGTCTCCGACCATCAGGCACCTGAGTCGCTGTCTTTTTCGTGACATTCAGTTCGCTGCGCTCACGGCTCTGGCAGTGAATGGGGGTAAATGGCACTACAGGCGCCTTTTATGGATTCATGCAAGGAAACTACCCATAATACAAGAAAAGCCCGTCACGGGCTTCTCAGGGCGTTTTATGGCGGGTCTGCTATGTGGTGCTATCTGACTTTTTGCTGTTCAGCAGTTCCTGCCCTCTGATTTTCCAGTCTGACCACTTCGGATTATCCCGTGACAGGTCATTCAGACTGGCTAATGCACCCAGTAAGGCAGCGGTATCATCAACAGGCTTACCCGTCTTACTGTCCCTAGTGCTTGGATTCTCACCAATAAAAAACGCCCGGCGGCAACCGAGCGTTCTGAACAAATCCAGATGGAGTTCTGAGGTCATTACTGGATCTATCAACAGGAGGGTCTCTGGGTGAAGTTCCTATTCTCTAGAAAGTATAGGAACTTC"
    # # print(scarIdentSitePosition(sequence))
    
