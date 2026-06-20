/**
 * 应用入口模块
 * 初始化应用、加载数据、绑定全局事件
 */

const App = {
    // 当前章节
    currentChapter: null,
    
    // 题库数据
    quizData: null,
    
    // 加载状态
    isLoading: true,

    /**
     * 初始化应用
     */
    async init() {
        console.log('会计考试题库 H5 应用初始化...');
        
        // 绑定全局事件
        this.bindGlobalEvents();

        // 加载题库数据
        await this.loadQuizData();

        // 初始化各模块
        if (this.quizData) {
            Navigation.init(this.quizData);
            Quiz.init();
            this.initWrongBook();
            this.initStats();
            this.initModeSelector();
        }

        this.isLoading = false;
        console.log('应用初始化完成');
    },

    /**
     * 加载题库数据
     */
    /**
     * 规范化题库数据：将 parts 结构转为扁平 chapters 数组
     */
    normalizeQuizData(raw) {
        const chapters = [];
        let globalIdx = 0;

        if (!raw.parts) {
            // 已经是旧格式，直接返回
            return raw;
        }

        for (const part of raw.parts) {
            // 客观题章节
            if (part.chapters) {
                for (const ch of part.chapters) {
                    const flatCh = {
                        id: 'obj_' + ch.id,
                        numId: ch.id,
                        title: ch.title,
                        partName: part.name,
                        partType: part.type,
                        sections: ch.sections.map(sec => ({
                            ...sec,
                            questions: sec.questions.map(q => ({
                                ...q,
                                id: 'q_' + (++globalIdx)
                            }))
                        }))
                    };
                    chapters.push(flatCh);
                }
            }

            // 主观题专题
            if (part.topics) {
                for (const topic of part.topics) {
                    const flatCh = {
                        id: 'subj_' + topic.name,
                        title: topic.name,
                        partName: part.name,
                        partType: part.type,
                        sections: topic.sections.map(sec => ({
                            ...sec,
                            questions: sec.questions.map(q => ({
                                ...q,
                                id: 'q_' + (++globalIdx)
                            }))
                        }))
                    };
                    chapters.push(flatCh);
                }
            }

            // 套卷
            if (part.papers) {
                for (const paper of part.papers) {
                    const flatCh = {
                        id: 'mock_' + paper.name,
                        title: paper.name,
                        partName: part.name,
                        partType: part.type,
                        sections: paper.sections.map(sec => ({
                            ...sec,
                            questions: sec.questions.map(q => ({
                                ...q,
                                id: 'q_' + (++globalIdx)
                            }))
                        }))
                    };
                    chapters.push(flatCh);
                }
            }
        }

        return { chapters, _raw: raw };
    },

    async loadQuizData() {
        try {
            if (this.quizData) return this.quizData;

            console.log('加载题库数据...');
            
            let raw = null;

            // 尝试嵌入式数据
            const embeddedScript = document.getElementById('embeddedQuizData');
            if (embeddedScript) {
                raw = JSON.parse(embeddedScript.textContent);
            } else {
                // fetch 加载
                const response = await fetch('questions.json');
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                raw = await response.json();
            }

            // 规范化数据
            this.quizData = this.normalizeQuizData(raw);
            console.log(`题库加载成功: ${this.quizData.chapters.length} 个章节`);
            return this.quizData;

        } catch (error) {
            console.error('加载题库失败:', error);
            this.showLoadError();
            return null;
        }
    },

    /**
     * 显示加载错误
     */
    showLoadError() {
        const mainContent = document.getElementById('mainContent');
        mainContent.innerHTML = `
            <div class="empty-state" style="padding: 60px 20px;">
                <div class="empty-state-icon">📚</div>
                <h3 style="margin-bottom: 12px;">题库加载失败</h3>
                <p class="empty-state-text">请确保 questions.json 文件存在</p>
                <p class="empty-state-text" style="margin-top: 8px; font-size: 12px; color: #999;">
                    运行 <code style="background: #f0f0f0; padding: 2px 6px; border-radius: 3px;">python3 pdf_parser.py --all</code> 生成题库
                </p>
                <button class="btn btn-primary" style="margin-top: 20px;" onclick="location.reload()">重新加载</button>
            </div>
        `;
    },

    /**
     * 绑定全局事件
     */
    bindGlobalEvents() {
        // 错题本按钮
        document.getElementById('wrongBookBtn').addEventListener('click', () => {
            this.showWrongBook();
        });

        // 统计按钮
        document.getElementById('statsBtn').addEventListener('click', () => {
            this.showStats();
        });
    },

    /**
     * 初始化模式选择器
     */
    initModeSelector() {
        const modeOptions = document.querySelectorAll('.mode-option');
        const currentMode = Storage.getMode();

        // 设置当前模式
        modeOptions.forEach(option => {
            const mode = option.dataset.mode;
            if (mode === currentMode) {
                option.classList.add('active');
                option.querySelector('input').checked = true;
            } else {
                option.classList.remove('active');
            }

            // 绑定点击事件
            option.addEventListener('click', () => {
                modeOptions.forEach(o => o.classList.remove('active'));
                option.classList.add('active');
                option.querySelector('input').checked = true;
                Storage.setMode(mode);
            });
        });
    },

    /**
     * 初始化错题本
     */
    initWrongBook() {
        const modal = document.getElementById('wrongBookModal');
        const closeBtn = document.getElementById('closeWrongBook');

        closeBtn.addEventListener('click', () => {
            modal.style.display = 'none';
        });

        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.style.display = 'none';
            }
        });
    },

    /**
     * 显示错题本
     */
    showWrongBook() {
        const modal = document.getElementById('wrongBookModal');
        const content = document.getElementById('wrongBookContent');
        const wrongQuestions = Storage.getWrongQuestions();

        if (wrongQuestions.length === 0) {
            content.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">🎉</div>
                    <p class="empty-state-text">暂无错题，继续保持！</p>
                </div>
            `;
        } else {
            const html = wrongQuestions.map(wrong => {
                const question = this.findQuestionById(wrong.questionId);
                if (!question) return '';

                return `
                    <div class="wrong-item">
                        <div class="wrong-item-header">
                            <span class="wrong-item-title">${question.sectionName || '题目'}</span>
                            <span class="wrong-item-meta">${new Date(wrong.timestamp).toLocaleDateString()}</span>
                        </div>
                        <div class="wrong-item-question">${question.question}</div>
                        <div class="wrong-item-answers">
                            <span class="your-answer">你的答案：${wrong.userAnswer.join(', ') || '未作答'}</span>
                            <span class="correct-answer">正确答案：${wrong.correctAnswer.join(', ')}</span>
                        </div>
                    </div>
                `;
            }).join('');

            content.innerHTML = html || '<div class="empty-state"><p>暂无错题</p></div>';
        }

        modal.style.display = 'flex';
    },

    /**
     * 初始化统计面板
     */
    initStats() {
        const modal = document.getElementById('statsModal');
        const closeBtn = document.getElementById('closeStats');

        closeBtn.addEventListener('click', () => {
            modal.style.display = 'none';
        });

        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.style.display = 'none';
            }
        });
    },

    /**
     * 显示统计面板
     */
    showStats() {
        const modal = document.getElementById('statsModal');
        const content = document.getElementById('statsContent');
        const stats = Storage.getStats();
        const history = Storage.getQuizHistory();

        let html = `
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">${stats.totalAttempts}</div>
                    <div class="stat-label">答题次数</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${stats.accuracy}%</div>
                    <div class="stat-label">正确率</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${stats.totalQuestions}</div>
                    <div class="stat-label">总题数</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${stats.wrongCount}</div>
                    <div class="stat-label">错题数</div>
                </div>
            </div>
        `;

        // 最近记录
        if (history.length > 0) {
            const recentHistory = history.slice(-5).reverse();
            html += `
                <div class="stats-history">
                    <h4>最近答题</h4>
                    ${recentHistory.map(h => {
                        const chapter = this.quizData?.chapters.find(ch => ch.id === h.chapterId);
                        return `
                            <div class="history-item">
                                <div class="history-item-info">
                                    ${chapter ? chapter.title : '未知章节'}<br>
                                    <small>${new Date(h.timestamp).toLocaleString()}</small>
                                </div>
                                <div class="history-item-score">${h.score}%</div>
                            </div>
                        `;
                    }).join('')}
                </div>
            `;
        }

        content.innerHTML = html;
        modal.style.display = 'flex';
    },

    /**
     * 根据 ID 查找题目
     */
    findQuestionById(questionId) {
        if (!this.quizData) return null;
        for (const chapter of this.quizData.chapters) {
            for (const section of chapter.sections) {
                for (const question of section.questions) {
                    if (question.id === questionId) {
                        return { ...question, sectionName: section.name, chapterTitle: chapter.title };
                    }
                }
            }
        }
        return null;
    }
};

// DOM 加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    App.init();
});
