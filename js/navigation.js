/**
 * 章节导航模块
 * 管理侧边栏导航和章节选择
 */

const Navigation = {
    // 当前题库数据
    quizData: null,
    
    // DOM 元素
    elements: {
        sidebar: null,
        overlay: null,
        menuBtn: null,
        closeBtn: null,
        sidebarNav: null,
        chapterGrid: null
    },

    /**
     * 初始化导航模块
     */
    init(quizData) {
        this.quizData = quizData;
        
        // 获取 DOM 元素
        this.elements.sidebar = document.getElementById('sidebar');
        this.elements.overlay = document.getElementById('overlay');
        this.elements.menuBtn = document.getElementById('menuBtn');
        this.elements.closeBtn = document.getElementById('closeBtn');
        this.elements.sidebarNav = document.getElementById('sidebarNav');
        this.elements.chapterGrid = document.getElementById('chapterGrid');

        // 绑定事件
        this.bindEvents();

        // 渲染章节列表
        this.renderSidebarNav();
        this.renderChapterGrid();
    },

    /**
     * 绑定事件
     */
    bindEvents() {
        // 打开侧边栏
        this.elements.menuBtn.addEventListener('click', () => this.openSidebar());
        
        // 关闭侧边栏
        this.elements.closeBtn.addEventListener('click', () => this.closeSidebar());
        this.elements.overlay.addEventListener('click', () => this.closeSidebar());

        // 键盘 ESC 关闭
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeSidebar();
            }
        });
    },

    /**
     * 打开侧边栏
     */
    openSidebar() {
        this.elements.sidebar.classList.add('open');
        this.elements.overlay.classList.add('visible');
    },

    /**
     * 关闭侧边栏
     */
    closeSidebar() {
        this.elements.sidebar.classList.remove('open');
        this.elements.overlay.classList.remove('visible');
    },

    /**
     * 渲染侧边栏导航
     */
    renderSidebarNav() {
        if (!this.quizData || !this.quizData.chapters) {
            this.elements.sidebarNav.innerHTML = '<div class="empty-state"><p>暂无章节数据</p></div>';
            return;
        }

        let html = '';
        let lastPart = '';

        this.quizData.chapters.forEach(chapter => {
            // 分组标题
            if (chapter.partName && chapter.partName !== lastPart) {
                lastPart = chapter.partName;
                html += `<div class="nav-group-title">${chapter.partName}</div>`;
            }

            const progress = Storage.getChapterProgressById(chapter.id);
            const questionCount = this.getChapterQuestionCount(chapter);
            const isActive = App.currentChapter && App.currentChapter.id === chapter.id;
            
            // 检查是否有答题进度（包括已完成的和进行中的）
            const hasProgress = progress && progress.completed;
            const answerProgress = Storage.getAnswerProgress(chapter.id);
            const hasAnsweredQuestions = answerProgress && Object.keys(answerProgress).length > 0;
            
            html += `
                <div class="nav-item ${isActive ? 'active' : ''}" data-chapter-id="${chapter.id}">
                    <div class="nav-item-title">${chapter.title}</div>
                    <div class="nav-item-meta">${questionCount} 题${hasProgress || hasAnsweredQuestions ? ' · 最佳 ' + (progress?.bestScore || 0) + '%' : ''}</div>
                </div>
            `;
        });

        this.elements.sidebarNav.innerHTML = html;

        this.elements.sidebarNav.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const chapterId = e.currentTarget.dataset.chapterId;
                this.selectChapter(chapterId);
            });
        });
    },

    /**
     * 渲染首页章节网格
     */
    renderChapterGrid() {
        if (!this.quizData || !this.quizData.chapters) {
            this.elements.chapterGrid.innerHTML = '<div class="empty-state"><p>暂无章节数据</p></div>';
            return;
        }

        let html = '';
        let lastPart = '';

        this.quizData.chapters.forEach(chapter => {
            if (chapter.partName && chapter.partName !== lastPart) {
                lastPart = chapter.partName;
                html += `<div class="grid-section-title">${chapter.partName}</div>`;
            }

            const progress = Storage.getChapterProgressById(chapter.id);
            const questionCount = this.getChapterQuestionCount(chapter);
            const progressPercent = progress ? progress.bestScore : 0;
            
            // 根据题型显示图标
            let icon = '📝';
            if (chapter.partType === 'subjective') icon = '📖';
            else if (chapter.partType === 'mock_exam') icon = '📝';

            html += `
                <div class="chapter-card" data-chapter-id="${chapter.id}">
                    <div class="chapter-card-icon">${icon}</div>
                    <div class="chapter-card-title">${chapter.title}</div>
                    <div class="chapter-card-meta">${questionCount} 道题目</div>
                    <div class="chapter-card-progress">
                        <div class="chapter-card-progress-bar" style="width: ${progressPercent}%"></div>
                    </div>
                </div>
            `;
        });

        this.elements.chapterGrid.innerHTML = html;

        this.elements.chapterGrid.querySelectorAll('.chapter-card').forEach(card => {
            card.addEventListener('click', (e) => {
                const chapterId = e.currentTarget.dataset.chapterId;
                this.selectChapter(chapterId);
            });
        });
    },

    /**
     * 选择章节
     */
    selectChapter(chapterId) {
        const chapter = this.quizData.chapters.find(ch => ch.id === chapterId);
        if (!chapter) return;
        App.currentChapter = chapter;
        Storage.updateChapterLastAccessed(chapterId);
        
        // 关闭侧边栏
        this.closeSidebar();

        // 启动答题
        Quiz.start(chapter);
    },

    /**
     * 获取章节题目总数
     */
    getChapterQuestionCount(chapter) {
        let count = 0;
        if (chapter.sections) {
            chapter.sections.forEach(section => {
                count += section.questions ? section.questions.length : 0;
            });
        }
        return count;
    },

    /**
     * 刷新导航显示
     */
    refresh() {
        this.renderSidebarNav();
        this.renderChapterGrid();
    },

    /**
     * 更新章节进度显示
     */
    updateProgress(chapterId) {
        const progress = Storage.getChapterProgressById(chapterId);
        
        // 检查是否有答题进度（包括已完成的和进行中的）
        const hasProgress = progress && progress.completed;
        const answerProgress = Storage.getAnswerProgress(chapterId);
        const hasAnsweredQuestions = answerProgress && Object.keys(answerProgress).length > 0;
        
        const navItem = this.elements.sidebarNav.querySelector(`[data-chapter-id="${chapterId}"]`);
        if (navItem && (hasProgress || hasAnsweredQuestions)) {
            const meta = navItem.querySelector('.nav-item-meta');
            const chapter = this.quizData.chapters.find(ch => ch.id === chapterId);
            const questionCount = this.getChapterQuestionCount(chapter);
            const scoreText = ' · 最佳 ' + (progress?.bestScore || 0) + '%';
            meta.textContent = `${questionCount} 题${scoreText}`;
        }

        const card = this.elements.chapterGrid.querySelector(`[data-chapter-id="${chapterId}"]`);
        if (card && progress) {
            const progressBar = card.querySelector('.chapter-card-progress-bar');
            progressBar.style.width = `${progress.bestScore}%`;
        }
    }
};
