from numpy import identity
from . import KmerIndex

class featureIdentify:
    def __init__(self):
        self.initFeatureIdentify()

    def initFeatureIdentify(self):
        self.OriginFeatureDict = {}
        self.CDSFeatureDict = {}
        self.PromoterFeatureDict = {}
        self.TerminatorFeatureDict = {}
        self.miscFeatureDict = {}
        self.primerBindDict = {}
        self.spaceFeatureDict = {}
        self.HomologyDict = {}
        self.AttpDict = {}
        self.IceyydmDict = {}
        self.BsubAmyDict = {}
        
        self.OriginFeatureKmer = KmerIndex.KmerIndex()
        self.CDSFeatureKmer = KmerIndex.KmerIndex()
        self.PromoterFeatureKmer = KmerIndex.KmerIndex()
        self.TerminatorFeatureKmer = KmerIndex.KmerIndex()
        self.miscFeatureKmer = KmerIndex.KmerIndex()
        self.primerBindKmer = KmerIndex.KmerIndex()
        self.spacerKmer = KmerIndex.KmerIndex()
        self.HomoKmer = KmerIndex.KmerIndex()
        self.AttpKmer = KmerIndex.KmerIndex()
        self.IceyydmKmer = KmerIndex.KmerIndex()
        self.BsubAmyKmer = KmerIndex.KmerIndex()
        
        type = ""
        with open(r'C:\Users\admin\Desktop\WebDatabase\WebDataWorld\LabDatabase\CaculateModule\BasicFeature.txt','r',encoding='utf-8') as file:
            lines = file.readlines()
            for line in lines:
                line = line.strip('\n')
                if(line.__contains__('#')):
                    type = "Origin" if line == "#Origin" else "CDS" if line == "#Protein" else "promoter" if line == "#Promoter" else "terminator" if line == "#terminator" else "primer_bind" if line == "#binding" else "spacer" if line=="#spacer" else "homo" if line=="#Homology Arm" else "attp" if line=="#Attp" else "iceyydm" if line=="#ICEyydm" else "Bsubamy" if line=="#B.subtilis amyE" else "misc_feature"
                else:
                    line_content = line.split(":")
                    if type == "Origin":
                        self.OriginFeatureDict[line_content[0]] = line_content[1]
                        self.OriginFeatureKmer.add_sequence(line_content[0],line_content[1])
                    elif type == "CDS":
                        self.CDSFeatureDict[line_content[0]] = line_content[1]
                        self.CDSFeatureKmer.add_sequence(line_content[0],line_content[1])
                    elif type == "promoter":
                        self.PromoterFeatureDict[line_content[0]] = line_content[1]
                        self.PromoterFeatureKmer.add_sequence(line_content[0],line_content[1])
                    elif type == "terminator":
                        self.TerminatorFeatureDict[line_content[0]] = line_content[1]
                        self.TerminatorFeatureKmer.add_sequence(line_content[0],line_content[1])
                    elif type == "primer_bind":
                        self.primerBindDict[line_content[0]] = line_content[1]
                        self.primerBindKmer.add_sequence(line_content[0],line_content[1])
                    elif type == "misc_feature":
                        self.miscFeatureDict[line_content[0]] = line_content[1]
                        self.miscFeatureKmer.add_sequence(line_content[0],line_content[1])
                    elif type == "spacer":
                        self.spaceFeatureDict[line_content[0]] = line_content[1]
                        self.spacerKmer.add_sequence(line_content[0],line_content[1])
                    elif type == "homo":
                        self.HomologyDict[line_content[0]] = line_content[1]
                        self.HomoKmer.add_sequence(line_content[0],line_content[1])
                    elif type == "attp":
                        self.AttpDict[line_content[0]] = line_content[1]
                        self.AttpKmer.add_sequence(line_content[0], line_content[1])
                    elif type == "iceyydm":
                        self.IceyydmDict[line_content[0]] = line_content[1]
                        self.IceyydmKmer.add_sequence(line_content[0], line_content[1])
                    elif type == "Bsubamy":
                        self.BsubAmyDict[line_content[0]] = line_content[1]
                        self.BsubAmyKmer.add_sequence(line_content[0], line_content[1])
                        
    

    def featureMatch(self, sequence):
        FeatureList = {}
        self.OriginResult = self.OriginFeatureKmer.query(sequence)
        self.CDSResult = self.CDSFeatureKmer.query(sequence)
        self.PromoterResult = self.PromoterFeatureKmer.query(sequence)
        self.TerminatorResult = self.TerminatorFeatureKmer.query(sequence)
        self.miscResult = self.miscFeatureKmer.query(sequence)
        self.primerResult = self.primerBindKmer.query(sequence)
        self.spaceResult = self.spacerKmer.query(sequence)
        self.HomoResult = self.HomoKmer.query(sequence)
        self.attpResult = self.AttpKmer.query(sequence)
        self.iceyydmResult = self.IceyydmKmer.query(sequence)
        self.BsubamyResult = self.BsubAmyKmer.query(sequence)
        
        for match in self.OriginResult.keys():
            seq_name = self.OriginResult[match]['seq_id']
            # db_seq = self.OriginFeatureDict[seq_name]
            q_start = self.OriginResult[match]['start']
            q_end = self.OriginResult[match]['end']
            # db_start = self.OriginResult[match]['offset']+self.OriginResult[match]['start']
            # db_end = self.OriginResult[match]['offset']+self.OriginResult[match]['end']
            # query_segment = sequence[q_start:q_end]
            # db_segment = db_seq[db_start:db_end]
            # match_length = len(query_segment)
            FeatureList[seq_name] = [q_start+1,q_end,"Origin"]
        for match in self.CDSResult.keys():
            seq_name = self.CDSResult[match]['seq_id']
            # db_seq = self.CDSFeatureDict[seq_name]
            q_start = self.CDSResult[match]['start']
            q_end = self.CDSResult[match]['end']
            # db_start = self.CDSResult[match]['offset']+self.CDSResult[match]['start']
            # db_end = self.CDSResult[match]['offset']+self.CDSResult[match]['end']
            # query_segment = sequence[q_start:q_end]
            # db_segment = db_seq[db_start:db_end]
            # match_length = len(query_segment)
            # if(match_length > 0):
            #     identical = sum(1 for a,b in zip(query_segment,db_segment) if a== b)
            #     similarity = round(identical / match_length,3)
            #     if(similarity >= 0.9):
            FeatureList[seq_name] = [q_start+1,q_end,"CDS"]
        for match in self.PromoterResult.keys():
            seq_name = self.PromoterResult[match]['seq_id']
            # db_seq = self.PromoterFeatureDict[seq_name]
            q_start = self.PromoterResult[match]['start']
            q_end = self.PromoterResult[match]['end']
            # db_start = self.PromoterResult[match]['offset']+self.PromoterResult[match]['start']
            # db_end = self.PromoterResult[match]['offset']+self.PromoterResult[match]['end']
            # query_segment = sequence[q_start:q_end]
            # db_segment = db_seq[db_start:db_end]
            # match_length = len(query_segment)
            # if(match_length > 0):
            #     identical = sum(1 for a,b in zip(query_segment,db_segment) if a== b)
            #     similarity = round(identical / match_length,3)
            #     if(similarity >= 0.98):
            FeatureList[seq_name] = [q_start+1,q_end,"Promoter"]
        for match in self.TerminatorResult.keys():
            seq_name = self.TerminatorResult[match]['seq_id']
            # db_seq = self.TerminatorFeatureDict[seq_name]
            q_start = self.TerminatorResult[match]['start']
            q_end = self.TerminatorResult[match]['end']
            # db_start = self.TerminatorResult[match]['offset']+self.TerminatorResult[match]['start']
            # db_end = self.TerminatorResult[match]['offset']+self.TerminatorResult[match]['end']
            # query_segment = sequence[q_start:q_end]
            # db_segment = db_seq[db_start:db_end]
            # match_length = len(query_segment)
            # if(match_length > 0):
            #     identical = sum(1 for a,b in zip(query_segment,db_segment) if a== b)
            #     similarity = round(identical / match_length,3)
            #     if(similarity >= 0.9):
            FeatureList[seq_name] = [q_start+1,q_end,"Terminator"]
        for match in self.miscResult.keys():
            seq_name = self.miscResult[match]['seq_id']
            # db_seq = self.miscFeatureDict[seq_name]
            q_start = self.miscResult[match]['start']
            q_end = self.miscResult[match]['end']
            # db_start = self.miscResult[match]['offset']+self.miscResult[match]['start']
            # db_end = self.miscResult[match]['offset']+self.miscResult[match]['end']
            # query_segment = sequence[q_start:q_end]
            # db_segment = db_seq[db_start:db_end]
            # match_length = len(query_segment)
            # if(match_length > 0):
            #     identical = sum(1 for a,b in zip(query_segment,db_segment) if a== b)
            #     similarity = round(identical / match_length,3)
            #     if(similarity >= 0.9):
            FeatureList[seq_name] = [q_start+1,q_end,"misc_feature"]
            
        for match in self.primerResult.keys():
            seq_name = self.primerResult[match]['seq_id']
            q_start = self.primerResult[match]['start']
            q_end = self.primerResult[match]['end']
            FeatureList[seq_name] = [q_start+1,q_end,"primer_bind"]
            
        for match in self.spaceResult.keys():
            seq_name=self.spaceResult[match]['seq_id']
            q_start = self.spaceResult[match]['start']
            q_end = self.spaceResult[match]['end']
            FeatureList[seq_name] = [q_start+1,q_end,"spacer"]
            
        for match in self.HomoResult.keys():
            seq_name=self.HomoResult[match]['seq_id']
            q_start = self.HomoResult[match]['start']
            q_end = self.HomoResult[match]['end']
            FeatureList[seq_name] = [q_start+1,q_end,"homo"]
            
        for match in self.attpResult.keys():
            seq_name = self.attpResult[match]['seq_id']
            q_start = self.attpResult[match]['start']
            q_end = self.attpResult[match]['end']
            FeatureList[seq_name] = [q_start+1,q_end,"attp"]
            
        for match in self.iceyydmResult.keys():
            seq_name = self.iceyydmResult[match]['seq_id']
            q_start = self.iceyydmResult[match]['start']
            q_end = self.iceyydmResult[match]['end']
            FeatureList[seq_name] = [q_start+1,q_end,"iceyydm"]
            
        for match in self.BsubamyResult.keys():
            seq_name = self.BsubamyResult[match]['seq_id']
            q_start = self.BsubamyResult[match]['start']
            q_end = self.BsubamyResult[match]['end']
            FeatureList[seq_name] = [q_start+1,q_end,"BsubAmy"]
        return FeatureList