#!/usr/bin/env python3
"""
会计题库 MD 文件结构分析器
扫描四个 MD 文件，建立完整的索引映射（章节位置、题型范围、答案对应关系）
"""
import re
import json
import os

WORK_DIR = os.path.dirname(os.path.abspath(__file__))
MD_DIR = os.path.join(WORK_DIR, 'file_json')

# ============================================================
# 正则表达式定义
# ============================================================

PART_RE = re.compile(r'^#{1,3}\s*(第一部分|第二部分|第三部分|第四部分)')
CHAPTER_RE = re.compile(r'^#{1,3}\s*第([一二三四五六七八九十百]+)章\s*(.*)')
TOPIC_RE = re.compile(r'^#{1,3}\s*(专题[一二三四五六七八九十]+)\s*(.*)$')
SECTION_RE = re.compile(r'^#{1,3}\s*(?:[一二三四]+、)?(单项选择题|多项选择题|计算分析题|综合题)')
PAPER_RE = re.compile(r'^#{1,3}\s*实战套卷[（\(]([一二三四五六七八九十]+)[）\)]')
QUESTION_RE = re.compile(r'^(\d+)\.\s*(.*)')

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
# 文件加载
# ============================================================

def load_md_files():
    """加载4个MD文件"""
    files = sorted(os.listdir(MD_DIR))
    
    upper_files = [f for f in files if f.endswith('.md') and '会计（上）' in f]
    lower_files = [f for f in files if f.endswith('.md') and '会计（下）' in f]
    
    def sort_key(name):
        m = re.match(r'MinerU_markdown_(\d+)_', name)
        return int(m.group(1)) if m else 0
    
    upper_files.sort(key=sort_key)
    lower_files.sort(key=sort_key)
    
    print(f'上册文件: {upper_files}')
    print(f'下册文件: {lower_files}')
    
    upper_texts = []
    for f in upper_files:
        with open(os.path.join(MD_DIR, f), 'r', encoding='utf-8') as fp:
            upper_texts.append(fp.read())
    
    lower_texts = []
    for f in lower_files:
        with open(os.path.join(MD_DIR, f), 'r', encoding='utf-8') as fp:
            lower_texts.append(fp.read())
    
    return upper_texts, lower_texts


# ============================================================
# 上册结构分析
# ============================================================

def analyze_upper_structure(texts):
    """分析上册结构"""
    structure = {
        'parts': []
    }
    
    current_part = None
    current_chapter = None
    current_topic = None
    current_paper = None
    current_section = None
    
    part_start_line = 0
    chapter_start_line = 0
    topic_start_line = 0
    paper_start_line = 0
    section_start_line = 0
    
    line_num = 0
    
    for text_idx, text in enumerate(texts):
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line = line.rstrip()
            actual_line_num = line_num + i + 1
            
            # 检测部分
            part_match = PART_RE.match(line)
            if part_match:
                if current_part:
                    current_part['end_line'] = actual_line_num - 1
                
                part_name = part_match.group(1)
                part_id = {'第一部分': 1, '第二部分': 2, '第三部分': 3, '第四部分': 4}.get(part_name, 0)
                
                current_part = {
                    'id': part_id,
                    'name': part_name,
                    'title': '',
                    'type': '',
                    'start_line': actual_line_num,
                    'end_line': len(text) + line_num,
                    'chapters': [],
                    'topics': [],
                    'papers': []
                }
                
                # 设置标题和类型
                if part_name == '第一部分':
                    current_part['title'] = '解题方法及技巧'
                    current_part['type'] = 'intro'
                elif part_name == '第二部分':
                    current_part['title'] = '分阶·刷小题'
                    current_part['type'] = 'objective'
                elif part_name == '第三部分':
                    current_part['title'] = '晋级·刷大题'
                    current_part['type'] = 'subjective'
                elif part_name == '第四部分':
                    current_part['title'] = '实战·刷套卷'
                    current_part['type'] = 'mock_exam'
                
                structure['parts'].append(current_part)
                continue
            
            # 检测章节（仅第二部分）
            if current_part and current_part['id'] == 2:
                ch_match = CHAPTER_RE.match(line)
                if ch_match:
                    if current_chapter:
                        current_chapter['end_line'] = actual_line_num - 1
                    
                    cn_num = ch_match.group(1)
                    title = ch_match.group(2).strip()
                    
                    current_chapter = {
                        'id': cn_to_num(cn_num),
                        'title': f'第{cn_num}章 {title}',
                        'start_line': actual_line_num,
                        'end_line': len(text) + line_num,
                        'sections': []
                    }
                    current_part['chapters'].append(current_chapter)
                    continue
                
                # 检测题型
                sec_match = SECTION_RE.match(line)
                if sec_match and current_chapter:
                    if current_section:
                        current_section['end_line'] = actual_line_num - 1
                    
                    sec_name = sec_match.group(1)
                    sec_type = {
                        '单项选择题': 'single_choice',
                        '多项选择题': 'multiple_choice',
                        '计算分析题': 'calculation',
                        '综合题': 'comprehensive'
                    }.get(sec_name, 'unknown')
                    
                    current_section = {
                        'name': sec_name,
                        'type': sec_type,
                        'start_line': actual_line_num,
                        'end_line': len(text) + line_num,
                        'questions': []
                    }
                    current_chapter['sections'].append(current_section)
                    continue
            
            # 检测专题（仅第三部分）
            if current_part and current_part['id'] == 3:
                topic_match = TOPIC_RE.match(line)
                if topic_match:
                    if current_topic:
                        current_topic['end_line'] = actual_line_num - 1
                    
                    topic_name = topic_match.group(1)
                    extra = topic_match.group(2).strip()
                    if extra:
                        topic_name += ' ' + extra
                    
                    current_topic = {
                        'name': topic_name,
                        'start_line': actual_line_num,
                        'end_line': len(text) + line_num,
                        'sections': []
                    }
                    current_part['topics'].append(current_topic)
                    continue
                
                # 检测题型
                sec_match = SECTION_RE.match(line)
                if sec_match and current_topic:
                    if current_section:
                        current_section['end_line'] = actual_line_num - 1
                    
                    sec_name = sec_match.group(1)
                    sec_type = {
                        '单项选择题': 'single_choice',
                        '多项选择题': 'multiple_choice',
                        '计算分析题': 'calculation',
                        '综合题': 'comprehensive'
                    }.get(sec_name, 'unknown')
                    
                    current_section = {
                        'name': sec_name,
                        'type': sec_type,
                        'start_line': actual_line_num,
                        'end_line': len(text) + line_num,
                        'questions': []
                    }
                    current_topic['sections'].append(current_section)
                    continue
            
            # 检测套卷（仅第四部分）
            if current_part and current_part['id'] == 4:
                paper_match = PAPER_RE.match(line)
                if paper_match:
                    if current_paper:
                        current_paper['end_line'] = actual_line_num - 1
                    
                    paper_num = paper_match.group(1)
                    
                    current_paper = {
                        'name': f'实战套卷（{paper_num}）',
                        'start_line': actual_line_num,
                        'end_line': len(text) + line_num,
                        'sections': []
                    }
                    current_part['papers'].append(current_paper)
                    continue
                
                # 检测题型
                sec_match = SECTION_RE.match(line)
                if sec_match and current_paper:
                    if current_section:
                        current_section['end_line'] = actual_line_num - 1
                    
                    sec_name = sec_match.group(1)
                    sec_type = {
                        '单项选择题': 'single_choice',
                        '多项选择题': 'multiple_choice',
                        '计算分析题': 'calculation',
                        '综合题': 'comprehensive'
                    }.get(sec_name, 'unknown')
                    
                    current_section = {
                        'name': sec_name,
                        'type': sec_type,
                        'start_line': actual_line_num,
                        'end_line': len(text) + line_num,
                        'questions': []
                    }
                    current_paper['sections'].append(current_section)
                    continue
        
        line_num += len(lines)
    
    # 保存最后一个元素
    if current_section:
        current_section['end_line'] = line_num
    if current_chapter:
        current_chapter['end_line'] = line_num
    if current_topic:
        current_topic['end_line'] = line_num
    if current_paper:
        current_paper['end_line'] = line_num
    if current_part:
        current_part['end_line'] = line_num
    
    return structure


# ============================================================
# 下册结构分析
# ============================================================

def analyze_lower_structure(texts):
    """分析下册结构（答案部分）"""
    structure = {
        'parts': []
    }
    
    current_part = None
    line_num = 0
    
    for text_idx, text in enumerate(texts):
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line = line.rstrip()
            actual_line_num = line_num + i + 1
            
            # 检测部分
            part_match = PART_RE.match(line)
            if part_match:
                if current_part:
                    current_part['end_line'] = actual_line_num - 1
                
                part_name = part_match.group(1)
                part_id = {'第一部分': 1, '第二部分': 2, '第三部分': 3, '第四部分': 4}.get(part_name, 0)
                
                current_part = {
                    'id': part_id,
                    'name': part_name,
                    'title': '',
                    'type': '',
                    'start_line': actual_line_num,
                    'end_line': len(text) + line_num
                }
                
                # 设置标题和类型
                if part_name == '第一部分':
                    current_part['title'] = '小题·参考答案及解析'
                    current_part['type'] = 'objective_answers'
                elif part_name == '第二部分':
                    current_part['title'] = '大题·参考答案及解析'
                    current_part['type'] = 'subjective_answers'
                elif part_name == '第三部分':
                    current_part['title'] = '套卷·参考答案及解析'
                    current_part['type'] = 'mock_exam_answers'
                
                structure['parts'].append(current_part)
                continue
        
        line_num += len(lines)
    
    # 保存最后一个元素
    if current_part:
        current_part['end_line'] = line_num
    
    return structure


# ============================================================
# 主流程
# ============================================================

def main():
    print('=' * 80)
    print('会计题库 MD 文件结构分析器')
    print('=' * 80)
    
    print('\n加载 MD 文件...')
    upper_texts, lower_texts = load_md_files()
    
    print('\n分析上册结构...')
    upper_structure = analyze_upper_structure(upper_texts)
    
    print('\n分析下册结构...')
    lower_structure = analyze_lower_structure(lower_texts)
    
    # 输出结果
    output = {
        'upper': upper_structure,
        'lower': lower_structure
    }
    
    output_path = os.path.join(WORK_DIR, 'structure_index.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f'\n✅ 结构索引已保存: {output_path}')
    
    # 打印统计信息
    print('\n' + '=' * 80)
    print('上册统计:')
    print('=' * 80)
    for part in upper_structure['parts']:
        print(f"\n{part['name']} - {part['title']} ({part['type']})")
        print(f"  行范围: {part['start_line']} - {part['end_line']}")
        
        if part['id'] == 2:  # 第二部分 - 章节
            print(f"  章节数: {len(part['chapters'])}")
            for ch in part['chapters'][:3]:  # 只显示前3章
                print(f"    {ch['title']}: {len(ch['sections'])}个题型")
            if len(part['chapters']) > 3:
                print(f"    ... 共 {len(part['chapters'])} 章")
        
        elif part['id'] == 3:  # 第三部分 - 专题
            print(f"  专题数: {len(part['topics'])}")
            for topic in part['topics'][:3]:  # 只显示前3个专题
                print(f"    {topic['name']}: {len(topic['sections'])}个题型")
            if len(part['topics']) > 3:
                print(f"    ... 共 {len(part['topics'])} 个专题")
        
        elif part['id'] == 4:  # 第四部分 - 套卷
            print(f"  套卷数: {len(part['papers'])}")
            for paper in part['papers']:
                print(f"    {paper['name']}: {len(paper['sections'])}个题型")
    
    print('\n' + '=' * 80)
    print('下册统计:')
    print('=' * 80)
    for part in lower_structure['parts']:
        print(f"\n{part['name']} - {part['title']} ({part['type']})")
        print(f"  行范围: {part['start_line']} - {part['end_line']}")


if __name__ == '__main__':
    main()
