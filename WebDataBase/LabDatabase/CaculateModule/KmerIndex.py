import numpy as np
from collections import defaultdict
import heapq
import sys

sys.path.append(r"C:\Users\admin\Desktop\LabDNASeqSearch")


#由于数据库不同，所以Seq_id存储值为Seq_name

class KmerIndex:
    def __init__(self,k=5):
        self.k = k
        self.index = defaultdict(list)
    
    def add_sequence(self,seq_id,sequence):
        sequence = sequence.upper()
        seq_len = len(sequence)

        if seq_len < self.k:
            return
        
        for i in range(seq_len - self.k +1):
            kmer = sequence[i:i+self.k]
            self.index[kmer].append((seq_id,i))

    def query(self,sequence, min_matches=4):
        sequence = sequence.upper()
        matches = defaultdict(list)
        query_len = len(sequence)
        for i in range(query_len - self.k+1):
            kmer = sequence[i:i+self.k]
            for seq_id,pos in self.index.get(kmer,[]):
                offset = pos -i
                matches[(seq_id, offset)].append(i)
        
        significant_matches = {}
        for (seq_id,offset), positions in matches.items():
            match_count = len(positions)
            density = match_count/(max(positions) - min(positions)+self.k) if len(positions)>1 else 1
            if match_count >= min_matches and density >= 0.9:
                if(significant_matches.keys().__contains__(seq_id)):
                    match_count_old = significant_matches[seq_id]['match_count']
                    offset_old = significant_matches[seq_id]['offset']
                    density_old = significant_matches[seq_id]['density']
                    start = significant_matches[seq_id]['start']
                    end = significant_matches[seq_id]['end']
                    start_new = min(positions)
                    end_new = max(positions)+self.k
                    if(start_new == 0 and end == query_len):
                        significant_matches[seq_id] = {'seq_id':seq_id,
                                                    'offset':min(offset_old, offset),
                                                    'match_count':match_count+match_count_old,
                                                    'density':max(density,density_old),
                                                    'start':start,
                                                    'end':end_new}
                    if(start == 0 and end_new == query_len):
                        significant_matches[seq_id] = {'seq_id':seq_id,
                                                      'offset':min(offset_old, offset),
                                                      'match_count':match_count+match_count_old,
                                                      'density':max(density,density_old),
                                                      'start':start_new,
                                                      'end':end}
                    if(start_new == end):
                        significant_matches[seq_id] = {'seq_id':seq_id,
                                                    'offset':min(offset_old, offset),
                                                    'match_count':match_count+match_count_old,
                                                    'density':max(density,density_old),
                                                    'start':start,
                                                    'end':end_new}
                else:
                    significant_matches[seq_id] = {'seq_id':seq_id,
                                            'offset':offset,
                                            'match_count':match_count,
                                            'density':density,
                                            'start':min(positions),
                                            'end':max(positions)+self.k}
        # significant_matches.sort(key=lambda x:x['match_count'],reverse=True)
        return significant_matches