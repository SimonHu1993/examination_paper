# 会计考试题库 H5 应用 - 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 开发一个纯 HTML/JS 的 H5 应用，支持从图片型 PDF 解析会计题库，提供开卷和闭卷两种答题模式，包含章节导航、错题本、统计面板等完整功能。

**Architecture:** 
- Python 脚本层：使用 pypdfium2 渲染 PDF 为图片 + tesseract OCR 识别文本 → 生成结构化 JSON 题库
- H5 应用层：纯前端架构，通过 fetch 加载 JSON 数据，localStorage 存储用户进度和错题
- 响应式设计：移动端优先，抽屉式侧边栏导航

**Tech Stack:** 
- 后端解析：Python 3.9+, pypdfium2, Pillow, tesseract-ocr
- 前端：HTML5, CSS3, ES6+ JavaScript（无框架）
- 数据存储：JSON 文件（题库）+ localStorage（用户数据）
- 构建工具：无（纯静态文件）

---

## 任务分解概览

| 阶段 | 任务数 | 预计工时 | 关键交付物 |
|------|--------|---------|-----------|
| 阶段1：PDF解析 | 8个任务 | 16小时 | `pdf_parser.py`, `requirements.txt`, 前3章 `questions.json` |
| 阶段2：H5基础框架 | 7个任务 | 16小时 | `index.html`, `css/style.css`, `js/app.js`, `js/navigation.js` |
| 阶段3：答题功能 | 10个任务 | 24小时 | `js/quiz.js`, 完整的开卷/闭卷逻辑 |
| 阶段4：增强功能 | 8个任务 | 16小时 | `js/storage.js`, `js/stats.js`, `js/wrongbook.js` |
| 阶段5：全量解析与测试 | 5个任务 | 8小时 | 完整 `questions.json`, 人工校对报告 |

**总计：** 38个任务，约 80 小时（10个工作日）

---

## 前置准备

### Task 0: 环境设置

**Files:**
- Create: `.venv/` (Python虚拟环境)
- Create: `requirements.txt`

- [ ] **Step 1: 创建 Python 虚拟环境**

```bash
cd "/Users/wodediannao/huzhiyang/ai_plugs/Accounting_Drills "
python3 -m venv .venv
source .venv/bin/activate
```

Expected: Virtual environment activated

- [ ] **Step 2: 安装 Python 依赖**

Create `requirements.txt`:
```txt
pypdfium2>=4.30.0
Pillow>=10.0.0
```

```bash
pip install -r requirements.txt
```

Expected: Successfully installed pypdfium2-4.30.x Pillow-10.x.x

- [ ] **Step 3: 验证 tesseract 安装**

```bash
tesseract --version
tesseract --list-langs | grep chi_sim
```

Expected: tesseract 5.x.x and chi_sim language pack available

- [ ] **Step 4: 初始化 Git 仓库（如未初始化）**

```bash
git status
# If not initialized:
git init
echo "*.pyc\n__pycache__/\n.venv/" >> .gitignore
git add .gitignore
git commit -m "chore: initialize git repository"
```

Expected: Clean git status with .gitignore committed

---

## 阶段1：PDF 解析（预计 2 天 / 16 小时）

### Task 1.1: 单页 OCR 测试脚本

**Files:**
- Create: `test_ocr.py`

**Dependencies:** None

- [ ] **Step 1: 编写单页渲染和 OCR 测试代码**

Create `test_ocr.py`:
```python
#!/usr/bin/env python3
"""测试单页 PDF 渲染和 OCR 识别"""

import pypdfium2 as pdfium
from PIL import Image
import subprocess
import sys

def render_page(pdf_path, page_num):
    """渲染指定页码为 PIL Image"""
    doc = pdfium.PdfDocument(pdf_path)
    page = doc[page_num - 1]  # 0-based index
    bitmap = page.render(scale=2, rotation=0)
    pil_image = bitmap.to_pil()
    doc.close()
    return pil_image

def ocr_image(image):
    """使用 tesseract 进行 OCR 识别"""
    temp_path = '/tmp/ocr_test.png'
    image.save(temp_path)
    
    result = subprocess.run([
        'tesseract', temp_path, 'stdout',
        '-l', 'chi_sim+eng',
        '--psm', '6'
    ], capture_output=True, timeout=60)
    
    if result.returncode != 0:
        raise RuntimeError(
            f"Tesseract OCR failed (code {result.returncode}): "
            f"{result.stderr.decode('utf-8', errors='replace')}"
        )
    
    return result.stdout.decode('utf-8', errors='replace')

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python test_ocr.py <pdf_path> <page_num>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    page_num = int(sys.argv[2])
    
    print(f"Rendering page {page_num} from {pdf_path}...")
    image = render_page(pdf_path, page_num)
    print(f"Image size: {image.size}")
    
    print("Running OCR...")
    text = ocr_image(image)
    print(f"OCR text length: {len(text)}")
    print("\n=== First 500 chars ===")
    print(text[:500])
```

- [ ] **Step 2: 测试上册第11页（第一章题目页）**

```bash
source .venv/bin/activate
python test_ocr.py "会计（上）.pdf" 11
```

Expected: Output shows ~1000+ characters of Chinese text including "第一章 总论" and multiple choice questions

- [ ] **Step 3: 测试下册第11页（对应答案页）**

```bash
python test_ocr.py "会计（下）.pdf" 11
```

Expected: Output shows answer explanations with "【解析】" markers

- [ ] **Step 4: Commit**

```bash
git add test_ocr.py requirements.txt
git commit -m "feat: add single-page OCR test script"
```

---

### Task 1.2: 题目文本解析器

**Files:**
- Create: `parsers/question_parser.py`

**Dependencies:** Task 1.1 completed

- [ ] **Step 1: 编写题目解析函数**

Create `parsers/__init__.py`:
```python
# Empty file to make parsers a package
```

Create `parsers/question_parser.py`:
```python
"""题目文本解析模块"""

import re
from typing import List, Dict, Any

def parse_questions_from_text(text: str, section_type: str) -> List[Dict[str, Any]]:
    """
    从 OCR 文本中提取题目结构
    
    Args:
        text: OCR 识别的原始文本
        section_type: 题型类型 ('single_choice', 'multiple_choice', 'true_false')
    
    Returns:
        题目列表，每个题目包含 number, question, options
    """
    questions = []
    
    # 正则匹配题号：如 "1."、"2."
    question_pattern = r'(\d+)\.\s*(.+?)(?=\n\d+\.|\Z)'
    
    for match in re.finditer(question_pattern, text, re.DOTALL):
        q_num = int(match.group(1))
        q_content = match.group(2).strip()
        
        # 提取题干和选项
        question_text, options = extract_question_and_options(q_content, section_type)
        
        questions.append({
            "number": q_num,
            "question": question_text,
            "options": options,
            "answer": None,  # 待匹配
            "explanation": None,
            "section_type": section_type
        })
    
    return questions

def extract_question_and_options(content: str, section_type: str) -> tuple:
    """
    从题目内容中提取题干和选项
    
    Returns:
        (question_text, options_list)
    """
    # 匹配选项标记 A. B. C. D.
    option_pattern = r'([A-D])\.\s*([^\n]+(?:\n(?![A-D]\.)[^\n]*)*)'
    
    options = []
    last_end = 0
    
    for match in re.finditer(option_pattern, content):
        label = match.group(1)
        text = match.group(2).strip()
        
        # 题干是第一个选项之前的内容
        if not options:
            question_text = content[:match.start()].strip()
        
        options.append({
            "label": label,
            "text": text
        })
        last_end = match.end()
    
    # 如果没有找到选项，整个内容作为题干
    if not options:
        question_text = content
        options = []
    
    return question_text, options

def parse_answers_from_text(text: str, section_type: str) -> List[Dict[str, Any]]:
    """
    从答案文本中提取答案和解析
    
    Args:
        text: OCR 识别的答案文本
        section_type: 题型类型
    
    Returns:
        答案列表，每个包含 number, answer, explanation
    """
    answers = []
    
    # 匹配题号和答案：如 "1. 【答案】D" 或 "1. D"
    answer_pattern = r'(\d+)\.\s*(?:【答案】)?\s*([A-D✓×]+)\s*(?:【解析】(.+?))?(?=\n\d+\.|\Z)'
    
    for match in re.finditer(answer_pattern, text, re.DOTALL):
        a_num = int(match.group(1))
        answer = match.group(2).strip()
        explanation = match.group(3).strip() if match.group(3) else ""
        
        answers.append({
            "number": a_num,
            "answer": list(answer) if len(answer) > 1 else [answer],  # 多选题转数组
            "explanation": explanation,
            "section_type": section_type
        })
    
    return answers
```

- [ ] **Step 2: 编写单元测试**

Create `tests/test_question_parser.py`:
```python
"""题目解析器测试"""

import pytest
from parsers.question_parser import parse_questions_from_text, parse_answers_from_text

def test_parse_single_choice_questions():
    """测试单选题解析"""
    text = """
1. 下列关于持续经营假设的表述中正确的是（ ）。
A. 持续经营应当假设企业永远不会破产清算
B. 由于理财产品只有固定有限的寿命
C. 如果判断企业不会持续经营
D. 当企业发生债务重组时

2. 下列关于会计信息质量要求的表述中正确的是（ ）。
A. 如果企业为了达到事先设定的结果
B. 因财务报表列报项目发生变化
C. 企业在利润表的列示中区分收入
D. 企业对不重要的前期差错直接调整
"""
    
    questions = parse_questions_from_text(text, 'single_choice')
    
    assert len(questions) == 2
    assert questions[0]['number'] == 1
    assert '持续经营假设' in questions[0]['question']
    assert len(questions[0]['options']) == 4
    assert questions[0]['options'][0]['label'] == 'A'

def test_parse_answers():
    """测试答案解析"""
    text = """
1. 【答案】D
【解析】持续经营假设是指企业在可预见的将来会一直经营下去。

2. 【答案】C
【解析】相关性要求企业提供的会计信息应当与决策相关。
"""
    
    answers = parse_answers_from_text(text, 'single_choice')
    
    assert len(answers) == 2
    assert answers[0]['number'] == 1
    assert answers[0]['answer'] == ['D']
    assert '持续经营' in answers[0]['explanation']

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
```

- [ ] **Step 3: 运行测试**

```bash
pip install pytest
pytest tests/test_question_parser.py -v
```

Expected: 2 passed

- [ ] **Step 4: Commit**

```bash
git add parsers/ tests/test_question_parser.py
git commit -m "feat: add question and answer parser modules"
```

---

### Task 1.3: 答案匹配算法

**Files:**
- Modify: `parsers/question_parser.py` (add match function)
- Test: `tests/test_question_parser.py` (add match tests)

**Dependencies:** Task 1.2 completed

- [ ] **Step 1: 添加答案匹配函数**

Append to `parsers/question_parser.py`:
```python
def match_answers_to_questions(
    questions: List[Dict[str, Any]], 
    answers: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    根据题型和题号匹配答案到题目
    
    Args:
        questions: 题目列表
        answers: 答案列表
    
    Returns:
        填充了答案的题目列表
    """
    # 构建复合键：(section_type, number)
    answer_map = {(a['section_type'], a['number']): a for a in answers}
    
    matched_count = 0
    for q in questions:
        key = (q['section_type'], q['number'])
        if key in answer_map:
            ans = answer_map[key]
            q['answer'] = ans['answer']
            q['explanation'] = ans['explanation']
            matched_count += 1
    
    print(f"Matched {matched_count}/{len(questions)} questions")
    return questions
```

- [ ] **Step 2: 添加匹配测试**

Append to `tests/test_question_parser.py`:
```python
from parsers.question_parser import match_answers_to_questions

def test_match_answers():
    """测试答案匹配"""
    questions = [
        {"number": 1, "question": "Q1", "options": [], "section_type": "single_choice"},
        {"number": 2, "question": "Q2", "options": [], "section_type": "single_choice"},
    ]
    
    answers = [
        {"number": 1, "answer": ["A"], "explanation": "Exp1", "section_type": "single_choice"},
        {"number": 2, "answer": ["B"], "explanation": "Exp2", "section_type": "single_choice"},
    ]
    
    matched = match_answers_to_questions(questions, answers)
    
    assert matched[0]['answer'] == ['A']
    assert matched[0]['explanation'] == 'Exp1'
    assert matched[1]['answer'] == ['B']

def test_match_with_different_types():
    """测试不同题型题号重复时的匹配"""
    questions = [
        {"number": 1, "section_type": "single_choice"},
        {"number": 1, "section_type": "multiple_choice"},  # 同题号不同题型
    ]
    
    answers = [
        {"number": 1, "answer": ["A"], "section_type": "single_choice"},
        {"number": 1, "answer": ["A", "B"], "section_type": "multiple_choice"},
    ]
    
    matched = match_answers_to_questions(questions, answers)
    
    # 应该正确匹配到对应的题型
    assert matched[0]['answer'] == ['A']
    assert matched[1]['answer'] == ['A', 'B']
```

- [ ] **Step 3: 运行测试**

```bash
pytest tests/test_question_parser.py::test_match_answers -v
pytest tests/test_question_parser.py::test_match_with_different_types -v
```

Expected: Both tests pass

- [ ] **Step 4: Commit**

```bash
git add parsers/question_parser.py tests/test_question_parser.py
git commit -m "feat: add answer matching algorithm with composite key"
```

---

### Task 1.4: 章节-页面映射表

**Files:**
- Create: `config/chapter_mapping.py`

**Dependencies:** Task 1.1 completed (need to analyze PDF structure)

- [ ] **Step 1: 分析 PDF 目录结构**

Run analysis script to determine chapter boundaries:
```bash
python3 << 'EOF'
import pypdfium2 as pdfium

doc = pdfium.PdfDocument('会计（上）.pdf')
print(f"Total pages: {len(doc)}")

# Sample pages to identify chapter boundaries
for i in range(0, min(50, len(doc)), 5):
    page = doc[i]
    bitmap = page.render(scale=1)
    # Just check if page has content
    print(f"Page {i+1}: {bitmap.width}x{bitmap.height}")
    page.close()

doc.close()
EOF
```

Expected: Identify that chapters start around pages 11, 25, 40, etc.

- [ ] **Step 2: 创建章节映射配置**

Create `config/__init__.py`:
```python
# Empty file
```

Create `config/chapter_mapping.py`:
```python
"""章节-页面对应关系配置

注意：此映射需要根据实际 PDF 结构调整
上册（题目）和下册（答案）的页码可能不对应
"""

CHAPTER_MAPPING = [
    {
        "id": 1,
        "title": "第一章 总论",
        "question_pages": list(range(11, 25)),      # 第11-24页
        "answer_pages": list(range(11, 20)),         # 答案在第11-19页
        "sections": [
            {"name": "单项选择题", "type": "single_choice"},
            {"name": "多项选择题", "type": "multiple_choice"},
            {"name": "判断题", "type": "true_false"},
        ]
    },
    {
        "id": 2,
        "title": "第二章 XXX",  # TODO: 更新实际章节名
        "question_pages": list(range(25, 40)),
        "answer_pages": list(range(20, 30)),
        "sections": [
            {"name": "单项选择题", "type": "single_choice"},
            {"name": "多项选择题", "type": "multiple_choice"},
        ]
    },
    # TODO: 补充剩余28个章节
    # 建议先完成前3章验证流程后再补充全部
]

# 前3章用于初期验证
VALIDATION_CHAPTERS = CHAPTER_MAPPING[:3]
```

- [ ] **Step 3: 验证映射准确性**

Test first chapter mapping:
```bash
python3 << 'EOF'
from config.chapter_mapping import VALIDATION_CHAPTERS
import pypdfium2 as pdfium

chapter = VALIDATION_CHAPTERS[0]
print(f"Testing: {chapter['title']}")
print(f"Question pages: {chapter['question_pages'][:3]}...")
print(f"Answer pages: {chapter['answer_pages'][:3]}...")

# Verify pages exist
doc_q = pdfium.PdfDocument('会计（上）.pdf')
doc_a = pdfium.PdfDocument('会计（下）.pdf')

for page_num in chapter['question_pages'][:1]:
    try:
        page = doc_q[page_num - 1]
        print(f"✓ Question page {page_num} exists")
        page.close()
    except Exception as e:
        print(f"✗ Question page {page_num} error: {e}")

for page_num in chapter['answer_pages'][:1]:
    try:
        page = doc_a[page_num - 1]
        print(f"✓ Answer page {page_num} exists")
        page.close()
    except Exception as e:
        print(f"✗ Answer page {page_num} error: {e}")

doc_q.close()
doc_a.close()
EOF
```

Expected: All tested pages exist without errors

- [ ] **Step 4: Commit**

```bash
git add config/
git commit -m "feat: add chapter-page mapping configuration (first 3 chapters)"
```

---

### Task 1.5: 完整 PDF 解析脚本

**Files:**
- Create: `pdf_parser.py`

**Dependencies:** Tasks 1.2, 1.3, 1.4 completed

- [ ] **Step 1: 编写主解析脚本**

Create `pdf_parser.py`:
```python
#!/usr/bin/env python3
"""
PDF 解析主脚本

功能：
1. 遍历所有章节页面
2. OCR 识别题目和答案
3. 解析并匹配答案
4. 输出结构化 JSON
"""

import json
import pypdfium2 as pdfium
from PIL import Image
import subprocess
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from parsers.question_parser import (
    parse_questions_from_text,
    parse_answers_from_text,
    match_answers_to_questions
)
from config.chapter_mapping import VALIDATION_CHAPTERS

def render_page(pdf_doc, page_num: int):
    """渲染指定页码为 PIL Image"""
    page = pdf_doc[page_num - 1]  # 0-based index
    bitmap = page.render(scale=2, rotation=0)
    return bitmap.to_pil()

def ocr_image(image) -> str:
    """使用 tesseract 进行 OCR 识别"""
    temp_path = '/tmp/ocr_temp.png'
    image.save(temp_path)
    
    result = subprocess.run([
        'tesseract', temp_path, 'stdout',
        '-l', 'chi_sim+eng',
        '--psm', '6'
    ], capture_output=True, timeout=60)
    
    if result.returncode != 0:
        raise RuntimeError(
            f"Tesseract OCR failed (code {result.returncode}): "
            f"{result.stderr.decode('utf-8', errors='replace')}"
        )
    
    return result.stdout.decode('utf-8', errors='replace')

def parse_chapter(chapter_config: Dict[str, Any]) -> Dict[str, Any]:
    """解析单个章节"""
    chapter_id = chapter_config['id']
    chapter_title = chapter_config['title']
    
    print(f"\n{'='*60}")
    print(f"Parsing Chapter {chapter_id}: {chapter_title}")
    print(f"{'='*60}")
    
    # 加载 PDF 文档
    question_pdf = pdfium.PdfDocument('会计（上）.pdf')
    answer_pdf = pdfium.PdfDocument('会计（下）.pdf')
    
    all_sections = []
    
    for section in chapter_config['sections']:
        section_name = section['name']
        section_type = section['type']
        
        print(f"\n  Parsing section: {section_name} ({section_type})")
        
        # 收集该章节所有页面的题目
        all_questions = []
        for page_num in chapter_config['question_pages']:
            try:
                img = render_page(question_pdf, page_num)
                text = ocr_image(img)
                
                if text.strip():
                    questions = parse_questions_from_text(text, section_type)
                    # 添加页码信息
                    for q in questions:
                        q['source_page'] = page_num
                        q['id'] = f"ch{chapter_id}_{section_type}_{q['number']}"
                    all_questions.extend(questions)
                    
            except Exception as e:
                print(f"    Warning: Failed to parse page {page_num}: {e}")
                continue
        
        # 收集答案
        all_answers = []
        if chapter_config.get('answer_pages'):
            for page_num in chapter_config['answer_pages']:
                try:
                    img = render_page(answer_pdf, page_num)
                    text = ocr_image(img)
                    
                    if text.strip():
                        answers = parse_answers_from_text(text, section_type)
                        all_answers.extend(answers)
                        
                except Exception as e:
                    print(f"    Warning: Failed to parse answer page {page_num}: {e}")
                    continue
        
        # 匹配答案
        if all_answers:
            all_questions = match_answers_to_questions(all_questions, all_answers)
        
        # 过滤掉没有答案的题目（可选）
        # all_questions = [q for q in all_questions if q['answer']]
        
        all_sections.append({
            "name": section_name,
            "type": section_type,
            "questions": all_questions
        })
        
        print(f"    Found {len(all_questions)} questions")
    
    # 关闭 PDF 文档
    question_pdf.close()
    answer_pdf.close()
    
    return {
        "id": chapter_id,
        "title": chapter_title,
        "sections": all_sections
    }

def main():
    """主函数"""
    print("Starting PDF parsing...")
    print(f"Processing {len(VALIDATION_CHAPTERS)} chapters")
    
    all_chapters = []
    total_questions = 0
    
    for chapter_config in VALIDATION_CHAPTERS:
        chapter_data = parse_chapter(chapter_config)
        all_chapters.append(chapter_data)
        
        # 统计题目数
        for section in chapter_data['sections']:
            total_questions += len(section['questions'])
    
    # 构建最终输出
    output = {
        "meta": {
            "version": "1.0",
            "generated_at": datetime.now().isoformat(),
            "total_chapters": len(all_chapters),
            "total_questions": total_questions
        },
        "chapters": all_chapters
    }
    
    # 保存 JSON
    output_path = Path('questions.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*60}")
    print(f"Parsing complete!")
    print(f"Total chapters: {len(all_chapters)}")
    print(f"Total questions: {total_questions}")
    print(f"Output saved to: {output_path}")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    main()
```

- [ ] **Step 2: 测试解析前3章**

```bash
source .venv/bin/activate
python pdf_parser.py
```

Expected: 
- Script runs without errors
- Outputs "Parsing complete!" with chapter/question counts
- Creates `questions.json` file (~50-100KB for 3 chapters)

- [ ] **Step 3: 验证生成的 JSON 结构**

```bash
python3 << 'EOF'
import json

with open('questions.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Meta: {data['meta']}")
print(f"\nFirst chapter: {data['chapters'][0]['title']}")
print(f"Sections: {[s['name'] for s in data['chapters'][0]['sections']]}")

# Check first question
if data['chapters'][0]['sections'][0]['questions']:
    q = data['chapters'][0]['sections'][0]['questions'][0]
    print(f"\nSample question:")
    print(f"  ID: {q['id']}")
    print(f"  Number: {q['number']}")
    print(f"  Question: {q['question'][:50]}...")
    print(f"  Options: {len(q['options'])}")
    print(f"  Answer: {q['answer']}")
    print(f"  Has explanation: {bool(q['explanation'])}")
EOF
```

Expected: JSON structure matches design spec, sample question has all required fields

- [ ] **Step 4: Commit**

```bash
git add pdf_parser.py
git commit -m "feat: add complete PDF parser script for first 3 chapters"
```

---

### Task 1.6: 人工抽样校对

**Files:**
- Modify: `questions.json` (fix OCR errors)
- Create: `docs/validation_report.md`

**Dependencies:** Task 1.5 completed

- [ ] **Step 1: 抽样检查每章5题**

Create validation checklist:
```markdown
# 前3章人工校对清单

## 第一章 总论
- [ ] 单选第1题：文字准确？选项完整？答案正确？
- [ ] 单选第5题：...
- [ ] 多选第1题：...
- [ ] 多选第3题：...
- [ ] 判断第1题：...

## 第二章 XXX
...

## 第三章 XXX
...
```

- [ ] **Step 2: 修正 OCR 错误**

Common OCR errors to fix:
- `O` → `0` (数字零)
- `l` → `1` (数字一)
- `·` → `.` (标点)
- 缺失的括号、引号

Edit `questions.json` directly or create a correction script

- [ ] **Step 3: 记录校对结果**

Create `docs/validation_report.md`:
```markdown
# PDF 解析验证报告

**日期**: 2026-06-14  
**范围**: 前3章（第一章至第三章）  
**抽样比例**: 每章5题，共15题

## 总体准确率

- 题目文本准确率: XX%
- 选项准确率: XX%
- 答案匹配准确率: XX%

## 发现的常见问题

1. ...
2. ...

## 改进建议

1. ...
2. ...
```

- [ ] **Step 4: Commit**

```bash
git add docs/validation_report.md questions.json
git commit -m "docs: add validation report for first 3 chapters"
```

---

### Task 1.7: 完善章节映射（剩余27章）

**Files:**
- Modify: `config/chapter_mapping.py`

**Dependencies:** Task 1.6 completed (understand PDF structure)

- [ ] **Step 1: 分析剩余章节边界**

Use PDF viewer or script to identify all chapter start pages

- [ ] **Step 2: 补充完整映射表**

Update `config/chapter_mapping.py` with all 30 chapters

- [ ] **Step 3: 验证映射完整性**

```bash
python3 << 'EOF'
from config.chapter_mapping import CHAPTER_MAPPING

total_pages_q = set()
total_pages_a = set()

for ch in CHAPTER_MAPPING:
    total_pages_q.update(ch['question_pages'])
    if ch.get('answer_pages'):
        total_pages_a.update(ch['answer_pages'])

print(f"Total chapters: {len(CHAPTER_MAPPING)}")
print(f"Question pages covered: {min(total_pages_q)}-{max(total_pages_q)}")
print(f"Answer pages covered: {min(total_pages_a)}-{max(total_pages_a)}")
print(f"Overlapping pages: {len(total_pages_q & total_pages_a)}")
EOF
```

Expected: All 245 question pages and 297 answer pages covered

- [ ] **Step 4: Commit**

```bash
git add config/chapter_mapping.py
git commit -m "feat: complete chapter mapping for all 30 chapters"
```

---

### Task 1.8: 全量解析并生成最终 JSON

**Files:**
- Modify: `pdf_parser.py` (use full mapping)
- Generate: `questions.json` (full version)

**Dependencies:** Task 1.7 completed

- [ ] **Step 1: 修改解析脚本使用完整映射**

Update `pdf_parser.py`:
```python
from config.chapter_mapping import CHAPTER_MAPPING  # Changed from VALIDATION_CHAPTERS

# In main():
print(f"Processing {len(CHAPTER_MAPPING)} chapters")
for chapter_config in CHAPTER_MAPPING:  # Changed
    ...
```

- [ ] **Step 2: 运行全量解析**

```bash
python pdf_parser.py
```

Expected: 
- Processing takes 30-60 minutes for all 30 chapters
- Generates `questions.json` (~2-5MB)
- Total questions: ~1500+

- [ ] **Step 3: 验证文件大小和结构**

```bash
ls -lh questions.json
python3 -c "import json; d=json.load(open('questions.json')); print(f'Chapters: {len(d[\"chapters\"])}, Questions: {d[\"meta\"][\"total_questions\"]}')"
```

Expected: File size 2-5MB, 30 chapters, 1500+ questions

- [ ] **Step 4: 备份并提交**

```bash
cp questions.json questions-full-backup.json
git add questions.json pdf_parser.py
git commit -m "feat: generate full question bank JSON (30 chapters, 1500+ questions)"
```

---

## 阶段1 验收标准

✅ **必须满足**：
- [ ] `pdf_parser.py` 能成功解析全部30章
- [ ] `questions.json` 包含 1500+ 题目
- [ ] 每道题目包含：id, number, question, options, answer, explanation
- [ ] 答案匹配准确率 ≥ 95%（人工抽样验证）
- [ ] JSON 结构符合设计文档规范

️ **已知限制**：
- OCR 可能有少量识别错误（需人工校对关键章节）
- 部分复杂排版题目可能需要手动调整

---

## 阶段2：H5 基础框架（预计 2 天 / 16 小时）

### Task 2.1: HTML 页面骨架

**Files:**
- Create: `index.html`

**Dependencies:** None (can work in parallel with Stage 1)

- [ ] **Step 1: 创建基础 HTML 结构**

Create `index.html`:
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>会计考试题库</title>
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <!-- Header -->
    <header class="app-header">
        <button class="hamburger-btn" id="menuBtn" aria-label="菜单">☰</button>
        <h1>会计考试题库</h1>
        <div class="header-controls">
            <button id="wrongBookBtn">📕 错题本</button>
            <button id="modeToggle">📝 闭卷模式</button>
            <button id="statsBtn">📊 统计</button>
        </div>
    </header>

    <!-- Main Container -->
    <div class="app-container">
        <!-- Sidebar: Chapter Navigation -->
        <aside class="sidebar" id="sidebar">
            <nav id="chapterNav">
                <!-- 动态生成章节列表 -->
            </nav>
        </aside>

        <!-- Main Content: Quiz Area -->
        <main class="main-content">
            <!-- Question Display -->
            <div id="questionArea">
                <div class="question-header">
                    <span id="questionNumber">请选择章节开始答题</span>
                    <span id="questionType"></span>
                </div>
                <div id="questionText"></div>
                <div id="optionsContainer"></div>
            </div>

            <!-- Answer Feedback -->
            <div id="feedbackArea" class="hidden">
                <div id="resultIcon"></div>
                <div id="correctAnswer"></div>
                <div id="explanation"></div>
            </div>

            <!-- Controls -->
            <div class="controls">
                <button id="prevBtn" disabled>上一题</button>
                <button id="nextBtn" disabled>下一题</button>
                <button id="showAnswerBtn" class="primary hidden">查看答案</button>
                <button id="submitBtn" class="primary hidden">提交答案</button>
            </div>
        </main>
    </div>

    <!-- Wrong Book Modal -->
    <div id="wrongBookModal" class="modal hidden">
        <!-- 错题本内容 -->
    </div>

    <!-- Stats Modal -->
    <div id="statsModal" class="modal hidden">
        <!-- 统计面板内容 -->
    </div>

    <!-- Overlay for mobile sidebar -->
    <div class="overlay" id="overlay"></div>

    <script src="js/storage.js"></script>
    <script src="js/navigation.js"></script>
    <script src="js/quiz.js"></script>
    <script src="js/stats.js"></script>
    <script src="js/wrongbook.js"></script>
    <script src="js/app.js"></script>
</body>
</html>
```

- [ ] **Step 2: 在浏览器中打开验证结构**

```bash
open index.html
```

Expected: Page loads with header, empty sidebar, and placeholder content

- [ ] **Step 3: Commit**

```bash
git add index.html
git commit -m "feat: create base HTML structure"
```

---

### Task 2.2: 基础 CSS 样式

**Files:**
- Create: `css/style.css`

**Dependencies:** Task 2.1 completed

- [ ] **Step 1: 创建 CSS 变量和重置样式**

Create `css/style.css`:
```css
/* CSS Variables */
:root {
    --primary-color: #1890ff;
    --success-color: #52c41a;
    --error-color: #ff4d4f;
    --warning-color: #faad14;
    --text-color: #333;
    --text-secondary: #666;
    --bg-color: #f5f5f5;
    --card-bg: #fff;
    --border-color: #e8e8e8;
    --header-height: 60px;
    --sidebar-width: 280px;
}

/* Reset */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
    background-color: var(--bg-color);
    color: var(--text-color);
    line-height: 1.6;
}

/* Header */
.app-header {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: var(--header-height);
    background: var(--card-bg);
    border-bottom: 1px solid var(--border-color);
    display: flex;
    align-items: center;
    padding: 0 16px;
    z-index: 100;
}

.hamburger-btn {
    display: none;
    font-size: 24px;
    background: none;
    border: none;
    cursor: pointer;
    margin-right: 12px;
}

.app-header h1 {
    font-size: 18px;
    font-weight: 600;
    flex: 1;
}

.header-controls {
    display: flex;
    gap: 8px;
}

.header-controls button {
    padding: 6px 12px;
    font-size: 14px;
    border: 1px solid var(--border-color);
    background: var(--card-bg);
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s;
}

.header-controls button:hover {
    border-color: var(--primary-color);
    color: var(--primary-color);
}

/* App Container */
.app-container {
    display: flex;
    margin-top: var(--header-height);
    min-height: calc(100vh - var(--header-height));
}

/* Sidebar */
.sidebar {
    width: var(--sidebar-width);
    background: var(--card-bg);
    border-right: 1px solid var(--border-color);
    overflow-y: auto;
    padding: 16px;
    position: fixed;
    left: 0;
    top: var(--header-height);
    bottom: 0;
    transition: transform 0.3s ease;
}

.chapter-item {
    margin-bottom: 12px;
}

.chapter-title {
    font-weight: 600;
    padding: 8px;
    cursor: pointer;
    border-radius: 4px;
    transition: background 0.2s;
}

.chapter-title:hover {
    background: var(--bg-color);
}

.section-list {
    margin-left: 16px;
    margin-top: 8px;
}

.section-item {
    padding: 6px 8px;
    font-size: 14px;
    color: var(--text-secondary);
    cursor: pointer;
    border-radius: 4px;
    display: flex;
    justify-content: space-between;
}

.section-item:hover {
    background: var(--bg-color);
    color: var(--primary-color);
}

.section-item.active {
    background: var(--primary-color);
    color: white;
}

.question-count {
    font-size: 12px;
    opacity: 0.7;
}

/* Main Content */
.main-content {
    flex: 1;
    margin-left: var(--sidebar-width);
    padding: 24px;
    max-width: 800px;
}

/* Question Area */
#questionArea {
    background: var(--card-bg);
    padding: 24px;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    margin-bottom: 24px;
}

.question-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--border-color);
}

#questionNumber {
    font-weight: 600;
    font-size: 16px;
}

#questionType {
    font-size: 14px;
    color: var(--text-secondary);
    background: var(--bg-color);
    padding: 4px 8px;
    border-radius: 4px;
}

#questionText {
    font-size: 16px;
    line-height: 1.8;
    margin-bottom: 20px;
}

/* Options */
.option-item {
    display: flex;
    align-items: flex-start;
    padding: 12px;
    margin-bottom: 8px;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s;
}

.option-item:hover {
    border-color: var(--primary-color);
    background: rgba(24, 144, 255, 0.05);
}

.option-item input {
    margin-right: 12px;
    margin-top: 4px;
}

.option-label {
    font-weight: 600;
    margin-right: 8px;
    min-width: 20px;
}

.option-text {
    flex: 1;
}

/* Feedback Area */
#feedbackArea {
    background: var(--card-bg);
    padding: 24px;
    border-radius: 8px;
    margin-bottom: 24px;
    border-left: 4px solid var(--primary-color);
}

#feedbackArea.hidden {
    display: none;
}

#resultIcon {
    font-size: 18px;
    font-weight: 600;
    margin-bottom: 12px;
}

#correctAnswer {
    margin-bottom: 12px;
}

#explanation {
    font-size: 14px;
    color: var(--text-secondary);
    line-height: 1.6;
}

/* Controls */
.controls {
    display: flex;
    gap: 12px;
    justify-content: center;
}

.controls button {
    padding: 10px 24px;
    font-size: 14px;
    border: 1px solid var(--border-color);
    background: var(--card-bg);
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s;
}

.controls button:hover:not(:disabled) {
    border-color: var(--primary-color);
    color: var(--primary-color);
}

.controls button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.controls button.primary {
    background: var(--primary-color);
    color: white;
    border-color: var(--primary-color);
}

.controls button.primary:hover:not(:disabled) {
    background: #096dd9;
}

.controls button.hidden {
    display: none;
}

/* Modal */
.modal {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
}

.modal.hidden {
    display: none;
}

.modal-content {
    background: var(--card-bg);
    padding: 24px;
    border-radius: 8px;
    max-width: 600px;
    width: 90%;
    max-height: 80vh;
    overflow-y: auto;
}

/* Overlay */
.overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    z-index: 99;
    display: none;
}

.overlay.show {
    display: block;
}

/* Mobile Responsive */
@media (max-width: 767px) {
    .hamburger-btn {
        display: block;
    }

    .sidebar {
        transform: translateX(-100%);
        z-index: 100;
    }

    .sidebar.open {
        transform: translateX(0);
    }

    .main-content {
        margin-left: 0;
        padding: 16px;
    }

    .controls {
        flex-wrap: wrap;
    }

    .controls button {
        flex: 1;
        min-width: 100px;
    }
}
```

- [ ] **Step 2: 刷新浏览器验证样式**

Expected: Page displays with proper layout, sidebar visible on desktop

- [ ] **Step 3: Commit**

```bash
git add css/style.css
git commit -m "feat: add base CSS styles with responsive design"
```

---

### Task 2.3: LocalStorage 存储模块

**Files:**
- Create: `js/storage.js`

**Dependencies:** None

- [ ] **Step 1: 实现存储模块**

Create `js/storage.js`:
```javascript
/**
 * 本地存储管理模块
 * 负责错题本、答题历史、章节进度、用户设置的持久化
 */

const Storage = {
    KEYS: {
        WRONG_QUESTIONS: 'accounting_wrong_questions',
        QUIZ_HISTORY: 'accounting_quiz_history',
        CHAPTER_PROGRESS: 'accounting_chapter_progress',
        SETTINGS: 'accounting_settings'
    },

    /**
     * 保存错题
     */
    saveWrongQuestion(questionId, userAnswer, correctAnswer) {
        const wrongQuestions = this.getWrongQuestions();
        
        // 检查是否已存在
        const existing = wrongQuestions.find(w => w.questionId === questionId);
        if (existing) {
            // 更新为最新的错误答案和正确答案
            existing.userAnswer = userAnswer;
            existing.correctAnswer = correctAnswer;
            existing.timestamp = Date.now();
            existing.reviewed = false;
        } else {
            wrongQuestions.push({
                questionId,
                userAnswer,
                correctAnswer,
                timestamp: Date.now(),
                reviewed: false
            });
        }
        
        localStorage.setItem(
            this.KEYS.WRONG_QUESTIONS,
            JSON.stringify(wrongQuestions)
        );
    },

    /**
     * 获取错题列表
     */
    getWrongQuestions() {
        const data = localStorage.getItem(this.KEYS.WRONG_QUESTIONS);
        return data ? JSON.parse(data) : [];
    },

    /**
     * 标记错题为已复习
     */
    markAsReviewed(questionId) {
        const wrongQuestions = this.getWrongQuestions();
        const question = wrongQuestions.find(w => w.questionId === questionId);
        if (question) {
            question.reviewed = true;
            localStorage.setItem(
                this.KEYS.WRONG_QUESTIONS,
                JSON.stringify(wrongQuestions)
            );
        }
    },

    /**
     * 保存答题历史
     */
    saveQuizHistory(chapterId, sectionType, score, total, correct, mode) {
        const history = this.getQuizHistory();
        history.push({
            chapterId,
            sectionType,
            score,
            totalQuestions: total,
            correctCount: correct,
            timestamp: Date.now(),
            mode
        });
        
        // 只保留最近100条
        if (history.length > 100) {
            history.shift();
        }
        
        localStorage.setItem(
            this.KEYS.QUIZ_HISTORY,
            JSON.stringify(history)
        );
        
        // 更新章节进度
        this.updateChapterProgress(chapterId, score);
    },

    /**
     * 获取答题历史
     */
    getQuizHistory() {
        const data = localStorage.getItem(this.KEYS.QUIZ_HISTORY);
        return data ? JSON.parse(data) : [];
    },

    /**
     * 更新章节进度
     */
    updateChapterProgress(chapterId, score) {
        const progress = this.getChapterProgresses();
        
        if (!progress[chapterId]) {
            progress[chapterId] = {
                completed: false,
                lastAccessed: Date.now(),
                bestScore: 0
            };
        }
        
        progress[chapterId].completed = true;
        progress[chapterId].lastAccessed = Date.now();
        progress[chapterId].bestScore = Math.max(
            progress[chapterId].bestScore,
            score
        );
        
        localStorage.setItem(
            this.KEYS.CHAPTER_PROGRESS,
            JSON.stringify(progress)
        );
    },

    /**
     * 获取章节进度
     */
    getChapterProgress(chapterId) {
        const progresses = this.getChapterProgresses();
        return progresses[chapterId] || null;
    },

    /**
     * 获取所有章节进度
     */
    getChapterProgresses() {
        const data = localStorage.getItem(this.KEYS.CHAPTER_PROGRESS);
        return data ? JSON.parse(data) : {};
    },

    /**
     * 保存设置
     */
    saveSettings(settings) {
        localStorage.setItem(
            this.KEYS.SETTINGS,
            JSON.stringify(settings)
        );
    },

    /**
     * 获取设置
     */
    getSettings() {
        const data = localStorage.getItem(this.KEYS.SETTINGS);
        return data ? JSON.parse(data) : {
            mode: 'open',
            theme: 'light',
            fontSize: 'medium'
        };
    }
};
```

- [ ] **Step 2: 测试存储功能**

Open browser console and test:
```javascript
// Test save and retrieve
Storage.saveWrongQuestion('test1', ['A'], ['D']);
console.log(Storage.getWrongQuestions());

Storage.saveSettings({mode: 'closed'});
console.log(Storage.getSettings());
```

Expected: Data persists correctly in localStorage

- [ ] **Step 3: Commit**

```bash
git add js/storage.js
git commit -m "feat: implement localStorage management module"
```

---

### Task 2.4: JSON 数据加载和缓存

**Files:**
- Create: `js/app.js` (partial - data loading only)

**Dependencies:** Task 2.3 completed

- [ ] **Step 1: 实现数据加载和缓存**

Create `js/app.js`:
```javascript
/**
 * 应用入口和数据管理
 */

// 全局数据缓存
let quizData = null;

/**
 * 加载题库数据（带缓存）
 */
async function loadQuizData() {
    if (!quizData) {
        console.log('Loading quiz data from questions.json...');
        try {
            const response = await fetch('questions.json');
            if (!response.ok) {
                throw new Error(`Failed to load questions.json: ${response.status}`);
            }
            quizData = await response.json();
            console.log(`Loaded ${quizData.meta.total_chapters} chapters, ${quizData.meta.total_questions} questions`);
        } catch (error) {
            console.error('Error loading quiz data:', error);
            alert('加载题库失败，请确保 questions.json 文件存在');
            throw error;
        }
    }
    return quizData;
}

/**
 * 应用初始化
 */
async function initApp() {
    console.log('Initializing app...');
    
    try {
        // 加载题库数据
        await loadQuizData();
        
        // 初始化各模块
        // TODO: Initialize navigation, quiz engine, etc.
        
        console.log('App initialized successfully');
    } catch (error) {
        console.error('App initialization failed:', error);
    }
}

// DOMContentLoaded 时初始化
document.addEventListener('DOMContentLoaded', initApp);
```

- [ ] **Step 2: 测试数据加载**

Open `index.html` in browser and check console:

Expected: Console shows "Loaded X chapters, Y questions"

- [ ] **Step 3: Commit**

```bash
git add js/app.js
git commit -m "feat: add quiz data loading with caching"
```

---

### Task 2.5: 章节导航模块

**Files:**
- Create: `js/navigation.js`

**Dependencies:** Task 2.4 completed

- [ ] **Step 1: 实现章节导航**

Create `js/navigation.js`:
```javascript
/**
 * 章节导航模块
 * 负责渲染侧边栏章节列表和处理章节切换
 */

class ChapterNavigation {
    constructor(onSectionSelect) {
        this.onSectionSelect = onSectionSelect;
        this.chapters = [];
    }

    /**
     * 加载并渲染章节列表
     */
    async loadChapters() {
        const data = await loadQuizData();
        this.chapters = data.chapters;
        
        this.renderSidebar();
        this.bindEvents();
    }

    /**
     * 渲染侧边栏
     */
    renderSidebar() {
        const navHtml = this.chapters.map(chapter => {
            const progress = Storage.getChapterProgress(chapter.id);
            const completedClass = progress?.completed ? 'completed' : '';
            
            return `
                <div class="chapter-item ${completedClass}" data-chapter-id="${chapter.id}">
                    <div class="chapter-title">${chapter.title}</div>
                    <div class="section-list">
                        ${chapter.sections.map(section => `
                            <div class="section-item" data-section-type="${section.type}">
                                <span>${section.name}</span>
                                <span class="question-count">(${section.questions.length}题)</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }).join('');
        
        document.getElementById('chapterNav').innerHTML = navHtml;
    }

    /**
     * 绑定事件
     */
    bindEvents() {
        // 章节项点击展开/折叠（可选）
        document.querySelectorAll('.chapter-title').forEach(title => {
            title.addEventListener('click', () => {
                const chapterItem = title.closest('.chapter-item');
                const sectionList = chapterItem.querySelector('.section-list');
                sectionList.style.display = sectionList.style.display === 'none' ? 'block' : 'none';
            });
        });

        // 题型项点击加载题目
        document.querySelectorAll('.section-item').forEach(item => {
            item.addEventListener('click', () => {
                const chapterItem = item.closest('.chapter-item');
                const chapterId = parseInt(chapterItem.dataset.chapterId);
                const sectionType = item.dataset.sectionType;
                
                // 高亮当前选中
                document.querySelectorAll('.section-item').forEach(i => 
                    i.classList.remove('active'));
                item.classList.add('active');
                
                // 调用回调函数
                if (this.onSectionSelect) {
                    this.onSectionSelect(chapterId, sectionType);
                }
                
                // 移动端关闭侧边栏
                if (window.innerWidth <= 767) {
                    closeSidebar();
                }
            });
        });
    }
}

/**
 * 移动端侧边栏控制
 */
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('overlay');
    
    sidebar.classList.toggle('open');
    overlay.classList.toggle('show');
}

function closeSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('overlay');
    
    sidebar.classList.remove('open');
    overlay.classList.remove('show');
}

// 绑定汉堡菜单按钮
document.addEventListener('DOMContentLoaded', () => {
    const menuBtn = document.getElementById('menuBtn');
    const overlay = document.getElementById('overlay');
    
    if (menuBtn) {
        menuBtn.addEventListener('click', toggleSidebar);
    }
    
    if (overlay) {
        overlay.addEventListener('click', closeSidebar);
    }
});
```

- [ ] **Step 2: 集成到 app.js**

Update `js/app.js`:
```javascript
// Add at top
let chapterNav = null;

// Update initApp function
async function initApp() {
    console.log('Initializing app...');
    
    try {
        // 加载题库数据
        await loadQuizData();
        
        // 初始化章节导航
        chapterNav = new ChapterNavigation((chapterId, sectionType) => {
            // TODO: Load questions for selected section
            console.log(`Selected: Chapter ${chapterId}, Section ${sectionType}`);
        });
        await chapterNav.loadChapters();
        
        console.log('App initialized successfully');
    } catch (error) {
        console.error('App initialization failed:', error);
    }
}
```

- [ ] **Step 3: 测试章节导航**

Refresh browser and click on sections:

Expected: Sidebar renders with all chapters, clicking highlights section

- [ ] **Step 4: Commit**

```bash
git add js/navigation.js js/app.js
git commit -m "feat: implement chapter navigation with mobile sidebar"
```

---

## 阶段2 验收标准

✅ **必须满足**：
- [ ] `index.html` 页面正常加载，无控制台错误
- [ ] 侧边栏显示全部30章，每章包含题型列表
- [ ] 点击题型项能高亮选中
- [ ] 移动端汉堡菜单能打开/关闭侧边栏
- [ ] `questions.json` 数据成功加载并缓存
- [ ] localStorage 读写功能正常

---

## 后续阶段概要

### 阶段3：答题功能（3天 / 24小时）
- Task 3.1-3.4: 答题引擎核心逻辑（`js/quiz.js`）
- Task 3.5-3.7: 开卷模式实现
- Task 3.8-3.10: 闭卷模式实现

### 阶段4：增强功能（2天 / 16小时）
- Task 4.1-4.3: 错题本模块（`js/wrongbook.js`）
- Task 4.4-4.6: 统计面板（`js/stats.js`）
- Task 4.7-4.8: 模式切换和用户体验优化

### 阶段5：全量解析与测试（1天 / 8小时）
- Task 5.1-5.5: 完整PDF解析、人工校对、全面测试、性能优化

---

## 风险与应对

### 高风险
1. **OCR 识别率低**
   - 应对：提高渲染 DPI，人工校对关键章节，提供报错反馈功能
   
2. **题目-答案匹配失败**
   - 应对：建立精确页面对应表，通过题型+题号复合键二次校验

### 中风险
3. **移动端兼容性问题**
   - 应对：使用标准 CSS，测试主流浏览器，提供降级方案

4. **JSON 文件过大导致加载慢**
   - 应对：已实现缓存机制，考虑按章节拆分（如需）

### 低风险
5. **localStorage 容量限制**
   - 应对：定期清理历史记录，仅保留最近100条

---

## 下一步行动

Plan complete and saved to `docs/superpowers/plans/2026-06-14-accounting-quiz-implementation.md`. 

Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
