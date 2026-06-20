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
        
        // 渲染Tab和列表
        this.renderWrongBookTabs(content, 'pending');
        
        modal.style.display = 'flex';
    },
    
    /**
     * 渲染错题本Tab和内容
     */
    renderWrongBookTabs(content, activeTab) {
        const wrongQuestions = Storage.getWrongQuestions();
        
        // 分离待复习和已理解的题目
        const pendingQuestions = wrongQuestions.filter(w => !w.understood);
        const understoodQuestions = wrongQuestions.filter(w => w.understood);
        
        // 构建Tab HTML
        let html = `
            <div class="wrong-book-tabs">
                <button class="tab-btn ${activeTab === 'pending' ? 'active' : ''}" data-tab="pending">
                    待复习 (${pendingQuestions.length})
                </button>
                <button class="tab-btn ${activeTab === 'understood' ? 'active' : ''}" data-tab="understood">
                    已理解 (${understoodQuestions.length})
                </button>
            </div>
            <div class="wrong-book-list">
        `;
        
        // 根据当前Tab显示对应的题目
        const displayQuestions = activeTab === 'pending' ? pendingQuestions : understoodQuestions;
        
        if (displayQuestions.length === 0) {
            html += `
                <div class="empty-state">
                    <div class="empty-state-icon"></div>
                    <p class="empty-state-text">${activeTab === 'pending' ? '暂无待复习的错题，继续保持！' : '暂无已理解的题目'}</p>
                </div>
            `;
        } else {
            html += displayQuestions.map(wrong => {
                const question = this.findQuestionById(wrong.questionId);
                if (!question) return '';

                return `
                    <div class="wrong-item" data-question-id="${wrong.questionId}">
                        <div class="wrong-item-header">
                            <span class="wrong-item-title">${question.sectionName || '题目'}</span>
                            <span class="wrong-item-meta">${new Date(wrong.timestamp).toLocaleDateString()}</span>
                        </div>
                        <div class="wrong-item-question">${this.formatText(question.question)}</div>
                        <div class="wrong-item-answers">
                            <span class="your-answer">你的答案：${wrong.userAnswer.join(', ') || '未作答'}</span>
                            <span class="correct-answer">正确答案：${wrong.correctAnswer.join(', ')}</span>
                        </div>
                        <div class="wrong-item-actions">
                            <button class="btn" onclick="App.showWrongDetail('${wrong.questionId}')">查看详情</button>
                            ${activeTab === 'pending' ? `<button class="btn" onclick="App.markAsUnderstood('${wrong.questionId}')">标记为已理解</button>` : `<button class="btn" onclick="App.unmarkAsUnderstood('${wrong.questionId}')">取消标记</button>`}
                        </div>
                    </div>
                `;
            }).join('');
        }
        
        html += '</div>';
        content.innerHTML = html;
        
        // 绑定Tab切换事件
        content.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const tab = btn.dataset.tab;
                this.renderWrongBookTabs(content, tab);
            });
        });
    },

    /**
     * 显示错题详情
     */
    showWrongDetail(questionId) {
        const question = this.findQuestionById(questionId);
        if (!question) return;

        // 获取错题记录
        const wrongQuestions = Storage.getWrongQuestions();
        const wrongRecord = wrongQuestions.find(w => w.questionId === questionId);
        if (!wrongRecord) return;

        // 构建选项HTML（如果是客观题）
        let optionsHtml = '';
        if (question.options && question.options.length > 0) {
            optionsHtml = '<ul class="detail-options-list">';
            question.options.forEach(option => {
                const isSelected = wrongRecord.userAnswer.includes(option.label);
                const isCorrect = question.answer.includes(option.label);
                let optionClass = 'detail-option-item';
                if (isCorrect) optionClass += ' correct';
                if (isSelected && !isCorrect) optionClass += ' incorrect';
                
                optionsHtml += `
                    <li class="${optionClass}">
                        <span class="option-label">${option.label}</span>
                        <span class="option-text">${this.formatText(option.text)}</span>
                        ${isSelected ? '<span class="user-selected-badge">✓ 你的选择</span>' : ''}
                        ${isCorrect ? '<span class="correct-badge">✓ 正确答案</span>' : ''}
                    </li>
                `;
            });
            optionsHtml += '</ul>';
        } else {
            optionsHtml = `<div class="subjective-note">💡 这是一道主观题，请在纸上作答后查看解析</div>`;
        }

        // 构建解析HTML
        let explanationHtml = '';
        if (question.explanation) {
            // 解析可能包含HTML标签（如表格），需要直接渲染
            explanationHtml = `
                <div class="detail-explanation">
                    <strong>解析：</strong>${question.explanation}
                </div>
            `;
        }

        // 创建详情模态框
        const detailModal = document.createElement('div');
        detailModal.className = 'modal detail-modal';
        detailModal.id = 'wrongDetailModal';
        detailModal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>错题详情</h3>
                    <button class="modal-close" id="closeWrongDetail">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="detail-section">
                        <div class="detail-label">题目</div>
                        <div class="detail-question">${this.formatText(question.question)}</div>
                    </div>
                    
                    <div class="detail-section">
                        <div class="detail-label">选项与答案</div>
                        ${optionsHtml}
                    </div>
                    
                    <div class="detail-section">
                        <div class="detail-label">答题情况</div>
                        <div class="detail-answers">
                            <span class="your-answer">你的答案：${wrongRecord.userAnswer.join(', ') || '未作答'}</span>
                            <span class="correct-answer">正确答案：${wrongRecord.correctAnswer.join(', ')}</span>
                        </div>
                    </div>
                    
                    ${explanationHtml}
                </div>
            </div>
        `;

        document.body.appendChild(detailModal);
        detailModal.style.display = 'flex';

        // 绑定关闭按钮事件
        const closeBtn = document.getElementById('closeWrongDetail');
        closeBtn.addEventListener('click', () => {
            detailModal.style.display = 'none';
        });

        // 绑定点击背景关闭事件
        detailModal.addEventListener('click', (e) => {
            if (e.target === detailModal) {
                detailModal.style.display = 'none';
            }
        });

        // MathJax 渲染
        if (window.MathJax && window.MathJax.typesetPromise) {
            window.MathJax.typesetPromise([detailModal]);
        }
    },
    
    /**
     * 标记为已理解
     */
    markAsUnderstood(questionId) {
        Storage.markWrongAsUnderstood(questionId, true);
        // 重新渲染错题本
        const content = document.getElementById('wrongBookContent');
        this.renderWrongBookTabs(content, 'pending');
    },
    
    /**
     * 取消标记为已理解
     */
    unmarkAsUnderstood(questionId) {
        Storage.markWrongAsUnderstood(questionId, false);
        // 重新渲染错题本
        const content = document.getElementById('wrongBookContent');
        this.renderWrongBookTabs(content, 'understood');
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
        // 传入题库数据以计算当前答题进度的正确率
        const stats = Storage.getStats(this.quizData);
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
    },

    /**
     * 格式化文本（处理换行和特殊符号）
     */
    formatText(text) {
        if (!text) return '';
        return text.replace(/\n/g, '<br>');
    }
};

// DOM 加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    App.init();
});
