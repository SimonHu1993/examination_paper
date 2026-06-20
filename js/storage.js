/**
 * 本地存储管理模块
 * 管理错题本、答题历史、章节进度、用户设置
 */

const Storage = {
    // 存储键名
    KEYS: {
        WRONG_QUESTIONS: 'wrongQuestions',
        QUIZ_HISTORY: 'quizHistory',
        CHAPTER_PROGRESS: 'chapterProgress',
        SETTINGS: 'settings',
        ANSWER_PROGRESS: 'answerProgress'  // 新增：答题进度
    },

    /**
     * 初始化存储
     */
    init() {
        // 确保所有键存在
        if (!localStorage.getItem(this.KEYS.WRONG_QUESTIONS)) {
            localStorage.setItem(this.KEYS.WRONG_QUESTIONS, JSON.stringify([]));
        }
        if (!localStorage.getItem(this.KEYS.QUIZ_HISTORY)) {
            localStorage.setItem(this.KEYS.QUIZ_HISTORY, JSON.stringify([]));
        }
        if (!localStorage.getItem(this.KEYS.CHAPTER_PROGRESS)) {
            localStorage.setItem(this.KEYS.CHAPTER_PROGRESS, JSON.stringify({}));
        }
        if (!localStorage.getItem(this.KEYS.SETTINGS)) {
            localStorage.setItem(this.KEYS.SETTINGS, JSON.stringify({
                mode: 'open',
                theme: 'light',
                fontSize: 'medium'
            }));
        }
    },

    // ==================== 错题本 ====================

    /**
     * 获取错题列表
     */
    getWrongQuestions() {
        return JSON.parse(localStorage.getItem(this.KEYS.WRONG_QUESTIONS) || '[]');
    },

    /**
     * 保存错题
     */
    saveWrongQuestion(questionId, userAnswer, correctAnswer) {
        const wrongQuestions = this.getWrongQuestions();
        
        // 检查是否已存在
        const existingIndex = wrongQuestions.findIndex(w => w.questionId === questionId);
        
        const wrongItem = {
            questionId,
            userAnswer,
            correctAnswer,
            timestamp: Date.now(),
            reviewed: false,
            understood: false  // 新增：标记是否已理解
        };

        if (existingIndex >= 0) {
            // 更新已有记录，保留understood状态
            wrongItem.understood = wrongQuestions[existingIndex].understood || false;
            wrongQuestions[existingIndex] = wrongItem;
        } else {
            // 添加新记录
            wrongQuestions.push(wrongItem);
        }

        localStorage.setItem(this.KEYS.WRONG_QUESTIONS, JSON.stringify(wrongQuestions));
    },

    /**
     * 移除错题（答对后移除）
     */
    removeWrongQuestion(questionId) {
        const wrongQuestions = this.getWrongQuestions();
        const filtered = wrongQuestions.filter(w => w.questionId !== questionId);
        localStorage.setItem(this.KEYS.WRONG_QUESTIONS, JSON.stringify(filtered));
    },

    /**
     * 标记错题为已复习
     */
    markWrongQuestionReviewed(questionId) {
        const wrongQuestions = this.getWrongQuestions();
        const item = wrongQuestions.find(w => w.questionId === questionId);
        if (item) {
            item.reviewed = true;
            localStorage.setItem(this.KEYS.WRONG_QUESTIONS, JSON.stringify(wrongQuestions));
        }
    },
    
    /**
     * 标记错题为已理解/取消理解
     */
    markWrongAsUnderstood(questionId, understood) {
        const wrongQuestions = this.getWrongQuestions();
        const item = wrongQuestions.find(w => w.questionId === questionId);
        if (item) {
            item.understood = understood;
            localStorage.setItem(this.KEYS.WRONG_QUESTIONS, JSON.stringify(wrongQuestions));
        }
    },

    /**
     * 获取错题数量
     */
    getWrongQuestionCount() {
        return this.getWrongQuestions().length;
    },

    // ==================== 答题历史 ====================

    /**
     * 获取答题历史
     */
    getQuizHistory() {
        return JSON.parse(localStorage.getItem(this.KEYS.QUIZ_HISTORY) || '[]');
    },

    /**
     * 保存答题历史
     */
    saveQuizHistory(chapterId, sectionType, score, totalQuestions, correctCount, mode) {
        const history = this.getQuizHistory();
        
        history.push({
            chapterId,
            sectionType,
            score,
            totalQuestions,
            correctCount,
            timestamp: Date.now(),
            mode
        });

        // 只保留最近 100 条记录
        if (history.length > 100) {
            history.shift();
        }

        localStorage.setItem(this.KEYS.QUIZ_HISTORY, JSON.stringify(history));
    },

    /**
     * 获取指定章节的历史
     */
    getChapterHistory(chapterId) {
        return this.getQuizHistory().filter(h => h.chapterId === chapterId);
    },

    // ==================== 章节进度 ====================

    /**
     * 获取所有章节进度
     */
    getChapterProgress() {
        return JSON.parse(localStorage.getItem(this.KEYS.CHAPTER_PROGRESS) || '{}');
    },

    /**
     * 获取指定章节进度
     */
    getChapterProgressById(chapterId) {
        const progress = this.getChapterProgress();
        return progress[chapterId] || null;
    },

    /**
     * 保存章节进度
     */
    saveChapterProgress(chapterId, completed, bestScore) {
        const progress = this.getChapterProgress();
        
        const existing = progress[chapterId] || {};
        progress[chapterId] = {
            completed,
            lastAccessed: Date.now(),
            bestScore: Math.max(existing.bestScore || 0, bestScore || 0)
        };

        localStorage.setItem(this.KEYS.CHAPTER_PROGRESS, JSON.stringify(progress));
    },

    /**
     * 更新章节最后访问时间
     */
    updateChapterLastAccessed(chapterId) {
        const progress = this.getChapterProgress();
        if (!progress[chapterId]) {
            progress[chapterId] = {};
        }
        progress[chapterId].lastAccessed = Date.now();
        localStorage.setItem(this.KEYS.CHAPTER_PROGRESS, JSON.stringify(progress));
    },

    // ==================== 用户设置 ====================

    /**
     * 获取用户设置
     */
    getSettings() {
        return JSON.parse(localStorage.getItem(this.KEYS.SETTINGS) || '{}');
    },

    /**
     * 保存设置
     */
    saveSettings(settings) {
        const current = this.getSettings();
        const updated = { ...current, ...settings };
        localStorage.setItem(this.KEYS.SETTINGS, JSON.stringify(updated));
    },

    /**
     * 获取答题模式
     */
    getMode() {
        return this.getSettings().mode || 'open';
    },

    /**
     * 设置答题模式
     */
    setMode(mode) {
        this.saveSettings({ mode });
    },

    // ==================== 统计 ====================

    /**
     * 获取总体统计
     */
    getStats(quizData = null) {
        const history = this.getQuizHistory();
        const wrongQuestions = this.getWrongQuestions();
        
        let totalAttempts = history.length;
        let totalQuestions = 0;
        let totalCorrect = 0;

        // 统计已完成的历史记录
        history.forEach(h => {
            totalQuestions += h.totalQuestions;
            totalCorrect += h.correctCount;
        });

        // 统计当前所有章节的答题进度
        if (quizData && quizData.chapters) {
            const allProgress = JSON.parse(localStorage.getItem(this.KEYS.ANSWER_PROGRESS) || '{}');
            
            Object.keys(allProgress).forEach(chapterId => {
                const chapterProgress = allProgress[chapterId];
                const answers = chapterProgress.answers || {};
                const answeredIds = Object.keys(answers);
                
                if (answeredIds.length > 0) {
                    totalAttempts++; // 增加答题次数
                    totalQuestions += answeredIds.length; // 增加总题数
                    
                    // 查找对应的章节和题目，计算正确数
                    const chapter = quizData.chapters.find(ch => ch.id === chapterId);
                    if (chapter) {
                        // 构建题目ID到题目的映射
                        const questionMap = {};
                        chapter.sections.forEach(section => {
                            section.questions.forEach(q => {
                                questionMap[q.id] = q;
                            });
                        });
                        
                        // 计算正确数
                        answeredIds.forEach(questionId => {
                            const question = questionMap[questionId];
                            const userAnswer = answers[questionId];
                            
                            if (question && userAnswer) {
                                const sorted1 = [...question.answer].sort().join(',');
                                const sorted2 = [...userAnswer].sort().join(',');
                                if (sorted1 === sorted2) {
                                    totalCorrect++;
                                }
                            }
                        });
                    }
                }
            });
        }

        return {
            totalAttempts,
            totalQuestions,
            totalCorrect,
            accuracy: totalQuestions > 0 ? Math.round((totalCorrect / totalQuestions) * 100) : 0,
            wrongCount: wrongQuestions.length
        };
    },

    // ==================== 清除数据 ====================

    /**
     * 清除所有数据
     */
    clearAll() {
        if (confirm('确定要清除所有数据吗？此操作不可撤销。')) {
            localStorage.removeItem(this.KEYS.WRONG_QUESTIONS);
            localStorage.removeItem(this.KEYS.QUIZ_HISTORY);
            localStorage.removeItem(this.KEYS.CHAPTER_PROGRESS);
            localStorage.removeItem(this.KEYS.ANSWER_PROGRESS);
            this.init();
            return true;
        }
        return false;
    },

    // ==================== 答题进度 ====================

    /**
     * 保存章节答题进度（每题的答案）
     */
    saveAnswerProgress(chapterId, userAnswers) {
        const progress = JSON.parse(localStorage.getItem(this.KEYS.ANSWER_PROGRESS) || '{}');
        progress[chapterId] = {
            answers: userAnswers,
            timestamp: Date.now()
        };
        localStorage.setItem(this.KEYS.ANSWER_PROGRESS, JSON.stringify(progress));
    },

    /**
     * 获取章节答题进度
     */
    getAnswerProgress(chapterId) {
        const progress = JSON.parse(localStorage.getItem(this.KEYS.ANSWER_PROGRESS) || '{}');
        const chapterProgress = progress[chapterId];
        
        if (!chapterProgress) return null;
        
        // 如果超过24小时，清除旧数据
        if (Date.now() - chapterProgress.timestamp > 24 * 60 * 60 * 1000) {
            delete progress[chapterId];
            localStorage.setItem(this.KEYS.ANSWER_PROGRESS, JSON.stringify(progress));
            return null;
        }
        
        return chapterProgress.answers || {};
    },

    /**
     * 清除章节答题进度
     */
    clearAnswerProgress(chapterId) {
        const progress = JSON.parse(localStorage.getItem(this.KEYS.ANSWER_PROGRESS) || '{}');
        delete progress[chapterId];
        localStorage.setItem(this.KEYS.ANSWER_PROGRESS, JSON.stringify(progress));
    }
};

// 初始化
Storage.init();
