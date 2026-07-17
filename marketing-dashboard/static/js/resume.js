/**
 * ResumeApp — LaTeX Resume Editor
 * Split-pane editor with real-time compilation, toolbar, PDF preview, and AI generation.
 * Inspired by Overleaf for educational use.
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
    searchCursor: null,
    searchResults: [],

    // Constants
    COMPILE_DELAY: 2000,
    MIN_ZOOM: 0.5,
    MAX_ZOOM: 2.5,
    ZOOM_STEP: 0.1,

    // ========================================================================
    // LATEX AUTO-COMPLETION WORD LIST
    // Comprehensive list of LaTeX commands, environments, and custom resume macros
    // ========================================================================

    LATEX_COMPLETIONS: [
        // ---- Document Structure ----
        { word: '\\documentclass', display: '\\documentclass[...]{...}', detail: 'Document class' },
        { word: '\\usepackage', display: '\\usepackage{...}', detail: 'Package import' },
        { word: '\\input', display: '\\input{...}', detail: 'Include file' },

        // ---- Sectioning Commands ----
        { word: '\\section', display: '\\section{...}', detail: 'Section heading' },
        { word: '\\subsection', display: '\\subsection{...}', detail: 'Subsection heading' },
        { word: '\\subsubsection', display: '\\subsubsection{...}', detail: 'Subsubsection heading' },
        { word: '\\paragraph', display: '\\paragraph{...}', detail: 'Paragraph heading' },
        { word: '\\subparagraph', display: '\\subparagraph{...}', detail: 'Subparagraph heading' },
        { word: '\\part', display: '\\part{...}', detail: 'Part' },
        { word: '\\chapter', display: '\\chapter{...}', detail: 'Chapter (book/report)' },
        { word: '\\appendix', display: '\\appendix', detail: 'Appendix start' },

        // ---- Text Formatting ----
        { word: '\\textbf', display: '\\textbf{...}', detail: 'Bold text' },
        { word: '\\textit', display: '\\textit{...}', detail: 'Italic text' },
        { word: '\\underline', display: '\\underline{...}', detail: 'Underline text' },
        { word: '\\emph', display: '\\emph{...}', detail: 'Emphasized text' },
        { word: '\\textsc', display: '\\textsc{...}', detail: 'Small caps' },
        { word: '\\texttt', display: '\\texttt{...}', detail: 'Typewriter text' },
        { word: '\\textsf', display: '\\textsf{...}', detail: 'Sans-serif text' },
        { word: '\\textrm', display: '\\textrm{...}', detail: 'Roman text' },
        { word: '\\textbf', display: '\\textbf{...}', detail: 'Bold' },
        { word: '\\textnormal', display: '\\textnormal{...}', detail: 'Normal text' },
        { word: '\\uppercase', display: '\\uppercase{...}', detail: 'Uppercase' },
        { word: '\\lowercase', display: '\\lowercase{...}', detail: 'Lowercase' },

        // ---- Font Sizes ----
        { word: '\\tiny', display: '\\tiny', detail: 'Smallest font' },
        { word: '\\scriptsize', display: '\\scriptsize', detail: 'Script size' },
        { word: '\\footnotesize', display: '\\footnotesize', detail: 'Footnote size' },
        { word: '\\small', display: '\\small', detail: 'Small font' },
        { word: '\\normalsize', display: '\\normalsize', detail: 'Default size' },
        { word: '\\large', display: '\\large', detail: 'Large font' },
        { word: '\\Large', display: '\\Large', detail: 'Larger font' },
        { word: '\\LARGE', display: '\\LARGE', detail: 'Very large font' },
        { word: '\\huge', display: '\\huge', detail: 'Huge font' },
        { word: '\\Huge', display: '\\Huge', detail: 'Biggest font' },

        // ---- Environments ----
        { word: '\\begin{document}', display: '\\begin{document}...\\end{document}', detail: 'Document body' },
        { word: '\\begin{itemize}', display: '\\begin{itemize}...\\end{itemize}', detail: 'Bullet list' },
        { word: '\\begin{enumerate}', display: '\\begin{enumerate}...\\end{enumerate}', detail: 'Numbered list' },
        { word: '\\begin{center}', display: '\\begin{center}...\\end{center}', detail: 'Centered block' },
        { word: '\\begin{tabular}', display: '\\begin{tabular}{...}...\\end{tabular}', detail: 'Table' },
        { word: '\\begin{abstract}', display: '\\begin{abstract}...\\end{abstract}', detail: 'Abstract' },
        { word: '\\begin{minipage}', display: '\\begin{minipage}{...}...\\end{minipage}', detail: 'Mini page' },
        { word: '\\begin{figure}', display: '\\begin{figure}...\\end{figure}', detail: 'Figure float' },
        { word: '\\begin{table}', display: '\\begin{table}...\\end{table}', detail: 'Table float' },
        { word: '\\begin{align}', display: '\\begin{align}...\\end{align}', detail: 'Math align' },
        { word: '\\begin{equation}', display: '\\begin{equation}...\\end{equation}', detail: 'Equation' },
        { word: '\\begin{flushleft}', display: '\\begin{flushleft}...\\end{flushleft}', detail: 'Left aligned' },
        { word: '\\begin{flushright}', display: '\\begin{flushright}...\\end{flushright}', detail: 'Right aligned' },
        { word: '\\begin{verbatim}', display: '\\begin{verbatim}...\\end{verbatim}', detail: 'Verbatim text' },
        { word: '\\begin{quote}', display: '\\begin{quote}...\\end{quote}', detail: 'Quote block' },
        { word: '\\begin{quotation}', display: '\\begin{quotation}...\\end{quotation}', detail: 'Long quotation' },
        { word: '\\end{document}', display: '\\end{document}', detail: 'End document' },
        { word: '\\end{itemize}', display: '\\end{itemize}', detail: 'End itemize' },
        { word: '\\end{enumerate}', display: '\\end{enumerate}', detail: 'End enumerate' },
        { word: '\\end{center}', display: '\\end{center}', detail: 'End center' },
        { word: '\\end{tabular}', display: '\\end{tabular}', detail: 'End tabular' },
        { word: '\\end{abstract}', display: '\\end{abstract}', detail: 'End abstract' },

        // ---- List Commands ----
        { word: '\\item', display: '\\item', detail: 'List item' },
        { word: '\\item[]', display: '\\item[...]', detail: 'List item with label' },

        // ---- Spacing ----
        { word: '\\vspace', display: '\\vspace{...}', detail: 'Vertical space' },
        { word: '\\hspace', display: '\\hspace{...}', detail: 'Horizontal space' },
        { word: '\\medskip', display: '\\medskip', detail: 'Medium vertical space' },
        { word: '\\smallskip', display: '\\smallskip', detail: 'Small vertical space' },
        { word: '\\bigskip', display: '\\bigskip', detail: 'Big vertical space' },
        { word: '\\fill', display: '\\fill', detail: 'Stretchable space' },
        { word: '\\hfill', display: '\\hfill', detail: 'Horizontal fill' },
        { word: '\\vfill', display: '\\vfill', detail: 'Vertical fill' },

        // ---- Page Layout ----
        { word: '\\newpage', display: '\\newpage', detail: 'Force new page' },
        { word: '\\clearpage', display: '\\clearpage', detail: 'Clear page & floats' },
        { word: '\\linebreak', display: '\\linebreak', detail: 'Line break' },
        { word: '\\pagebreak', display: '\\pagebreak', detail: 'Page break' },
        { word: '\\newline', display: '\\newline', detail: 'New line' },
        { word: '\\\\', display: '\\\\', detail: 'Line break (double backslash)' },
        { word: '\\par', display: '\\par', detail: 'New paragraph' },
        { word: '\\noindent', display: '\\noindent', detail: 'No indent' },
        { word: '\\indent', display: '\\indent', detail: 'Indent paragraph' },

        // ---- Colors ----
        { word: '\\color', display: '\\color{...}', detail: 'Set text color' },
        { word: '\\textcolor', display: '\\textcolor{...}{...}', detail: 'Colored text' },
        { word: '\\colorbox', display: '\\colorbox{...}{...}', detail: 'Colored background' },
        { word: '\\definecolor', display: '\\definecolor{...}{...}{...}', detail: 'Define custom color' },

        // ---- Tables ----
        { word: '\\hline', display: '\\hline', detail: 'Horizontal line in table' },
        { word: '\\cline', display: '\\cline{...}', detail: 'Partial horizontal line' },
        { word: '\\multicolumn', display: '\\multicolumn{...}{...}{...}', detail: 'Multi-column cell' },

        // ---- Math Symbols ----
        { word: '\\alpha', display: '\\alpha', detail: 'Greek alpha' },
        { word: '\\beta', display: '\\beta', detail: 'Greek beta' },
        { word: '\\gamma', display: '\\gamma', detail: 'Greek gamma' },
        { word: '\\delta', display: '\\delta', detail: 'Greek delta' },
        { word: '\\epsilon', display: '\\epsilon', detail: 'Greek epsilon' },
        { word: '\\theta', display: '\\theta', detail: 'Greek theta' },
        { word: '\\lambda', display: '\\lambda', detail: 'Greek lambda' },
        { word: '\\mu', display: '\\mu', detail: 'Greek mu' },
        { word: '\\pi', display: '\\pi', detail: 'Greek pi' },
        { word: '\\sigma', display: '\\sigma', detail: 'Greek sigma' },
        { word: '\\omega', display: '\\omega', detail: 'Greek omega' },
        { word: '\\infty', display: '\\infty', detail: 'Infinity' },
        { word: '\\in', display: '\\in', detail: 'Set membership' },
        { word: '\\sum', display: '\\sum', detail: 'Summation' },
        { word: '\\prod', display: '\\prod', detail: 'Product' },
        { word: '\\int', display: '\\int', detail: 'Integral' },
        { word: '\\partial', display: '\\partial', detail: 'Partial derivative' },
        { word: '\\nabla', display: '\\nabla', detail: 'Gradient (del/nabla)' },
        { word: '\\emptyset', display: '\\emptyset', detail: 'Empty set' },
        { word: '\\forall', display: '\\forall', detail: 'For all' },
        { word: '\\exists', display: '\\exists', detail: 'There exists' },
        { word: '\\neg', display: '\\neg', detail: 'Negation / not' },
        { word: '\\wedge', display: '\\wedge', detail: 'Logical AND' },
        { word: '\\vee', display: '\\vee', detail: 'Logical OR' },
        { word: '\\oplus', display: '\\oplus', detail: 'Circled plus' },
        { word: '\\otimes', display: '\\otimes', detail: 'Circled times' },
        { word: '\\bullet', display: '\\bullet', detail: 'Bullet point' },
        { word: '\\cdot', display: '\\cdot', detail: 'Center dot' },
        { word: '\\times', display: '\\times', detail: 'Multiplication sign' },
        { word: '\\rightarrow', display: '\\rightarrow', detail: 'Right arrow' },
        { word: '\\leftarrow', display: '\\leftarrow', detail: 'Left arrow' },
        { word: '\\Rightarrow', display: '\\Rightarrow', detail: 'Right double arrow' },
        { word: '\\Leftarrow', display: '\\Leftarrow', detail: 'Left double arrow' },
        { word: '\\mapsto', display: '\\mapsto', detail: 'Maps to' },
        { word: '\\approx', display: '\\approx', detail: 'Approximately' },
        { word: '\\equiv', display: '\\equiv', detail: 'Equivalent' },
        { word: '\\sim', display: '\\sim', detail: 'Similar to' },
        { word: '\\propto', display: '\\propto', detail: 'Proportional to' },

        // ---- References & Links ----
        { word: '\\label', display: '\\label{...}', detail: 'Label for referencing' },
        { word: '\\ref', display: '\\ref{...}', detail: 'Reference label' },
        { word: '\\pageref', display: '\\pageref{...}', detail: 'Page reference' },
        { word: '\\cite', display: '\\cite{...}', detail: 'Citation' },
        { word: '\\href', display: '\\href{url}{...}', detail: 'Hyperlink' },
        { word: '\\url', display: '\\url{...}', detail: 'URL display' },

        // ---- Packages ----
        { word: '\\usepackage{amsmath}', display: '\\usepackage{amsmath}', detail: 'Advanced math' },
        { word: '\\usepackage{amssymb}', display: '\\usepackage{amssymb}', detail: 'Math symbols' },
        { word: '\\usepackage{graphicx}', display: '\\usepackage{graphicx}', detail: 'Images' },
        { word: '\\usepackage{hyperref}', display: '\\usepackage{hyperref}', detail: 'Hyperlinks' },
        { word: '\\usepackage{geometry}', display: '\\usepackage{geometry}', detail: 'Page geometry' },
        { word: '\\usepackage{enumitem}', display: '\\usepackage{enumitem}', detail: 'Custom lists' },
        { word: '\\usepackage{titlesec}', display: '\\usepackage{titlesec}', detail: 'Section formatting' },
        { word: '\\usepackage{fancyhdr}', display: '\\usepackage{fancyhdr}', detail: 'Header/footer' },
        { word: '\\usepackage{color}', display: '\\usepackage{color}', detail: 'Color support' },
        { word: '\\usepackage{xcolor}', display: '\\usepackage{xcolor}', detail: 'Extended colors' },
        { word: '\\usepackage{multicol}', display: '\\usepackage{multicol}', detail: 'Multi-column' },
        { word: '\\usepackage{booktabs}', display: '\\usepackage{booktabs}', detail: 'Professional tables' },
        { word: '\\usepackage{tikz}', display: '\\usepackage{tikz}', detail: 'Drawing/graphics' },
        { word: '\\usepackage{listings}', display: '\\usepackage{listings}', detail: 'Code listings' },

        // ---- Resume Template Commands ----
        { word: '\\resumeItem', display: '\\resumeItem{...}', detail: 'Resume bullet item' },
        { word: '\\resumeSubheading', display: '\\resumeSubheading{School}{Loc}{Deg}{Dates}', detail: 'Resume subheading (4 args)' },
        { word: '\\resumeProjectHeading', display: '\\resumeProjectHeading{Name $|$ Stack}{Dates}', detail: 'Project heading (2 args)' },
        { word: '\\resumeSubItem', display: '\\resumeSubItem{...}', detail: 'Resume sub item' },
        { word: '\\resumeSubHeadingListStart', display: '\\resumeSubHeadingListStart', detail: 'Start subheading list' },
        { word: '\\resumeSubHeadingListEnd', display: '\\resumeSubHeadingListEnd', detail: 'End subheading list' },
        { word: '\\resumeItemListStart', display: '\\resumeItemListStart', detail: 'Start item list' },
        { word: '\\resumeItemListEnd', display: '\\resumeItemListEnd', detail: 'End item list' },
        { word: '\\resumeProjectHeading', display: '\\resumeProjectHeading{...}{...}', detail: 'Project heading' },
        { word: '\\resumeItemPlain', display: '\\resumeItemPlain{...}', detail: 'Plain item (no bold)' },
        { word: '\\resumeSubSubheading', display: '\\resumeSubSubheading{...}', detail: 'Sub-subheading' },

        // ---- Miscellaneous ----
        { word: '\\today', display: '\\today', detail: 'Current date' },
        { word: '\\LaTeX', display: '\\LaTeX', detail: 'LaTeX logo' },
        { word: '\\TeX', display: '\\TeX', detail: 'TeX logo' },
        { word: '\\dots', display: '\\dots', detail: 'Ellipsis' },
        { word: '\\ldots', display: '\\ldots', detail: 'Ellipsis (low)' },
        { word: '\\S', display: '\\S', detail: 'Section symbol' },
        { word: '\\P', display: '\\P', detail: 'Paragraph symbol' },
        { word: '\\pounds', display: '\\pounds', detail: 'Pound sterling' },
        { word: '\\%', display: '\\%', detail: 'Percent sign' },
        { word: '\\$', display: '\\$', detail: 'Dollar sign' },
        { word: '\\#', display: '\\#', detail: 'Hash/pound sign' },
        { word: '\\&', display: '\\&', detail: 'Ampersand' },
        { word: '\\_{}', display: '\\_{}', detail: 'Underscore' },
        { word: '\\^{}', display: '\\^{}', detail: 'Caret/circumflex' },
        { word: '\\~{}', display: '\\~{}', detail: 'Tilde' },
    ],

    /**
     * Custom CodeMirror hint function for LaTeX.
     * Activated when user types '\' or triggers Ctrl+Space.
     */
    latexHint(cm, options) {
        const cursor = cm.getCursor();
        const line = cm.getLine(cursor.line);
        const token = cm.getTokenAt(cursor);

        // Determine what the user has typed so far
        let start = cursor.ch;
        let word = '';

        // Walk backwards from cursor to find where the command started
        for (let i = cursor.ch - 1; i >= 0; i--) {
            const ch = line[i];
            if (ch === '\\') {
                // Found the backslash - this is the start of our command
                word = line.substring(i, cursor.ch);
                start = i;
                break;
            } else if (!/[a-zA-Z*@]/.test(ch)) {
                // Not part of a command word
                break;
            }
        }

        // Only show hints for backslash-prefixed terms
        if (!word.startsWith('\\')) {
            return null;
        }

        const query = word.substring(1).toLowerCase(); // Remove backslash for matching

        // Filter completions
        const matches = ResumeApp.LATEX_COMPLETIONS.filter(item => {
            const cmdName = item.word.substring(1).toLowerCase(); // Remove leading \
            return cmdName.startsWith(query);
        });

        if (matches.length === 0) {
            return null;
        }

        return {
            list: matches.map(item => ({
                text: item.word,
                displayText: item.display || item.word,
                className: 'latex-hint',
                hint: function(cm, data, completion) {
                    // Replace from start of backslash to cursor with the selected command
                    cm.replaceRange(completion.text, { line: cursor.line, ch: start }, cursor);
                },
                // Render method for custom HTML in the hint popup
                render: function(element, self, data) {
                    element.innerHTML = '';
                    const cmdSpan = document.createElement('span');
                    cmdSpan.className = 'hint-cmd';
                    cmdSpan.textContent = data.displayText || data.text;
                    element.appendChild(cmdSpan);
                    if (data.detail) {
                        const detailSpan = document.createElement('span');
                        detailSpan.className = 'hint-detail';
                        detailSpan.textContent = data.detail;
                        element.appendChild(detailSpan);
                    }
                }
            })),
            from: { line: cursor.line, ch: start },
            to: { line: cursor.line, ch: cursor.ch }
        };
    },

    // Hardcoded fallback template so the editor is NEVER empty on load
    FALLBACK_TEMPLATE: `\\documentclass[letterpaper,11pt]{article}
\\usepackage[empty]{fullpage}
\\usepackage{titlesec}
\\usepackage{marvosym}
\\usepackage[usenames,dvipsnames]{color}
\\usepackage{verbatim}
\\usepackage{enumitem}
\\usepackage[hidelinks]{hyperref}
\\usepackage{fancyhdr}
\\usepackage[english]{babel}
\\usepackage{tabularx}
\\input{glyphtounicode}

\\pagestyle{fancy}
\\fancyhf{}
\\fancyfoot{}
\\renewcommand{\\headrulewidth}{0pt}
\\renewcommand{\\footrulewidth}{0pt}

\\addtolength{\\oddsidemargin}{-0.5in}
\\addtolength{\\evensidemargin}{-0.5in}
\\addtolength{\\textwidth}{1in}
\\addtolength{\\topmargin}{-.5in}
\\addtolength{\\textheight}{1.0in}

\\urlstyle{same}
\\raggedbottom
\\raggedright
\\setlength{\\tabcolsep}{0in}

\\titleformat{\\section}{
  \\vspace{-4pt}\\scshape\\raggedright\\large
}{}{0em}{}[\\color{black}\\titlerule \\vspace{-5pt}]

\\pdfgentounicode=1

\\newcommand{\\resumeItem}[1]{
  \\item\\small{
    {#1 \\vspace{-2pt}}
  }
}

\\newcommand{\\resumeSubheading}[4]{
  \\vspace{-2pt}\\item
    \\begin{tabular*}{0.97\\textwidth}[t]{l@{\\extracolsep{\\fill}}r}
      \\textbf{#1} & #2 \\\\
      \\textit{\\small#3} & \\textit{\\small #4} \\\\
    \\end{tabular*}\\vspace{-7pt}
}

\\newcommand{\\resumeProjectHeading}[2]{
    \\item
    \\begin{tabular*}{0.97\\textwidth}{l@{\\extracolsep{\\fill}}r}
      \\small#1 & #2 \\\\
    \\end{tabular*}\\vspace{-7pt}
}

\\newcommand{\\resumeSubItem}[1]{\\resumeItem{#1}\\vspace{-4pt}}

\\renewcommand\\labelitemii{$\\vcenter{\\hbox{\\tiny$\\bullet$}}$}

\\newcommand{\\resumeSubHeadingListStart}{\\begin{itemize}[leftmargin=0.15in, label={}]}
\\newcommand{\\resumeSubHeadingListEnd}{\\end{itemize}}
\\newcommand{\\resumeItemListStart}{\\begin{itemize}}
\\newcommand{\\resumeItemListEnd}{\\end{itemize}\\vspace{-5pt}}

\\begin{document}

\\begin{center}
    \\textbf{\\Huge \\scshape Jake Ryan} \\\\ \\vspace{1pt}
    \\small 123-456-7890 $|$ \\href{mailto:x@x.com}{\\underline{jake@su.edu}} $|$
    \\href{https://linkedin.com/in/...}{\\underline{linkedin.com/in/jake}} $|$
    \\href{https://github.com/...}{\\underline{github.com/jake}}
\\end{center}

\\section{Education}
  \\resumeSubHeadingListStart
    \\resumeSubheading
      {Southwestern University}{Georgetown, TX}
      {Bachelor of Arts in Computer Science, Minor in Business}{Aug. 2018 -- May 2021}
  \\resumeSubHeadingListEnd

\\section{Experience}
  \\resumeSubHeadingListStart
    \\resumeSubheading
      {Undergraduate Research Assistant}{June 2020 -- Present}
      {Texas A\\&M University}{College Station, TX}
      \\resumeItemListStart
        \\resumeItem{Developed a REST API using FastAPI and PostgreSQL}
        \\resumeItem{Developed a full-stack web application using Flask, React, PostgreSQL and Docker}
      \\resumeItemListEnd
  \\resumeSubHeadingListEnd

\\section{Projects}
    \\resumeSubHeadingListStart
      \\resumeProjectHeading
          {\\textbf{Gitlytics} $|$ \\emph{Python, Flask, React, PostgreSQL, Docker}}{June 2020 -- Present}
          \\resumeItemListStart
            \\resumeItem{Developed a full-stack web application using with Flask serving a REST API with React}
            \\resumeItem{Implemented GitHub OAuth to get data from user repositories}
          \\resumeItemListEnd
    \\resumeSubHeadingListEnd

\\section{Technical Skills}
 \\begin{itemize}[leftmargin=0.15in, label={}]
    \\small{\\item{
     \\textbf{Languages}{: Java, Python, C/C++, SQL (Postgres), JavaScript, HTML/CSS, R} \\\\
     \\textbf{Frameworks}{: React, Node.js, Flask, JUnit, WordPress, Material-UI, FastAPI} \\\\
     \\textbf{Developer Tools}{: Git, Docker, TravisCI, Google Cloud Platform, VS Code, Visual Studio, PyCharm, IntelliJ, Eclipse} \\\\
     \\textbf{Libraries}{: pandas, NumPy, Matplotlib}
    }}
 \\end{itemize}

\\end{document}`,

    /**
     * Initialize the resume editor
     */
    async init() {
        try {
            this.hideStatus();
            this.activeTemplate = 'jake';

            // STEP 1: Initialize CodeMirror IMMEDIATELY with the hardcoded fallback template
            // This ensures the editor is NEVER empty when the page loads.
            this.initEditor(this.FALLBACK_TEMPLATE);

            // Initialize PDF.js
            pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

            // STEP 2: Setup event listeners (toolbar, keyboard shortcuts, etc.)
            this.setupEventListeners();

            // STEP 3: Load the template from the API (asynchronously, will overwrite the fallback)
            this.loadTemplateFromApi('jake');

            console.log('✅ ResumeApp initialized');
        } catch (error) {
            console.error('❌ ResumeApp init failed:', error);
            this.showStatus('Initialization error', 'error');
        }
    },

    /**
     * Asynchronously load template from API and set it in the editor.
     * Falls back silently if the API fails.
     */
    async loadTemplateFromApi(template) {
        // Update activeTemplate immediately so the template selector shows correct value
        this.activeTemplate = template;
        document.getElementById('templateSelect').value = template;

        try {
            this.showStatus('Loading template...', 'pending');
            const response = await fetch(`/api/latex/template?template=${template}`);
            const data = await response.json();
            if (data.success && data.latex_source) {
                this.editor.setValue(data.latex_source);
                // Auto-compile after template loads
                setTimeout(() => this.compile(), 500);
                return;
            }
        } catch (e) {
            console.warn('Could not load from API, using fallback template:', e);
        }
        // Fallback: if API fails, start compiling the fallback already in the editor
        this.showStatus('Using fallback template', 'pending');
        setTimeout(() => this.compile(), 500);
    },

    // ========================================================================
    // CODE MIRROR EDITOR
    // ========================================================================

    initEditor(source) {
        const textarea = document.getElementById('latexEditor');
        if (!textarea) return;

        // If CodeMirror already exists, just update the value
        if (this.editor) {
            this.editor.setValue(source);
            return;
        }

        // Register the LaTeX hint function with CodeMirror
        CodeMirror.registerHelper('hint', 'latex', (cm, options) => this.latexHint(cm, options));

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
                'Ctrl-Enter': () => this.compile(),
                'Cmd-Enter': () => this.compile(),
                'Ctrl-=': () => this.zoomIn(),
                'Cmd-=': () => this.zoomIn(),
                'Ctrl--': () => this.zoomOut(),
                'Cmd--': () => this.zoomOut(),
                // F11 is handled in global keydown to avoid double-firing
                'Ctrl-B': () => this.insertBold(),
                'Cmd-B': () => this.insertBold(),
                'Ctrl-I': () => this.insertItalic(),
                'Cmd-I': () => this.insertItalic(),
                'Ctrl-H': () => this.openSearch(),
                'Cmd-H': () => this.openSearch(),
                'Ctrl-F': () => this.openSearch(),
                'Cmd-F': () => this.openSearch(),
                'Ctrl-Space': (cm) => cm.showHint({ hint: CodeMirror.hint.latex }),
                'Cmd-Space': (cm) => cm.showHint({ hint: CodeMirror.hint.latex }),
                '\\': (cm) => {
                    // Insert the backslash first, then trigger hints
                    cm.replaceRange('\\', cm.getCursor());
                    // Show hints immediately after inserting backslash
                    setTimeout(() => {
                        cm.showHint({ hint: CodeMirror.hint.latex });
                    }, 10);
                },
            }
        });

        // Also trigger hints when typing any character after a backslash
        this.editor.on('inputRead', (cm, change) => {
            if (change.text && change.text.length === 1) {
                const ch = change.text[0];
                // Check if we're typing letters after a backslash
                if (/[a-zA-Z*]/.test(ch)) {
                    const cursor = cm.getCursor();
                    const line = cm.getLine(cursor.line);
                    // Walk back from cursor to find backslash
                    let i = cursor.ch - 1;
                    while (i >= 0 && /[a-zA-Z*]/.test(line[i])) i--;
                    if (i >= 0 && line[i] === '\\') {
                        // Auto-show hints when typing after backslash
                        cm.showHint({ hint: CodeMirror.hint.latex, completeSingle: false });
                    }
                }
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
    // LATEX SNIPPETS (Quick Actions)
    // ========================================================================

    SNIPPETS: {
        'resume-header': `\\begin{center}
    \\textbf{\\Huge \\scshape Your Name} \\\\ \\vspace{1pt}
    \\small +1-123-456-7890 $|$ \\href{mailto:email@example.com}{\\underline{email@example.com}} $|$
    \\href{https://linkedin.com/in/you}{\\underline{linkedin.com/in/you}} $|$
    \\href{https://github.com/you}{\\underline{github.com/you}}
\\end{center}`,

        'resume-experience': `\\resumeSubheading
  {Company Name}{Location}
  {Job Title}{Month Year -- Present}
  \\resumeItemListStart
    \\resumeItem{Accomplishment or responsibility with quantified impact}
    \\resumeItem{Another key achievement using relevant technologies}
    \\resumeItem{Additional bullet point highlighting results}
  \\resumeItemListEnd`,

        'resume-education': `\\resumeSubheading
  {University Name}{City, State}
  {Degree in Field, Minor}{Month Year -- Month Year}
\\vspace{-5pt}`,

        'resume-project': `\\resumeProjectHeading
  {\\textbf{Project Name} $|$ \\emph{Tech Stack}}{Timeline}
  \\resumeItemListStart
    \\resumeItem{Built feature X using technology Y resulting in Z}
    \\resumeItem{Implemented component A to solve problem B}
  \\resumeItemListEnd`,

        'resume-skills': `\\section{Skills}
 \\begin{itemize}[leftmargin=0.15in, label={}]
    \\small{\\item{
     \\textbf{Languages}{: Skill1, Skill2, Skill3} \\\\
     \\textbf{Frameworks}{: Framework1, Framework2} \\\\
     \\textbf{Tools}{: Tool1, Tool2, Tool3}
    }}
 \\end{itemize}`,

        'bullet-list': `\\begin{itemize}
  \\item First item
  \\item Second item
  \\item Third item
\\end{itemize}`,

        'numbered-list': `\\begin{enumerate}
  \\item First item
  \\item Second item
  \\item Third item
\\end{enumerate}`,

        'table': `\\begin{center}
  \\begin{tabular}{|l|c|r|}
    \\hline
    Header 1 & Header 2 & Header 3 \\\\
    \\hline
    Cell 1 & Cell 2 & Cell 3 \\\\
    Cell 4 & Cell 5 & Cell 6 \\\\
    \\hline
  \\end{tabular}
\\end{center}`,

        'center': `\\begin{center}
  Centered text here
\\end{center}`,

        'minipage': `\\begin{minipage}{0.48\\textwidth}
  Left content
\\end{minipage}
\\hfill
\\begin{minipage}{0.48\\textwidth}
  Right content
\\end{minipage}`,

        'figure': `\\begin{figure}[h]
  \\centering
  \\includegraphics[width=0.8\\textwidth]{image.png}
  \\caption{Caption here}
  \\label{fig:label}
\\end{figure}`,

        'code-block': `\\begin{verbatim}
code goes here
\\end{verbatim}`,

        'hyperlink': `\\href{https://example.com}{\\underline{Display Text}}`
    },

    /**
     * Toggle the snippets panel
     */
    toggleSnippets() {
        const panel = document.getElementById('snippetsPanel');
        if (panel) {
            const isVisible = panel.style.display === 'block';
            // Close symbol picker if open
            const symbolPicker = document.getElementById('symbolPicker');
            if (symbolPicker) symbolPicker.style.display = 'none';
            panel.style.display = isVisible ? 'none' : 'block';
        }
    },

    /**
     * Insert a LaTeX snippet at the cursor position
     */
    insertSnippet(snippetKey) {
        if (!this.editor || !this.SNIPPETS[snippetKey]) return;

        const template = this.SNIPPETS[snippetKey];
        const cursor = this.editor.getCursor();

        // Insert the snippet at cursor, with a blank line before if not at line start
        const prefix = cursor.ch > 0 ? '\n' : '';
        const fullInsert = prefix + template;

        this.editor.replaceRange(fullInsert, cursor);

        // Move cursor to after the inserted content
        const newLine = cursor.line + fullInsert.split('\n').length - 1;
        const newCh = fullInsert.split('\n').pop().length;
        this.editor.setCursor({ line: newLine, ch: newCh });
        this.editor.focus();

        // Close the snippets panel
        this.toggleSnippets();

        // Trigger compile
        this.scheduleCompile();
    },

    // ========================================================================
    // TOOLBAR ACTIONS
    // ========================================================================

    /**
     * Undo last edit
     */
    undo() {
        if (this.editor) {
            this.editor.undo();
        }
    },

    /**
     * Redo last undone edit
     */
    redo() {
        if (this.editor) {
            this.editor.redo();
        }
    },

    /**
     * Wrap selected text with \textbf{}
     */
    insertBold() {
        if (!this.editor) return;
        const selection = this.editor.getSelection();
        if (selection) {
            this.editor.replaceSelection(`\\textbf{${selection}}`);
        } else {
            const cursor = this.editor.getCursor();
            this.editor.replaceRange('\\textbf{}', cursor);
            // Move cursor between the braces
            this.editor.setCursor({ line: cursor.line, ch: cursor.ch + 7 });
        }
        this.editor.focus();
    },

    /**
     * Wrap selected text with \textit{}
     */
    insertItalic() {
        if (!this.editor) return;
        const selection = this.editor.getSelection();
        if (selection) {
            this.editor.replaceSelection(`\\textit{${selection}}`);
        } else {
            const cursor = this.editor.getCursor();
            this.editor.replaceRange('\\textit{}', cursor);
            this.editor.setCursor({ line: cursor.line, ch: cursor.ch + 7 });
        }
        this.editor.focus();
    },

    /**
     * Insert a LaTeX command at cursor position
     */
    insertSymbol(command) {
        if (!this.editor) return;
        const cursor = this.editor.getCursor();
        this.editor.replaceRange(command, cursor);
        this.editor.setCursor({ line: cursor.line, ch: cursor.ch + command.length });
        this.editor.focus();
    },

    /**
     * Toggle the symbol picker dropdown
     */
    toggleSymbolPicker() {
        const picker = document.getElementById('symbolPicker');
        if (picker) {
            picker.style.display = picker.style.display === 'none' ? 'block' : 'none';
        }
    },

    // ========================================================================
    // SEARCH & REPLACE
    // ========================================================================

    /**
     * Open the search & replace modal
     */
    openSearch() {
        const overlay = document.getElementById('searchModalOverlay');
        if (overlay) {
            overlay.style.display = 'flex';
            document.getElementById('searchQuery').value = '';
            document.getElementById('searchReplace').value = '';
            document.getElementById('searchMatchCount').textContent = '0 matches';
            document.getElementById('searchCurrentMatch').textContent = '';
            document.getElementById('searchQuery').focus();
            this.clearSearchHighlights();
        }
    },

    closeSearch() {
        const overlay = document.getElementById('searchModalOverlay');
        if (overlay) {
            overlay.style.display = 'none';
        }
        this.clearSearchHighlights();
        if (this.editor) this.editor.focus();
    },

    clearSearchHighlights() {
        if (this.editor) {
            // Remove all search highlights by re-rendering
            this.editor.getAllMarks().forEach(mark => mark.clear());
        }
        this.searchCursor = null;
        this.searchResults = [];
    },

    /**
     * Perform search and highlight all matches
     */
    performSearch() {
        const query = document.getElementById('searchQuery').value;
        const caseSensitive = document.getElementById('searchCaseSensitive').checked;
        const useRegex = document.getElementById('searchRegex').checked;

        if (!this.editor) return;

        // Clear previous highlights
        this.clearSearchHighlights();

        if (!query) {
            document.getElementById('searchMatchCount').textContent = '0 matches';
            document.getElementById('searchCurrentMatch').textContent = '';
            return;
        }

        try {
            // Build search cursor
            let searchQuery = query;
            if (!useRegex) {
                searchQuery = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
            }

            const cursor = this.editor.getSearchCursor(searchQuery, null, {
                caseFold: !caseSensitive
            });

            this.searchCursor = cursor;
            this.searchResults = [];

            // Iterate through all matches and highlight them
            while (cursor.findNext()) {
                this.searchResults.push({
                    from: cursor.from(),
                    to: cursor.to()
                });
                // Highlight the match
                this.editor.markText(cursor.from(), cursor.to(), {
                    className: 'cm-search-match',
                    css: 'background: rgba(255, 235, 59, 0.4) !important;'
                });
            }

            // Update match count
            const count = this.searchResults.length;
            document.getElementById('searchMatchCount').textContent = `${count} match${count !== 1 ? 'es' : ''}`;
            document.getElementById('searchCurrentMatch').textContent = '';

            // If there are matches, select the first one
            if (count > 0) {
                this.searchCursor = this.editor.getSearchCursor(searchQuery, null, {
                    caseFold: !caseSensitive
                });
                this.searchCursor.findNext();
                this.editor.setSelection(this.searchCursor.from(), this.searchCursor.to());
                this.editor.scrollIntoView({ from: this.searchCursor.from(), to: this.searchCursor.to() }, 20);
                document.getElementById('searchCurrentMatch').textContent = '1/' + count;
            }

        } catch (e) {
            console.error('Search error:', e);
            document.getElementById('searchMatchCount').textContent = 'Invalid regex';
        }
    },

    /**
     * Go to next search match
     */
    searchNext() {
        if (!this.searchCursor) {
            this.performSearch();
            return;
        }

        const found = this.searchCursor.findNext();
        if (found) {
            this.editor.setSelection(this.searchCursor.from(), this.searchCursor.to());
            this.editor.scrollIntoView({ from: this.searchCursor.from(), to: this.searchCursor.to() }, 20);
            // Update current match position
            const currentPos = this.getCurrentMatchIndex();
            document.getElementById('searchCurrentMatch').textContent = `${currentPos}/${this.searchResults.length}`;
        } else {
            // Wrap around
            this.searchCursor = this.editor.getSearchCursor(
                this.searchCursor.query,
                null,
                { caseFold: !document.getElementById('searchCaseSensitive').checked }
            );
            if (this.searchCursor.findNext()) {
                this.editor.setSelection(this.searchCursor.from(), this.searchCursor.to());
                this.editor.scrollIntoView({ from: this.searchCursor.from(), to: this.searchCursor.to() }, 20);
                document.getElementById('searchCurrentMatch').textContent = `1/${this.searchResults.length}`;
            }
        }
    },

    /**
     * Go to previous search match
     */
    searchPrev() {
        if (!this.searchCursor) {
            this.performSearch();
            return;
        }

        const found = this.searchCursor.findPrevious();
        if (found) {
            this.editor.setSelection(this.searchCursor.from(), this.searchCursor.to());
            this.editor.scrollIntoView({ from: this.searchCursor.from(), to: this.searchCursor.to() }, 20);
            const currentPos = this.getCurrentMatchIndex();
            document.getElementById('searchCurrentMatch').textContent = `${currentPos}/${this.searchResults.length}`;
        } else {
            // Wrap around to last
            const query = document.getElementById('searchQuery').value;
            let searchQuery = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
            this.searchCursor = this.editor.getSearchCursor(
                searchQuery,
                { line: this.editor.lastLine(), ch: this.editor.getLine(this.editor.lastLine()).length },
                { caseFold: !document.getElementById('searchCaseSensitive').checked }
            );
            if (this.searchCursor.findPrevious()) {
                this.editor.setSelection(this.searchCursor.from(), this.searchCursor.to());
                this.editor.scrollIntoView({ from: this.searchCursor.from(), to: this.searchCursor.to() }, 20);
                document.getElementById('searchCurrentMatch').textContent = `${this.searchResults.length}/${this.searchResults.length}`;
            }
        }
    },

    /**
     * Replace current match
     */
    searchReplace() {
        if (!this.searchCursor || this.searchResults.length === 0) {
            return;
        }

        const replacement = document.getElementById('searchReplace').value;

        // Get the current selection
        const selection = this.editor.getSelection();
        if (!selection) {
            // No selection, find next match first
            this.searchNext();
            return;
        }

        // Replace the current selection
        this.editor.replaceSelection(replacement);

        // Re-run search to update highlights
        setTimeout(() => this.performSearch(), 50);
    },

    /**
     * Replace all matches
     */
    searchReplaceAll() {
        const query = document.getElementById('searchQuery').value;
        const replacement = document.getElementById('searchReplace').value;
        const caseSensitive = document.getElementById('searchCaseSensitive').checked;
        const useRegex = document.getElementById('searchRegex').checked;

        if (!this.editor || !query) return;

        try {
            let searchQuery = query;
            if (!useRegex) {
                searchQuery = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
            }

            // Use the internal CodeMirror replaceAll approach
            const cursor = this.editor.getSearchCursor(searchQuery, null, {
                caseFold: !caseSensitive
            });

            let count = 0;
            // Start from the beginning
            cursor.findNext();
            // Need to find all from start
            const startCursor = this.editor.getSearchCursor(searchQuery, null, {
                caseFold: !caseSensitive
            });

            // Collect all match positions first
            const positions = [];
            while (startCursor.findNext()) {
                positions.push({ from: startCursor.from(), to: startCursor.to() });
            }

            // Replace in reverse order to preserve positions
            for (let i = positions.length - 1; i >= 0; i--) {
                this.editor.replaceRange(replacement, positions[i].from, positions[i].to);
                count++;
            }

            this.clearSearchHighlights();
            document.getElementById('searchMatchCount').textContent = `0 matches (replaced ${count})`;
            document.getElementById('searchCurrentMatch').textContent = '';

            // Show status
            this.showStatus(`Replaced ${count} occurrence${count !== 1 ? 's' : ''}`, 'success');
            this.autoHideStatus(2000);

        } catch (e) {
            console.error('Replace all error:', e);
        }
    },

    /**
     * Get the current match index (1-based)
     */
    getCurrentMatchIndex() {
        if (!this.searchCursor || !this.searchResults || this.searchResults.length === 0) return 0;

        const cursorPos = this.editor.getCursor('start');
        for (let i = 0; i < this.searchResults.length; i++) {
            const match = this.searchResults[i];
            if (match.from.line === cursorPos.line && match.from.ch === cursorPos.ch) {
                return i + 1;
            }
        }
        return 0;
    },

    // ========================================================================
    // EVENT LISTENERS
    // ========================================================================

    setupEventListeners() {
        // ---- Toolbar Buttons ----
        document.getElementById('undoBtn')?.addEventListener('click', () => this.undo());
        document.getElementById('redoBtn')?.addEventListener('click', () => this.redo());
        document.getElementById('boldBtn')?.addEventListener('click', () => this.insertBold());
        document.getElementById('italicBtn')?.addEventListener('click', () => this.insertItalic());

        // Symbol picker toggle
        document.getElementById('symbolBtn')?.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleSymbolPicker();
        });
        document.getElementById('symbolPickerClose')?.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleSymbolPicker();
        });

        // Symbol item click
        document.querySelectorAll('.symbol-item').forEach(btn => {
            btn.addEventListener('click', () => {
                const symbol = btn.textContent;
                this.insertSymbol(symbol);
                this.toggleSymbolPicker();
            });
        });

        // Close symbol picker when clicking outside
        document.addEventListener('click', (e) => {
            const picker = document.getElementById('symbolPicker');
            const symbolBtn = document.getElementById('symbolBtn');
            if (picker && picker.style.display === 'block') {
                if (!picker.contains(e.target) && e.target !== symbolBtn && !symbolBtn?.contains(e.target)) {
                    picker.style.display = 'none';
                }
            }
        });

        // Search & Replace
        document.getElementById('searchBtn')?.addEventListener('click', () => this.openSearch());

        // Search modal events
        document.getElementById('searchModalClose')?.addEventListener('click', () => this.closeSearch());
        document.getElementById('searchModalOverlay')?.addEventListener('click', (e) => {
            if (e.target === e.currentTarget) this.closeSearch();
        });
        document.getElementById('searchQuery')?.addEventListener('input', () => this.performSearch());
        document.getElementById('searchQuery')?.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                if (e.shiftKey) this.searchPrev();
                else this.searchNext();
            }
        });
        document.getElementById('searchCaseSensitive')?.addEventListener('change', () => this.performSearch());
        document.getElementById('searchRegex')?.addEventListener('change', () => this.performSearch());
        document.getElementById('searchNextBtn')?.addEventListener('click', () => this.searchNext());
        document.getElementById('searchPrevBtn')?.addEventListener('click', () => this.searchPrev());
        document.getElementById('searchReplaceBtn')?.addEventListener('click', () => this.searchReplace());
        document.getElementById('searchReplaceAllBtn')?.addEventListener('click', () => this.searchReplaceAll());

        // ---- Download button ----
        document.getElementById('downloadBtn')?.addEventListener('click', () => this.download());

        // ---- Reset button ----
        document.getElementById('resetBtn')?.addEventListener('click', () => this.resetToDefault());

        // ---- Template selector ----
        document.getElementById('templateSelect')?.addEventListener('change', (e) => {
            if (confirm('Switching templates will overwrite your current changes. Are you sure?')) {
                this.loadTemplateFromApi(e.target.value);
            } else {
                e.target.value = this.activeTemplate;
            }
        });

        // ---- Snippets button ----
        document.getElementById('snippetsBtn')?.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleSnippets();
        });

        // ---- Snippet item clicks ----
        document.querySelectorAll('.snippet-item').forEach(item => {
            item.addEventListener('click', () => {
                const snippetKey = item.dataset.snippet;
                if (snippetKey) this.insertSnippet(snippetKey);
            });
        });

        // Close snippets panel when clicking outside
        document.addEventListener('click', (e) => {
            const panel = document.getElementById('snippetsPanel');
            const btn = document.getElementById('snippetsBtn');
            if (panel && panel.style.display === 'block') {
                if (!panel.contains(e.target) && e.target !== btn && !btn?.contains(e.target)) {
                    panel.style.display = 'none';
                }
            }
        });

        // ---- Compile button ----
        document.getElementById('compileBtn')?.addEventListener('click', () => this.compile());

        // ---- Shortcuts button ----
        document.getElementById('shortcutsBtn')?.addEventListener('click', () => this.openShortcutsModal());

        // ---- AI Generate button ----
        document.getElementById('aiGenerateBtn')?.addEventListener('click', () => this.openAiModal());

        // ---- Shortcuts Modal events ----
        document.getElementById('shortcutsModalClose')?.addEventListener('click', () => this.closeShortcutsModal());
        document.getElementById('shortcutsModalOverlay')?.addEventListener('click', (e) => {
            if (e.target === e.currentTarget) this.closeShortcutsModal();
        });

        // ---- AI Modal events ----
        document.getElementById('aiModalClose')?.addEventListener('click', () => this.closeAiModal());
        document.getElementById('aiModalCancel')?.addEventListener('click', () => this.closeAiModal());
        document.getElementById('aiModalGenerate')?.addEventListener('click', () => this.generateWithAi());
        document.getElementById('aiModalOverlay')?.addEventListener('click', (e) => {
            if (e.target === e.currentTarget) this.closeAiModal();
        });

        // ---- Word wrap toggle ----
        document.getElementById('wrapToggle')?.addEventListener('change', (e) => {
            if (this.editor) this.editor.setOption('lineWrapping', e.target.checked);
        });

        // ---- Line numbers toggle ----
        document.getElementById('lineNumToggle')?.addEventListener('change', (e) => {
            if (this.editor) this.editor.setOption('lineNumbers', e.target.checked);
        });

        // ---- Full-screen toggle ----
        document.getElementById('fullscreenBtn')?.addEventListener('click', () => this.toggleFullscreen());

        // ---- Zoom controls ----
        document.getElementById('zoomInBtn')?.addEventListener('click', () => this.zoomIn());
        document.getElementById('zoomOutBtn')?.addEventListener('click', () => this.zoomOut());

        // ---- PDF page navigation ----
        document.getElementById('prevPageBtn')?.addEventListener('click', () => this.prevPage());
        document.getElementById('nextPageBtn')?.addEventListener('click', () => this.nextPage());

        // ---- Resize handle for split pane ----
        this.setupResizeHandle();

        // ---- Global keyboard shortcuts ----
        document.addEventListener('keydown', (e) => {
            // Search modal shortcuts
            if (document.getElementById('searchModalOverlay')?.style.display === 'flex') {
                if (e.key === 'Escape') {
                    this.closeSearch();
                    return;
                }
            }
            // Shortcuts modal shortcuts
            if (document.getElementById('shortcutsModalOverlay')?.style.display === 'flex') {
                if (e.key === 'Escape') {
                    this.closeShortcutsModal();
                    return;
                }
            }
            // AI modal shortcuts
            if (document.getElementById('aiModalOverlay')?.style.display === 'flex') {
                if (e.key === 'Escape') {
                    this.closeAiModal();
                    return;
                }
            }
            // Full-screen toggle (F11)
            if (e.code === 'F11') {
                e.preventDefault();
                this.toggleFullscreen();
                return;
            }

            // Line numbers toggle (Ctrl+Shift+L)
            if ((e.key === 'L' || e.key === 'l') && e.ctrlKey && e.shiftKey) {
                e.preventDefault();
                const toggle = document.getElementById('lineNumToggle');
                if (toggle) {
                    toggle.checked = !toggle.checked;
                    toggle.dispatchEvent(new Event('change'));
                }
                return;
            }

            // Shortcuts modal shortcut (use e.code for layout-independent key detection)
            if (e.code === 'Slash' && e.ctrlKey && e.shiftKey) {
                e.preventDefault();
                this.openShortcutsModal();
                return;
            }

            // Editor shortcuts (when not in an input)
            if (e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
                if (e.key === 'Escape') {
                    if (this.editor) this.editor.focus();
                }
            }
        });
    },

    setupResizeHandle() {
        const handle = document.getElementById('resizeHandle');
        const editor = document.querySelector('.editor-pane');
        const preview = document.querySelector('.preview-pane');
        let isDragging = false;

        handle.addEventListener('mousedown', () => {
            isDragging = true;
            document.body.style.cursor = 'col-resize';
            document.body.style.userSelect = 'none';
        });

        document.addEventListener('mousemove', (e) => {
            if (!isDragging) return;
            const container = document.querySelector('.resume-editor');
            const rect = container.getBoundingClientRect();
            const percentage = ((e.clientX - rect.left) / rect.width) * 100;
            const clamped = Math.max(20, Math.min(80, percentage));
            editor.style.flex = `0 0 ${clamped}%`;
            preview.style.flex = `0 0 ${100 - clamped}%`;
            if (this.editor) this.editor.refresh();
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
        if (this.isCompiling || !this.editor) return;

        const source = this.editor.getValue();
        if (!source || source.trim().length < 10) {
            this.showStatus('Source too short', 'error');
            this.autoHideStatus(3000);
            return;
        }

        this.isCompiling = true;
        this.showStatus('Compiling...', 'compiling');
        const downloadBtn = document.getElementById('downloadBtn');
        if (downloadBtn) downloadBtn.disabled = true;

        try {
            const response = await fetch('/api/latex/build', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ latex_source: source })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => null);
                throw new Error(errorData?.error || `Compilation failed (${response.status})`);
            }

            const pdfBlob = await response.blob();

            if (pdfBlob.size < 100) {
                throw new Error('Generated PDF is too small — compilation likely failed');
            }

            // Revoke old URL
            if (this.latestPdfUrl) {
                URL.revokeObjectURL(this.latestPdfUrl);
            }

            this.latestPdfUrl = URL.createObjectURL(pdfBlob);
            await this.loadPdf(this.latestPdfUrl);

            this.showStatus('Compiled successfully ✓', 'success');
            this.autoHideStatus(2500);
            if (downloadBtn) downloadBtn.disabled = false;

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
    // PDF RENDERING (with fixed zoom)
    // ========================================================================

    async loadPdf(url) {
        try {
            this.pdfDoc = await pdfjsLib.getDocument(url).promise;

            document.getElementById('previewPlaceholder').style.display = 'none';
            document.getElementById('previewError').style.display = 'none';
            document.getElementById('pdfRenderArea').style.display = 'block';

            document.getElementById('pageInfo').textContent = `1 / ${this.pdfDoc.numPages}`;
            document.getElementById('prevPageBtn').disabled = true;
            document.getElementById('nextPageBtn').disabled = this.pdfDoc.numPages <= 1;

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
            // Base scale of 1.5 gives a good readable size
            const scale = this.zoomLevel * 1.5;
            const viewport = page.getViewport({ scale });

            // Set canvas dimensions to match the viewport at this zoom level
            canvas.height = viewport.height;
            canvas.width = viewport.width;

            // Remove any fixed width/height constraints on the canvas wrapper
            canvas.style.width = viewport.width + 'px';
            canvas.style.height = viewport.height + 'px';

            // Render the page
            const renderContext = {
                canvasContext: context,
                viewport: viewport
            };

            // Cancel any in-progress render
            if (this._renderTask) {
                try { this._renderTask.cancel(); } catch(e) {}
            }

            this._renderTask = page.render(renderContext);
            await this._renderTask.promise;

            // Update page info
            document.getElementById('pageInfo').textContent = `${pageNum} / ${this.pdfDoc.numPages}`;
            document.getElementById('prevPageBtn').disabled = pageNum <= 1;
            document.getElementById('nextPageBtn').disabled = pageNum >= this.pdfDoc.numPages;
            document.getElementById('zoomLevel').textContent = `${Math.round(this.zoomLevel * 100)}%`;

        } catch (error) {
            if (error.name !== 'RenderingCancelledException') {
                console.error('Page render error:', error);
            }
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
        const oldZoom = this.zoomLevel;
        this.zoomLevel = Math.min(this.MAX_ZOOM, +(this.zoomLevel + this.ZOOM_STEP).toFixed(1));
        if (this.zoomLevel !== oldZoom && this.pdfDoc) {
            this.renderPage(this.currentPage);
        }
    },

    zoomOut() {
        const oldZoom = this.zoomLevel;
        this.zoomLevel = Math.max(this.MIN_ZOOM, +(this.zoomLevel - this.ZOOM_STEP).toFixed(1));
        if (this.zoomLevel !== oldZoom && this.pdfDoc) {
            this.renderPage(this.currentPage);
        }
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
    // RESET TO DEFAULT
    // ========================================================================

    async resetToDefault() {
        try {
            const template = this.activeTemplate || 'jake';
            this.showStatus('Resetting to default...', 'pending');
            this.loadTemplateFromApi(template);
        } catch (e) {
            console.error('Reset failed:', e);
        }
    },

    // ========================================================================
    // KEYBOARD SHORTCUTS MODAL
    // ========================================================================

    openShortcutsModal() {
        document.getElementById('shortcutsModalOverlay').style.display = 'flex';
        document.body.style.overflow = 'hidden';
    },

    closeShortcutsModal() {
        document.getElementById('shortcutsModalOverlay').style.display = 'none';
        document.body.style.overflow = '';
    },

    // ========================================================================
    // FULL-SCREEN MODE
    // ========================================================================

    toggleFullscreen() {
        const body = document.body;
        const btn = document.getElementById('fullscreenBtn');
        const isFullscreen = body.classList.toggle('resume-fullscreen');

        // Update button icon
        if (btn) {
            const icon = btn.querySelector('.material-symbols-outlined');
            if (icon) {
                icon.textContent = isFullscreen ? 'fullscreen_exit' : 'fullscreen';
            }
            btn.title = isFullscreen ? 'Exit full-screen editor (F11)' : 'Toggle full-screen editor (F11)';
        }

        // Refresh CodeMirror to fill new dimensions
        if (this.editor) {
            setTimeout(() => this.editor.refresh(), 100);
        }

        // Show status
        this.showStatus(isFullscreen ? 'Full-screen editor mode' : 'Split-pane mode', 'pending');
        this.autoHideStatus(1500);
    },

    // ========================================================================
    // AI GENERATE
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

        document.getElementById('aiModalGenerate').style.display = 'none';
        this.showAiStatus('Generating your resume with AI...', 'loading');

        try {
            const response = await fetch('/api/latex/generate', {
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

            this.editor.setValue(data.latex_source);
            this.closeAiModal();
            this.showStatus('AI generated! Compiling...', 'pending');
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
        statusEl.className = 'ai-status';
        if (type) statusEl.classList.add(type);
    },

    // ========================================================================
    // UI HELPERS
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
