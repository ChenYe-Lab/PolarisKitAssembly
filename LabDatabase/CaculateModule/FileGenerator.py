import datetime
import os
from Bio.Seq import Seq



DATE_FORMAT = "%Y-%m-%d"


def _normalize_feature_position(position, sequence_length):
    if position is None:
        return 1
    return max(1, min(int(position), sequence_length))


def _infer_part_prefix_length(sequence, enzyme):
    sequence = (sequence or "").upper()
    enzyme = (enzyme or "").upper()

    if not sequence:
        return 0

    if enzyme == "BSAI":
        fixed_prefixes = [
            "GGTCTCAATCA",
            "GGTCTCAGTGC",
            "GGTCTCATAAA",
            "GGTCTCAAATG",
            "GGTCTCAAT",
            "GGTCTCAA",
            "GGTCTCA",
        ]
        custom_anchor = "GGTCTCA"
    else:
        fixed_prefixes = [
            "GAAGACCTATCA",
            "GAAGACCTGTGC",
            "GAAGACCTTAAA",
            "GAAGACCTAATG",
            "GAAGACCTAT",
            "GAAGACCTA",
            "GAAGACCT",
        ]
        custom_anchor = "GAAGACCT"

    for prefix in fixed_prefixes:
        if sequence.startswith(prefix):
            return len(prefix)

    if sequence.startswith(custom_anchor) and len(sequence) >= len(custom_anchor) + 4:
        return len(custom_anchor) + 4

    return 0


def _shift_part_features(feature_list, sequence, enzyme):
    """
    偏移Part feature
    """
    prefix_length = _infer_part_prefix_length(sequence, enzyme)
    if prefix_length <= 0:
        return feature_list

    sequence_length = len(sequence)
    shifted_features = []
    for each_feature in feature_list:
        new_feature = dict(each_feature)
        new_feature["feature_start"] = _normalize_feature_position(
            each_feature.get("feature_start", 1) + prefix_length,
            sequence_length,
        )
        new_feature["feature_end"] = _normalize_feature_position(
            each_feature.get("feature_end", 1) + prefix_length,
            sequence_length,
        )
        shifted_features.append(new_feature)
    return shifted_features


class SequenceAnnotator:
    def __init__(self,sequence,feature_list,reverse_feature_list,EnzymeList,name = "Unknow",species = "synthetic DNA construct",Reference = ""):
        self.length = len(sequence)
        self.sequence = sequence
        # self.seq_obj = Seq(sequence)
        # self.complementSeq = str(self.seq_obj.reverse_complement())
        self.name = name
        self.EnzymeList = EnzymeList

        self.feature_list = feature_list
        self.reverse_feature_list = reverse_feature_list
        self.species = species
        self.reference = Reference
        self.colors = {
            'promoter':'#FFCC00',
            'CDS':'#83FF83',
            'terminator':'#74DAFF',
            'rbs':'#FFE1C4',
            'ori':'#999999',
            'scar':'#ff0000',
            'restriction_site':'#4f46fe',
            'binding':'#cccccc',
            'spacer':'#ABABC6',
            'homo':'#99CCFF',
            'attp':'#CBE7FF',
            'iceyydm':'#cccccc',
            'BsubAmy':'#cccccc',
            'sgRNA':'#FF9CCD',
        }
    def add_feature(self, new_feature):
        try:
            key = list(new_feature.keys())[0]
            value = list(new_feature[key])
            self.feature_list[key] = value
        except Exception as e:
            raise e
    def add_features(self, new_feature_list):
        try:
            keys = new_feature_list.keys()
            for key in keys:
                self.feature_list[key] = new_feature_list[key]
        except Exception as e:
            raise e
        
    def add_reverse_feature(self, new_feature):
        try:
            key = list(new_feature.keys())[0]
            value = list(new_feature[key])
            self.reverse_feature_list[key] = value
        except Exception as e:
            raise e
        
    def add_reverse_features(self, new_feature_list):
        try:
            keys = new_feature_list.keys()
            for key in keys:
                self.reverse_feature_list[key] = new_feature_list[key]
        except Exception as e:
            raise e
    @staticmethod
    def GeneratorBackboneNoSa(name,sequence,file_address, feature_list):
        try:
            print("NoSA")
            accession = "."
            version = "1.0"
            Keywords = "."
            definition = "synthetic circular DNA"
            reference = "synthetic"
            # if os.path.exists(os.path.join(f'{file_address}',f'{name}.gbk')):
            #     return
            with open(os.path.join(f'{file_address}',f'{name}.gbk'),'w') as file:
                file.write(("LOCUS       Exported              {0:>6} bp    DNA     {1:>8} CST \
                    {2}\n").format(len(sequence),"circular",datetime.datetime.now().strftime(DATE_FORMAT)))
                file.write("DEFINITION  {}\n".format(definition))
                file.write("ACCESSION   {}\n".format(accession))
                file.write("VERSION     {}\n".format(version))
                file.write("KEYWODS     {}\n".format(Keywords))
                file.write("SOURCE      {}\n".format(reference))
                file.write("FEATURES             Location/Qualifiers\n")

                for each_feature in feature_list:
                    if(each_feature["feature_start"] > each_feature["feature_end"]):
                        if(each_feature["feature_type"].upper() == "CDS"):
                            # if(sequence[each_feature["feature_start"]-1:each_feature["feature_start"]+2].upper() == "ATG" or sequence[each_feature["feature_start"]-1:each_feature["feature_start"]+2].upper() == "GTG" or sequence[each_feature["feature_start"]-1:each_feature["feature_start"]+2].upper() == "TTG"
                            # or sequence[each_feature["feature_start"]-1:each_feature["feature_start"]+2].upper() == "ATC" or sequence[each_feature["feature_start"]-1:each_feature["feature_start"]+2].upper() == "ATA" or sequence[each_feature["feature_start"]-1:each_feature["feature_start"]+2].upper() == "ACG"
                            # or sequence[each_feature["feature_start"]-1:each_feature["feature_start"]+2].upper() == "CTG"):
                            file.write(f"     {each_feature['feature_type']}{' '*(16-len(each_feature['feature_type']))}join({each_feature['feature_start']}..{len(sequence)},1..{each_feature['feature_end']})\n")
                            # else:
                            #     file.write(f"     {each_feature['feature_type']}{' '*(16-len(each_feature['feature_type']))}complement(join({each_feature['feature_start']}..{len(sequence)},1..{each_feature['feature_end']}))\n")
                        else:
                            file.write(f"     {each_feature['feature_type']}{' '*(16-len(each_feature['feature_type']))}join({each_feature['feature_start']}..{len(sequence)},1..{each_feature['feature_end']})\n")
                        file.write(f"                     /label={each_feature['feature_label']}\n")

                        if(each_feature["feature_color"] != None and each_feature["feature_color"] != ""):
                            file.write(f"                     /color={each_feature['feature_color']}\n")
                            file.write(f"                     /ApEinfo_fwdcolor={each_feature['feature_color']}\n")
                        elif(each_feature["feature_apeinfo"] != None and each_feature["feature_apeinfo"] != ""):
                            file.write(f"                     /color={each_feature['feature_apeinfo']}\n")
                            file.write(f"                     /ApEinfo_fwdcolor={each_feature['feature_apeinfo']}\n")
                        else:
                            file.write(f"                     /color=#ffff80\n")
                            file.write(f"                     /ApEinfo_fwdcolor=#ffff80\n")
                    else:
                        if(each_feature["feature_type"].upper() == "CDS"):
                            # print(sequence[each_feature["feature_start"]-1:each_feature["feature_start"]+2].upper())
                            # if(sequence[each_feature["feature_start"]-1:each_feature["feature_start"]+2].upper() == "ATG" or sequence[each_feature["feature_start"]-1:each_feature["feature_start"]+2].upper() == "GTG" or sequence[each_feature["feature_start"]-1:each_feature["feature_start"]+2].upper() == "TTG"
                            # or sequence[each_feature["feature_start"]-1:each_feature["feature_start"]+2].upper() == "ATC" or sequence[each_feature["feature_start"]-1:each_feature["feature_start"]+2].upper() == "ATA" or sequence[each_feature["feature_start"]-1:each_feature["feature_start"]+2].upper() == "ACG"
                            # or sequence[each_feature["feature_start"]-1:each_feature["feature_start"]+2].upper() == "CTG"):
                            #     print("zhengxiang")
                            file.write(f"     {each_feature['feature_type']}{' '*(16-len(each_feature['feature_type']))}{each_feature['feature_start']}..{each_feature['feature_end']}\n")
                            # else:
                            #     print("fanxiang")
                            #     file.write(f"     {each_feature['feature_type']}{' '*(16-len(each_feature['feature_type']))}complement({each_feature['feature_start']}..{each_feature['feature_end']})\n")
                        else:
                            file.write(f"     {each_feature['feature_type']}{' '*(16-len(each_feature['feature_type']))}{each_feature['feature_start']}..{each_feature['feature_end']}\n")
                        file.write(f"                     /label={each_feature['feature_label']}\n")
                        if(each_feature["feature_color"] != None and each_feature["feature_color"] != ""):
                            file.write(f"                     /color={each_feature['feature_color']}\n")
                            file.write(f"                     /ApEinfo_fwdcolor={each_feature['feature_color']}\n")
                        elif(each_feature["feature_apeinfo"] != None and each_feature["feature_apeinfo"] != ""):
                            file.write(f"                     /color={each_feature['feature_apeinfo']}\n")
                            file.write(f"                     /ApEinfo_fwdcolor={each_feature['feature_apeinfo']}\n")
                        else:
                            file.write(f"                     /color=#ffff80\n")
                            file.write(f"                     /ApEinfo_fwdcolor=#ffff80\n")

                file.write("ORIGIN\n")
                numOfline = (len(sequence) // 60) + 1
                offset = 0
                for each_line in range(0,numOfline):
                    file.write(f" "*(9-len(str(1+(60*each_line))))+f"{1+(60*each_line)} ")
                    if each_line != numOfline - 1:
                        for i in range(0,6):
                            if(i != 5):
                                file.write(f"{sequence[offset:offset+10]} ")
                                offset = offset + 10
                            else:
                                file.write(f"{sequence[offset:offset+10]}")
                                offset = offset + 10
                    else:
                        col_number = (len(sequence[offset:]) // 10) + 1
                        for i in range(0,col_number):
                            if(i != col_number -1):
                                file.write(f"{sequence[offset:offset+10]} ")
                                offset = offset + 10
                            else:
                                file.write(f"{sequence[offset:offset+10]} ")
                                offset = offset + 10
                    file.write("\n")
                file.write('//')
                file.flush()
                file.close()
        except Exception as exc:
            raise exc
    
    def GeneratorPartNoSa(name,sequence,file_address,feature_list,enzyme=""):
        try:
        # print("NoSA")
        # print(feature_list)
            accession = "."
            version = "1.0"
            Keywords = "."
            definition = "synthetic circular DNA"
            reference = "synthetic"
            feature_list = _shift_part_features(feature_list, sequence, enzyme)
            # if os.path.exists(os.path.join(f'{file_address}',f'{name}.gbk')):
            #     return
            with open(os.path.join(f'{file_address}',f'{name}.gbk'),'w') as file:
                file.write(("LOCUS       Exported              {0:>6} bp    DNA     {1:>8} CST \
                {2}\n").format(len(sequence),"circular",datetime.datetime.now().strftime(DATE_FORMAT)))
                file.write("DEFINITION  {}\n".format(definition))
                file.write("ACCESSION   {}\n".format(accession))
                file.write("VERSION     {}\n".format(version))
                file.write("KEYWODS     {}\n".format(Keywords))
                file.write("SOURCE      {}\n".format(reference))
                file.write("FEATURES             Location/Qualifiers\n")
            
                for each_feature in feature_list:
                    if(each_feature["feature_start"] > each_feature["feature_end"]):
                        if(each_feature["feature_type"].upper() == "CDS"):
                            # if(sequence[each_feature["feature_start"]-1:each_feature["feature_start"]+2].upper() == "ATG" or sequence[each_feature["feature_start"]-1:each_feature["feature_start"]+2].upper() == "GTG" or sequence[each_feature["feature_start"]-1:each_feature["feature_start"]+2].upper() == "TTG"
                            # or sequence[each_feature["feature_start"]-1:each_feature["feature_start"]+2].upper() == "ATC" or sequence[each_feature["feature_start"]-1:each_feature["feature_start"]+2].upper() == "ATA" or sequence[each_feature["feature_start"]-1:each_feature["feature_start"]+2].upper() == "ACG"
                            # or sequence[each_feature["feature_start"]-1:each_feature["feature_start"]+2].upper() == "CTG"):
                            file.write(f"     {each_feature['feature_type']}{' '*(16-len(each_feature['feature_type']))}join({each_feature['feature_start']}..{len(sequence)},1..{each_feature['feature_end']})\n")
                            # else:
                            #     file.write(f"     {each_feature['feature_type']}{' '*(16-len(each_feature['feature_type']))}complement(join({each_feature['feature_start']}..{len(sequence)},1..{each_feature['feature_end']}))\n")
                        else:
                            file.write(f"     {each_feature['feature_type']}{' '*(16-len(each_feature['feature_type']))}join({each_feature['feature_start']}..{len(sequence)},1..{each_feature['feature_end']})\n")
                        file.write(f"                     /label={each_feature['feature_label']}\n")

                        if(each_feature["feature_color"] != None and each_feature["feature_color"] != ""):
                            file.write(f"                     /color={each_feature['feature_color']}\n")
                            file.write(f"                     /ApEinfo_fwdcolor={each_feature['feature_color']}\n")
                        elif(each_feature["feature_apeinfo"] != None and each_feature["feature_apeinfo"] != ""):
                            file.write(f"                     /color={each_feature['feature_apeinfo']}\n")
                            file.write(f"                     /ApEinfo_fwdcolor={each_feature['feature_apeinfo']}\n")
                        else:
                            file.write(f"                     /color=#ffff80\n")
                            file.write(f"                     /ApEinfo_fwdcolor=#ffff80\n")
                    else:
                        if(each_feature["feature_type"].upper() == "CDS"):
                            # if(sequence[each_feature["feature_start"]-1:each_feature["feature_start"]+2].upper() == "ATG" or sequence[each_feature["feature_start"]-1:each_feature["feature_start"]+2].upper() == "GTG" or sequence[each_feature["feature_start"]-1:each_feature["feature_start"]+2].upper() == "TTG"
                            # or sequence[each_feature["feature_start"]-1:each_feature["feature_start"]+2].upper() == "ATC" or sequence[each_feature["feature_start"]-1:each_feature["feature_start"]+2].upper() == "ATA" or sequence[each_feature["feature_start"]-1:each_feature["feature_start"]+2].upper() == "ACG"
                            # or sequence[each_feature["feature_start"]-1:each_feature["feature_start"]+2].upper() == "CTG"):
                                # print("zhengxiang")
                            file.write(f"     {each_feature['feature_type']}{' '*(16-len(each_feature['feature_type']))}{each_feature['feature_start']}..{each_feature['feature_end']}\n")
                            # else:
                            #     print("fanxiang")
                            #     file.write(f"     {each_feature['feature_type']}{' '*(16-len(each_feature['feature_type']))}complement({each_feature['feature_start']}..{each_feature['feature_end']})\n")
                        else:
                            file.write(f"     {each_feature['feature_type']}{' '*(16-len(each_feature['feature_type']))}{each_feature['feature_start']}..{each_feature['feature_end']}\n")
                        file.write(f"                     /label={each_feature['feature_label']}\n")
                        if(each_feature["feature_color"] != None and each_feature["feature_color"] != ""):
                            file.write(f"                     /color={each_feature['feature_color']}\n")
                            file.write(f"                     /ApEinfo_fwdcolor={each_feature['feature_color']}\n")
                        elif(each_feature["feature_apeinfo"] != None and each_feature["feature_apeinfo"] != ""):
                            file.write(f"                     /color={each_feature['feature_apeinfo']}\n")
                            file.write(f"                     /ApEinfo_fwdcolor={each_feature['feature_apeinfo']}\n")
                        else:
                            file.write(f"                     /color=#ffff80\n")
                            file.write(f"                     /ApEinfo_fwdcolor=#ffff80\n")

                file.write("ORIGIN\n")
                numOfline = (len(sequence) // 60) + 1
                offset = 0
                for each_line in range(0,numOfline):
                    file.write(f" "*(9-len(str(1+(60*each_line))))+f"{1+(60*each_line)} ")
                    if each_line != numOfline - 1:
                        for i in range(0,6):
                            if(i != 5):
                                file.write(f"{sequence[offset:offset+10]} ")
                                offset = offset + 10
                            else:
                                file.write(f"{sequence[offset:offset+10]}")
                                offset = offset + 10
                    else:
                        col_number = (len(sequence[offset:]) // 10) + 1
                        for i in range(0,col_number):
                            if(i != col_number -1):
                                file.write(f"{sequence[offset:offset+10]} ")
                                offset = offset + 10
                            else:
                                file.write(f"{sequence[offset:offset+10]} ")
                                offset = offset + 10
                    file.write("\n")
                file.write('//')
                file.flush()
                file.close()
        except Exception as exc:
            raise exc

    def GenerateGBKFile(self, file_address, type="circular"):
        try:
            print("SA")
            if(type == "circular"):
                definition = "synthetic circular DNA"
            else:
                definition = "synthetic linear DNA"
            accession = "."
            version = "1.0"
            Keywords = "."
            # if os.path.exists(os.path.join(f'{file_address}',f'{self.name}.gbk')):
            #     return
            with open(os.path.join(f'{file_address}',f'{self.name}.gbk'),'w') as file:
                if(type == "circular"):
                    file.write(("LOCUS       Exported              {0:>6} bp    DNA     {1:>8} CST \
                    {2}\n").format(len(self.sequence),"circular",datetime.datetime.now().strftime(DATE_FORMAT)))
                else:
                    file.write(("LOCUS       Exported              {0:>6} bp    DNA     {1:>8} CST \
                    {2}\n").format(len(self.sequence),"linear",datetime.datetime.now().strftime(DATE_FORMAT)))
                file.write("DEFINITION  {}\n".format(definition))
                file.write("ACCESSION   {}\n".format(accession))
                file.write("VERSION     {}\n".format(version))
                file.write("KEYWODS     {}\n".format(Keywords))
                file.write("SOURCE      {}\n".format(self.reference))
                file.write("FEATURES             Location/Qualifiers\n")
                for each_feature in self.feature_list.keys():
                    if(self.feature_list[each_feature][2].lower() == "origin" or self.feature_list[each_feature][2].lower() == "rep_origin"):
                        if(self.feature_list[each_feature][0] > self.feature_list[each_feature][1]):
                            file.write(f"     rep_origin      join({self.feature_list[each_feature][0]}..{self.length},1..{self.feature_list[each_feature][1]})\n")
                            file.write(f"                     /label={each_feature}\n")
                            if(len(self.feature_list[each_feature]) > 3):
                                file.write(f"                     /color={self.feature_list[each_feature][3]}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.colors['ori']}\n")
                            else:
                                file.write(f"                     /color={self.colors['ori']}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.feature_list[each_feature][3]}\n")
                        else:
                            file.write(f"     rep_origin      {self.feature_list[each_feature][0]}..{self.feature_list[each_feature][1]}\n")
                            file.write(f"                     /label={each_feature}\n")
                            if(len(self.feature_list[each_feature]) > 3):
                                file.write(f"                     /color={self.feature_list[each_feature][3]}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.feature_list[each_feature][3]}\n")
                            else:
                                file.write(f"                     /color={self.colors['ori']}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.colors['ori']}\n")
                    elif(self.feature_list[each_feature][2].lower() == "cds"):
                        if(self.feature_list[each_feature][0] > self.feature_list[each_feature][1]):
                            if(self.sequence[self.feature_list[each_feature][0]-1:self.feature_list[each_feature][0]+2].upper() == "ATG" or self.sequence[self.feature_list[each_feature][0]-1:self.feature_list[each_feature][0]+2].upper() == "GTG" or self.sequence[self.feature_list[each_feature][0]-1:self.feature_list[each_feature][0]+2].upper() == "TTG"
                                or self.sequence[self.feature_list[each_feature][0]-1:self.feature_list[each_feature][0]+2].upper() == "ATC" or self.sequence[self.feature_list[each_feature][0]-1:self.feature_list[each_feature]+2].upper() == "ATA" or self.sequence[self.feature_list[each_feature][0]-1:self.feature_list[each_feature][0]+2].upper() == "ACG"
                                or self.sequence[self.feature_list[each_feature][0]-1:self.feature_list[each_feature][0]+2].upper() == "CTG"):
                                file.write(f"     CDS             join({self.feature_list[each_feature][0]}..{self.length},1..{self.feature_list[each_feature][1]})\n")
                            else:
                                file.write(f"     CDS             complement(join({self.feature_list[each_feature][0]}..{self.length},1..{self.feature_list[each_feature][1]}))\n")

                            file.write(f"                     /label={each_feature}\n")
                            if(len(self.feature_list[each_feature]) > 3):
                                file.write(f"                     /color={self.feature_list[each_feature][3]}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.feature_list[each_feature][3]}\n")
                            else:
                                file.write(f"                     /color={self.colors['CDS']}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.colors['CDS']}\n")
                        else:
                            if(self.sequence[self.feature_list[each_feature][0]-1:self.feature_list[each_feature][0]+2].upper() == "ATG" or self.sequence[self.feature_list[each_feature][0]-1:self.feature_list[each_feature][0]+2].upper() == "GTG" or self.sequence[self.feature_list[each_feature][0]-1:self.feature_list[each_feature][0]+2].upper() == "TTG"
                                or self.sequence[self.feature_list[each_feature][0]-1:self.feature_list[each_feature][0]+2].upper() == "ATC" or self.sequence[self.feature_list[each_feature][0]-1:self.feature_list[each_feature][0]+2].upper() == "ATA" or self.sequence[self.feature_list[each_feature][0]-1:self.feature_list[each_feature][0]+2].upper() == "ACG"
                                or self.sequence[self.feature_list[each_feature][0]-1:self.feature_list[each_feature][0]+2].upper() == "CTG"):
                                file.write(f"     CDS             {self.feature_list[each_feature][0]}..{self.feature_list[each_feature][1]}\n")
                            else:
                                file.write(f"     CDS             complement({self.feature_list[each_feature][0]}..{self.feature_list[each_feature][1]})\n")
                            file.write(f"                     /label={each_feature}\n")
                            if(len(self.feature_list[each_feature]) > 3):
                                file.write(f"                     /color={self.feature_list[each_feature][3]}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.feature_list[each_feature][3]}\n")
                            else:
                                file.write(f"                     /color={self.colors['CDS']}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.colors['CDS']}\n")
                    elif(self.feature_list[each_feature][2].lower() == "promoter"):
                        if(self.feature_list[each_feature][0] > self.feature_list[each_feature][1]):
                            file.write(f"     promoter        join({self.feature_list[each_feature][0]}..{self.length},1..{self.feature_list[each_feature][1]})\n")
                            file.write(f"                     /label={each_feature}\n")
                            if(len(self.feature_list[each_feature]) > 3):
                                file.write(f"                     /color={self.feature_list[each_feature][3]}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.feature_list[each_feature][3]}\n")
                            else:
                                file.write(f"                     /color={self.colors['promoter']}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.colors['promoter']}\n")
                        else:
                            file.write(f"     promoter        {self.feature_list[each_feature][0]}..{self.feature_list[each_feature][1]}\n")
                            file.write(f"                     /label={each_feature}\n")
                            if(len(self.feature_list[each_feature]) > 3):
                                file.write(f"                     /color={self.feature_list[each_feature][3]}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.feature_list[each_feature][3]}\n")
                            else:
                                file.write(f"                     /color={self.colors['promoter']}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.colors['promoter']}\n")
                    elif(self.feature_list[each_feature][2].lower() == "terminator"):
                        if(self.feature_list[each_feature][0] > self.feature_list[each_feature][1]):
                            file.write(f"     terminator      join({self.feature_list[each_feature][0]}..{self.length},1..{self.feature_list[each_feature][1]})\n")
                            file.write(f"                     /label={each_feature}\n")
                            if(len(self.feature_list[each_feature]) > 3):
                                file.write(f"                     /color={self.feature_list[each_feature][3]}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.feature_list[each_feature][3]}\n")
                            else:
                                file.write(f"                     /color={self.colors['terminator']}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.colors['terminator']}\n")
                        else:
                            file.write(f"     terminator      {self.feature_list[each_feature][0]}..{self.feature_list[each_feature][1]}\n")
                            file.write(f"                     /label={each_feature}\n")
                            if(len(self.feature_list[each_feature]) > 3):
                                file.write(f"                     /color={self.feature_list[each_feature][3]}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.feature_list[each_feature][3]}\n")
                            else:
                                file.write(f"                     /color={self.colors['terminator']}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.colors['terminator']}\n")
                    elif(self.feature_list[each_feature][2].lower() == "misc_feature"):
                        if(self.feature_list[each_feature][0] > self.feature_list[each_feature][1]):
                            file.write(f"     misc_feature    join({self.feature_list[each_feature][0]}..{self.length},1..{self.feature_list[each_feature][1]})\n")
                            file.write(f"                     /label={each_feature}\n")
                            if(len(self.feature_list[each_feature]) > 3):
                                file.write(f"                     /color={self.feature_list[each_feature][3]}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.feature_list[each_feature][3]}\n")
                            else:
                                file.write(f"                     /color={self.colors['restriction_site']}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.colors['restriction_site']}\n")
                        else:
                            file.write(f"     misc_feature    {self.feature_list[each_feature][0]}..{self.feature_list[each_feature][1]}\n")
                            file.write(f"                     /label={each_feature}\n")
                            if(len(self.feature_list[each_feature]) > 3):
                                file.write(f"                     /color={self.feature_list[each_feature][3]}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.feature_list[each_feature][3]}\n")
                            else:
                                file.write(f"                     /color={self.colors['restriction_site']}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.colors['restriction_site']}\n")
                    elif(self.feature_list[each_feature][2].lower() == "scar"):
                        if(self.feature_list[each_feature][0] > self.feature_list[each_feature][1]):
                            file.write(f"     scar            join({self.feature_list[each_feature][0]}..{self.length},1..{self.feature_list[each_feature][1]})\n")
                            file.write(f"                     /label={each_feature}\n")
                            if(len(self.feature_list[each_feature]) > 3):
                                file.write(f"                     /color={self.feature_list[each_feature][3]}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.feature_list[each_feature][3]}\n")
                            else:
                                file.write(f"                     /color={self.colors['scar']}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.colors['scar']}\n")
                        else:
                            file.write(f"     scar            {self.feature_list[each_feature][0]}..{self.feature_list[each_feature][1]}\n")
                            file.write(f"                     /label={each_feature}\n")
                            if(len(self.feature_list[each_feature]) > 3):
                                file.write(f"                     /color={self.feature_list[each_feature][3]}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.feature_list[each_feature][3]}\n")
                            else:
                                file.write(f"                     /color={self.colors['scar']}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.colors['scar']}\n")
                    elif(self.feature_list[each_feature][2].lower() == "primer_bind"):
                        if(self.feature_list[each_feature][0] > self.feature_list[each_feature][1]):
                            file.write(f"     primer_bind     join({self.feature_list[each_feature][0]}..{self.length},1..{self.feature_list[each_feature][1]})\n")
                            file.write(f"                     /label={each_feature}\n")
                            if(len(self.feature_list[each_feature]) > 3):
                                file.write(f"                     /color={self.feature_list[each_feature][3]}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.feature_list[each_feature][3]}\n")
                            else:
                                file.write(f"                     /color={self.colors['binding']}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.colors['binding']}\n")
                        else:
                            file.write(f"     primer_bind     {self.feature_list[each_feature][0]}..{self.feature_list[each_feature][1]}\n")
                            file.write(f"                     /label={each_feature}\n")
                            if(len(self.feature_list[each_feature]) > 3):
                                file.write(f"                     /color={self.feature_list[each_feature][3]}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.feature_list[each_feature][3]}\n")
                            else:
                                file.write(f"                     /color={self.colors['binding']}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.colors['binding']}\n")
                    elif(self.feature_list[each_feature][2].lower() == "spacer"):
                        if(self.feature_list[each_feature][0] > self.feature_list[each_feature][1]):
                            file.write(f"     misc_feature     join({self.feature_list[each_feature][0]}..{self.length},1..{self.feature_list[each_feature][1]})\n")
                            file.write(f"                     /label={each_feature}\n")
                            if(len(self.feature_list[each_feature]) > 3):
                                file.write(f"                     /color={self.feature_list[each_feature][3]}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.feature_list[each_feature][3]}\n")
                            else:
                                file.write(f"                     /color={self.colors['spacer']}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.colors['spacer']}\n")
                        else:
                            file.write(f"     misc_feature     {self.feature_list[each_feature][0]}..{self.feature_list[each_feature][1]}\n")
                            file.write(f"                     /label={each_feature}\n")
                            if(len(self.feature_list[each_feature]) > 3):
                                file.write(f"                     /color={self.feature_list[each_feature][3]}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.feature_list[each_feature][3]}\n")
                            else:
                                file.write(f"                     /color={self.colors['spacer']}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.colors['spacer']}\n")
                    elif(self.feature_list[each_feature][2].lower() == "homo"):
                        if(self.feature_list[each_feature][0] > self.feature_list[each_feature][1]):
                            file.write(f"     misc_feature     join({self.feature_list[each_feature][0]}..{self.length},1..{self.feature_list[each_feature][1]})\n")
                            file.write(f"                     /label={each_feature}\n")
                            if(len(self.feature_list[each_feature]) > 3):
                                file.write(f"                     /color={self.feature_list[each_feature][3]}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.feature_list[each_feature][3]}\n")
                            else:
                                file.write(f"                     /color={self.colors['homo']}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.colors['homo']}\n")
                        else:
                            file.write(f"     misc_feature     {self.feature_list[each_feature][0]}..{self.feature_list[each_feature][1]}\n")
                            file.write(f"                     /label={each_feature}\n")
                            if(len(self.feature_list[each_feature]) > 3):
                                file.write(f"                     /color={self.feature_list[each_feature][3]}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.feature_list[each_feature][3]}\n")
                            else:
                                file.write(f"                     /color={self.colors['homo']}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.colors['homo']}\n")
                    elif(self.feature_list[each_feature][2].lower() == "attp"):
                        if(self.feature_list[each_feature][0] > self.feature_list[each_feature][1]):
                            file.write(f"     misc_feature     join({self.feature_list[each_feature][0]}..{self.length},1..{self.feature_list[each_feature][1]})\n")
                            file.write(f"                     /label={each_feature}\n")
                            if(len(self.feature_list[each_feature]) > 3):
                                file.write(f"                     /color={self.feature_list[each_feature][3]}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.feature_list[each_feature][3]}\n")
                            else:
                                file.write(f"                     /color={self.colors['attp']}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.colors['attp']}\n")
                        else:
                            file.write(f"     misc_feature     {self.feature_list[each_feature][0]}..{self.feature_list[each_feature][1]}\n")
                            file.write(f"                     /label={each_feature}\n")
                            if(len(self.feature_list[each_feature]) > 3):
                                file.write(f"                     /color={self.feature_list[each_feature][3]}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.feature_list[each_feature][3]}\n")
                            else:
                                file.write(f"                     /color={self.colors['attp']}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.colors['attp']}\n")
                    elif(self.feature_list[each_feature][2].lower() == "iceyydm"):
                        if(self.feature_list[each_feature][0] > self.feature_list[each_feature][1]):
                            file.write(f"     misc_feature     join({self.feature_list[each_feature][0]}..{self.length},1..{self.feature_list[each_feature][1]})\n")
                            file.write(f"                     /label={each_feature}\n")
                            if(len(self.feature_list[each_feature]) > 3):
                                file.write(f"                     /color={self.feature_list[each_feature][3]}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.feature_list[each_feature][3]}\n")
                            else:
                                file.write(f"                     /color={self.colors['iceyydm']}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.colors['iceyydm']}\n")
                        else:
                            file.write(f"     misc_feature     {self.feature_list[each_feature][0]}..{self.feature_list[each_feature][1]}\n")
                            file.write(f"                     /label={each_feature}\n")
                            if(len(self.feature_list[each_feature]) > 3):
                                file.write(f"                     /color={self.feature_list[each_feature][3]}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.feature_list[each_feature][3]}\n")
                            else:
                                file.write(f"                     /color={self.colors['iceyydm']}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.colors['iceyydm']}\n")
                    elif(self.feature_list[each_feature][2].lower() == "bsubamy"):
                        if(self.feature_list[each_feature][0] > self.feature_list[each_feature][1]):
                            file.write(f"     misc_feature     join({self.feature_list[each_feature][0]}..{self.length},1..{self.feature_list[each_feature][1]})\n")
                            file.write(f"                     /label={each_feature}\n")
                            if(len(self.feature_list[each_feature]) > 3):
                                file.write(f"                     /color={self.feature_list[each_feature][3]}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.feature_list[each_feature][3]}\n")
                            else:
                                file.write(f"                     /color={self.colors['BsubAmy']}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.colors['BsubAmy']}\n")
                        else:
                            file.write(f"     misc_feature     {self.feature_list[each_feature][0]}..{self.feature_list[each_feature][1]}\n")
                            file.write(f"                     /label={each_feature}\n")
                            if(len(self.feature_list[each_feature]) > 3):
                                file.write(f"                     /color={self.feature_list[each_feature][3]}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.feature_list[each_feature][3]}\n")
                            else:
                                file.write(f"                     /color={self.colors['BsubAmy']}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.colors['BsubAmy']}\n")
                    elif(self.feature_list[each_feature][2].lower() == "rbs"):
                        if(self.feature_list[each_feature][0] > self.feature_list[each_feature][1]):
                            file.write(f"     misc_feature     join({self.feature_list[each_feature][0]}..{self.length},1..{self.feature_list[each_feature][1]})\n")
                            file.write(f"                     /label={each_feature}\n")
                            if(len(self.feature_list[each_feature]) > 3):
                                file.write(f"                     /color={self.feature_list[each_feature][3]}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.feature_list[each_feature][3]}\n")
                            else:
                                file.write(f"                     /color={self.colors['rbs']}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.colors['rbs']}\n")
                        else:
                            file.write(f"     misc_feature     {self.feature_list[each_feature][0]}..{self.feature_list[each_feature][1]}\n")
                            file.write(f"                     /label={each_feature}\n")
                            if(len(self.feature_list[each_feature]) > 3):
                                file.write(f"                     /color={self.feature_list[each_feature][3]}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.feature_list[each_feature][3]}\n")
                            else:
                                file.write(f"                     /color={self.colors['rbs']}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.colors['rbs']}\n")
                    else:
                        if(self.feature_list[each_feature][0] > self.feature_list[each_feature][1]):
                            file.write(f"     misc_feature     join({self.feature_list[each_feature][0]}..{self.length},1..{self.feature_list[each_feature][1]})\n")
                            file.write(f"                     /label={each_feature}\n")
                            if(len(self.feature_list[each_feature]) > 3):
                                file.write(f"                     /color={self.feature_list[each_feature][3]}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.feature_list[each_feature][3]}\n")
                            else:
                                file.write(f"                     /color={self.colors['binding']}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.colors['binding']}\n")
                        else:
                            file.write(f"     misc_feature     {self.feature_list[each_feature][0]}..{self.feature_list[each_feature][1]}\n")
                            file.write(f"                     /label={each_feature}\n")
                            if(len(self.feature_list[each_feature]) > 3):
                                file.write(f"                     /color={self.feature_list[each_feature][3]}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.feature_list[each_feature][3]}\n")
                            else:
                                file.write(f"                     /color={self.colors['binding']}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.colors['binding']}\n")

                
                for each_feature in self.reverse_feature_list.keys():
                    if(self.reverse_feature_list[each_feature][2].lower() == "origin"):
                        if(self.reverse_feature_list[each_feature][0] > self.reverse_feature_list[each_feature][1]):
                            file.write(f"     rep_origin      complement(join({self.length - self.reverse_feature_list[each_feature][1] + 1}..{self.length},1..{self.length - self.reverse_feature_list[each_feature][0]+1}))\n")
                            file.write(f"                     /label={each_feature}\n")
                            file.write(f"                     /color={self.colors['ori']}\n")
                            file.write(f"                     /ApEinfo_fwdcolor={self.colors['ori']}\n")
                        else:
                            file.write(f"     rep_origin      complement({self.length - self.reverse_feature_list[each_feature][1] + 1}..{self.length - self.reverse_feature_list[each_feature][0]+1})\n")
                            file.write(f"                     /label={each_feature}\n")
                            file.write(f"                     /color={self.colors['ori']}\n")
                            file.write(f"                     /ApEinfo_fwdcolor={self.colors['ori']}\n")
                    elif(self.reverse_feature_list[each_feature][2].lower() == "cds"):
                        if(self.reverse_feature_list[each_feature][0] > self.reverse_feature_list[each_feature][1]):
                            file.write(f"     CDS             complement(join({self.length - self.reverse_feature_list[each_feature][1] + 1}..{self.length},1..{self.length - self.reverse_feature_list[each_feature][0]+1}))\n")
                            file.write(f"                     /label={each_feature}\n")
                            file.write(f"                     /color={self.colors['CDS']}\n")
                            file.write(f"                     /ApEinfo_fwdcolor={self.colors['CDS']}\n")
                        else:
                            file.write(f"     CDS             complement({self.length - self.reverse_feature_list[each_feature][1] + 1}..{self.length - self.reverse_feature_list[each_feature][0] + 1})\n")
                            file.write(f"                     /label={each_feature}\n")
                            file.write(f"                     /color={self.colors['CDS']}\n")
                            file.write(f"                     /ApEinfo_fwdcolor={self.colors['CDS']}\n")
                    elif(self.reverse_feature_list[each_feature][2].lower() == "promoter"):
                        if(self.reverse_feature_list[each_feature][0] > self.reverse_feature_list[each_feature][1]):
                            file.write(f"     promoter        complement(join({self.length - self.reverse_feature_list[each_feature][1] + 1}..{self.length},1..{self.length - self.reverse_feature_list[each_feature][0]+1}))\n")
                            file.write(f"                     /label={each_feature}\n")
                            file.write(f"                     /color={self.colors['promoter']}\n")
                            file.write(f"                     /ApEinfo_fwdcolor={self.colors['promoter']}\n")
                        else:
                            file.write(f"     promoter        complement({self.length - self.reverse_feature_list[each_feature][1] + 1}..{self.length - self.reverse_feature_list[each_feature][0] + 1})\n")
                            file.write(f"                     /label={each_feature}\n")
                            file.write(f"                     /color={self.colors['promoter']}\n")
                            file.write(f"                     /ApEinfo_fwdcolor={self.colors['promoter']}\n")
                    elif(self.reverse_feature_list[each_feature][2].lower() == "terminator"):
                        if(self.reverse_feature_list[each_feature][0] > self.reverse_feature_list[each_feature][1]):
                            file.write(f"     terminator      complement(join({self.length - self.reverse_feature_list[each_feature][1] + 1}..{self.length},1..{self.length - self.reverse_feature_list[each_feature][0]+1}))\n")
                            file.write(f"                     /label={each_feature}\n")
                            file.write(f"                     /color={self.colors['terminator']}\n")
                            file.write(f"                     /ApEinfo_fwdcolor={self.colors['terminator']}\n")
                        else:
                            file.write(f"     terminator      complement({self.length - self.reverse_feature_list[each_feature][1] + 1}..{self.length - self.reverse_feature_list[each_feature][0] + 1})\n")
                            file.write(f"                     /label={each_feature}\n")
                            file.write(f"                     /color={self.colors['terminator']}\n")
                            file.write(f"                     /ApEinfo_fwdcolor={self.colors['terminator']}\n")
                    elif(self.reverse_feature_list[each_feature][2].lower() == "scar"):
                        if(self.reverse_feature_list[each_feature][0] > self.reverse_feature_list[each_feature][1]):
                            file.write(f"     scar            complement(join({self.length - self.reverse_feature_list[each_feature][1] + 1}..{self.length},1..{self.length - self.reverse_feature_list[each_feature][0]+1}))\n")
                            file.write(f"                     /label={each_feature}\n")
                            file.write(f"                     /color={self.colors['scar']}\n")
                            file.write(f"                     /ApEinfo_fwdcolor={self.colors['scar']}\n")
                        else:
                            file.write(f"     scar            complement({self.length - self.reverse_feature_list[each_feature][1] + 1}..{self.length - self.reverse_feature_list[each_feature][0] + 1})\n")
                            file.write(f"                     /label={each_feature}\n")
                            file.write(f"                     /color={self.colors['scar']}\n")
                            file.write(f"                     /ApEinfo_fwdcolor={self.colors['scar']}\n")
                    elif(self.reverse_feature_list[each_feature][2].lower() == "misc_feature"):
                        if(self.reverse_feature_list[each_feature][0] > self.reverse_feature_list[each_feature][1]):
                            file.write(f"     misc_feature    complement(join({self.length - self.reverse_feature_list[each_feature][1] + 1}..{self.length},1..{self.length - self.reverse_feature_list[each_feature][0]+1}))\n")
                            file.write(f"                     /label={each_feature}\n")
                            file.write(f"                     /color={self.colors['restriction_site']}\n")
                            file.write(f"                     /ApEinfo_fwdcolor={self.colors['restriction_site']}\n")
                        else:
                            file.write(f"     misc_feature    complement({self.length - self.reverse_feature_list[each_feature][1] + 1}..{self.length - self.reverse_feature_list[each_feature][0] + 1})\n")
                            file.write(f"                     /label={each_feature}\n")
                            file.write(f"                     /color={self.colors['restriction_site']}\n")
                            file.write(f"                     /ApEinfo_fwdcolor={self.colors['restriction_site']}\n")
                    elif(self.reverse_feature_list[each_feature][2].lower() == "primer_bind"):
                        if(self.reverse_feature_list[each_feature][0] > self.reverse_feature_list[each_feature][1]):
                            file.write(f"     primer_bind     complement(join({self.length - self.reverse_feature_list[each_feature][1] + 1}..{self.length},1..{self.length - self.reverse_feature_list[each_feature][0]+1}))\n")
                            file.write(f"                     /label={each_feature}\n")
                            file.write(f"                     /color={self.colors['binding']}\n")
                            file.write(f"                     /ApEinfo_fwdcolor={self.colors['binding']}\n")
                        else:
                            file.write(f"     primer_bind     complement({self.length - self.reverse_feature_list[each_feature][1] + 1}..{self.length - self.reverse_feature_list[each_feature][0] + 1})\n")
                            file.write(f"                     /label={each_feature}\n")
                            file.write(f"                     /color={self.colors['binding']}\n")
                            file.write(f"                     /ApEinfo_fwdcolor={self.colors['binding']}\n")
                    elif(self.reverse_feature_list[each_feature][2].lower() == "spacer"):
                        if(self.reverse_feature_list[each_feature][0] > self.reverse_feature_list[each_feature][1]):
                            file.write(f"     spacer          complement(join({self.length - self.reverse_feature_list[each_feature][1] + 1}..{self.length},1..{self.length - self.reverse_feature_list[each_feature][0]+1}))\n")
                            file.write(f"                     /label={each_feature}\n")
                            file.write(f"                     /color={self.colors['spacer']}\n")
                            file.write(f"                     /ApEinfo_fwdcolor={self.colors['spacer']}\n")
                        else:
                            file.write(f"     spacer          complement({self.length - self.reverse_feature_list[each_feature][1] + 1}..{self.length - self.reverse_feature_list[each_feature][0] + 1})\n")
                            file.write(f"                     /label={each_feature}\n")
                            file.write(f"                     /color={self.colors['spacer']}\n")
                            file.write(f"                     /ApEinfo_fwdcolor={self.colors['spacer']}\n")
                    elif(self.reverse_feature_list[each_feature][2].lower() == "homo"):
                        if(self.reverse_feature_list[each_feature][0] > self.reverse_feature_list[each_feature][1]):
                            file.write(f"     misc_feature     complement(join({self.length - self.reverse_feature_list[each_feature][1] + 1}..{self.length},1..{self.length - self.reverse_feature_list[each_feature][0]+1}))\n")
                            file.write(f"                     /label={each_feature}\n")
                            file.write(f"                     /color={self.colors['homo']}\n")
                            file.write(f"                     /ApEinfo_fwdcolor={self.colors['homo']}\n")
                        else:
                            file.write(f"     misc_feature     complement({self.length - self.reverse_feature_list[each_feature][1] + 1}..{self.length - self.reverse_feature_list[each_feature][0] + 1})\n")
                            file.write(f"                     /label={each_feature}\n")
                            file.write(f"                     /color={self.colors['homo']}\n")
                            file.write(f"                     /ApEinfo_fwdcolor={self.colors['homo']}\n")
                    elif(self.reverse_feature_list[each_feature][2].lower() == "attp"):
                        if(self.reverse_feature_list[each_feature][0] > self.reverse_feature_list[each_feature][1]):
                            file.write(f"     misc_feature     complement(join({self.length - self.reverse_feature_list[each_feature][1] + 1}..{self.length},1..{self.length - self.reverse_feature_list[each_feature][0]+1}))\n")
                            file.write(f"                     /label={each_feature}\n")
                            file.write(f"                     /color={self.colors['attp']}\n")
                            file.write(f"                     /ApEinfo_fwdcolor={self.colors['attp']}\n")
                        else:
                            file.write(f"     misc_feature     complement({self.length - self.reverse_feature_list[each_feature][1] + 1}..{self.length - self.reverse_feature_list[each_feature][0] + 1})\n")
                            file.write(f"                     /label={each_feature}\n")
                            file.write(f"                     /color={self.colors['attp']}\n")
                            file.write(f"                     /ApEinfo_fwdcolor={self.colors['attp']}\n")
                    elif(self.reverse_feature_list[each_feature][2].lower() == "iceyydm"):
                        if(self.reverse_feature_list[each_feature][0] > self.reverse_feature_list[each_feature][1]):
                            file.write(f"     misc_feature     complement(join({self.length - self.reverse_feature_list[each_feature][1] + 1}..{self.length},1..{self.length - self.reverse_feature_list[each_feature][0]+1}))\n")
                            file.write(f"                     /label={each_feature}\n")
                            file.write(f"                     /color={self.colors['iceyydm']}\n")
                            file.write(f"                     /ApEinfo_fwdcolor={self.colors['iceyydm']}\n")
                        else:
                            file.write(f"     misc_feature     complement({self.length - self.reverse_feature_list[each_feature][1] + 1}..{self.length - self.reverse_feature_list[each_feature][0] + 1})\n")
                            file.write(f"                     /label={each_feature}\n")
                            file.write(f"                     /color={self.colors['iceyydm']}\n")
                            file.write(f"                     /ApEinfo_fwdcolor={self.colors['iceyydm']}\n")
                    elif(self.reverse_feature_list[each_feature][2].lower() == "bsubamy"):
                        if(self.reverse_feature_list[each_feature][0] > self.reverse_feature_list[each_feature][1]):
                            file.write(f"     misc_feature     complement(join({self.length - self.reverse_feature_list[each_feature][1] + 1}..{self.length},1..{self.length - self.reverse_feature_list[each_feature][0]+1}))\n")
                            file.write(f"                     /label={each_feature}\n")
                            file.write(f"                     /color={self.colors['BsubAmy']}\n")
                            file.write(f"                     /ApEinfo_fwdcolor={self.colors['BsubAmy']}\n")
                        else:
                            file.write(f"     misc_feature     complement({self.length - self.reverse_feature_list[each_feature][1] + 1}..{self.length - self.reverse_feature_list[each_feature][0] + 1})\n")
                            file.write(f"                     /label={each_feature}\n")
                            file.write(f"                     /color={self.colors['BsubAmy']}\n")
                            file.write(f"                     /ApEinfo_fwdcolor={self.colors['BsubAmy']}\n")
                    elif(self.reverse_feature_list[each_feature][2].lower() == "rbs"):
                        if(self.reverse_feature_list[each_feature][0] > self.reverse_feature_list[each_feature][1]):
                            file.write(f"     misc_feature     complement(join({self.length - self.reverse_feature_list[each_feature][1] + 1}..{self.length},1..{self.length - self.reverse_feature_list[each_feature][0]+1}))\n")
                            file.write(f"                     /label={each_feature}\n")
                            file.write(f"                     /color={self.colors['rbs']}\n")
                            file.write(f"                     /ApEinfo_fwdcolor={self.colors['rbs']}\n")
                        else:
                            file.write(f"     misc_feature     complement({self.length - self.reverse_feature_list[each_feature][1] + 1}..{self.length - self.reverse_feature_list[each_feature][0] + 1})\n")
                            file.write(f"                     /label={each_feature}\n")
                            file.write(f"                     /color={self.colors['rbs']}\n")
                            file.write(f"                     /ApEinfo_fwdcolor={self.colors['rbs']}\n")
                    else:
                        if(self.reverse_feature_list[each_feature][0] > self.reverse_feature_list[each_feature][1]):
                            file.write(f"     misc_feature     complement(join({self.length - self.reverse_feature_list[each_feature][1] + 1}..{self.length},1..{self.length - self.reverse_feature_list[each_feature][0]+1}))\n")
                            file.write(f"                     /label={each_feature}\n")
                            file.write(f"                     /color={self.colors['binding']}\n")
                            file.write(f"                     /ApEinfo_fwdcolor={self.colors['binding']}\n")
                        else:
                            file.write(f"     misc_feature     complement({self.length - self.reverse_feature_list[each_feature][1] + 1}..{self.length - self.reverse_feature_list[each_feature][0] + 1})\n")
                            file.write(f"                     /label={each_feature}\n")
                            file.write(f"                     /color={self.colors['binding']}\n")
                            file.write(f"                     /ApEinfo_fwdcolor={self.colors['binding']}\n")

                if(type == "promoter" or type == "p+r"):
                    file.write(f"     promoter        1..{self.length}\n")
                    file.write(f"                     /label={self.name}\n")
                    file.write(f"                     /color={self.colors['promoter']}\n")
                    file.write(f"                     /ApEinfo_fwdcolor={self.colors['promoter']}\n")
                elif(type == "terminator"):
                    file.write(f"     promoter        1..{self.length}\n")
                    file.write(f"                     /label={self.name}\n")
                    file.write(f"                     /color={self.colors['terminator']}\n")
                    file.write(f"                     /ApEinfo_fwdcolor={self.colors['terminator']}\n")
                elif(type == "rbs"):
                    file.write(f"     promoter        1..{self.length}\n")
                    file.write(f"                     /label={self.name}\n")
                    file.write(f"                     /color={self.colors['rbs']}\n")
                    file.write(f"                     /ApEinfo_fwdcolor={self.colors['rbs']}\n")
                elif(type == "cds"):
                    file.write(f"     promoter        1..{self.length}\n")
                    file.write(f"                     /label={self.name}\n")
                    file.write(f"                     /color={self.colors['CDS']}\n")
                    file.write(f"                     /ApEinfo_fwdcolor={self.colors['CDS']}\n")
                for each_feature in self.EnzymeList:
                    EnzymeName = next(iter(each_feature.keys()))
                    EnzymeInfo = each_feature[EnzymeName]
                    EnzymeScarName = EnzymeInfo['name']
                    NameIndex = 0
                    # 通过scar位置判断酶切位点位置
                    for each_index in EnzymeInfo['index']:
                        if(EnzymeScarName[NameIndex]!= "undefine"):
                        #BsmBI forward
                            if(self.sequence[each_index-8:each_index-2].upper() == "CGTCTC"):
                                file.write(f"     misc_feature    {each_index-7}..{each_index-2}\n")
                                file.write(f"                     /label={EnzymeName}\n")
                                file.write(f"                     /color={self.colors['restriction_site']}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.colors['restriction_site']}\n")
                                file.write(f"     Scar            {each_index}..{each_index+3}\n")
                                file.write(f"                     /label=Scar {EnzymeScarName[NameIndex]}\n")
                                file.write(f"                     /color={self.colors['scar']}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.colors['scar']}\n")
                            #BsmBI reverse
                            elif(self.sequence[each_index+4:each_index+10].upper() == "GAGACG"):
                                file.write(f"     misc_feature    {each_index+5}..{each_index+10}\n")
                                file.write(f"                     /label={EnzymeName}\n")
                                file.write(f"                     /color={self.colors['restriction_site']}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.colors['restriction_site']}\n")
                                file.write(f"     Scar            {each_index}..{each_index+3}\n")
                                file.write(f"                     /label=Scar {EnzymeScarName[NameIndex]}\n")                            
                                file.write(f"                     /color={self.colors['scar']}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.colors['scar']}\n")

                            #BsaI forward
                            elif(self.sequence[each_index-8:each_index-2].upper() == "GGTCTC"):
                                file.write(f"     misc_feature    {each_index-7}..{each_index-2}\n")
                                file.write(f"                     /label={EnzymeName}\n")
                                file.write(f"                     /color={self.colors['restriction_site']}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.colors['restriction_site']}\n")
                                file.write(f"     Scar            {each_index}..{each_index+3}\n")
                                file.write(f"                     /label=Scar {EnzymeScarName[NameIndex]}\n")
                                file.write(f"                     /color={self.colors['scar']}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.colors['scar']}\n")
                            #BsaI reverse
                            elif(self.sequence[each_index+4:each_index+10].upper() == "GAGACC"):
                                file.write(f"     misc_feature    {each_index+5}..{each_index+10}\n")
                                file.write(f"                     /label={EnzymeName}\n")
                                file.write(f"                     /color={self.colors['restriction_site']}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.colors['restriction_site']}\n")
                                file.write(f"     Scar            {each_index}..{each_index+3}\n")
                                file.write(f"                     /label=Scar {EnzymeScarName[NameIndex]}\n")                            
                                file.write(f"                     /color={self.colors['scar']}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.colors['scar']}\n")

                            #BbsI forward
                            elif(self.sequence[each_index-9:each_index-3].upper() == "GAAGAC"):
                                file.write(f"     misc_feature    {each_index-8}..{each_index-3}\n")
                                file.write(f"                     /label={EnzymeName}\n")
                                file.write(f"                     /color={self.colors['restriction_site']}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.colors['restriction_site']}\n")
                                file.write(f"     Scar            {each_index}..{each_index+3}\n")
                                file.write(f"                     /label=Scar {EnzymeScarName[NameIndex]}\n")                            
                                file.write(f"                     /color={self.colors['scar']}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.colors['scar']}\n")
                            #BbsI reverse
                            elif(self.sequence[each_index+5:each_index+11].upper() == "GTCTTC"):
                                file.write(f"     misc_feature    {each_index+6}..{each_index+11}\n")
                                file.write(f"                     /label={EnzymeName}\n")
                                file.write(f"                     /color={self.colors['restriction_site']}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.colors['restriction_site']}\n")
                                file.write(f"     Scar            {each_index}..{each_index+3}\n")
                                file.write(f"                     /label=Scar {EnzymeScarName[NameIndex]}\n")                            
                                file.write(f"                     /color={self.colors['scar']}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.colors['scar']}\n")

                            #AarI forward
                            elif(self.sequence[each_index-12:each_index-5].upper() == "CACCTGC"):
                                file.write(f"     misc_feature    {each_index-13}..{each_index-5}\n")
                                file.write(f"                     /label={EnzymeName}\n")
                                file.write(f"                     /color={self.colors['restriction_site']}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.colors['restriction_site']}\n")
                                file.write(f"     Scar            {each_index}..{each_index+3}\n")
                                file.write(f"                     /label=Scar {EnzymeScarName[NameIndex]}\n")                            
                                file.write(f"                     /color={self.colors['scar']}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.colors['scar']}\n")

                            #AarI reverse
                            elif(self.sequence[each_index+7:each_index+14].upper() == "GCAGGTG"):
                                file.write(f"     misc_feature    {each_index+8}..{each_index+14}\n")
                                file.write(f"                     /label={EnzymeName}\n")
                                file.write(f"                     /color={self.colors['restriction_site']}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.colors['restriction_site']}\n")
                                file.write(f"     Scar            {each_index}..{each_index+3}\n")
                                file.write(f"                     /label=Scar {EnzymeScarName[NameIndex]}\n")                            
                                file.write(f"                     /color={self.colors['scar']}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.colors['scar']}\n")

                            #SapI forward
                            elif(self.sequence[each_index-9:each_index-2].upper() == "GCTCTTC"):
                                file.write(f"     misc_feature    {each_index-8}..{each_index-2}\n")
                                file.write(f"                     /label={EnzymeName}\n")
                                file.write(f"                     /color={self.colors['restriction_site']}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.colors['restriction_site']}\n")
                                file.write(f"     Scar            {each_index}..{each_index+2}\n")
                                file.write(f"                     /label=Scar {EnzymeScarName[NameIndex]}\n")                            
                                file.write(f"                     /color={self.colors['scar']}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.colors['scar']}\n")

                            #SapI reverse
                            elif(self.sequence[each_index+3:each_index+10].upper() == "GAAGAGC"):
                                file.write(f"     misc_feature    {each_index+4}..{each_index+10}\n")
                                file.write(f"                     /label={EnzymeName}\n")
                                file.write(f"                     /color={self.colors['restriction_site']}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.colors['restriction_site']}\n")
                                file.write(f"     Scar            {each_index}..{each_index+2}\n")
                                file.write(f"                     /label=Scar {EnzymeScarName[NameIndex]}\n")                            
                                file.write(f"                     /color={self.colors['scar']}\n")
                                file.write(f"                     /ApEinfo_fwdcolor={self.colors['scar']}\n")
                        NameIndex += 1
                file.write("ORIGIN\n")
                numOfline = (self.length // 60) + 1
                offset = 0
                for each_line in range(0,numOfline):
                    file.write(f" "*(9-len(str(1+(60*each_line))))+f"{1+(60*each_line)} ")
                    if each_line != numOfline - 1:
                        for i in range(0,6):
                            if(i != 5):
                                file.write(f"{self.sequence[offset:offset+10]} ")
                                offset = offset + 10
                            else:
                                file.write(f"{self.sequence[offset:offset+10]}")
                                offset = offset + 10
                    else:
                        col_number = (len(self.sequence[offset:]) // 10) + 1
                        for i in range(0,col_number):
                            if(i != col_number -1):
                                file.write(f"{self.sequence[offset:offset+10]} ")
                                offset = offset + 10
                            else:
                                file.write(f"{self.sequence[offset:offset+10]} ")
                                offset = offset + 10
                    file.write("\n")
                file.write('//')
                file.flush()
                file.close()
                
        except Exception as exc:
            raise exc
    def GenerateAPEFile(self,name, sequence):
        pass
