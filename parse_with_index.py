#!/usr/bin/env python3
"""
会计题库主解析器（基于结构索引）
根据 structure_index.json 的索引信息，从MD文件中提取题目和答案，生成 questions.json
"""
import re
import json
import os

WORK_DIR = os.path.dirname(os.path.abspath(__file__))
MD_DIR = os.path.join(WORK_DIR, 'file_json')

# ============================================================
# 正则表达式
# ============================================================

QUESTION_RE = re.compile(r'^(\d+)\.\s*(.*)')
OPTION_RE = re.compile(r'^([A-H])\.\s*(.*)')

# 下册答案题号格式
ANS_HEADING_RE = re.compile(r'^#{1,3}\s*(\d+)\.\s*(.*)')
PLAIN_NUM_RE = re.compile(r'^(\d+)\.\s*$')
PLAIN_ENTRY_RE = re.compile(r'^(\d+)\.\s+(.+)')

# 结构检测
CHAPTER_RE = re.compile(r'^#{1,3}\s*第([一二三四五六七八九十百]+)章\s*(.*)')
TOPIC_RE = re.compile(r'^#{1,3}\s*(专题[一二三四五六七八九十]+)\s*(.*)$')
SECTION_RE = re.compile(r'^#{1,3}\s*(?:[一二三四]+、)?(单项选择题|多项选择题|计算分析题|综合题)')
PAPER_RE = re.compile(r'^#{1,3}\s*实战套卷[（\(]([一二三四五六七八九十]+)[）\)]')

CN_NUM = {
    '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
    '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
    '十一': 11, '十二': 12, '十三': 13, '十四': 14, '十五': 15,
    '十六': 16, '十七': 17, '十八': 18, '十九': 19, '二十': 20,
    '二十一': 21, '二十二': 22, '二十三': 23, '二十四': 24, '二十五': 25,
    '二十六': 26, '二十七': 27, '二十八': 28, '二十九': 29, '三十': 30,
}


def cn_to_num(cn):
    return CN_NUM.get(cn, 0)


def sec_type(name):
    return {
        '单项选择题': 'single_choice',
        '多项选择题': 'multiple_choice',
        '计算分析题': 'calculation',
        '综合题': 'comprehensive',
    }.get(name, 'unknown')


# ============================================================
# 文件加载
# ============================================================

def load_md_files():
    """加载4个MD文件，返回 (upper_texts, lower_texts)"""
    files = sorted(os.listdir(MD_DIR))
    upper = sorted(
        [f for f in files if f.endswith('.md') and '会计（上）' in f],
        key=lambda n: int(re.match(r'MinerU_markdown_(\d+)_', n).group(1))
    )
    lower = sorted(
        [f for f in files if f.endswith('.md') and '会计（下）' in f],
        key=lambda n: int(re.match(r'MinerU_markdown_(\d+)_', n).group(1))
    )
    print(f'上册文件: {upper}')
    print(f'下册文件: {lower}')

    def read_list(flist):
        texts = []
        for f in flist:
            with open(os.path.join(MD_DIR, f), 'r', encoding='utf-8') as fp:
                texts.append(fp.read())
        return texts

    return read_list(upper), read_list(lower)


def extract_text_range(texts, start_line, end_line):
    """提取指定行范围的文本（1-based inclusive）"""
    result = []
    cur = 1
    for text in texts:
        lines = text.split('\n')
        for i, line in enumerate(lines):
            ln = cur + i
            if start_line <= ln <= end_line:
                result.append(line)
            elif ln > end_line:
                break
        cur += len(lines)
        if cur > end_line:
            break
    return '\n'.join(result)


# ============================================================
# 答案字母提取
# ============================================================

def extract_answer_letters(line):
    """从一行文本中提取答案字母列表，返回 [] 表示未找到"""
    s = line.strip()
    if not s:
        return []

    # ## N. （答案 C） 或 ## N. (答案 C)
    m = re.search(r'[（(]\s*答案\s*[A-H]*\s*[)）]\s*([A-H]+)', s)
    if m and m.group(1):
        return list(m.group(1))

    # ## N. （答案） B  或 (答案) B
    m = re.search(r'[（(]\s*答案\s*[)）]\s*([A-H]+)', s)
    if m and m.group(1):
        return list(m.group(1))

    # 答案 | BC  或 答案 BC  或 答案·BC
    m = re.match(r'^(?:#{1,3}\s*)?(?:\d+\.\s*)?答案\s*[\|·]?\s*([A-H]{1,8})\s*$', s)
    if m:
        return list(m.group(1))

    # （答案 C） standalone
    m = re.search(r'[（(]答案\s*([A-H]+)[)）]', s)
    if m:
        return list(m.group(1))

    return []


def is_standalone_answer_line(line):
    """判断是否是独立的答案行（如 '答案 A', '答案 | BC', '(答案) C'）"""
    s = line.strip()
    if not s:
        return False, []

    # 答案 | BC / 答案 BC
    if re.match(r'^答案\s*[\|·]?\s*([A-H]{1,8})\s*$', s):
        m = re.match(r'^答案\s*[\|·]?\s*([A-H]{1,8})\s*$', s)
        return True, list(m.group(1))

    # (答案) C / （答案） B
    m = re.match(r'^[（(]\s*答案\s*[)）]\s*([A-H]+)', s)
    if m:
        return True, list(m.group(1))

    return False, []


# ============================================================
# 上册：客观题解析（单选/多选）
# ============================================================

def parse_objective_questions(text_segment):
    """解析客观题（单选/多选）"""
    questions = []
    lines = text_segment.split('\n')

    q_num = None
    q_text = []
    q_options = []
    cur_label = None
    cur_opt_text = []

    def flush_opt():
        nonlocal cur_label, cur_opt_text
        if cur_label and cur_opt_text:
            q_options.append({'label': cur_label, 'text': ' '.join(cur_opt_text).strip()})
        cur_label = None
        cur_opt_text = []

    def flush_q():
        nonlocal q_num, q_text, q_options
        flush_opt()
        if q_num is not None and q_text:
            questions.append({
                'number': q_num,
                'question': ' '.join(q_text).strip(),
                'options': q_options[:],
                'answer': [],
                'explanation': '',
            })
        q_num = None
        q_text = []
        q_options = []

    for line in lines:
        line = line.strip()
        if not line or line.startswith('![') or line.startswith('<table'):
            continue

        qm = QUESTION_RE.match(line)
        if qm:
            flush_q()
            q_num = int(qm.group(1))
            q_text = [qm.group(2)] if qm.group(2) else []
            continue

        om = OPTION_RE.match(line)
        if om:
            flush_opt()
            cur_label = om.group(1)
            cur_opt_text = [om.group(2)]
            continue

        if q_num is not None:
            if cur_label is not None:
                cur_opt_text.append(line)
            else:
                q_text.append(line)

    flush_q()
    return questions


# ============================================================
# 上册：主观题解析（计算分析题/综合题）
# ============================================================

def parse_subjective_questions(text_segment):
    """解析主观题（计算分析题/综合题）"""
    questions = []
    lines = text_segment.split('\n')

    q_num = None
    q_text = []
    requirements = []
    other_info = []
    collecting_req = False
    collecting_other = False

    def flush_q():
        nonlocal q_num, q_text, requirements, other_info, collecting_req, collecting_other
        if q_num is not None and q_text:
            full = '\n'.join(q_text).strip()
            if other_info:
                full += '\n\n' + '\n'.join(other_info)
            if requirements:
                full += '\n\n## 要求:\n' + '\n'.join(requirements)
            questions.append({
                'number': q_num,
                'question': full,
                'options': [],
                'answer': [],
                'explanation': '',
            })
        q_num = None
        q_text = []
        requirements = []
        other_info = []
        collecting_req = False
        collecting_other = False

    for line in lines:
        ls = line.rstrip()

        if re.match(r'^#{1,3}\s*其他资料[:：]?$', ls):
            collecting_other = True
            collecting_req = False
            other_info.append(ls)
            continue
        elif re.match(r'^#{1,3}\s*要求[:：]?$', ls):
            collecting_req = True
            collecting_other = False
            continue

        qm = QUESTION_RE.match(ls)
        if qm:
            flush_q()
            q_num = int(qm.group(1))
            q_text = [qm.group(2)] if qm.group(2) else []
            continue

        if q_num is not None:
            if collecting_req:
                requirements.append(ls)
            elif collecting_other:
                other_info.append(ls)
            else:
                q_text.append(ls)

    flush_q()
    return questions


# ============================================================
# 下册：客观答案解析
# ============================================================

def parse_objective_answers_in_range(text):
    """在给定文本范围内解析客观题答案，返回 {chapter_id: {sec_type: {qnum: {answer, explanation}}}}"""
    result = {}
    lines = text.split('\n')

    cur_ch = None
    cur_sec = None
    cur_qnum = None
    answer_letters = []
    answer_found = False
    expl_lines = []
    first_content = True

    def save():
        nonlocal cur_qnum
        if cur_qnum is not None and cur_ch is not None and cur_sec is not None:
            result.setdefault(cur_ch, {}).setdefault(cur_sec, {})[cur_qnum] = {
                'answer': answer_letters[:],
                'explanation': '\n'.join(expl_lines).strip(),
            }

    for raw_line in lines:
        line = raw_line.rstrip()
        if not line.strip():
            continue
        if line.strip().startswith('![') or line.strip().startswith('<table'):
            if cur_qnum is not None and answer_found:
                expl_lines.append(line.rstrip())
            continue

        # 章节标题
        ch_m = CHAPTER_RE.match(line)
        if ch_m:
            save()
            cur_ch = cn_to_num(ch_m.group(1))
            cur_sec = None
            cur_qnum = None
            continue

        # 题型标题
        sec_m = SECTION_RE.match(line)
        if sec_m:
            save()
            cur_sec = sec_type(sec_m.group(1))
            cur_qnum = None
            continue

        if cur_ch is None or cur_sec is None:
            continue

        # 带 # 的题号行
        ah_m = ANS_HEADING_RE.match(line)
        if ah_m:
            save()
            cur_qnum = int(ah_m.group(1))
            rest = ah_m.group(2).strip()
            answer_letters = extract_answer_letters(line)
            answer_found = bool(answer_letters)
            expl_lines = []
            first_content = True
            continue

        # 纯数字行 (如 "13.")
        pn_m = PLAIN_NUM_RE.match(line)
        if pn_m:
            save()
            cur_qnum = int(pn_m.group(1))
            answer_letters = []
            answer_found = False
            expl_lines = []
            first_content = True
            continue

        # 无#前缀的题号行 (如 "1. 答案 B", "3. (答案) D")
        pe_m = PLAIN_ENTRY_RE.match(line)
        if pe_m and not line.startswith('#'):
            save()
            cur_qnum = int(pe_m.group(1))
            rest = pe_m.group(2).strip()
            answer_letters = extract_answer_letters(line)
            answer_found = bool(answer_letters)
            expl_lines = []
            first_content = True
            continue

        # 收集内容
        if cur_qnum is not None:
            # 首行尝试提取答案
            if not answer_found and first_content:
                # 检查 ## 答案 X 格式
                heading_ans = extract_answer_letters(line)
                if heading_ans:
                    answer_letters = heading_ans
                    answer_found = True
                    first_content = False
                    continue
                is_sa, sa_letters = is_standalone_answer_line(line)
                if is_sa:
                    answer_letters = sa_letters
                    answer_found = True
                    first_content = False
                    continue
                first_content = False

            # 解析标记
            if re.search(r'【解析】|\[解析\]', line):
                expl_lines.append(line.rstrip())
                answer_found = True
            elif not answer_found:
                # 还没找到答案，继续找
                expl_lines.append(line.rstrip())
            else:
                expl_lines.append(line.rstrip())

    save()
    return result


# ============================================================
# 下册：主观答案解析
# ============================================================

def parse_subjective_answers_in_range(text):
    """解析主观题答案，返回 {topic_name: {sec_type: {qnum: {answer, explanation}}}}"""
    result = {}
    lines = text.split('\n')

    # 先找专题和题型的位置
    topics = []
    for i, line in enumerate(lines):
        m = TOPIC_RE.match(line.rstrip())
        if m:
            name = m.group(1)
            extra = m.group(2).strip()
            if extra:
                name += ' ' + extra
            topics.append({'name': name, 'line': i})

    for ti, topic in enumerate(topics):
        start = topic['line']
        end = topics[ti + 1]['line'] if ti + 1 < len(topics) else len(lines)
        topic_text = '\n'.join(lines[start:end])
        topic_result = {}

        secs = []
        sec_lines = topic_text.split('\n')
        for si, sl in enumerate(sec_lines):
            sm = SECTION_RE.match(sl.rstrip())
            if sm:
                secs.append({'type': sec_type(sm.group(1)), 'name': sm.group(1), 'line': si})

        for si, sec in enumerate(secs):
            s_start = sec['line']
            s_end = secs[si + 1]['line'] if si + 1 < len(secs) else len(sec_lines)
            sec_text = '\n'.join(sec_lines[s_start:s_end])

            q_entries = []
            sec_all = sec_text.split('\n')
            for qi, ql in enumerate(sec_all):
                qm = ANS_HEADING_RE.match(ql.rstrip())
                if qm:
                    q_entries.append({'num': int(qm.group(1)), 'line': qi})

            for qi, qe in enumerate(q_entries):
                q_start = qe['line']
                q_end = q_entries[qi + 1]['line'] if qi + 1 < len(q_entries) else len(sec_all)
                content = '\n'.join(sec_all[q_start:q_end])

                all_content = []
                for cl in content.split('\n')[1:]:
                    if cl.strip():
                        all_content.append(cl.rstrip())

                topic_result.setdefault(sec['type'], {})[qe['num']] = {
                    'answer': [],
                    'explanation': '\n'.join(all_content).strip(),
                }

        result[topic['name']] = topic_result

    return result


# ============================================================
# 下册：套卷答案解析
# ============================================================

def parse_mock_exam_answers_in_range(text):
    """解析套卷答案，返回 {paper_name: {sec_type: {qnum: {answer, explanation}}}}"""
    result = {}
    lines = text.split('\n')

    papers = []
    for i, line in enumerate(lines):
        m = PAPER_RE.match(line.rstrip())
        if m:
            papers.append({'name': f'实战套卷（{m.group(1)}）', 'line': i})

    for pi, paper in enumerate(papers):
        start = paper['line']
        end = papers[pi + 1]['line'] if pi + 1 < len(papers) else len(lines)
        paper_lines = lines[start:end]

        secs = []
        for si, sl in enumerate(paper_lines):
            sm = SECTION_RE.match(sl.rstrip())
            if sm:
                secs.append({'type': sec_type(sm.group(1)), 'name': sm.group(1), 'line': si})

        paper_result = {}
        for si, sec in enumerate(secs):
            s_start = sec['line']
            s_end = secs[si + 1]['line'] if si + 1 < len(secs) else len(paper_lines)
            sec_text = '\n'.join(paper_lines[s_start:s_end])

            if sec['type'] in ['single_choice', 'multiple_choice']:
                answers = {}
                sec_lines_list = sec_text.split('\n')
                cur_qnum = None
                ans_letters = []
                ans_found = False
                expl = []
                first_c = True

                def save_ans():
                    nonlocal cur_qnum
                    if cur_qnum is not None:
                        answers[cur_qnum] = {
                            'answer': ans_letters[:],
                            'explanation': '\n'.join(expl).strip(),
                        }

                for sl in sec_lines_list[1:]:
                    ls = sl.rstrip()
                    if not ls.strip():
                        continue
                    if ls.strip().startswith('![') or ls.strip().startswith('<table'):
                        if cur_qnum is not None and ans_found:
                            expl.append(ls)
                        continue

                    ah_m = ANS_HEADING_RE.match(ls)
                    if ah_m:
                        save_ans()
                        cur_qnum = int(ah_m.group(1))
                        ans_letters = extract_answer_letters(ls)
                        ans_found = bool(ans_letters)
                        expl = []
                        first_c = True
                        continue

                    pn_m = PLAIN_NUM_RE.match(ls)
                    if pn_m:
                        save_ans()
                        cur_qnum = int(pn_m.group(1))
                        ans_letters = []
                        ans_found = False
                        expl = []
                        first_c = True
                        continue

                    # 无#前缀的题号行
                    pe_m = PLAIN_ENTRY_RE.match(ls)
                    if pe_m and not ls.startswith('#'):
                        save_ans()
                        cur_qnum = int(pe_m.group(1))
                        ans_letters = extract_answer_letters(ls)
                        ans_found = bool(ans_letters)
                        expl = []
                        first_c = True
                        continue

                    if cur_qnum is not None:
                        if not ans_found and first_c:
                            # 检查 ## 答案 X 格式
                            heading_ans = extract_answer_letters(ls)
                            if heading_ans:
                                ans_letters = heading_ans
                                ans_found = True
                                first_c = False
                                continue
                            is_sa, sa_l = is_standalone_answer_line(ls)
                            if is_sa:
                                ans_letters = sa_l
                                ans_found = True
                                first_c = False
                                continue
                            first_c = False
                        if re.search(r'【解析】|\[解析\]', ls):
                            ans_found = True
                            expl.append(ls)
                        else:
                            expl.append(ls)

                save_ans()
                paper_result[sec['type']] = answers
            else:
                answers = {}
                sec_lines_list = sec_text.split('\n')
                q_entries = []
                for qi, ql in enumerate(sec_lines_list):
                    qm = ANS_HEADING_RE.match(ql.rstrip())
                    if qm:
                        q_entries.append({'num': int(qm.group(1)), 'line': qi})
                        continue
                    # 也支持无##前缀的纯数字题号 (如 "1.")
                    pm = PLAIN_NUM_RE.match(ql.rstrip())
                    if pm:
                        q_entries.append({'num': int(pm.group(1)), 'line': qi})

                for qi, qe in enumerate(q_entries):
                    q_start = qe['line']
                    q_end = q_entries[qi + 1]['line'] if qi + 1 < len(q_entries) else len(sec_lines_list)
                    content = '\n'.join(sec_lines_list[q_start:q_end])
                    all_content = [cl.rstrip() for cl in content.split('\n')[1:] if cl.strip()]
                    answers[qe['num']] = {
                        'answer': [],
                        'explanation': '\n'.join(all_content).strip(),
                    }

                paper_result[sec['type']] = answers

        result[paper['name']] = paper_result

    return result


# ============================================================
# 下册子结构扫描
# ============================================================

def find_sub_chapters(text):
    """在文本中查找章节位置，返回 [(chapter_id, start_line_index)]"""
    chapters = []
    lines = text.split('\n')
    for i, line in enumerate(lines):
        m = CHAPTER_RE.match(line.rstrip())
        if m:
            chapters.append((cn_to_num(m.group(1)), i))
    return chapters


def find_sub_topics(text):
    """在文本中查找专题位置"""
    topics = []
    lines = text.split('\n')
    for i, line in enumerate(lines):
        m = TOPIC_RE.match(line.rstrip())
        if m:
            name = m.group(1)
            extra = m.group(2).strip()
            if extra:
                name += ' ' + extra
            topics.append((name, i))
    return topics


def find_sub_papers(text):
    """在文本中查找套卷位置"""
    papers = []
    lines = text.split('\n')
    for i, line in enumerate(lines):
        m = PAPER_RE.match(line.rstrip())
        if m:
            papers.append((f'实战套卷（{m.group(1)}）', i))
    return papers


# ============================================================
# 主流程
# ============================================================

def main():
    print('=' * 80)
    print('会计题库主解析器（基于结构索引）')
    print('=' * 80)

    # 加载结构索引
    with open(os.path.join(WORK_DIR, 'structure_index.json'), 'r', encoding='utf-8') as f:
        structure = json.load(f)

    print('\n加载 MD 文件...')
    upper_texts, lower_texts = load_md_files()

    result = {'parts': []}

    # ==================== 解析上册题目 ====================
    print('\n===== 解析上册题目 =====')
    for part in structure['upper']['parts']:
        if part['type'] == 'intro':
            continue

        part_data = {
            'id': part['id'],
            'name': part['name'],
            'title': part['title'],
            'type': part['type'],
        }

        if part['type'] == 'objective':
            part_data['chapters'] = []
            for ch in part['chapters']:
                ch_data = {'id': ch['id'], 'title': ch['title'], 'sections': []}
                for sec in ch['sections']:
                    text = extract_text_range(upper_texts, sec['start_line'], sec['end_line'])
                    qs = parse_objective_questions(text)
                    ch_data['sections'].append({
                        'name': sec['name'],
                        'type': sec['type'],
                        'questions': qs,
                    })
                    print(f"  {ch['title']} - {sec['name']}: {len(qs)}题")
                part_data['chapters'].append(ch_data)

        elif part['type'] == 'subjective':
            part_data['topics'] = []
            for topic in part['topics']:
                t_data = {'name': topic['name'], 'sections': []}
                for sec in topic['sections']:
                    text = extract_text_range(upper_texts, sec['start_line'], sec['end_line'])
                    if sec['type'] in ['single_choice', 'multiple_choice']:
                        qs = parse_objective_questions(text)
                    else:
                        qs = parse_subjective_questions(text)
                    t_data['sections'].append({
                        'name': sec['name'],
                        'type': sec['type'],
                        'questions': qs,
                    })
                    print(f"  {topic['name']} - {sec['name']}: {len(qs)}题")
                part_data['topics'].append(t_data)

        elif part['type'] == 'mock_exam':
            part_data['papers'] = []
            for paper in part['papers']:
                p_data = {'name': paper['name'], 'sections': []}
                for sec in paper['sections']:
                    text = extract_text_range(upper_texts, sec['start_line'], sec['end_line'])
                    if sec['type'] in ['single_choice', 'multiple_choice']:
                        qs = parse_objective_questions(text)
                    else:
                        qs = parse_subjective_questions(text)
                    p_data['sections'].append({
                        'name': sec['name'],
                        'type': sec['type'],
                        'questions': qs,
                    })
                    print(f"  {paper['name']} - {sec['name']}: {len(qs)}题")
                part_data['papers'].append(p_data)

        result['parts'].append(part_data)

    # ==================== 解析下册答案 ====================
    print('\n===== 解析下册答案 =====')
    obj_answers = {}
    subj_answers = {}
    mock_answers = {}

    for part in structure['lower']['parts']:
        text = extract_text_range(lower_texts, part['start_line'], part['end_line'])
        print(f"\n{part['name']} - {part['title']}")

        if part['type'] == 'objective_answers':
            obj_answers = parse_objective_answers_in_range(text)
            for ch_id in sorted(obj_answers.keys()):
                total = sum(len(v) for v in obj_answers[ch_id].values())
                print(f"  第{ch_id}章: {total}个答案")

        elif part['type'] == 'subjective_answers':
            subj_answers = parse_subjective_answers_in_range(text)
            for tn in subj_answers:
                total = sum(len(v) for v in subj_answers[tn].values())
                print(f"  {tn}: {total}个答案")

        elif part['type'] == 'mock_exam_answers':
            mock_answers = parse_mock_exam_answers_in_range(text)
            for pn in mock_answers:
                total = sum(len(v) for v in mock_answers[pn].values())
                print(f"  {pn}: {total}个答案")

    # ==================== 匹配答案 ====================
    print('\n===== 匹配答案 =====')
    matched = 0
    total_qs = 0

    for part in result['parts']:
        if part['type'] == 'objective':
            for ch in part['chapters']:
                for sec in ch['sections']:
                    for q in sec['questions']:
                        total_qs += 1
                        ans = obj_answers.get(ch['id'], {}).get(sec['type'], {}).get(q['number'])
                        if ans:
                            q['answer'] = ans['answer']
                            q['explanation'] = ans['explanation']
                            if ans['answer']:
                                matched += 1

        elif part['type'] == 'subjective':
            for topic in part['topics']:
                # 找到匹配的答案专题
                ans_topic = None
                for at_name in subj_answers:
                    if topic['name'] in at_name or at_name in topic['name']:
                        ans_topic = subj_answers[at_name]
                        break
                if not ans_topic:
                    # 尝试模糊匹配
                    for at_name in subj_answers:
                        t1 = topic['name'].split()[0] if topic['name'].split() else topic['name']
                        t2 = at_name.split()[0] if at_name.split() else at_name
                        if t1 == t2:
                            ans_topic = subj_answers[at_name]
                            break

                for sec in topic['sections']:
                    for q in sec['questions']:
                        total_qs += 1
                        if ans_topic:
                            ans = ans_topic.get(sec['type'], {}).get(q['number'])
                            if ans:
                                q['answer'] = ans['answer']
                                q['explanation'] = ans['explanation']
                                matched += 1

        elif part['type'] == 'mock_exam':
            for paper in part['papers']:
                ans_paper = mock_answers.get(paper['name'], {})
                for sec in paper['sections']:
                    for q in sec['questions']:
                        total_qs += 1
                        ans = ans_paper.get(sec['type'], {}).get(q['number'])
                        if ans:
                            q['answer'] = ans['answer']
                            q['explanation'] = ans['explanation']
                            if ans['answer'] or ans['explanation']:
                                matched += 1

    # ==================== 输出 ====================
    output_path = os.path.join(WORK_DIR, 'questions.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f'\n✅ 输出: {output_path}')
    print(f'总题数: {total_qs}')
    print(f'匹配答案: {matched}/{total_qs} ({matched / total_qs * 100:.1f}%)')

    # 详细统计
    print('\n===== 详细统计 =====')
    for part in result['parts']:
        if part['type'] == 'objective':
            for ch in part['chapters']:
                for sec in ch['sections']:
                    with_ans = sum(1 for q in sec['questions'] if q['answer'])
                    print(f"  {ch['title']} {sec['name']}: {len(sec['questions'])}题, {with_ans}有答案")
        elif part['type'] == 'subjective':
            for topic in part['topics']:
                for sec in topic['sections']:
                    with_ans = sum(1 for q in sec['questions'] if q['answer'] or q['explanation'])
                    print(f"  {topic['name']} {sec['name']}: {len(sec['questions'])}题, {with_ans}有答案")
        elif part['type'] == 'mock_exam':
            for paper in part['papers']:
                for sec in paper['sections']:
                    with_ans = sum(1 for q in sec['questions'] if q['answer'] or q['explanation'])
                    print(f"  {paper['name']} {sec['name']}: {len(sec['questions'])}题, {with_ans}有答案")


if __name__ == '__main__':
    main()
