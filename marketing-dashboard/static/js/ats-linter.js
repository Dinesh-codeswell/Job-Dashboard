/**
 * ATS Resume Linter & Action Verb Auditor (100% Deterministic, 0-AI)
 * Inspired by Resume-Matcher and OpenResume.
 * Analyzes LaTeX resume code against ATS rules and job descriptions.
 */
const ATSLinter = {
    // Curated dictionaries of strong action verbs
    STRONG_VERBS: new Set([
        // Leadership & Ownership
        'accelerated', 'achieved', 'administered', 'advocated', 'aligned', 'allocated',
        'amplified', 'apppointed', 'arbitrated', 'architected', 'assembled', 'assigned',
        'attained', 'authorized', 'boosted', 'budgeted', 'built', 'cataloged', 'centralized',
        'championed', 'chaired', 'co-founded', 'coached', 'collaborated', 'commanded',
        'commissioned', 'consolidated', 'constructed', 'contracted', 'controlled', 'coordinated',
        'cultivated', 'delegated', 'delivered', 'deployed', 'designated', 'designed', 'directed',
        'discovered', 'dispatched', 'diversified', 'documented', 'doubled', 'drove',
        // Engineering & Technical
        'automated', 'built', 'calibrated', 'coded', 'composed', 'computed', 'configured',
        'containerized', 'converted', 'debugged', 'deciphered', 'decreased', 'defined',
        'derived', 'developed', 'devised', 'diagnosed', 'drafted', 'eliminated', 'engineered',
        'enhanced', 'established', 'evaluated', 'executed', 'expanded', 'expedited',
        'fabricated', 'facilitated', 'fixed', 'formulated', 'founded', 'generated',
        'governed', 'guided', 'halved', 'harnessed', 'headed', 'identified', 'implemented',
        'improved', 'improvised', 'indexed', 'initiated', 'innovated', 'inspected', 'installed',
        'instituted', 'integrated', 'intensified', 'introduced', 'invented', 'investigated',
        'launched', 'led', 'leveraged', 'maintained', 'managed', 'mapped', 'masterminded',
        'maximized', 'measured', 'mediated', 'mentored', 'migrated', 'minimized', 'mobilized',
        'modeled', 'modernized', 'monitored', 'motivated', 'navigated', 'negotiated',
        'optimized', 'orchestrated', 'organized', 'originated', 'outperformed', 'overhauled',
        'oversaw', 'partnered', 'performed', 'piloted', 'pioneered', 'planned', 'prepared',
        'programmed', 'promoted', 'proposed', 'provided', 'published', 're-engineered',
        'rebuilt', 'reconfigured', 'rectified', 'redesigned', 'reduced', 'refactored',
        'refined', 'reformed', 'regulated', 'remodeled', 'reorganized', 'replaced',
        'researched', 'resolved', 'restructured', 'revamped', 'revised', 'revitalized',
        'scaled', 'scheduled', 'secured', 'selected', 'simplified', 'simulated', 'slashed',
        'solicited', 'solved', 'spearheaded', 'specialized', 'standardized', 'steered',
        'streamlined', 'strengthened', 'structured', 'supervised', 'synthesized', 'systematized',
        'targeted', 'tested', 'trained', 'transformed', 'transitioned', 'translated',
        'tripled', 'troubleshot', 'unified', 'upgraded', 'validated', 'visualized', 'yielded'
    ]),

    // Weak / Passive phrases to flag
    WEAK_PATTERNS: [
        { pattern: /\b(responsible for|duties included|tasked with)\b/i, label: 'Responsible for / Duties included', fix: 'Replace with direct action (e.g., "Led", "Engineered", "Managed")' },
        { pattern: /\b(worked on|worked with|helped with|helped to)\b/i, label: 'Worked on / Helped with', fix: 'Replace with specific contribution (e.g., "Co-developed", "Collaborated on", "Implemented")' },
        { pattern: /\b(assisted in|assisted with)\b/i, label: 'Assisted in / with', fix: 'Specify your exact role (e.g., "Supported", "Facilitated", "Contributed to")' },
        { pattern: /\b(handled)\b/i, label: 'Handled', fix: 'Replace with more authoritative verb (e.g., "Administered", "Directed", "Executed")' },
        { pattern: /\b(attempted|tried to)\b/i, label: 'Attempted / Tried to', fix: 'Focus directly on achieved outcomes' }
    ],

    // Common English Stopwords for keyword matching
    STOPWORDS: new Set([
        'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', 'aren\'t', 'as', 'at',
        'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by', 'can\'t', 'cannot', 'could',
        'couldn\'t', 'did', 'didn\'t', 'do', 'does', 'doesn\'t', 'doing', 'don\'t', 'down', 'during', 'each', 'few', 'for',
        'from', 'further', 'had', 'hadn\'t', 'has', 'hasn\'t', 'have', 'haven\'t', 'having', 'he', 'he\'d', 'he\'ll', 'he\'s',
        'her', 'here', 'here\'s', 'hers', 'herself', 'him', 'himself', 'his', 'how', 'how\'s', 'i', 'i\'d', 'i\'ll', 'i\'m',
        'i\'ve', 'if', 'in', 'into', 'is', 'isn\'t', 'it', 'it\'s', 'its', 'itself', 'let\'s', 'me', 'more', 'most', 'mustn\'t',
        'my', 'myself', 'no', 'nor', 'not', 'of', 'off', 'on', 'once', 'only', 'or', 'other', 'ought', 'our', 'ours', 'ourselves',
        'out', 'over', 'own', 'same', 'shan\'t', 'she', 'she\'d', 'she\'ll', 'she\'s', 'should', 'shouldn\'t', 'so', 'some',
        'such', 'than', 'that', 'that\'s', 'the', 'their', 'theirs', 'them', 'themselves', 'then', 'there', 'there\'s', 'these',
        'they', 'they\'d', 'they\'ll', 'they\'re', 'they\'ve', 'this', 'those', 'through', 'to', 'too', 'under', 'until', 'up',
        'very', 'was', 'wasn\'t', 'we', 'we\'d', 'we\'ll', 'we\'re', 'we\'ve', 'were', 'weren\'t', 'what', 'what\'s', 'when',
        'when\'s', 'where', 'where\'s', 'which', 'while', 'who', 'who\'s', 'whom', 'why', 'why\'s', 'with', 'won\'t', 'would',
        'wouldn\'t', 'you', 'you\'d', 'you\'ll', 'you\'re', 'you\'ve', 'your', 'yours', 'yourself', 'yourselves',
        'will', 'also', 'etc', 'via', 'using', 'per', 'within', 'across', 'well', 'must', 'plus'
    ]),

    /**
     * Audit full LaTeX resume source
     */
    audit(latexSource, targetJobDesc = '') {
        const bullets = this.extractBullets(latexSource);
        const contacts = this.auditContacts(latexSource);
        const sections = this.auditSections(latexSource);
        const verbsAudit = this.auditActionVerbs(bullets);
        const metricsAudit = this.auditMetrics(bullets);
        const formattingAudit = this.auditFormatting(latexSource, bullets);
        const keywordMatch = targetJobDesc ? this.matchKeywords(latexSource, targetJobDesc) : null;

        // Calculate score (0-100)
        let score = 0;
        // 1. Contact Info: 15 pts
        score += contacts.score;
        // 2. Section Completeness: 20 pts
        score += sections.score;
        // 3. Action Verbs: 25 pts
        score += verbsAudit.score;
        // 4. Quantifiable Metrics: 25 pts
        score += metricsAudit.score;
        // 5. Formatting & Length: 15 pts
        score += formattingAudit.score;

        return {
            overallScore: Math.min(100, Math.round(score)),
            contacts,
            sections,
            verbs: verbsAudit,
            metrics: metricsAudit,
            formatting: formattingAudit,
            keywordMatch
        };
    },

    /**
     * Extract raw bullet texts from LaTeX
     */
    extractBullets(latex) {
        const bullets = [];
        // Matches \resumeItem{...}, \resumeItemPlain{...}, or \item ...
        const lines = latex.split('\n');
        for (let i = 0; i < lines.length; i++) {
            const line = lines[i].trim();
            if (line.startsWith('%')) continue; // Ignore LaTeX comments

            // Match \resumeItem{text}
            const resumeItemMatch = line.match(/\\resumeItem(?:Plain)?\{([^}]+)/);
            if (resumeItemMatch) {
                bullets.push({ lineNum: i + 1, text: this.cleanLatexText(resumeItemMatch[1]) });
                continue;
            }

            // Match generic \item text
            if (line.startsWith('\\item') && !line.includes('\\begin') && !line.includes('\\end')) {
                const text = line.replace(/^\\item(\[[^\]]*\])?\s*/, '');
                if (text.length > 5 && !text.startsWith('\\small') && !text.startsWith('\\textbf')) {
                    bullets.push({ lineNum: i + 1, text: this.cleanLatexText(text) });
                }
            }
        }
        return bullets;
    },

    cleanLatexText(str) {
        return str
            .replace(/\\[a-zA-Z]+\*?(\{.*?\})?/g, ' ')
            .replace(/[{}$%_&#\\]/g, ' ')
            .replace(/\s+/g, ' ')
            .trim();
    },

    auditContacts(latex) {
        let score = 0;
        const checks = {
            email: /\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b/.test(latex),
            phone: /(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}/.test(latex),
            linkedin: /linkedin\.com\/(?:in|company)\/[a-zA-Z0-9-_]+/i.test(latex),
            github: /github\.com\/[a-zA-Z0-9-_]+/i.test(latex)
        };

        if (checks.email) score += 5;
        if (checks.phone) score += 4;
        if (checks.linkedin) score += 3;
        if (checks.github) score += 3;

        return { score, checks };
    },

    auditSections(latex) {
        let score = 0;
        const lower = latex.toLowerCase();
        const checks = {
            experience: /\\section\{(?:experience|work\s+experience|professional\s+experience)\}/i.test(latex) || lower.includes('experience'),
            education: /\\section\{education\}/i.test(latex) || lower.includes('education'),
            skills: /\\section\{(?:technical\s+skills|skills|programming\s+skills)\}/i.test(latex) || lower.includes('skills'),
            projects: /\\section\{(?:projects|technical\s+projects|academic\s+projects)\}/i.test(latex) || lower.includes('projects')
        };

        if (checks.experience) score += 7;
        if (checks.education) score += 5;
        if (checks.skills) score += 4;
        if (checks.projects) score += 4;

        return { score, checks };
    },

    auditActionVerbs(bullets) {
        if (!bullets.length) return { score: 10, total: 0, strongCount: 0, weakCount: 0, items: [] };

        let strongCount = 0;
        let weakCount = 0;
        const items = [];

        for (const b of bullets) {
            const firstWord = (b.text.split(' ')[0] || '').toLowerCase().replace(/[^a-z]/g, '');
            let isStrong = this.STRONG_VERBS.has(firstWord);

            let weakMatch = null;
            for (const w of this.WEAK_PATTERNS) {
                if (w.pattern.test(b.text)) {
                    weakMatch = w;
                    break;
                }
            }

            if (weakMatch) {
                weakCount++;
                items.push({ lineNum: b.lineNum, text: b.text, status: 'weak', label: weakMatch.label, fix: weakMatch.fix });
            } else if (isStrong) {
                strongCount++;
                items.push({ lineNum: b.lineNum, text: b.text, status: 'strong', verb: firstWord });
            } else {
                items.push({ lineNum: b.lineNum, text: b.text, status: 'neutral', firstWord });
            }
        }

        const strongRatio = bullets.length > 0 ? (strongCount / bullets.length) : 0;
        // Max 25 points based on percentage of bullets with strong verbs minus penalties for weak
        let score = Math.round(strongRatio * 25);
        score = Math.max(0, score - (weakCount * 3));

        return { score, total: bullets.length, strongCount, weakCount, items };
    },

    auditMetrics(bullets) {
        if (!bullets.length) return { score: 10, count: 0, bulletsWithoutMetrics: [] };

        // Regex for numbers, percentages, dollar values, multipliers, times
        const metricRegex = /\b(\d+[\%xXkK]?|\$\d+|\d+\+|\d+ms|\d+tb|\d+gb|\d+x)\b/i;
        let count = 0;
        const bulletsWithoutMetrics = [];

        for (const b of bullets) {
            if (metricRegex.test(b.text)) {
                count++;
            } else {
                bulletsWithoutMetrics.push(b);
            }
        }

        const ratio = bullets.length > 0 ? (count / bullets.length) : 0;
        // Target is at least 50% of bullets having a metric
        const score = Math.min(25, Math.round((ratio / 0.5) * 25));

        return { score, count, total: bullets.length, bulletsWithoutMetrics };
    },

    auditFormatting(latex, bullets) {
        let score = 15;
        const issues = [];

        // Check unescaped special characters
        const unescapedChars = latex.match(/(?<!\\)[%$#_&](?![a-zA-Z0-9_\\])/g);
        if (unescapedChars && unescapedChars.length > 2) {
            score -= 5;
            issues.push(`Found unescaped special characters (%, $, &, _, #)`);
        }

        // Check bullet length (ideal is between 8 and 35 words)
        let tooLong = 0;
        let tooShort = 0;
        for (const b of bullets) {
            const wordCount = b.text.split(/\s+/).length;
            if (wordCount > 40) tooLong++;
            if (wordCount < 6) tooShort++;
        }

        if (tooLong > 2) {
            score -= 3;
            issues.push(`${tooLong} bullet points are excessively long (> 40 words)`);
        }
        if (tooShort > 2) {
            score -= 2;
            issues.push(`${tooShort} bullet points are too short (< 6 words)`);
        }

        return { score: Math.max(0, score), issues };
    },

    /**
     * Deterministic keyword matching between resume and a target job description
     */
    matchKeywords(latexSource, jobDescription) {
        const cleanResume = this.cleanLatexText(latexSource).toLowerCase();
        
        // Extract technical and skill terms from job description (1-word and 2-word tokens)
        const rawTokens = jobDescription
            .toLowerCase()
            .replace(/[^a-z0-9+#.\s]/g, ' ')
            .split(/\s+/)
            .filter(t => t.length > 2 && !this.STOPWORDS.has(t));

        // Frequency map of keywords
        const freqMap = {};
        for (const t of rawTokens) {
            freqMap[t] = (freqMap[t] || 0) + 1;
        }

        // Top 30 keywords sorted by frequency
        const sortedKeywords = Object.keys(freqMap)
            .sort((a, b) => freqMap[b] - freqMap[a])
            .slice(0, 30);

        const matched = [];
        const missing = [];

        for (const kw of sortedKeywords) {
            // Check word boundary or presence
            const regex = new RegExp(`\\b${kw.replace(/[.+*?^${}()|[\]\\]/g, '\\$&')}\\b`, 'i');
            if (regex.test(cleanResume)) {
                matched.push(kw);
            } else {
                missing.push(kw);
            }
        }

        const matchPercent = sortedKeywords.length > 0 
            ? Math.round((matched.length / sortedKeywords.length) * 100) 
            : 0;

        return {
            matchPercent,
            matched,
            missing,
            totalKeywords: sortedKeywords.length
        };
    }
};

if (typeof module !== 'undefined' && module.exports) {
    module.exports = ATSLinter;
}
