import json
import os

class KnowledgeBase:
    def __init__(self):
        self.idiom_dict = {}      # szdt -> 守株待兔
        self.xiehouyu_dict = {}   # 谜面 -> 谜底
        self.definition_dict = {} # 词/字 -> 解释
        self.emoji_dict = {}      # haha -> 😂 (新增!)
        
    def load_data(self, root_dir):
        """ 加载所有 JSON 数据 """
        print(f"正在加载特色语料库: {root_dir} ...")
        
        # 依次加载各类数据
        self._load_json(root_dir, "idiom.json", "成语")
        self._load_json(root_dir, "xiehouyu.json", "歇后语")
        self._load_json(root_dir, "ci.json", "词语")
        self._load_json(root_dir, "word.json", "汉字")
        self._load_json(root_dir, "emoji.json", "Emoji") # <--- 新增

        print(f"知识库加载完毕: 成语 {len(self.idiom_dict)} | Emoji {len(self.emoji_dict)}")

    def _load_json(self, root_dir, filename, type_name):
        path = os.path.join(root_dir, filename)
        if not os.path.exists(path): return

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                if type_name == "成语":
                    for item in data:
                        abbr = item.get('abbreviation', '')
                        word = item.get('word', '')
                        expl = item.get('explanation', '')
                        if abbr and word: self.idiom_dict[abbr] = word
                        if word and expl: self.definition_dict[word] = f"[成语] {expl}"

                elif type_name == "歇后语":
                    for item in data:
                        riddle = item.get('riddle', '')
                        answer = item.get('answer', '')
                        if riddle:
                            clean_riddle = riddle.replace('，', '').replace(',', '')
                            self.xiehouyu_dict[clean_riddle] = answer
                            self.definition_dict[riddle] = f"[歇后语] {answer}"

                elif type_name == "词语":
                    for item in data:
                        ci = item.get('ci', '')
                        expl = item.get('explanation', '')
                        if ci and expl and ci not in self.definition_dict:
                            self.definition_dict[ci] = f"[解释] {expl}"

                elif type_name == "汉字":
                    for item in data:
                        word = item.get('word', '')
                        strokes = item.get('strokes', '')
                        radicals = item.get('radicals', '')
                        if word: self.definition_dict[word] = f"[字典] 部首:{radicals} | 笔画:{strokes}"
                
                # Emoji 解析逻辑 
                elif type_name == "Emoji":
                    for item in data:
                        py = item.get('pinyin', '')
                        emoji = item.get('emoji', '')
                        if py and emoji:
                            self.emoji_dict[py] = emoji
                            # 给表情加个简单的解释，防止报错
                            self.definition_dict[emoji] = f"[表情] 拼音: {py}"

        except Exception as e:
            print(f"[Warn] 加载 {filename} 失败: {e}")

    def get_idiom(self, abbr):
        return self.idiom_dict.get(abbr)

    def get_xiehouyu(self, text):
        if text in self.xiehouyu_dict: return self.xiehouyu_dict[text]
        return None

    def get_definition(self, text):
        if "——" in text: text = text.split("——")[0].strip()
        return self.definition_dict.get(text, "暂无详细收录")

    # 新增接口
    def get_emoji(self, pinyin):
        return self.emoji_dict.get(pinyin)