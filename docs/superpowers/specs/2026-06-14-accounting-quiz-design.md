# 会计考试题库 H5 应用 - 设计文档

**版本**: 1.0  
**日期**: 2026-06-14  
**作者**: AI Assistant  
**状态**: Draft

---

## 1. 项目概述

### 1.1 项目背景
开发一个基于纯 HTML/JS 的 H5 应用，用于会计教材（上册题目 + 下册答案）的在线学习和考试练习。应用支持开卷和闭卷两种模式，提供完整的答题、评分、错题本等功能。

### 1.2 核心需求
- **PDF 解析**：从图片型 PDF 中提取题目和答案，生成结构化 JSON 题库
- **开卷模式**：选择选项后立即显示正确答案和解析
- **闭卷模式**：完成所有题目后提交，统一显示结果和解析
- **章节导航**：按章节组织题目，支持快速跳转
- **错题本**：自动记录错题，支持复习
- **本地存储**：使用 localStorage 保存学习进度和设置

### 1.3 技术选型
- **前端框架**：纯 HTML/CSS/JavaScript（无框架依赖）
- **PDF 解析**：Python + pypdfium2（渲染）+ tesseract（OCR）
- **数据存储**：JSON 文件（题库）+ localStorage（用户数据）
- **响应式设计**：移动端优先，适配手机浏览器

---

## 2. 系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────┐
│         PDF 解析层 (Python)              │
│  ┌──────────────┐  ┌─────────────────┐  │
│  │ pypdfium2    │→│ tesseract OCR   │  │
│  │ 渲染PDF为图片 │  │ 识别中文文本     │  │
│  └──────────────┘  └────────────────┘  │
│                             ↓            │
│                    ┌──────────────┐      │
│                    │ JSON题库生成  │      │
│                    │ questions.json│      │
│                    └──────────────      │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│         H5 应用层 (纯HTML/JS)            │
│  ┌──────────┐  ┌──────────┐  ┌───────┐  │
│  │章节导航   │  │答题引擎   │  │本地存储│  │
│  │          │  │开卷/闭卷  │  │       │  │
│  └──────────┘  └──────────┘  └───────┘  │
└─────────────────────────────────────────┘
```

### 2.2 项目结构

```
Accounting_Drills/
├── pdf_parser.py              # PDF解析脚本
├── requirements.txt           # Python依赖
├── questions.json             # 生成的题库JSON
├── index.html                 # H5主页面
├── css/
│   └── style.css              # 样式文件
├── js/
│   ├── app.js                 # 应用入口和初始化
│   ├── quiz.js                # 答题引擎核心逻辑
│   ├── navigation.js          # 章节导航
│   ├── storage.js             # 本地存储管理
│   └── stats.js               # 统计面板
├── docs/
│   └── superpowers/specs/
│       └── 2026-06-14-accounting-quiz-design.md  # 本文档
└── README.md                  # 使用说明
```

---

## 3. 数据设计

### 3.1 JSON 题库结构

```json
{
  "meta": {
    "version": "1.0",
    "generated_at": "2026-06-14T16:30:00Z",
    "total_chapters": 30,
    "total_questions": 1500
  },
  "chapters": [
    {
      "id": 1,
      "title": "第一章 总论",
      "sections": [
        {
          "name": "单项选择题",
          "type": "single_choice",
          "questions": [
            {
              "id": "ch1_single_1",
              "number": 1,
              "question": "下列关于持续经营假设的表述中正确的是（ ）。",
              "options": [
                {"label": "A", "text": "持续经营应当假设企业永远不会破产清算..."},
                {"label": "B", "text": "由于理财产品只有固定有限的寿命..."},
                {"label": "C", "text": "如果判断企业不会持续经营..."},
                {"label": "D", "text": "当企业发生债务重组时..."}
              ],
              "answer": ["D"],
              "explanation": "【解析】持续经营假设是指...",
              "difficulty": "基础",
              "tags": ["持续经营", "会计基本假设"],
              "source_page": 11
            }
          ]
        },
        {
          "name": "多项选择题",
          "type": "multiple_choice",
          "questions": [...]
        },
        {
          "name": "判断题",
          "type": "true_false",
          "questions": [...]
        }
      ]
    }
  ]
}
```

### 3.2 题型定义

| 题型 | type 值 | answer 格式 | 说明 |
|------|---------|-------------|------|
| 单选题 | `single_choice` | `["A"]` | 单个字母 |
| 多选题 | `multiple_choice` | `["A", "C", "D"]` | 多个字母数组 |
| 判断题 | `true_false` | `["✓"]` 或 `[""]` | 对/错符号 |

### 3.3 LocalStorage 数据结构

```javascript
// 错题本
{
  "wrongQuestions": [
    {
      "questionId": "ch1_single_1",
      "userAnswer": ["A"],
      "correctAnswer": ["D"],
      "timestamp": 1718352000000,
      "reviewed": false
    }
  ]
}

// 答题历史
{
  "quizHistory": [
    {
      "chapterId": 1,
      "sectionType": "single_choice",
      "score": 85,
      "totalQuestions": 20,
      "correctCount": 17,
      "timestamp": 1718352000000,
      "mode": "closed"
    }
  ]
}

// 章节进度
{
  "chapterProgress": {
    "1": {
      "completed": true,
      "lastAccessed": 1718352000000,
      "bestScore": 90
    }
  }
}

// 用户设置
{
  "settings": {
    "mode": "open",  // "open" 或 "closed"
    "theme": "light",
    "fontSize": "medium"
  }
}
```

---

## 4. 功能模块设计

### 4.1 PDF 解析模块 (`pdf_parser.py`)

#### 4.1.1 核心流程

```python
def main():
    # 1. 加载两个 PDF
    question_pdf = PdfDocument('会计（上）.pdf')
    answer_pdf = PdfDocument('会计（下）.pdf')
    
    # 2. 遍历所有章节页面
    for chapter_info in chapter_mapping:
        chapter_id = chapter_info['id']
        question_pages = chapter_info['question_pages']
        answer_pages = chapter_info['answer_pages']
        
        # 3. 解析题目页面
        questions = []
        for page_num in question_pages:
            img = render_page(question_pdf, page_num)
            text = ocr_image(img)
            parsed = parse_questions_from_text(text)
            questions.extend(parsed)
        
        # 4. 解析答案页面并匹配
        if answer_pages:
            answers = []
            for page_num in answer_pages:
                img = render_page(answer_pdf, page_num)
                text = ocr_image(img)
                parsed = parse_answers_from_text(text)
                answers.extend(parsed)
            
            match_answers_to_questions(questions, answers)
        
        # 5. 组装章节数据
        chapter_data = build_chapter(chapter_id, questions)
        all_chapters.append(chapter_data)
    
    # 6. 输出 JSON
    output = {
        "meta": {...},
        "chapters": all_chapters
    }
    save_json(output, 'questions.json')
```

#### 4.1.2 关键函数

**渲染 PDF 页面为图片**
```python
def render_page(pdf_doc, page_num):
    """将指定页码渲染为 PIL Image"""
    page = pdf_doc[page_num - 1]  # 0-based index
    bitmap = page.render(scale=2, rotation=0)
    return bitmap.to_pil()
```

**OCR 识别**
```python
def ocr_image(image):
    """使用 tesseract 进行 OCR 识别"""
    temp_path = '/tmp/ocr_temp.png'
    image.save(temp_path)
    
    result = subprocess.run([
        'tesseract', temp_path, 'stdout',
        '-l', 'chi_sim+eng',
        '--psm', '6'
    ], capture_output=True, timeout=60)
    
    # 检查返回码，确保 OCR 成功
    if result.returncode != 0:
        raise RuntimeError(
            f"Tesseract OCR failed (code {result.returncode}): "
            f"{result.stderr.decode('utf-8', errors='replace')}"
        )
    
    return result.stdout.decode('utf-8', errors='replace')
```

**解析题目文本**
```python
def parse_questions_from_text(text):
    """从 OCR 文本中提取题目结构"""
    questions = []
    
    # 正则匹配题号：如 "1."、"2."
    question_pattern = r'(\d+)\.\s*(.+?)(?=\n\d+\.|\Z)'
    
    for match in re.finditer(question_pattern, text, re.DOTALL):
        q_num = int(match.group(1))
        q_content = match.group(2).strip()
        
        # 提取题干和选项
        question_text, options = extract_question_and_options(q_content)
        
        questions.append({
            "number": q_num,
            "question": question_text,
            "options": options,
            "answer": None,  # 待匹配
            "explanation": None
        })
    
    return questions
```

**匹配答案到题目**
```python
def match_answers_to_questions(questions, answers):
    """根据题型和题号匹配答案（避免同章节不同题型题号重复）"""
    # 构建复合键：(section_type, number)
    answer_map = {(a['section_type'], a['number']): a for a in answers}
    
    for q in questions:
        key = (q['section_type'], q['number'])
        if key in answer_map:
            ans = answer_map[key]
            q['answer'] = ans['answer']
            q['explanation'] = ans['explanation']
```

#### 4.1.3 章节-页面对应表

由于 PDF 没有明确的章节标记，需要手动建立映射：

```python
# 示例：前几章的页面对应关系
chapter_mapping = [
    {
        "id": 1,
        "title": "第一章 总论",
        "question_pages": list(range(11, 25)),  # 第11-24页
        "answer_pages": list(range(11, 20))      # 答案在第11-19页
    },
    {
        "id": 2,
        "title": "第二章 XXX",
        "question_pages": list(range(25, 40)),
        "answer_pages": list(range(20, 30))
    },
    # ... 更多章节
]
```

**注意**：实际映射需要通过分析 PDF 目录或人工确认来确定。

---

### 4.2 H5 应用模块

#### 4.2.1 页面布局

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>会计考试题库</title>
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <!-- Header -->
    <header class="app-header">
        <h1>会计考试题库</h1>
        <div class="header-controls">
            <button id="wrongBookBtn"> 错题本</button>
            <button id="modeToggle">📝 闭卷模式</button>
            <button id="statsBtn">📊 统计</button>
        </div>
    </header>

    <!-- Main Container -->
    <div class="app-container">
        <!-- Sidebar: Chapter Navigation -->
        <aside class="sidebar">
            <nav id="chapterNav">
                <!-- 动态生成章节列表 -->
            </nav>
        </aside>

        <!-- Main Content: Quiz Area -->
        <main class="main-content">
            <!-- Question Display -->
            <div id="questionArea">
                <div class="question-header">
                    <span id="questionNumber">第 1 题</span>
                    <span id="questionType">单选题</span>
                </div>
                <div id="questionText"></div>
                <div id="optionsContainer"></div>
            </div>

            <!-- Answer Feedback (Closed Mode) -->
            <div id="feedbackArea" class="hidden">
                <div id="resultIcon"></div>
                <div id="correctAnswer"></div>
                <div id="explanation"></div>
            </div>

            <!-- Controls -->
            <div class="controls">
                <button id="prevBtn">上一题</button>
                <button id="nextBtn">下一题</button>
                <button id="showAnswerBtn" class="primary">查看答案</button>
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

    <script src="js/storage.js"></script>
    <script src="js/navigation.js"></script>
    <script src="js/quiz.js"></script>
    <script src="js/stats.js"></script>
    <script src="js/wrongbook.js"></script>
    <script src="js/app.js"></script>
</body>
</html>
```

#### 4.2.2 答题引擎 (`quiz.js`)

```javascript
class QuizEngine {
    constructor() {
        this.mode = Storage.getSettings().mode || 'open';
        this.currentChapter = null;
        this.currentSection = null;
        this.currentQuestionIndex = 0;
        this.questions = [];
        this.userAnswers = {};
        this.score = 0;
    }

    /**
     * 加载章节题目
     */
    loadChapter(chapterId, sectionType) {
        fetch('questions.json')
            .then(res => res.json())
            .then(data => {
                const chapter = data.chapters.find(c => c.id === chapterId);
                const section = chapter.sections.find(s => s.type === sectionType);
                
                this.currentChapter = chapter;
                this.currentSection = section;
                this.questions = section.questions;
                this.currentQuestionIndex = 0;
                this.userAnswers = {};
                
                this.renderQuestion();
            });
    }

    /**
     * 渲染当前题目
     */
    renderQuestion() {
        const q = this.questions[this.currentQuestionIndex];
        
        // 更新题号和类型
        document.getElementById('questionNumber').textContent = 
            `第 ${q.number} 题`;
        document.getElementById('questionType').textContent = 
            this.getTypeLabel(this.currentSection.type);
        
        // 渲染题干
        document.getElementById('questionText').innerHTML = q.question;
        
        // 渲染选项（开卷模式添加自动触发）
        const optionsHtml = q.options.map(opt => `
            <label class="option-item">
                <input type="${this.getInputType()}" 
                       name="answer" 
                       value="${opt.label}"
                       ${this.mode === 'open' ? 'onchange="app.quizEngine.submitCurrentAnswer()"' : ''}
                       ${this.userAnswers[q.id] ? 
                         (Array.isArray(this.userAnswers[q.id]) ? 
                          this.userAnswers[q.id].includes(opt.label) ? 'checked' : '' :
                          this.userAnswers[q.id] === opt.label ? 'checked' : '') 
                         : ''}>
                <span class="option-label">${opt.label}.</span>
                <span class="option-text">${opt.text}</span>
            </label>
        `).join('');
        
        document.getElementById('optionsContainer').innerHTML = optionsHtml;
        
        // 隐藏反馈区
        document.getElementById('feedbackArea').classList.add('hidden');
        
        // 更新按钮状态
        this.updateButtonStates();
    }

    /**
     * 获取输入类型（单选/多选）
     */
    getInputType() {
        return this.currentSection.type === 'multiple_choice' ? 'checkbox' : 'radio';
    }

    /**
     * 提交当前题目答案
     */
    submitCurrentAnswer() {
        const q = this.questions[this.currentQuestionIndex];
        const selected = this.getSelectedOptions();
        
        if (!selected.length) {
            return; // 未选择，不处理
        }
        
        // 防止重复提交
        if (this.userAnswers[q.id]) {
            return;
        }
        
        this.userAnswers[q.id] = selected;
        
        if (this.mode === 'open') {
            // 开卷模式：立即显示答案
            this.showImmediateFeedback(q, selected);
            
            // 检查是否完成本节所有题目
            this.checkSectionCompletion();
        } else {
            // 闭卷模式：仅记录，不显示
            // 用户需手动点击“提交答案”按钮
        }
    }

    /**
     * 显示即时反馈（开卷模式）
     */
    showImmediateFeedback(question, userAnswer) {
        const isCorrect = this.checkAnswer(question.answer, userAnswer);
        
        document.getElementById('resultIcon').innerHTML = 
            isCorrect ? '✅ 正确' : '❌ 错误';
        document.getElementById('correctAnswer').innerHTML = 
            `正确答案：${question.answer.join(', ')}`;
        document.getElementById('explanation').innerHTML = 
            question.explanation || '暂无解析';
        
        document.getElementById('feedbackArea').classList.remove('hidden');
        
        // 保存到错题本
        if (!isCorrect) {
            Storage.saveWrongQuestion(question.id, userAnswer, question.answer);
        }
    }

    /**
     * 提交所有答案（闭卷模式）
     */
    submitAll() {
        let correctCount = 0;
        
        this.questions.forEach(q => {
            if (this.userAnswers[q.id]) {
                const isCorrect = this.checkAnswer(q.answer, this.userAnswers[q.id]);
                if (isCorrect) correctCount++;
            }
        });
        
        this.score = Math.round((correctCount / this.questions.length) * 100);
        
        // 显示结果
        this.showResults(correctCount);
        
        // 保存历史记录
        Storage.saveQuizHistory(
            this.currentChapter.id,
            this.currentSection.type,
            this.score,
            this.questions.length,
            correctCount,
            this.mode
        );
    }

    /**
     * 检查答案是否正确
     */
    checkAnswer(correctAnswer, userAnswer) {
        if (Array.isArray(correctAnswer) && Array.isArray(userAnswer)) {
            // 多选题：完全匹配（使用副本避免污染原数组）
            return [...correctAnswer].sort().join(',') === [...userAnswer].sort().join(',');
        }
        return correctAnswer[0] === userAnswer[0];
    }

    /**
     * 获取用户选择的选项
     */
    getSelectedOptions() {
        const inputs = document.querySelectorAll('input[name="answer"]:checked');
        return Array.from(inputs).map(input => input.value);
    }

    /**
     * 导航到上一题/下一题
     */
    navigate(direction) {
        if (direction === 'prev' && this.currentQuestionIndex > 0) {
            this.currentQuestionIndex--;
            this.renderQuestion();
        } else if (direction === 'next' && 
                   this.currentQuestionIndex < this.questions.length - 1) {
            this.currentQuestionIndex++;
            this.renderQuestion();
        }
    }

    /**
     * 更新按钮状态
     */
    updateButtonStates() {
        document.getElementById('prevBtn').disabled = 
            this.currentQuestionIndex === 0;
        document.getElementById('nextBtn').disabled = 
            this.currentQuestionIndex === this.questions.length - 1;
        
        // 最后一题显示提交按钮
        const isLastQuestion = 
            this.currentQuestionIndex === this.questions.length - 1;
        document.getElementById('submitBtn').style.display = 
            isLastQuestion && this.mode === 'closed' ? 'block' : 'none';
    }

    /**
     * 检查本节是否已完成
     */
    checkSectionCompletion() {
        // 检查是否所有题目都已作答
        const allAnswered = this.questions.every(q => this.userAnswers[q.id]);
        
        if (allAnswered && this.mode === 'open') {
            // 计算得分并保存历史记录
            let correctCount = 0;
            this.questions.forEach(q => {
                if (this.checkAnswer(q.answer, this.userAnswers[q.id])) {
                    correctCount++;
                }
            });
            
            const score = Math.round((correctCount / this.questions.length) * 100);
            
            // 保存答题历史
            Storage.saveQuizHistory(
                this.currentChapter.id,
                this.currentSection.type,
                score,
                this.questions.length,
                correctCount,
                this.mode
            );
            
            // 提示用户
            setTimeout(() => {
                alert(`本节已完成！得分：${score}分`);
            }, 500);
        }
    }

    /**
     * 获取题型标签
     */
    getTypeLabel(type) {
        const labels = {
            'single_choice': '单选题',
            'multiple_choice': '多选题',
            'true_false': '判断题'
        };
        return labels[type] || type;
    }
}
```

#### 4.2.3 章节导航 (`navigation.js`)

```javascript
class ChapterNavigation {
    constructor(quizEngine) {
        this.quizEngine = quizEngine;
        this.chapters = [];
    }

    /**
     * 加载章节列表
     */
    async loadChapters() {
        const response = await fetch('questions.json');
        const data = await response.json();
        this.chapters = data.chapters;
        
        this.renderSidebar();
    }

    /**
     * 渲染侧边栏
     */
    renderSidebar() {
        const navHtml = this.chapters.map(chapter => {
            const progress = Storage.getChapterProgress(chapter.id);
            const completedClass = progress?.completed ? 'completed' : '';
            
            return `
                <div class="chapter-item ${completedClass}" 
                     data-chapter-id="${chapter.id}">
                    <div class="chapter-title">${chapter.title}</div>
                    <div class="section-list">
                        ${chapter.sections.map(section => `
                            <div class="section-item" 
                                 data-section-type="${section.type}">
                                <span>${section.name}</span>
                                <span class="question-count">
                                    (${section.questions.length}题)
                                </span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }).join('');
        
        document.getElementById('chapterNav').innerHTML = navHtml;
        
        // 绑定点击事件
        this.bindEvents();
    }

    /**
     * 绑定事件
     */
    bindEvents() {
        document.querySelectorAll('.section-item').forEach(item => {
            item.addEventListener('click', () => {
                const chapterItem = item.closest('.chapter-item');
                const chapterId = parseInt(chapterItem.dataset.chapterId);
                const sectionType = item.dataset.sectionType;
                
                this.quizEngine.loadChapter(chapterId, sectionType);
                
                // 高亮当前选中
                document.querySelectorAll('.section-item').forEach(i => 
                    i.classList.remove('active'));
                item.classList.add('active');
            });
        });
    }
}
```

#### 4.2.4 本地存储 (`storage.js`)

```javascript
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

#### 4.2.5 统计面板 (`stats.js`)

```javascript
class StatsPanel {
    constructor() {
        this.modal = document.getElementById('statsModal');
    }

    /**
     * 显示统计面板
     */
    show() {
        const history = Storage.getQuizHistory();
        const wrongQuestions = Storage.getWrongQuestions();
        
        // 计算总体统计
        const totalQuizzes = history.length;
        const avgScore = totalQuizzes > 0 ? 
            Math.round(history.reduce((sum, h) => sum + h.score, 0) / totalQuizzes) : 0;
        const totalWrong = wrongQuestions.length;
        const unreviewedWrong = wrongQuestions.filter(w => !w.reviewed).length;
        
        // 渲染统计内容
        this.modal.innerHTML = `
            <div class="modal-content">
                <h2>📊 学习统计</h2>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value">${totalQuizzes}</div>
                        <div class="stat-label">已完成测试</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${avgScore}%</div>
                        <div class="stat-label">平均得分</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${totalWrong}</div>
                        <div class="stat-label">错题总数</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${unreviewedWrong}</div>
                        <div class="stat-label">待复习错题</div>
                    </div>
                </div>
                
                <h3>最近记录</h3>
                <div class="history-list">
                    ${history.slice(-10).reverse().map(h => `
                        <div class="history-item">
                            <span>第${h.chapterId}章 - ${this.getSectionLabel(h.sectionType)}</span>
                            <span class="score ${h.score >= 80 ? 'good' : 'bad'}">${h.score}分</span>
                            <span class="time">${this.formatTime(h.timestamp)}</span>
                        </div>
                    `).join('')}
                </div>
                
                <button onclick="document.getElementById('statsModal').classList.add('hidden')">
                    关闭
                </button>
            </div>
        `;
        
        this.modal.classList.remove('hidden');
    }

    getSectionLabel(type) {
        const labels = {
            'single_choice': '单选题',
            'multiple_choice': '多选题',
            'true_false': '判断题'
        };
        return labels[type] || type;
    }

    formatTime(timestamp) {
        const date = new Date(timestamp);
        return `${date.getMonth() + 1}/${date.getDate()} ${date.getHours()}:${String(date.getMinutes()).padStart(2, '0')}`;
    }
}
```

#### 4.2.6 错题本模块 (`wrongbook.js`)

```javascript
class WrongBook {
    constructor(quizEngine) {
        this.quizEngine = quizEngine;
        this.modal = document.getElementById('wrongBookModal');
        this.wrongQuestions = [];
        this.currentIndex = 0;
    }

    /**
     * 显示错题本
     */
    show() {
        this.wrongQuestions = Storage.getWrongQuestions();
        this.currentIndex = 0;
        
        if (this.wrongQuestions.length === 0) {
            this.showEmptyState();
            return;
        }
        
        this.renderWrongQuestion();
        this.modal.classList.remove('hidden');
    }

    /**
     * 显示空状态
     */
    showEmptyState() {
        this.modal.innerHTML = `
            <div class="modal-content">
                <h2> 错题本</h2>
                <p class="empty-message">暂无错题，继续保持！</p>
                <button onclick="document.getElementById('wrongBookModal').classList.add('hidden')">
                    关闭
                </button>
            </div>
        `;
        this.modal.classList.remove('hidden');
    }

    /**
     * 渲染当前错题
     */
    renderWrongQuestion() {
        const wrongQ = this.wrongQuestions[this.currentIndex];
        
        // 从题库中查找完整题目信息
        fetch('questions.json')
            .then(res => res.json())
            .then(data => {
                const question = this.findQuestionById(data, wrongQ.questionId);
                
                if (!question) {
                    alert('题目数据未找到');
                    return;
                }
                
                this.modal.innerHTML = `
                    <div class="modal-content">
                        <h2> 错题本 (${this.currentIndex + 1}/${this.wrongQuestions.length})</h2>
                        
                        <div class="wrong-question">
                            <div class="question-text">${question.question}</div>
                            
                            <div class="options-review">
                                ${question.options.map(opt => `
                                    <div class="option-review ${wrongQ.correctAnswer.includes(opt.label) ? 'correct' : ''}">
                                        <span>${opt.label}. ${opt.text}</span>
                                    </div>
                                `).join('')}
                            </div>
                            
                            <div class="answer-info">
                                <div class="user-answer">
                                    <strong>你的答案：</strong>
                                    <span class="wrong">${wrongQ.userAnswer.join(', ')}</span>
                                </div>
                                <div class="correct-answer">
                                    <strong>正确答案：</strong>
                                    <span class="right">${wrongQ.correctAnswer.join(', ')}</span>
                                </div>
                            </div>
                            
                            <div class="explanation">
                                <strong>【解析】</strong>
                                <p>${question.explanation || '暂无解析'}</p>
                            </div>
                        </div>
                        
                        <div class="controls">
                            <button id="prevWrongBtn" ${this.currentIndex === 0 ? 'disabled' : ''}>上一题</button>
                            <button id="retryBtn">再做一次</button>
                            <button id="markReviewedBtn" class="primary">标记已复习</button>
                            <button id="nextWrongBtn" ${this.currentIndex === this.wrongQuestions.length - 1 ? 'disabled' : ''}>下一题</button>
                        </div>
                        
                        <button class="close-btn" onclick="document.getElementById('wrongBookModal').classList.add('hidden')">
                            关闭
                        </button>
                    </div>
                `;
                
                this.bindWrongBookEvents(question);
            });
    }

    /**
     * 绑定错题本事件
     */
    bindWrongBookEvents(question) {
        document.getElementById('prevWrongBtn')?.addEventListener('click', () => {
            if (this.currentIndex > 0) {
                this.currentIndex--;
                this.renderWrongQuestion();
            }
        });
        
        document.getElementById('nextWrongBtn')?.addEventListener('click', () => {
            if (this.currentIndex < this.wrongQuestions.length - 1) {
                this.currentIndex++;
                this.renderWrongQuestion();
            }
        });
        
        document.getElementById('markReviewedBtn').addEventListener('click', () => {
            Storage.markAsReviewed(question.id);
            
            // 从列表中移除
            this.wrongQuestions.splice(this.currentIndex, 1);
            
            if (this.wrongQuestions.length === 0) {
                this.showEmptyState();
            } else {
                // 调整索引
                if (this.currentIndex >= this.wrongQuestions.length) {
                    this.currentIndex = this.wrongQuestions.length - 1;
                }
                this.renderWrongQuestion();
            }
        });
        
        document.getElementById('retryBtn').addEventListener('click', () => {
            // 关闭错题本，加载该题目所在章节进行重做
            this.modal.classList.add('hidden');
            // TODO: 实现跳转到对应章节的逻辑
            alert('即将跳转到对应章节重新练习');
        });
    }

    /**
     * 从题库中查找题目
     */
    findQuestionById(data, questionId) {
        for (const chapter of data.chapters) {
            for (const section of chapter.sections) {
                const found = section.questions.find(q => q.id === questionId);
                if (found) return found;
            }
        }
        return null;
    }
}
```

---

## 5. 交互流程

### 5.1 开卷模式流程

```
用户打开应用
    ↓
选择章节和题型
    ↓
加载第一题
    ↓
用户选择选项 → 点击"查看答案"
    ↓
立即显示：✅/❌ + 正确答案 + 解析
    ↓
自动记录到错题本（如果错误）
    ↓
点击"下一题"继续
```

### 5.2 闭卷模式流程

```
用户打开应用
    ↓
切换到“闭卷模式”
    ↓
选择章节和题型
    ↓
逐题作答（不显示答案）
    ↓
完成所有题目 → 点击“提交答案”
    ↓
计算得分
    ↓
逐题显示：对错 + 正确答案 + 解析
    ↓
错题自动加入错题本
    ↓
保存答题历史
```

### 5.3 错题复习流程

```
用户点击“错题本”按钮
    ↓
加载错题列表
    ↓
逐题显示：题干 + 用户答案 + 正确答案 + 解析
    ↓
用户点击“标记已复习” → 从待复习列表移除
或
用户点击“再做一次” → 重新答题
```

---

## 6. 样式设计

### 6.1 配色方案

```css
:root {
    --primary-color: #1890ff;
    --success-color: #52c41a;
    --error-color: #ff4d4f;
    --warning-color: #faad14;
    --text-color: #333;
    --bg-color: #f5f5f5;
    --card-bg: #fff;
    --border-color: #e8e8e8;
}
```

### 6.2 响应式断点

```css
/* 移动端 (< 768px) */
@media (max-width: 767px) {
    .sidebar { 
        position: fixed;
        left: -100%;
        top: 0;
        width: 80%;
        height: 100vh;
        background: #fff;
        z-index: 1000;
        transition: left 0.3s ease;
        box-shadow: 2px 0 8px rgba(0,0,0,0.1);
    }
    
    .sidebar.open {
        left: 0;
    }
    
    .main-content { 
        padding: 10px; 
    }
    
    /* 汉堡菜单按钮 */
    .hamburger-btn {
        display: block;
        font-size: 24px;
        cursor: pointer;
    }
}

/* 平板端 (768px - 1024px) */
@media (min-width: 768px) and (max-width: 1023px) {
    .sidebar { width: 200px; }
}

/* 桌面端 (>= 1024px) */
@media (min-width: 1024px) {
    .sidebar { width: 250px; }
    .main-content { max-width: 800px; margin: 0 auto; }
}
```

---

## 7. 风险与应对

### 7.1 技术风险

| 风险 | 影响 | 概率 | 应对措施 |
|------|------|------|----------|
| OCR 识别率低 | 题目文本错误 | 中 | 1. 提高渲染 DPI<br>2. 人工校对关键章节<br>3. 提供"报错"功能 |
| 题目-答案匹配失败 | 答案错位 | 低 | 1. 建立精确页面对应表<br>2. 通过题号二次校验<br>3. 抽样验证 |
| JSON 文件过大 | 加载缓慢 | 低 | 1. 按章节拆分 JSON<br>2. 懒加载未访问章节<br>3. 压缩 JSON |
| 浏览器兼容性 | 部分功能异常 | 低 | 1. 使用 ES6+ 但提供 polyfill<br>2. 测试主流浏览器<br>3. 降级方案 |

### 7.2 内容风险

| 风险 | 影响 | 应对措施 |
|------|------|----------|
| PDF 版本更新 | 题库过期 | 重新运行解析脚本生成新 JSON |
| 版权争议 | 法律风险 | 仅用于个人学习，注明出处 |

---

## 8. 开发里程碑

### 阶段 1：PDF 解析（预计 2 天）

**目标**：完成前 3 章的解析并生成 JSON

**任务**：
- [ ] 安装依赖：`pypdfium2`, `Pillow`
- [ ] 实现单页 OCR 测试脚本
- [ ] 编写完整解析脚本 `pdf_parser.py`
- [ ] 建立前 3 章的页面对应表
- [ ] 生成 `questions.json` 并人工抽样校对

**验收标准**：
- 前 3 章 JSON 结构正确
- 题目、选项、答案、解析完整
- OCR 准确率 ≥ 90%（人工抽样检查）

---

### 阶段 2：H5 基础框架（预计 2 天）

**目标**：完成页面布局和章节导航

**任务**：
- [ ] 创建 `index.html` 和基本 CSS
- [ ] 实现 JSON 数据加载
- [ ] 实现章节导航侧边栏
- [ ] 实现题目展示区域
- [ ] 实现开卷模式基础交互

**验收标准**：
- 页面在手机上正常显示
- 可选择章节并加载题目
- 开卷模式下可查看答案

---

### 阶段 3：答题功能（预计 3 天）

**目标**：完成开卷和闭卷两种模式

**任务**：
- [ ] 完善开卷模式：即时反馈、错题记录
- [ ] 实现闭卷模式：答案暂存、批量提交
- [ ] 实现答案校验逻辑（单选/多选/判断）
- [ ] 实现上一题/下一题导航
- [ ] 实现提交后的结果展示

**验收标准**：
- 开卷模式：选择后立即显示对错和解析
- 闭卷模式：提交后显示总分和每题详情
- 错题自动保存到 localStorage

---

### 阶段 4：增强功能（预计 2 天）

**目标**：完成错题本和统计面板

**任务**：
- [ ] 实现错题本查看和标记复习
- [ ] 实现答题历史记录
- [ ] 实现统计面板（总分、平均分、错题数）
- [ ] 实现模式切换（开卷/闭卷）
- [ ] 优化 UI/UX（加载动画、提示消息）

**验收标准**：
- 错题本可正常查看和标记
- 统计面板显示准确数据
- 模式切换流畅

---

### 阶段 5：全量解析与测试（预计 1 天）

**目标**：完成全部 30 章解析并全面测试

**任务**：
- [ ] 建立完整章节-页面对应表
- [ ] 运行全量解析脚本
- [ ] 人工抽样校对（每章抽 5 题）
- [ ] 修复 OCR 错误
- [ ] 全面功能测试
- [ ] 性能优化（JSON 加载速度）

**验收标准**：
- 全部 30 章 JSON 生成成功
- 总题目数 ≥ 1500
- 无明显功能 bug
- 移动端体验流畅

---

## 9. 后续优化方向

1. **搜索功能**：支持按关键词搜索题目
2. **随机组卷**：从各章节随机抽取题目组成试卷
3. **计时考试**：添加倒计时功能
4. **导出功能**：导出错题为 PDF 或打印
5. **云端同步**：接入后端服务，多设备同步进度
6. **AI 辅助**：接入大模型 API，生成相似题目

### 9.3 JSON 数据缓存策略

为避免每次切换章节重复请求 `questions.json`，采用以下策略：

```javascript
// app.js - 全局数据缓存
let quizData = null;

async function loadQuizData() {
    if (!quizData) {
        const response = await fetch('questions.json');
        quizData = await response.json();
    }
    return quizData;
}

// 各模块使用缓存数据
const data = await loadQuizData();
```

**优势**：
- 首次加载后所有模块共享同一份数据
- 避免重复网络请求
- 减少内存占用（仅一份副本）

---

## 10. 附录

### 10.1 Python 依赖清单

```txt
pypdfium2>=4.30.0
Pillow>=10.0.0
```

### 10.2 Tesseract 安装

```bash
# macOS
brew install tesseract tesseract-lang

# 验证安装
tesseract --version
tesseract --list-langs  # 应包含 chi_sim
```

### 10.3 浏览器兼容性

| 浏览器 | 最低版本 | 备注 |
|--------|---------|------|
| Chrome | 80+ | 推荐 |
| Safari | 13+ | iOS 13+ |
| Firefox | 75+ | - |
| Edge | 80+ | - |

---

**文档结束**
