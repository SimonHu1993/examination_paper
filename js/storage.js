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
        SETTINGS: 'settings'
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
            reviewed: false
        };

        if (existingIndex >= 0) {
            // 更新已有记录
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
    getStats() {
        const history = this.getQuizHistory();
        const wrongQuestions = this.getWrongQuestions();
        
        let totalQuestions = 0;
        let totalCorrect = 0;
        let totalAttempts = history.length;

        history.forEach(h => {
            totalQuestions += h.totalQuestions;
            totalCorrect += h.correctCount;
        });

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
            this.init();
            return true;
        }
        return false;
    }
};

// 初始化
Storage.init();
