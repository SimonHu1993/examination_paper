/**
 * 答题引擎模块
 * 处理答题逻辑：开卷/闭卷模式、答案校验、结果显示
 */

const Quiz = {
    // 当前状态
    currentChapter: null,
    currentSection: null,
    questions: [],
    currentIndex: 0,
    userAnswers: {},
    mode: 'open',
    showExplanation: false,
    
    // DOM 元素
    elements: {},

    /**
     * 初始化答题引擎
     */
    init() {
        this.elements = {
            homeView: document.getElementById('homeView'),
            quizView: document.getElementById('quizView'),
            resultView: document.getElementById('resultView'),
            quizTitle: document.getElementById('quizTitle'),
            quizProgress: document.getElementById('quizProgress'),
            questionContainer: document.getElementById('questionContainer'),
            prevBtn: document.getElementById('prevBtn'),
            nextBtn: document.getElementById('nextBtn'),
            submitBtn: document.getElementById('submitBtn'),
            resultScore: document.getElementById('resultScore'),
            resultStats: document.getElementById('resultStats'),
            retryBtn: document.getElementById('retryBtn'),
            backBtn: document.getElementById('backBtn')
        };

        this.bindEvents();
    },

    /**
     * 绑定事件
     */
    bindEvents() {
        this.elements.prevBtn.addEventListener('click', () => this.prevQuestion());
        this.elements.nextBtn.addEventListener('click', () => this.nextQuestion());
        this.elements.submitBtn.addEventListener('click', () => this.submitAll());
        this.elements.retryBtn.addEventListener('click', () => this.retry());
        this.elements.backBtn.addEventListener('click', () => this.goHome());
    },

    /**
     * 开始答题
     */
    start(chapter) {
        this.currentChapter = chapter;
        this.mode = Storage.getMode();
        this.userAnswers = {};
        this.currentIndex = 0;
        this.showExplanation = false;

        // 合并所有章节的题目
        this.questions = [];
        chapter.sections.forEach(section => {
            section.questions.forEach(q => {
                this.questions.push({
                    ...q,
                    sectionType: section.type,
                    sectionName: section.name
                });
            });
        });

        if (this.questions.length === 0) {
            alert('本章节暂无题目');
            return;
        }

        // 切换视图
        this.showView('quiz');
        
        // 更新标题
        this.elements.quizTitle.textContent = chapter.title;

        // 渲染第一题
        this.renderQuestion();
        this.updateButtons();
    },

    /**
     * 渲染当前题目
     */
    renderQuestion() {
        const question = this.questions[this.currentIndex];
        if (!question) return;

        const isSubjective = !question.options || question.options.length === 0;
        const selectedOptions = this.userAnswers[question.id] || [];
        const isAnswered = selectedOptions.length > 0;
        const showFeedback = this.mode === 'open' && isAnswered;

        let html = `
            <div class="question-number">第 ${this.currentIndex + 1} 题 / 共 ${this.questions.length} 题 · ${question.sectionName}</div>
            <div class="question-text">${this.formatText(question.question)}</div>
        `;

        if (isSubjective) {
            // 主观题：显示题目 + "查看解析"按钮
            html += `
                <div class="subjective-prompt">💡 这是一道主观题，请先在纸上作答，然后点击查看解析</div>
            `;
            if (this.showExplanation || this.mode === 'open') {
                html += this.renderExplanation(question);
            }
            html += `<button class="btn btn-show-explanation" id="showExplBtn">查看解析</button>`;
        } else {
            // 客观题：显示选项
            html += '<ul class="options-list">';
            question.options.forEach(option => {
                let className = 'option-item';
                if (selectedOptions.includes(option.label)) className += ' selected';
                if (showFeedback) {
                    if (question.answer.includes(option.label)) className += ' correct';
                    else if (selectedOptions.includes(option.label)) className += ' incorrect';
                }
                html += `
                    <li class="${className}" data-label="${option.label}">
                        <span class="option-label">${option.label}</span>
                        <span class="option-text">${this.formatText(option.text)}</span>
                    </li>
                `;
            });
            html += '</ul>';

            if (showFeedback) {
                const isCorrect = this.checkAnswer(question.answer, selectedOptions);
                html += this.renderFeedback(isCorrect, question);
            }
        }

        this.elements.questionContainer.innerHTML = html;

        // 绑定事件
        this.elements.questionContainer.querySelectorAll('.option-item').forEach(item => {
            item.addEventListener('click', (e) => this.selectOption(e));
        });

        const showExplBtn = document.getElementById('showExplBtn');
        if (showExplBtn) {
            showExplBtn.addEventListener('click', () => {
                this.showExplanation = true;
                this.renderQuestion();
            });
        }

        // MathJax 渲染
        if (window.MathJax && window.MathJax.typesetPromise) {
            window.MathJax.typesetPromise([this.elements.questionContainer]);
        }

        this.elements.quizProgress.textContent = `${this.currentIndex + 1} / ${this.questions.length}`;
    },

    /**
     * 格式化文本（处理换行和特殊符号）
     */
    formatText(text) {
        if (!text) return '';
        return text.replace(/\n/g, '<br>');
    },

    /**
     * 渲染解析内容
     */
    renderExplanation(question) {
        if (!question.explanation) return '';
        return `
            <div class="feedback-explanation">
                <strong>解析：</strong>${this.formatText(question.explanation)}
            </div>
        `;
    },

    /**
     * 渲染反馈信息
     */
    renderFeedback(isCorrect, question) {
        const feedbackClass = isCorrect ? 'correct' : 'incorrect';
        const feedbackTitle = isCorrect ? '✓ 回答正确!' : '✗ 回答错误';
        
        let explanation = '';
        if (question.explanation) {
            explanation = `
                <div class="feedback-explanation">
                    <strong>解析：</strong>${this.formatText(question.explanation)}
                </div>
            `;
        }

        return `
            <div class="feedback ${feedbackClass}">
                <div class="feedback-title">${feedbackTitle}</div>
                <div>正确答案：${question.answer.join(', ')}</div>
                ${explanation}
            </div>
        `;
    },

    /**
     * 选择选项
     */
    selectOption(e) {
        const question = this.questions[this.currentIndex];
        const label = e.currentTarget.dataset.label;
        
        // 开卷模式下，已答题不允许再改
        if (this.mode === 'open' && this.userAnswers[question.id]) {
            return;
        }

        // 获取当前选择
        let selected = this.userAnswers[question.id] || [];

        if (question.sectionType === 'multiple_choice') {
            // 多选题：切换选择
            if (selected.includes(label)) {
                selected = selected.filter(l => l !== label);
            } else {
                selected = [...selected, label].sort();
            }
        } else {
            // 单选题：直接替换
            selected = [label];
        }

        this.userAnswers[question.id] = selected;

        // 开卷模式：选择后立即显示反馈
        if (this.mode === 'open') {
            // 记录错题
            const isCorrect = this.checkAnswer(question.answer, selected);
            if (!isCorrect) {
                Storage.saveWrongQuestion(question.id, selected, question.answer);
            } else {
                Storage.removeWrongQuestion(question.id);
            }

            // 检查是否完成本节
            this.checkSectionCompletion();
        }

        // 重新渲染
        this.renderQuestion();
    },

    /**
     * 检查答案
     */
    checkAnswer(correctAnswer, userAnswer) {
        if (!userAnswer || userAnswer.length === 0) return false;
        
        const sorted1 = [...correctAnswer].sort().join(',');
        const sorted2 = [...userAnswer].sort().join(',');
        return sorted1 === sorted2;
    },

    /**
     * 上一题
     */
    prevQuestion() {
        if (this.currentIndex > 0) {
            this.currentIndex--;
            this.showExplanation = false;
            this.renderQuestion();
            this.updateButtons();
        }
    },

    /**
     * 下一题
     */
    nextQuestion() {
        if (this.currentIndex < this.questions.length - 1) {
            this.currentIndex++;
            this.showExplanation = false;
            this.renderQuestion();
            this.updateButtons();
        }
    },

    /**
     * 更新按钮状态
     */
    updateButtons() {
        this.elements.prevBtn.disabled = this.currentIndex === 0;
        
        const isLast = this.currentIndex === this.questions.length - 1;
        
        if (this.mode === 'closed') {
            this.elements.nextBtn.style.display = isLast ? 'none' : 'inline-block';
            this.elements.submitBtn.style.display = isLast ? 'inline-block' : 'none';
        } else {
            this.elements.nextBtn.style.display = 'inline-block';
            this.elements.submitBtn.style.display = 'none';
        }
    },

    /**
     * 提交所有答案（闭卷模式）
     */
    submitAll() {
        if (!confirm('确定要提交答案吗？')) return;

        let correctCount = 0;
        const totalQuestions = this.questions.length;

        this.questions.forEach(question => {
            const userAnswer = this.userAnswers[question.id] || [];
            const isCorrect = this.checkAnswer(question.answer, userAnswer);
            
            if (isCorrect) {
                correctCount++;
                Storage.removeWrongQuestion(question.id);
            } else if (userAnswer.length > 0) {
                Storage.saveWrongQuestion(question.id, userAnswer, question.answer);
            }
        });

        const score = Math.round((correctCount / totalQuestions) * 100);

        // 保存历史
        Storage.saveQuizHistory(
            this.currentChapter.id,
            'all',
            score,
            totalQuestions,
            correctCount,
            this.mode
        );

        // 保存进度
        Storage.saveChapterProgress(this.currentChapter.id, true, score);

        // 显示结果
        this.showResult(score, correctCount, totalQuestions);
    },

    /**
     * 检查本节是否完成（开卷模式）
     */
    checkSectionCompletion() {
        const answeredCount = Object.keys(this.userAnswers).length;
        
        if (answeredCount === this.questions.length) {
            // 全部完成，计算得分
            let correctCount = 0;
            this.questions.forEach(question => {
                const userAnswer = this.userAnswers[question.id] || [];
                if (this.checkAnswer(question.answer, userAnswer)) {
                    correctCount++;
                }
            });

            const score = Math.round((correctCount / this.questions.length) * 100);

            // 保存历史和进度
            Storage.saveQuizHistory(
                this.currentChapter.id,
                'all',
                score,
                this.questions.length,
                correctCount,
                this.mode
            );
            Storage.saveChapterProgress(this.currentChapter.id, true, score);

            // 更新导航进度
            Navigation.updateProgress(this.currentChapter.id);
        }
    },

    /**
     * 显示结果
     */
    showResult(score, correctCount, totalQuestions) {
        this.showView('result');

        this.elements.resultScore.textContent = `${score}分`;
        this.elements.resultStats.innerHTML = `
            <p>答对 ${correctCount} 题 / 共 ${totalQuestions} 题</p>
            <p>正确率 ${Math.round((correctCount / totalQuestions) * 100)}%</p>
        `;

        // 更新导航进度
        Navigation.updateProgress(this.currentChapter.id);
    },

    /**
     * 重新答题
     */
    retry() {
        if (this.currentChapter) {
            this.start(this.currentChapter);
        }
    },

    /**
     * 返回首页
     */
    goHome() {
        this.showView('home');
        Navigation.refresh();
    },

    /**
     * 切换视图
     */
    showView(view) {
        this.elements.homeView.style.display = view === 'home' ? 'block' : 'none';
        this.elements.quizView.style.display = view === 'quiz' ? 'block' : 'none';
        this.elements.resultView.style.display = view === 'result' ? 'flex' : 'none';
    }
};
