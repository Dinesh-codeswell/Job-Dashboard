/**
 * ResumeApp  LaTeX Resume Editor
 * Split-pane editor with real-time compilation and PDF preview
 */
const ResumeApp = {
    // State
    editor: null,
    pdfDoc: null,
    currentPage: 1,
    zoomLevel: 1.0,
    compileTimer: null,
    isCompiling: false,
    latestPdfUrl: null,
    activeTemplate: 'jake',

    // Constants
    COMPILE_DELAY: 2000, // 2 seconds after user stops typing
    MIN_ZOOM: 0.5,
    MAX_ZOOM: 2.5,
    ZOOM_STEP: 0.1,

    /**
     * Initialize the resume editor
     */
    async init() {
        try {
            // Start with status bar hidden
            this.hideStatus();

            this.activeTemplate = 'jake';

            // Load the default LaTeX source
            const defaultSource = await this.loadDefaultSource(this.activeTemplate);

            // Initialize CodeMirror
            this.initEditor(defaultSource);

            // Initialize PDF.js
            pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

            // Setup event listeners
            this.setupEventListeners();

            // Initial compilation after a short delay
            setTimeout(() => this.compile(), 1000);

            console.log(' ResumeApp initialized');
        } catch (error) {
            console.error(' ResumeApp init failed:', error);
            this.showStatus('Initialization error', 'error');
        }
    },

    // ========================================================================
    // DATA LOADING
    // ========================================================================

    async loadDefaultSource(template = 'jake') {
        try {
            const response = await fetch(`/api/resume/default?template=${template}`);
            const data = await response.json();
            if (data.success && data.latex_source) {
                return data.latex_source;
            }
        } catch (e) {
            console.warn('Could not load default source:', e);
        }
        // Fallback minimal template
        return `\\documentclass[letterpaper,11pt]{article}
\\usepackage[empty]{fullpage}
\\usepackage{titlesec}
\\usepackage{hyperref}
\\usepackage{enumitem}

\\pagestyle{fancy}
\\fancyhf{}
\\fancyfoot{}
\\renewcommand{\\headrulewidth}{0pt}
\\renewcommand{\\footrulewidth}{0pt}

\\titleformat{\\section}{
  \\vspace{-4pt}\\scshape\\raggedright\\large
}{}{0em}{}[\\color{black}\\titlerule \\vspace{-5pt}]

\\begin{document}

\\begin{center}
    \\textbf{\\Huge \\scshape Your Name} \\\\ \\vspace{1pt}
    \\href{mailto:email@example.com}{email@example.com}
\\end{center}

\\section{Education}
  \\begin{itemize}
    \\item \\textbf{University Name}  Degree in Field, 2021
  \\end{itemize}

\\section{Experience}
  \\begin{itemize}
    \\item \\textbf{Company}  Job Title (2020 -- Present)\\\\
    Description of your role and accomplishments.
  \\end{itemize}

\\section{Skills}
  \\begin{itemize}
    \\item Python, JavaScript, React, Flask
  \\end{itemize}

\\end{document}`;
    },

    // ========================================================================
    // CODE MIRROR EDITOR
    // ========================================================================

    initEditor(source) {
        const textarea = document.getElementById('latexEditor');
        if (!textarea) return;

        this.editor = CodeMirror.fromTextArea(textarea, {
            value: source,
            mode: 'stex',
            theme: 'material-darker',
            lineNumbers: true,
            lineWrapping: true,
            matchBrackets: true,
            indentUnit: 2,
            tabSize: 2,
            indentWithTabs: false,
            foldGutter: true,
            gutters: ['CodeMirror-foldgutter', 'CodeMirror-linenumbers'],
            extraKeys: {
                'Ctrl-S': () => this.compile(),
                'Cmd-S': () => this.compile(),
                'Ctrl-Alt-L': () => this.formatLatex(),
            }
        });

        // Auto-compile on changes with debounce
        this.editor.on('change', () => {
            this.scheduleCompile();
        });

        // Focus the editor
        this.editor.focus();
    },

    // ========================================================================
    // EVENT LISTENERS
    // ========================================================================

    setupEventListeners() {
        // Download button
        document.getElementById('downloadBtn')?.addEventListener('click', () => this.download());

        // Reset button
        document.getElementById('resetBtn')?.addEventListener('click', () => this.resetToDefault());

        // Template selector
        document.getElementById('templateSelect')?.addEventListener('change', (e) => {
            const confirmChange = confirm("Switching templates will overwrite your current changes in the editor. Are you sure you want to proceed?");
            if (confirmChange) {
                this.loadTemplate(e.target.value);
            } else {
                e.target.value = this.activeTemplate;
            }
        });

        // Compile button
        document.getElementById('compileBtn')?.addEventListener('click', () => this.compile());

        // AI Generate button and modal
        document.getElementById('aiGenerateBtn')?.addEventListener('click', () => this.openAiModal());
        document.getElementById('aiModalClose')?.addEventListener('click', () => this.closeAiModal());
        document.getElementById('aiModalCancel')?.addEventListener('click', () => this.closeAiModal());
        document.getElementById('aiModalGenerate')?.addEventListener('click', () => this.generateWithAi());
        document.getElementById('aiModalOverlay')?.addEventListener('click', (e) => {
            if (e.target === e.currentTarget) this.closeAiModal();
        });

        // Word wrap toggle
        document.getElementById('wrapToggle')?.addEventListener('change', (e) => {
            this.editor.setOption('lineWrapping', e.target.checked);
        });

        // Zoom controls
        document.getElementById('zoomInBtn')?.addEventListener('click', () => this.zoomIn());
        document.getElementById('zoomOutBtn')?.addEventListener('click', () => this.zoomOut());

        // PDF page navigation
        document.getElementById('prevPageBtn')?.addEventListener('click', () => this.prevPage());
        document.getElementById('nextPageBtn')?.addEventListener('click', () => this.nextPage());

        // Resize handle for split pane
        this.setupResizeHandle();

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'Enter') {
                e.preventDefault();
                this.compile();
            }
            if (e.key === 'Escape') {
                this.closeAiModal();
                this.editor.focus();
            }
        });
    },

    setupResizeHandle() {
        const handle = document.getElementById('resizeHandle');
        const editor = document.querySelector('.editor-pane');
        const preview = document.querySelector('.preview-pane');
        let isDragging = false;

        handle.addEventListener('mousedown', (e) => {
            isDragging = true;
            document.body.style.cursor = 'col-resize';
            document.body.style.userSelect = 'none';
        });

        document.addEventListener('mousemove', (e) => {
            if (!isDragging) return;
            const container = document.querySelector('.resume-editor');
            const rect = container.getBoundingClientRect();
            const percentage = ((e.clientX - rect.left) / rect.width) * 100;

            // Clamp between 20% and 80%
            const clamped = Math.max(20, Math.min(80, percentage));
            editor.style.flex = `0 0 ${clamped}%`;
            preview.style.flex = `0 0 ${100 - clamped}%`;
            this.editor.refresh();
        });

        document.addEventListener('mouseup', () => {
            if (isDragging) {
                isDragging = false;
                document.body.style.cursor = '';
                document.body.style.userSelect = '';
            }
        });
    },

    // ========================================================================
    // COMPILATION
    // ========================================================================

    scheduleCompile() {
        if (this.compileTimer) {
            clearTimeout(this.compileTimer);
        }
        this.showStatus('Will compile...', 'pending');
        this.compileTimer = setTimeout(() => this.compile(), this.COMPILE_DELAY);
    },

    async compile() {
        if (this.isCompiling) return;

        const source = this.editor.getValue();
        if (!source || source.trim().length < 10) {
            this.showStatus('Source too short', 'error');
            this.autoHideStatus(3000);
            return;
        }

        this.isCompiling = true;
        this.showStatus('Compiling...', 'compiling');
        document.getElementById('downloadBtn').disabled = true;

        try {
            const response = await fetch('/api/resume/compile', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ latex_source: source })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => null);
                throw new Error(errorData?.error || `Compilation failed (${response.status})`);
            }

            // Get the PDF as blob
            const pdfBlob = await response.blob();

            if (pdfBlob.size < 100) {
                throw new Error('Generated PDF is too small - compilation likely failed');
            }

            // Revoke old URL if exists
            if (this.latestPdfUrl) {
                URL.revokeObjectURL(this.latestPdfUrl);
            }

            // Create blob URL and load PDF
            this.latestPdfUrl = URL.createObjectURL(pdfBlob);
            await this.loadPdf(this.latestPdfUrl);

            this.showStatus('Compiled successfully', 'success');
            this.autoHideStatus(2500);
            document.getElementById('downloadBtn').disabled = false;

        } catch (error) {
            console.error('Compilation error:', error);
            this.showStatus('Compilation failed', 'error');
            this.autoHideStatus(4000);
            this.showError(error.message);
        } finally {
            this.isCompiling = false;
        }
    },

    // ========================================================================
    // PDF RENDERING
    // ========================================================================

    async loadPdf(url) {
        try {
            this.pdfDoc = await pdfjsLib.getDocument(url).promise;

            // Show render area, hide placeholder and error
            document.getElementById('previewPlaceholder').style.display = 'none';
            document.getElementById('previewError').style.display = 'none';
            document.getElementById('pdfRenderArea').style.display = 'block';

            // Update page controls
            document.getElementById('pageInfo').textContent = `1 / ${this.pdfDoc.numPages}`;
            document.getElementById('prevPageBtn').disabled = true;
            document.getElementById('nextPageBtn').disabled = this.pdfDoc.numPages <= 1;

            // Render first page
            this.currentPage = 1;
            await this.renderPage(this.currentPage);

        } catch (error) {
            console.error('PDF load error:', error);
            this.showError('Failed to render PDF preview: ' + error.message);
        }
    },

    async renderPage(pageNum) {
        if (!this.pdfDoc) return;

        try {
            const page = await this.pdfDoc.getPage(pageNum);
            const canvas = document.getElementById('pdfCanvas');
            const context = canvas.getContext('2d');

            // Calculate viewport with zoom
            const viewport = page.getViewport({ scale: this.zoomLevel * 1.5 });

            // Set canvas dimensions
            canvas.height = viewport.height;
            canvas.width = viewport.width;

            // Render the page
            const renderContext = {
                canvasContext: context,
                viewport: viewport
            };

            await page.render(renderContext).promise;

            // Update page info
            document.getElementById('pageInfo').textContent = `${pageNum} / ${this.pdfDoc.numPages}`;
            document.getElementById('prevPageBtn').disabled = pageNum <= 1;
            document.getElementById('nextPageBtn').disabled = pageNum >= this.pdfDoc.numPages;
            document.getElementById('zoomLevel').textContent = `${Math.round(this.zoomLevel * 100)}%`;

        } catch (error) {
            console.error('Page render error:', error);
        }
    },

    nextPage() {
        if (this.pdfDoc && this.currentPage < this.pdfDoc.numPages) {
            this.currentPage++;
            this.renderPage(this.currentPage);
        }
    },

    prevPage() {
        if (this.pdfDoc && this.currentPage > 1) {
            this.currentPage--;
            this.renderPage(this.currentPage);
        }
    },

    zoomIn() {
        this.zoomLevel = Math.min(this.MAX_ZOOM, this.zoomLevel + this.ZOOM_STEP);
        if (this.pdfDoc) this.renderPage(this.currentPage);
    },

    zoomOut() {
        this.zoomLevel = Math.max(this.MIN_ZOOM, this.zoomLevel - this.ZOOM_STEP);
        if (this.pdfDoc) this.renderPage(this.currentPage);
    },

    // ========================================================================
    // DOWNLOAD
    // ========================================================================

    download() {
        if (!this.latestPdfUrl) return;

        const link = document.createElement('a');
        link.href = this.latestPdfUrl;
        link.download = 'resume.pdf';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    },

    // ========================================================================
    // RESET & LOAD TEMPLATES
    // ========================================================================

    async loadTemplate(template) {
        try {
            this.showStatus('Loading template...', 'pending');
            const defaultSource = await this.loadDefaultSource(template);
            this.editor.setValue(defaultSource);
            this.activeTemplate = template;
            this.showStatus('Template loaded! Compiling...', 'pending');
            this.compile();
        } catch (e) {
            console.error('Failed to load template:', e);
            this.showStatus('Error loading template', 'error');
        }
    },

    async resetToDefault() {
        try {
            const defaultSource = await this.loadDefaultSource(this.activeTemplate);
            this.editor.setValue(defaultSource);
            this.showStatus('Reset to default', 'idle');
            this.autoHideStatus(2000);
            this.scheduleCompile();
        } catch (e) {
            console.error('Reset failed:', e);
        }
    },

    // ========================================================================
    // AI GENERATE - OpenRouter Resume Generation
    // ========================================================================

    openAiModal() {
        document.getElementById('aiModalOverlay').style.display = 'flex';
        document.getElementById('aiResumeInput').value = '';
        document.getElementById('aiStatus').style.display = 'none';
        document.getElementById('aiModalGenerate').style.display = 'inline-flex';
        document.getElementById('aiResumeInput').focus();
        document.body.style.overflow = 'hidden';
    },

    closeAiModal() {
        document.getElementById('aiModalOverlay').style.display = 'none';
        document.body.style.overflow = '';
    },

    async generateWithAi() {
        const input = document.getElementById('aiResumeInput');
        const content = input.value.trim();

        if (!content || content.length < 20) {
            this.showAiStatus('Please paste your full resume content (at least 20 characters)', 'error');
            return;
        }

        // Show loading state
        document.getElementById('aiModalGenerate').style.display = 'none';
        this.showAiStatus('Generating your resume with AI...', 'loading');

        try {
            const response = await fetch('/api/resume/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    resume_content: content,
                    template: this.activeTemplate
                })
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(data.error || `Generation failed (${response.status})`);
            }

            // Populate the editor with the generated LaTeX
            this.editor.setValue(data.latex_source);

            // Close the modal
            this.closeAiModal();

            // Show success in status bar
            this.showStatus('AI generated! Compiling...', 'pending');

            // Auto-compile after a short delay
            setTimeout(() => this.compile(), 500);

        } catch (error) {
            console.error('AI generation error:', error);
            this.showAiStatus(error.message || 'Generation failed. Please try again.', 'error');
            document.getElementById('aiModalGenerate').style.display = 'inline-flex';
        }
    },

    showAiStatus(message, type) {
        const statusEl = document.getElementById('aiStatus');
        const textEl = document.getElementById('aiStatusText');

        statusEl.style.display = 'flex';
        textEl.textContent = message;

        // Reset classes
        statusEl.className = 'ai-status';
        if (type) statusEl.classList.add(type);
    },

    // ========================================================================
    // UI HELPERS - Status bar with auto-hide
    // ========================================================================

    hideStatus() {
        const statusEl = document.getElementById('compileStatus');
        if (statusEl) statusEl.style.display = 'none';
    },

    showStatus(message, type) {
        const statusEl = document.getElementById('compileStatus');
        const textEl = document.getElementById('statusText');
        const dot = statusEl?.querySelector('.status-dot');

        if (!statusEl) return;

        // Make visible
        statusEl.style.display = 'flex';

        if (textEl) textEl.textContent = message;
        if (dot) {
            dot.className = 'status-dot';
            if (type) dot.classList.add(type);
        }
        statusEl.className = 'compile-status';
        if (type) statusEl.classList.add(type);
    },

    autoHideStatus(delay = 2500) {
        if (this.autoHideTimer) {
            clearTimeout(this.autoHideTimer);
        }
        this.autoHideTimer = setTimeout(() => {
            this.hideStatus();
        }, delay);
    },

    showError(message) {
        document.getElementById('previewPlaceholder').style.display = 'none';
        document.getElementById('pdfRenderArea').style.display = 'none';
        document.getElementById('previewError').style.display = 'flex';
        document.getElementById('errorMessage').textContent = message || 'Unknown error';
    }
};

// Expose globally
window.ResumeApp = ResumeApp;
