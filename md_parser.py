#!/usr/bin/env python3
"""
基于 MinerU Markdown 的题库解析器
从 MD 文件中提取题目和答案，输出 questions.json
"""
import re
import json
import os

WORK_DIR = os.path.dirname(os.path.abspath(__file__))
MD_DIR = os.path.join(WORK_DIR, 'file_json')

# ============================================================
# 文件加载
# ============================================================

def load_md_files():
    """加载4个MD文件，返回 (上册文本, 下册文本)"""
    files = sorted(os.listdir(MD_DIR))
    
    upper_files = [f for f in files if f.endswith('.md') and '会计（上）' in f]
    lower_files = [f for f in files if f.endswith('.md') and '会计（下）' in f]
    
    # 按文件名中的起始页码排序: MinerU_1_ < MinerU_126_
    def sort_key(name):
        m = re.match(r'MinerU_markdown_(\d+)_', name)
        return int(m.group(1)) if m else 0
    
    upper_files.sort(key=sort_key)
    lower_files.sort(key=sort_key)
    
    upper_text = ''
    for f in upper_files:
        with open(os.path.join(MD_DIR, f), 'r', encoding='utf-8') as fp:
            upper_text += fp.read() + '\n'
    
    lower_text = ''
    for f in lower_files:
        with open(os.path.join(MD_DIR, f), 'r', encoding='utf-8') as fp:
            lower_text += fp.read() + '\n'
    
    print(f'上册文本: {len(upper_text)} 字符')
    print(f'下册文本: {len(lower_text)} 字符')
    
    return upper_text, lower_text


# ============================================================
# 中文数字转换
# ============================================================

CN_NUM = {
    '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
    '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
    '十一': 11, '十二': 12, '十三': 13, '十四': 14, '十五': 15,
    '十六': 16, '十七': 17, '十八': 18, '十九': 19, '二十': 20,
    '二十一': 21, '二十二': 22, '二十三': 23, '二十四': 24, '二十五': 25,
    '二十六': 26, '二十七': 27, '二十八': 28, '二十九': 29, '三十': 30,
}

def cn_to_num(cn):
    """中文数字转阿拉伯数字"""
    return CN_NUM.get(cn, 0)


# ============================================================
# 上册题目解析
# ============================================================

# 正则表达式
CHAPTER_RE = re.compile(r'^#{1,3}\s*第([一二三四五六七八九十百]+)章\s*(.*)')
SECTION_RE = re.compile(r'^#{1,3}\s*[一二三四五六七八九十]+、(单项选择题|多项选择题|计算分析题|综合题)')
# 题号: "1. " 或 "1." 或 "10.（非标准题）"
QUESTION_RE = re.compile(r'^(\d+)\.\s*(.*)')
# 选项: "A. xxx" 或 "A.xxx"
OPTION_RE = re.compile(r'^([A-H])\.\s*(.*)')
# 套卷/大题部分标记（第四部分及专题）
STOP_RE = re.compile(r'^#{1,3}\s*(第四部分|专题[一二三四五六七八九十]+)')
# 子标题（基础提升、终极试炼等，忽略）
SUB_LABEL_RE = re.compile(r'^#{1,3}\s*(基础提升|终极试炼|扫码做题)')


def parse_questions(text):
    """从上册 MD 文本解析所有客观题"""
    chapters = {}  # {chapter_num: {'title': str, 'sections': {section_type: [questions]}}}
    
    current_chapter = None
    current_section = None  # 'single_choice' or 'multiple_choice'
    stop_parsing = False
    
    # 当前正在构建的题目
    q_num = None
    q_text = []
    q_options = []  # [(label, text)]
    current_option_label = None
    current_option_text = []
    
    lines = text.split('\n')
    
    def flush_option():
        """保存当前选项"""
        nonlocal current_option_label, current_option_text
        if current_option_label and current_option_text:
            q_options.append((current_option_label, ' '.join(current_option_text).strip()))
        current_option_label = None
        current_option_text = []
    
    def flush_question():
        """保存当前题目"""
        nonlocal q_num, q_text, q_options, current_option_label, current_option_text
        flush_option()
        if q_num is not None and q_text:
            question_text = ' '.join(q_text).strip()
            if current_chapter and current_section:
                if current_chapter not in chapters:
                    chapters[current_chapter] = {'title': '', 'sections': {}}
                sec_key = current_section
                if sec_key not in chapters[current_chapter]['sections']:
                    chapters[current_chapter]['sections'][sec_key] = []
                chapters[current_chapter]['sections'][sec_key].append({
                    'number': q_num,
                    'question': question_text,
                    'options': [{'label': lbl, 'text': txt} for lbl, txt in q_options]
                })
        q_num = None
        q_text = []
        q_options = []
        current_option_label = None
        current_option_text = []
    
    for line in lines:
        line = line.strip()
        
        # 跳过空行
        if not line:
            continue
        
        # 跳过图片
        if line.startswith('!['):
            continue
        
        # 跳过表格
        if line.startswith('<table') or line.startswith('</table'):
            continue
        
        # 检查是否进入套卷/大题部分 -> 停止解析章节题目
        if STOP_RE.match(line):
            flush_question()
            stop_parsing = True
            continue
        
        if stop_parsing:
            continue
        
        # 检查章节标题
        ch_match = CHAPTER_RE.match(line)
        if ch_match:
            flush_question()
            cn = ch_match.group(1)
            title = ch_match.group(2).strip()
            current_chapter = cn_to_num(cn)
            if current_chapter and current_chapter not in chapters:
                chapters[current_chapter] = {
                    'title': f'第{cn}章 {title}',
                    'sections': {}
                }
            current_section = None
            continue
        
        # 检查题型标题
        sec_match = SECTION_RE.match(line)
        if sec_match:
            flush_question()
            sec_name = sec_match.group(1)
            if sec_name == '单项选择题':
                current_section = 'single_choice'
            elif sec_name == '多项选择题':
                current_section = 'multiple_choice'
            else:
                current_section = None  # 主观题不处理
            continue
        
        # 跳过子标签（基础提升、终极试炼等）
        if SUB_LABEL_RE.match(line):
            continue
        
        # 跳过其他 # 标题（如“扫码做题”）
        if line.startswith('#'):
            continue
        
        # 跳过非题目相关文本
        if line.startswith('使用') and '扫码做题' in line:
            continue
        
        # 检查选项 (A-H)
        opt_match = OPTION_RE.match(line)
        if opt_match and current_option_label is None or opt_match:
            if q_num is not None:
                flush_option()
                current_option_label = opt_match.group(1)
                current_option_text = [opt_match.group(2)]
                continue
        
        # 如果当前有选项在收集，继续收集选项文本
        if current_option_label is not None:
            # 检查是否是新题号
            q_match = QUESTION_RE.match(line)
            if q_match:
                flush_question()
                q_num = int(q_match.group(1))
                q_text = [q_match.group(2)] if q_match.group(2) else []
                continue
            # 检查是否是另一个选项
            opt_match2 = OPTION_RE.match(line)
            if opt_match2:
                flush_option()
                current_option_label = opt_match2.group(1)
                current_option_text = [opt_match2.group(2)]
                continue
            # 继续收集选项文本
            current_option_text.append(line)
            continue
        
        # 检查题号
        q_match = QUESTION_RE.match(line)
        if q_match:
            flush_question()
            q_num = int(q_match.group(1))
            q_text = [q_match.group(2)] if q_match.group(2) else []
            continue
        
        # 如果当前有题目在收集，继续收集题目文本
        if q_num is not None:
            q_text.append(line)
    
    # 处理最后一题
    flush_question()
    
    return chapters


def parse_subjective_questions_upper(text):
    """
    从上册 MD 文本解析第三部分的主观题题目。
    
    返回: {topic_name: {section_type: {qnum: {'question': str, 'requirements': list, 'other_info': list}}}}
    """
    results = {}
    current_topic = None
    current_section = None
    current_qnum = None
    in_question = False
    question_lines = []
    requirements = []
    other_info = []
    collecting_requirements = False
    
    lines = text.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i].rstrip()
        if not line:
            i += 1
            continue
        
        # 检测第三部分开始
        if re.match(r'^#{1,3}\s*第三部分', line):
            current_topic = None
            current_section = None
            current_qnum = None
            in_question = False
            question_lines = []
            requirements = []
            other_info = []
            collecting_requirements = False
            i += 1
            continue
        
        # 如果不在第三部分，跳过
        if not any(re.match(r'^#{1,3}\s*第三部分', l) for l in lines[:i+1]):
            i += 1
            continue
        
        # 检测专题标题（专题一、专题二等）
        topic_match = re.match(r'^#{1,3}\s*(专题[一二三四五六七八九十]+)\s*(.*)$', line)
        if topic_match:
            # 保存上一题
            if current_qnum and current_section and current_topic:
                topic_dict = results.setdefault(current_topic, {})
                sec_dict = topic_dict.setdefault(current_section, {})
                sec_dict[current_qnum] = {
                    'question': '\n'.join(question_lines).strip(),
                    'requirements': requirements[:],
                    'other_info': other_info[:]
                }
            
            current_topic = topic_match.group(1)
            if topic_match.group(2).strip():
                current_topic += ' ' + topic_match.group(2).strip()
            current_section = None
            current_qnum = None
            in_question = False
            question_lines = []
            requirements = []
            other_info = []
            collecting_requirements = False
            i += 1
            continue
        
        # 检测题型（一、计算分析题 / 二、综合题）
        section_match = re.match(r'^#{1,3}\s*[一二]+、(.+)', line)
        if section_match:
            # 保存上一题
            if current_qnum and current_section and current_topic:
                topic_dict = results.setdefault(current_topic, {})
                sec_dict = topic_dict.setdefault(current_section, {})
                sec_dict[current_qnum] = {
                    'question': '\n'.join(question_lines).strip(),
                    'requirements': requirements[:],
                    'other_info': other_info[:]
                }
            
            current_section = section_match.group(1)
            current_qnum = None
            in_question = False
            question_lines = []
            requirements = []
            other_info = []
            collecting_requirements = False
            i += 1
            continue
        
        # 检测题号（1. 2×24 年至...）
        qnum_match = QUESTION_RE.match(line)
        if qnum_match:
            # 保存上一题
            if current_qnum and current_section and current_topic:
                topic_dict = results.setdefault(current_topic, {})
                sec_dict = topic_dict.setdefault(current_section, {})
                sec_dict[current_qnum] = {
                    'question': '\n'.join(question_lines).strip(),
                    'requirements': requirements[:],
                    'other_info': other_info[:]
                }
            
            current_qnum = int(qnum_match.group(1))
            in_question = True
            question_lines = [qnum_match.group(2)]
            requirements = []
            other_info = []
            collecting_requirements = False
            i += 1
            continue
        
        # 收集题目内容
        if in_question and current_qnum:
            # 检测特殊段落标记
            if re.match(r'^#{1,3}\s*其他资料[:：]?$', line):
                collecting_requirements = False
                other_info.append(line)
                i += 1
                continue
            elif re.match(r'^#{1,3}\s*要求[:：]?$', line):
                collecting_requirements = True
                i += 1
                continue
            
            if collecting_requirements:
                requirements.append(line)
            else:
                question_lines.append(line)
        
        i += 1
    
    # 保存最后一题
    if current_qnum and current_section and current_topic:
        topic_dict = results.setdefault(current_topic, {})
        sec_dict = topic_dict.setdefault(current_section, {})
        sec_dict[current_qnum] = {
            'question': '\n'.join(question_lines).strip(),
            'requirements': requirements[:],
            'other_info': other_info[:]
        }
    
    print(f'上册主观题统计:')
    for topic_name, topic_data in results.items():
        print(f'  {topic_name}:')
        for sec_name, q_dict in topic_data.items():
            print(f'    {sec_name}: {len(q_dict)}题')
    
    return results


# ============================================================
# 下册主观题解析（第三部分）
# ============================================================

def parse_subjective_questions(text):
    """
    从下册 MD 文本解析第三部分的主观题答案。
    
    返回: {topic_name: {section_type: {qnum: explanation}}}
    """
    results = {}
    current_topic = None
    current_section = None
    current_qnum = None
    in_answer = False
    answer_lines = []
    
    lines = text.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i].rstrip()
        if not line:
            i += 1
            continue
        
        # 检测第三部分开始
        if re.match(r'^#{1,3}\s*第三部分', line):
            current_topic = None
            current_section = None
            current_qnum = None
            in_answer = False
            answer_lines = []
            i += 1
            continue
        
        # 如果不在第三部分，跳过
        if not any(re.match(r'^#{1,3}\s*第三部分', l) for l in lines[:i+1]):
            i += 1
            continue
        
        # 检测专题标题（专题一、专题二等）
        topic_match = re.match(r'^#{1,3}\s*(专题[一二三四五六七八九十]+)\s*(.*)$', line)
        if topic_match:
            # 保存上一题的答案
            if current_qnum and current_section and current_topic:
                topic_dict = results.setdefault(current_topic, {})
                sec_dict = topic_dict.setdefault(current_section, {})
                sec_dict[current_qnum] = '\n'.join(answer_lines).strip()
            
            current_topic = topic_match.group(1)
            if topic_match.group(2).strip():
                current_topic += ' ' + topic_match.group(2).strip()
            current_section = None
            current_qnum = None
            in_answer = False
            answer_lines = []
            i += 1
            continue
        
        # 检测题型（一、计算分析题 / 二、综合题）
        section_match = re.match(r'^#{1,3}\s*[一二]+、(.+)', line)
        if section_match:
            # 保存上一题的答案
            if current_qnum and current_section and current_topic:
                topic_dict = results.setdefault(current_topic, {})
                sec_dict = topic_dict.setdefault(current_section, {})
                sec_dict[current_qnum] = '\n'.join(answer_lines).strip()
            
            current_section = section_match.group(1)
            current_qnum = None
            in_answer = False
            answer_lines = []
            i += 1
            continue
        
        # 检测题号行（## 1. 【答案】 或 ## 1. 或 1. ）
        qnum_match = QNUM_LINE_RE.match(line)
        if qnum_match:
            # 保存上一题的答案
            if current_qnum and current_section and current_topic:
                topic_dict = results.setdefault(current_topic, {})
                sec_dict = topic_dict.setdefault(current_section, {})
                sec_dict[current_qnum] = '\n'.join(answer_lines).strip()
            
            current_qnum = int(qnum_match.group(1))
            in_answer = True
            # 检查同行是否有【答案】标记
            if '【答案】' in line or '[答案]' in line:
                # 提取答案后的内容作为解析开头
                m = re.search(r'[【\[]答案[】\]](.*)$', line)
                if m:
                    answer_lines = [m.group(1).strip()]
                else:
                    answer_lines = []
            else:
                answer_lines = []
            i += 1
            continue
        
        # 收集答案内容
        if in_answer and current_qnum:
            # 遇到下一个题号或章节标题时停止
            if (QNUM_LINE_RE.match(line) or 
                re.match(r'^#{1,3}\s*[一二]+、', line) or
                re.match(r'^#{1,3}\s*第[一二三四五六七八九十百]+章', line) or
                re.match(r'^#{1,3}\s*第四部分', line) or
                re.match(r'^#{1,3}\s*专题[一二三四五六七八九十]+', line)):
                # 回退一行，让外层循环处理
                i -= 1
                break
            
            answer_lines.append(line)
        
        i += 1
    
    # 保存最后一题
    if current_qnum and current_section and current_topic:
        topic_dict = results.setdefault(current_topic, {})
        sec_dict = topic_dict.setdefault(current_section, {})
        sec_dict[current_qnum] = '\n'.join(answer_lines).strip()
    
    print(f'下册主观题答案统计:')
    for topic_name, topic_data in results.items():
        print(f'  {topic_name}:')
        for sec_name, sec_data in topic_data.items():
            print(f'    {sec_name}: {len(sec_data)}题')
    
    return results


# ============================================================
# 下册答案解析
# ============================================================

# 答案格式变体非常多，用统一的策略：
# 1. 提取行中的所有 A-H 字母序列
# 2. 找到 "答案" 关键字
# 3. 取 "答案" 之后最近的字母序列

# 题号格式: "## N." 或 "N." 或 "## N. xxx" 或 "N. xxx"
QNUM_LINE_RE = re.compile(r'^#{0,2}\s*(\d+)\.\s*(.*)')
# 单独的题号: "N." 或 "## N."
QNUM_ONLY_RE = re.compile(r'^#{0,2}\s*(\d+)\.\s*$')
# "答案" 关键字后跟字母（可能中间有各种分隔符）
ANSWER_LETTERS_RE = re.compile(r'答案[^A-H]*([A-H]{1,8})')
# 纯答案行（无题号）: "答案 A" / "## 答案 | C" / "答案 BC"
ANSWER_LINE_RE = re.compile(r'^#{0,2}\s*答案[^A-H]*([A-H]{1,8})')



def parse_answers(text):
    """从下册 MD 文本解析答案和解析"""
    answers = {}  # {chapter_num: {section_type: {q_num: {'answer': [...], 'explanation': str}}}}
    
    current_chapter = None
    current_section = None  # 'single_choice' or 'multiple_choice'
    stop_parsing = False
    
    # 当前答案条目
    current_q_num = None
    current_answer_letters = []
    current_explanation = []
    
    lines = text.split('\n')
    
    def flush_answer():
        """保存当前答案"""
        nonlocal current_q_num, current_answer_letters, current_explanation
        if current_q_num is not None and current_answer_letters:
            if current_chapter not in answers:
                answers[current_chapter] = {}
            sec = current_section or 'single_choice'
            if sec not in answers[current_chapter]:
                answers[current_chapter][sec] = {}
            explanation_text = '\n'.join(current_explanation).strip()
            answers[current_chapter][sec][current_q_num] = {
                'answer': list(current_answer_letters),
                'explanation': explanation_text
            }
        current_q_num = None
        current_answer_letters = []
        current_explanation = []
    
    def try_extract_answer(line_text):
        """从一行中提取答案字母"""
        m = ANSWER_LETTERS_RE.search(line_text)
        if m:
            return list(m.group(1))
        return None
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        i += 1
        
        if not line:
            continue
        
        # 跳过图片
        if line.startswith('!['):
            continue
        
        # 跳过表格
        if line.startswith('<table') or line.startswith('</table'):
            continue
        
        # 检查是否进入大题/套卷部分 -> 停止
        if STOP_RE.match(line) or re.match(r'^##\s*(第二部分|第三部分|第四部分)', line):
            flush_answer()
            stop_parsing = True
            continue
        
        if stop_parsing:
            continue
        
        # 检查章节标题
        ch_match = CHAPTER_RE.match(line)
        if ch_match:
            flush_answer()
            cn = ch_match.group(1)
            current_chapter = cn_to_num(cn)
            current_section = None
            continue
        
        # 检查题型标题
        sec_match = SECTION_RE.match(line)
        if sec_match:
            flush_answer()
            sec_name = sec_match.group(1)
            if sec_name == '单项选择题':
                current_section = 'single_choice'
            elif sec_name == '多项选择题':
                current_section = 'multiple_choice'
            else:
                current_section = None
            continue
        
        # 跳过解题通法
        if '解题通法' in line:
            continue
        
        # 检查是否是纯答案行（无题号）: "答案 A" / "## 答案 | C"
        ans_line = ANSWER_LINE_RE.match(line)
        if ans_line and current_q_num is not None and not current_answer_letters:
            current_answer_letters = list(ans_line.group(1))
            continue
        
        # 检查是否是题号行: "## N." / "N." / "## N. xxx" / "N. xxx"
        qnum_match = QNUM_LINE_RE.match(line)
        if qnum_match:
            q_num = int(qnum_match.group(1))
            rest = qnum_match.group(2).strip()
            
            # 先保存上一个答案
            flush_answer()
            current_q_num = q_num
            
            # 检查同一行是否有答案: "## 1. （答案 C）" / "## 2. 答案 D" / "## 3. (答案) B"
            if '答案' in rest:
                letters = try_extract_answer(rest)
                if letters:
                    current_answer_letters = letters
                else:
                    # "答案" 但没有字母（可能在下一行）
                    current_answer_letters = []
            else:
                # 题号行没有答案，查看后续行
                current_answer_letters = []
                while i < len(lines):
                    next_line = lines[i].strip()
                    i += 1
                    if not next_line:
                        continue
                    # 尝试提取答案
                    if '答案' in next_line:
                        letters = try_extract_answer(next_line)
                        if letters:
                            current_answer_letters = letters
                        else:
                            # "答案" 后面没有字母，字母可能在下一行
                            while i < len(lines):
                                nl = lines[i].strip()
                                i += 1
                                if not nl:
                                    continue
                                # 尝试匹配字母序列
                                letter_match = re.match(r'^#{0,2}\s*([A-H]{1,8})\s*$', nl)
                                if letter_match:
                                    current_answer_letters = list(letter_match.group(1))
                                break
                        break
                    # 如果是【解析】，说明没有单独的答案字母行
                    if next_line.startswith('【解析】'):
                        current_explanation.append(next_line)
                        break
                    # 如果是新题号或章节标题，回退
                    if QNUM_LINE_RE.match(next_line) or CHAPTER_RE.match(next_line):
                        i -= 1  # 回退
                        break
                    break
            continue
        
        # 收集解析文本
        if line.startswith('【解析】'):
            current_explanation.append(line)
        elif current_explanation or (current_q_num and current_answer_letters):
            if not line.startswith('#') and not line.startswith('!['):
                current_explanation.append(line)
    
    # 处理最后一个答案
    flush_answer()
    
    return answers


# ============================================================
# 合并题目和答案
# ============================================================

def merge_qa(chapters, answers):
    """将题目和答案合并，输出 questions.json 格式"""
    result_chapters = []
    
    total_q = 0
    total_a = 0
    
    for ch_num in sorted(chapters.keys()):
        ch_data = chapters[ch_num]
        ch_title = ch_data['title']
        
        sections = []
        for sec_type in ['single_choice', 'multiple_choice']:
            if sec_type not in ch_data['sections']:
                continue
            
            questions = ch_data['sections'][sec_type]
            sec_name = '单项选择题' if sec_type == 'single_choice' else '多项选择题'
            
            sec_questions = []
            for q in questions:
                total_q += 1
                # 查找对应答案
                answer = []
                explanation = ''
                if ch_num in answers and sec_type in answers[ch_num]:
                    ans_data = answers[ch_num][sec_type].get(q['number'])
                    if ans_data:
                        answer = ans_data['answer']
                        explanation = ans_data['explanation']
                        total_a += 1
                
                sec_questions.append({
                    'number': q['number'],
                    'question': q['question'],
                    'options': q['options'],
                    'answer': answer,
                    'explanation': explanation
                })
            
            if sec_questions:
                sections.append({
                    'name': sec_name,
                    'type': sec_type,
                    'questions': sec_questions
                })
        
        if sections:
            result_chapters.append({
                'id': ch_num,
                'title': ch_title,
                'sections': sections
            })
    
    print(f'\n合并统计:')
    print(f'  总题数: {total_q}')
    print(f'  有答案: {total_a} ({total_a*100//total_q}%)')
    
    return {'chapters': result_chapters}


# ============================================================
# 主流程
# ============================================================

def main():
    print('加载 MD 文件...')
    upper_text, lower_text = load_md_files()
    
    print('\n解析上册题目...')
    chapters = parse_questions(upper_text)
    
    # 打印各章统计
    for ch_num in sorted(chapters.keys()):
        ch = chapters[ch_num]
        sc = len(ch['sections'].get('single_choice', []))
        mc = len(ch['sections'].get('multiple_choice', []))
        print(f'  {ch["title"]}: {sc}单选 + {mc}多选 = {sc+mc}题')
    
    print('\n解析上册第三部分主观题...')
    subj_upper = parse_subjective_questions_upper(upper_text)
    
    print('\n解析下册答案...')
    answers = parse_answers(lower_text)
    
    # 打印答案统计
    for ch_num in sorted(answers.keys()):
        sc = len(answers[ch_num].get('single_choice', {}))
        mc = len(answers[ch_num].get('multiple_choice', {}))
        print(f'  第{ch_num}章: {sc}单选答案 + {mc}多选答案')
    
    print('\n解析第三部分主观题...')
    subj_answers = parse_subjective_questions(lower_text)
    
    print('\n合并题目和答案...')
    result = merge_qa(chapters, answers)
    
    # 添加主观题章节（按专题组织）
    if subj_answers and subj_upper:
        part3_chapter = {
            'id': 999,  # 特殊ID表示主观题部分
            'title': '第三部分 晋级·刷大题',
            'sections': []
        }
        
        # 遍历所有专题
        for topic_name in sorted(subj_answers.keys()):
            topic_data = subj_answers[topic_name]
            upper_topic_data = subj_upper.get(topic_name, {})
            
            # 为每个专题创建一个section group
            topic_section = {
                'name': topic_name,
                'type': 'topic_group',
                'subsections': []
            }
            
            # 遍历该专题下的题型（计算分析题、综合题等）
            for sec_name in sorted(topic_data.keys()):
                q_dict = topic_data[sec_name]
                section = {
                    'name': sec_name,
                    'type': 'subjective',
                    'questions': []
                }
                
                # 获取对应题型的所有题目（从上册）
                upper_questions = upper_topic_data.get(sec_name, {})
                
                for qnum in sorted(q_dict.keys()):
                    # 获取题目内容
                    upper_q = upper_questions.get(qnum, {})
                    question_text = upper_q.get('question', '')
                    requirements = upper_q.get('requirements', [])
                    other_info = upper_q.get('other_info', [])
                    
                    # 构建完整题目文本
                    full_question = question_text
                    if other_info:
                        full_question += '\n\n' + '\n'.join(other_info)
                    if requirements:
                        full_question += '\n\n## 要求:\n' + '\n'.join(requirements)
                    
                    question = {
                        'number': qnum,
                        'question': full_question.strip(),
                        'options': [],
                        'answer': [],
                        'explanation': q_dict[qnum]
                    }
                    section['questions'].append(question)
                
                topic_section['subsections'].append(section)
            
            part3_chapter['sections'].append(topic_section)
        
        result['chapters'].append(part3_chapter)
        print(f'  已添加主观题章节: {len(subj_answers)}个专题')
    
    # 输出
    output_path = os.path.join(WORK_DIR, 'questions.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f'\n✅ 输出: {output_path}')
    print(f'  文件大小: {os.path.getsize(output_path) / 1024:.1f} KB')
    
    # 详细统计
    total = sum(len(sec['questions']) for ch in result['chapters'] for sec in ch['sections'])
    with_ans = sum(1 for ch in result['chapters'] for sec in ch['sections'] for q in sec['questions'] if q['answer'] or q.get('explanation'))
    print(f'\n最终统计:')
    print(f'  章节数: {len(result["chapters"])}')
    print(f'  总题数: {total}')
    print(f'  有答案/解析: {with_ans} ({with_ans*100//total}%)')
    
    # 答案缺口
    missing = []
    for ch in result['chapters']:
        ch_missing = []
        for sec in ch['sections']:
            for q in sec['questions']:
                if not q['answer']:
                    ch_missing.append(f"Q{q['number']}({sec['type'][:1]})")
        if ch_missing:
            missing.append(f"  {ch['title']}: 缺 {ch_missing}")
    if missing:
        print(f'\n答案缺口:')
        for m in missing:
            print(m)


if __name__ == '__main__':
    main()
