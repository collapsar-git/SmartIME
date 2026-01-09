import os
import math
import heapq
from knowledge import KnowledgeBase

class HMM_Model:
    def __init__(self):
        self.start_p = {}  
        self.trans_p = {}  
        self.emit_p = {}   
        self.pinyin_set = set() 
        self.min_prob = -100.0 
        
        # 初始化知识库
        self.kb = KnowledgeBase()
        # 指定的路径
        self.plus_data_path = r".\data"
        if os.path.exists(self.plus_data_path):
            self.kb.load_data(self.plus_data_path)

    def load_data(self, pinyin_file, char_file, bigram_file):
        """ 加载 HMM 语料 """
        print("正在加载 HMM 语料...")
        if not os.path.exists(pinyin_file):
            print(f"[Error] 找不到文件: {pinyin_file}")
            return

        with open(pinyin_file, 'r', encoding='gb18030') as f:
            for line in f:
                line = line.strip()
                if not line or ':' not in line: continue
                pinyin, chars = line.split(':')
                self.emit_p[pinyin] = list(chars)
                self.pinyin_set.add(pinyin)

        char_count = {}
        total_count = 0
        if os.path.exists(char_file):
            with open(char_file, 'r', encoding='gb18030') as f:
                for line in f:
                    if line.startswith('/*') or not line.strip(): continue
                    parts = line.strip().split('\t')
                    if len(parts) < 3: continue
                    char, freq = parts[1], int(parts[2])
                    char_count[char] = freq
                    total_count += freq
        
        for char, freq in char_count.items():
            self.start_p[char] = math.log(freq / total_count) if total_count else self.min_prob

        if os.path.exists(bigram_file):
            with open(bigram_file, 'r', encoding='gb18030') as f:
                for line in f:
                    if line.startswith('/*') or not line.strip(): continue
                    parts = line.strip().split('\t')
                    if len(parts) < 3: continue
                    word, freq = parts[1], int(parts[2])
                    if len(word) != 2: continue
                    prev, curr = word[0], word[1]
                    if prev not in self.trans_p: self.trans_p[prev] = {}
                    if prev in char_count and char_count[prev] > 0:
                        self.trans_p[prev][curr] = math.log(freq / char_count[prev])
        print("HMM 语料加载完成！")

    def split_pinyin(self, text):
        res = []
        i = 0
        text = text.replace(" ", "")
        length = len(text)
        while i < length:
            found = False
            for step in range(6, 0, -1):
                if i + step > length: continue
                sub = text[i : i+step]
                if sub in self.pinyin_set:
                    res.append(sub)
                    i += step
                    found = True
                    break
            if not found: i += 1
        return res

    def get_trans_score(self, prev_char, curr_char):
        if prev_char in self.trans_p and curr_char in self.trans_p[prev_char]:
            return self.trans_p[prev_char][curr_char]
        return self.start_p.get(curr_char, self.min_prob) - 8.0 

    def beam_search(self, pinyin_list, top_k=5):
        if not pinyin_list: return []
        BEAM_WIDTH = 30 
        first_py = pinyin_list[0]
        first_chars = self.emit_p.get(first_py, [])
        
        current_paths = []
        for char in first_chars:
            score = self.start_p.get(char, self.min_prob)
            current_paths.append( (score, char, char) )
        current_paths = heapq.nlargest(BEAM_WIDTH, current_paths, key=lambda x: x[0])

        for i in range(1, len(pinyin_list)):
            next_py = pinyin_list[i]
            next_chars = self.emit_p.get(next_py, [])
            if not next_chars: continue 
            new_paths = []
            for prev_score, prev_path, prev_char in current_paths:
                for curr_char in next_chars:
                    trans = self.get_trans_score(prev_char, curr_char)
                    new_score = prev_score + trans
                    new_path = prev_path + curr_char
                    new_paths.append( (new_score, new_path, curr_char) )
            current_paths = heapq.nlargest(BEAM_WIDTH, new_paths, key=lambda x: x[0])

        return [path for score, path, last_char in current_paths[:top_k]]

    def get_top_candidates(self, pinyin_input, top_k=5):
        """
        获取候选词：成语速录 > HMM计算
        """
        final_results = []
        
        # 检查成语速录 (Feature: szdt -> 守株待兔)
        # 如果输入是纯字母且没有空格，尝试查成语
        raw_input = ""
        if isinstance(pinyin_input, list):
            raw_input = "".join(pinyin_input)
        elif isinstance(pinyin_input, str):
            raw_input = pinyin_input.replace(" ", "")
            
        idiom_match = self.kb.get_idiom(raw_input)
        if idiom_match:
            final_results.append(idiom_match)

        # 运行 HMM 
        if isinstance(pinyin_input, str):
            if ' ' in pinyin_input:
                py_list = pinyin_input.split()
            else:
                py_list = self.split_pinyin(pinyin_input)
        else:
            py_list = pinyin_input

        if py_list:
            if len(py_list) == 1:
                chars = self.emit_p.get(py_list[0], [])
                sorted_chars = sorted(chars, key=lambda c: self.start_p.get(c, self.min_prob), reverse=True)
                hmm_res = sorted_chars[:top_k]
            else:
                hmm_res = self.beam_search(py_list, top_k)
            
            # 合并结果，去重
            for res in hmm_res:
                if res not in final_results:
                    final_results.append(res)

        return final_results[:top_k]

    def get_associations(self, last_char, top_k=5):
        if last_char not in self.trans_p: return []
        next_chars = self.trans_p[last_char]
        sorted_chars = sorted(next_chars.items(), key=lambda x: x[1], reverse=True)
        return [char for char, prob in sorted_chars[:top_k]]
    
    # 歇后语接口
    def get_xiehouyu_answer(self, text):
        return self.kb.get_xiehouyu(text)