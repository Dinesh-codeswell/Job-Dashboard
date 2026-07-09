"""
🎯 Non-Tech Roles Dashboard - Marketing, Accounts, UI/UX, Entrepreneurial Roles
Reads job listings directly from Notion database and displays them
with the SayBriefly design system.
"""
import os
import sys
import re
import json
import uuid
import tempfile
import logging
import subprocess
from pathlib import Path
from datetime import datetime, timedelta, timezone
from flask import Flask, render_template, jsonify, request, Response
from flask_cors import CORS
from dotenv import load_dotenv

# Try to import requests for online LaTeX compilation fallback
try:
    import requests as requests_lib
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Load environment variables - look in project root AND current directory
# The .env file with API keys is at the project root level
load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')
load_dotenv()  # Also check CWD as fallback

# Create Flask app
app = Flask(__name__)
CORS(app)

# Configuration
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemma-4-31b-it:free")

# Prioritized list of free OpenRouter models based on user rankings/scores
FALLBACK_MODELS = [
    "google/gemma-4-31b-it:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "openai/gpt-oss-120b:free",
    "google/gemma-4-26b-a4b-it:free",
    "qwen/qwen3-coder:free",
    "openai/gpt-oss-20b:free",
    "nvidia/nemotron-3-nano-30b-a3b:free",
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
    "qwen/qwen3-next-80b-a3b-instruct:free",
    "nvidia/nemotron-nano-12b-v2-vl:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "nvidia/nemotron-nano-9b-v2:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "liquid/lfm-2.5-1.2b-thinking:free",
    "liquid/lfm-2.5-1.2b-instruct:free",
    "nousresearch/hermes-3-llama-3.1-405b:free",
    "openrouter/free"
]


# Cache for jobs (to avoid hitting Notion API on every request)
_jobs_cache = []
_jobs_cache_timestamp = None
CACHE_DURATION = 120  # seconds

# ============================================================================
# ROLES CONFIGURATION
# ============================================================================

# Role domain keywords for filtering
ROLE_DOMAINS = {
    "All": [],
    "Marketing": ["marketing", "brand", "growth", "social media", "content", "campaign",
                   "demand generation", "pr manager", "communications", "seo"],
    "Accounts": ["account manager", "account executive", "key account", "client partner",
                  "client services", "account director", "customer success", "business development"],
    "UI/UX": ["ui designer", "ux designer", "ui/ux", "product designer", "ux researcher",
               "interaction designer", "visual designer", "ux lead", "ux architect", "user experience"],
    "Founders Office": ["founder's office", "founders office", "chief of staff",
                         "entrepreneur in residence", "eir"],
}


def categorize_role(role_title: str) -> str:
    """Determine which domain a role belongs to based on keywords."""
    if not role_title:
        return "Other"
    title_lower = role_title.lower()

    # Check Founder's Office first (high priority)
    founders_keywords = ["founder's office", "founders office", "chief of staff",
                         "entrepreneur in residence", "entrepreneur-in-residence", "eir"]
    for kw in founders_keywords:
        if kw in title_lower:
            return "Founders Office"

    # Check Marketing
    marketing_keywords = ["marketing", "brand", "growth", "social media", "content marketing",
                          "campaign", "demand generation", "pr", "communications", "seo",
                          "digital marketing", "product marketing", "performance marketing"]
    for kw in marketing_keywords:
        if kw in title_lower:
            return "Marketing"

    # Check UI/UX
    ux_keywords = ["ui designer", "ux designer", "ui/ux", "ui ux", "product designer",
                   "ux researcher", "interaction designer", "visual designer", "ux lead",
                   "ux architect", "user experience", "user interface"]
    for kw in ux_keywords:
        if kw in title_lower:
            return "UI/UX"

    # Check Accounts
    accounts_keywords = ["account manager", "account executive", "key account",
                         "client partner", "client services", "account director",
                         "customer success", "client relationship", "account lead",
                         "business development manager", "strategic account"]
    for kw in accounts_keywords:
        if kw in title_lower:
            return "Accounts"

    return "Other"


# ============================================================================
# NOTION API READER
# ============================================================================

def _notion_request(method, endpoint, body=None):
    """Make a direct HTTP request to the Notion API (bypasses library version issues)."""
    import urllib.request, urllib.error, json

    url = f"https://api.notion.com/v1/{endpoint}"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    data = json.dumps(body).encode("utf-8") if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        raise Exception(f"Notion API HTTP {e.code}: {error_body}")


def fetch_jobs_from_notion() -> list:
    """Fetch all jobs from the Notion database using direct HTTP requests."""
    if not NOTION_API_KEY or not NOTION_DATABASE_ID:
        print("Notion API key or database ID not configured")
        return []

    try:
        all_jobs = []
        has_more = True
        start_cursor = None

        while has_more:
            query_body = {"page_size": 100}
            if start_cursor:
                query_body["start_cursor"] = start_cursor

            response = _notion_request("POST", f"databases/{NOTION_DATABASE_ID}/query", query_body)
            has_more = response.get("has_more", False)
            start_cursor = response.get("next_cursor")

            for page in response.get("results", []):
                props = page.get("properties", {})

                # Extract Company (Title)
                company = ""
                company_prop = props.get("Company", {})
                if company_prop.get("type") == "title":
                    title_list = company_prop.get("title", [])
                    if title_list:
                        company = title_list[0].get("plain_text", "")

                # Extract Position (Rich text)
                role = ""
                position_prop = props.get("Position", {})
                if position_prop.get("type") == "rich_text":
                    rt_list = position_prop.get("rich_text", [])
                    if rt_list:
                        role = rt_list[0].get("plain_text", "")

                # Extract Location (Rich text)
                location = ""
                location_prop = props.get("Location", {})
                if location_prop.get("type") == "rich_text":
                    loc_list = location_prop.get("rich_text", [])
                    if loc_list:
                        location = loc_list[0].get("plain_text", "")

                # Extract Application Link (URL)
                job_url = ""
                url_prop = props.get("Application Link", {})
                if url_prop.get("type") == "url":
                    job_url = url_prop.get("url", "")

                # Extract Date Posted
                date_str = ""
                date_prop = props.get("Date Posted", {})
                if date_prop.get("type") == "date":
                    date_data = date_prop.get("date", {})
                    if date_data:
                        date_str = date_data.get("start", "")

                # Extract role domain
                domain = categorize_role(role)

                all_jobs.append({
                    "id": page.get("id", ""),
                    "company": company or "Unknown",
                    "role": role or "Unknown",
                    "location": location or "India",
                    "url": job_url or "",
                    "date_added": date_str or datetime.now().strftime("%Y-%m-%d"),
                    "domain": domain,
                    "created_time": page.get("created_time", ""),
                    "last_edited_time": page.get("last_edited_time", ""),
                })

        return all_jobs

    except ImportError:
        return []
    except Exception as e:
        print(f"Error fetching from Notion: {e}")
        return []


def get_jobs(force_refresh: bool = False) -> list:
    """Get jobs with caching."""
    global _jobs_cache, _jobs_cache_timestamp

    now = datetime.now()

    if (not force_refresh
        and _jobs_cache_timestamp
        and (now - _jobs_cache_timestamp).seconds < CACHE_DURATION
        and _jobs_cache):
        return _jobs_cache

    jobs = fetch_jobs_from_notion()

    # Sort by date_added (most recent first)
    jobs.sort(key=lambda j: j.get("date_added", ""), reverse=True)

    _jobs_cache = jobs
    _jobs_cache_timestamp = now

    return jobs


# ============================================================================
# FRONTEND ROUTES
# ============================================================================

@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('index.html')

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/api/jobs', methods=['GET'])
def api_jobs():
    """Get jobs with optional filtering and pagination."""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 30))
        domain = request.args.get('domain', '').strip()
        search = request.args.get('search', '').strip()
        force_refresh = request.args.get('refresh', '').lower() == 'true'

        jobs = get_jobs(force_refresh=force_refresh)

        # Apply domain filter
        if domain and domain != "All":
            domain_lower = domain.lower()
            jobs = [j for j in jobs if j.get("domain", "").lower() == domain_lower]

        # Apply search filter
        if search:
            search_lower = search.lower()
            jobs = [
                j for j in jobs
                if search_lower in j.get("role", "").lower()
                or search_lower in j.get("company", "").lower()
                or search_lower in j.get("location", "").lower()
            ]

        # Calculate pagination
        total = len(jobs)
        total_pages = max(1, (total + limit - 1) // limit) if total else 1
        start = (page - 1) * limit
        end = start + limit
        paginated_jobs = jobs[start:end] if start < total else []

        return jsonify({
            "success": True,
            "jobs": paginated_jobs,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": total_pages,
            }
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/stats', methods=['GET'])
def api_stats():
    """Get dashboard statistics."""
    try:
        jobs = get_jobs()

        total = len(jobs)
        domains = {}
        for job in jobs:
            d = job.get("domain", "Other")
            domains[d] = domains.get(d, 0) + 1

        companies = {}
        for job in jobs:
            c = job.get("company", "Unknown")
            companies[c] = companies.get(c, 0) + 1

        return jsonify({
            "success": True,
            "stats": {
                "total_jobs": total,
                "domains": dict(sorted(domains.items(), key=lambda x: x[1], reverse=True)),
                "companies": dict(sorted(companies.items(), key=lambda x: x[1], reverse=True)[:20]),
                "total_companies": len(companies),
            }
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/domains', methods=['GET'])
def api_domains():
    """Get list of available role domains."""
    return jsonify({
        "success": True,
        "domains": ["All", "Marketing", "Accounts", "UI/UX", "Founders Office"]
    })


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "source": "notion"})


@app.route('/api/refresh', methods=['POST'])
def api_refresh():
    """Force refresh the jobs cache from Notion."""
    try:
        jobs = get_jobs(force_refresh=True)
        return jsonify({
            "success": True,
            "message": f"Refreshed {len(jobs)} jobs from Notion",
            "count": len(jobs)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/debug', methods=['GET'])
def api_debug():
    """Diagnostic endpoint to check Notion configuration."""
    result = {
        "env_vars_set": {
            "NOTION_API_KEY": bool(NOTION_API_KEY),
            "NOTION_DATABASE_ID": bool(NOTION_DATABASE_ID),
        },
        "api_key_prefix": NOTION_API_KEY[:10] + "..." if NOTION_API_KEY else "NOT SET",
        "database_id": NOTION_DATABASE_ID or "NOT SET",
        "notion_connection": False,
        "notion_error": None,
    }

    if NOTION_API_KEY and NOTION_DATABASE_ID:
        try:
            # Try to retrieve database info
            db_info = _notion_request("GET", f"databases/{NOTION_DATABASE_ID}")
            title = db_info.get("title", [{}])
            db_title = title[0].get("plain_text", "Untitled") if title else "Untitled"
            props = db_info.get("properties", {})
            result["notion_connection"] = True
            result["database_title"] = db_title
            result["database_properties"] = list(props.keys())

            # Try a query
            test_query = _notion_request("POST", f"databases/{NOTION_DATABASE_ID}/query", {"page_size": 5})
            result["sample_count"] = len(test_query.get("results", []))
            result["has_more"] = test_query.get("has_more", False)

        except ImportError as e:
            result["notion_error"] = f"notion_client not installed: {e}"
        except Exception as e:
            result["notion_error"] = str(e)[:200]
    else:
        result["notion_error"] = "Missing environment variables"

    return jsonify(result)


# ============================================================================
# RESUME - LaTeX Editor
# ============================================================================

# Default LaTeX source (Jake's Resume template with placeholder text)
DEFAULT_LATEX_SOURCE = Path(__file__).parent.parent / "Latex resume" / "resume-jake" / "resume.tex"
if DEFAULT_LATEX_SOURCE.exists():
    with open(DEFAULT_LATEX_SOURCE, "r") as f:
        _default_resume_source = f.read()
    _default_resume_source = r"""\documentclass[letterpaper,11pt]{article}

\usepackage{latexsym}
\usepackage[empty]{fullpage}
\usepackage{titlesec}
\usepackage{marvosym}
\usepackage[usenames,dvipsnames]{color}
\usepackage{verbatim}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{fancyhdr}
\usepackage[english]{babel}
\usepackage{tabularx}
\input{glyphtounicode}


%----------FONT OPTIONS----------
% sans-serif
% \usepackage[sfdefault]{FiraSans}
% \usepackage[sfdefault]{roboto}
% \usepackage[sfdefault]{noto-sans}
% \usepackage[default]{sourcesanspro}

% serif
% \usepackage{CormorantGaramond}
% \usepackage{charter}


\pagestyle{fancy}
\fancyhf{} % clear all header and footer fields
\fancyfoot{}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}

% Adjust margins
\addtolength{\oddsidemargin}{-0.5in}
\addtolength{\evensidemargin}{-0.5in}
\addtolength{\textwidth}{1in}
\addtolength{\topmargin}{-.5in}
\addtolength{\textheight}{1.0in}

\urlstyle{same}

\raggedbottom
\raggedright
\setlength{\tabcolsep}{0in}

% Sections formatting
\titleformat{\section}{
  \vspace{-4pt}\scshape\raggedright\large
}{}{0em}{}[\color{black}\titlerule \vspace{-5pt}]

% Ensure that generate pdf is machine readable/ATS parsable
\pdfgentounicode=1

%-------------------------
% Custom commands
\newcommand{\resumeItem}[1]{
  \item\small{
    {#1 \vspace{-2pt}}
  }
}

\newcommand{\resumeSubheading}[4]{
  \vspace{-2pt}\item
    \begin{tabular*}{0.97\textwidth}[t]{l@{\extracolsep{\fill}}r}
      \textbf{#1} & #2 \\
      \textit{\small#3} & \textit{\small #4} \\
    \end{tabular*}\vspace{-7pt}
}

\newcommand{\resumeSubSubheading}[2]{
    \item
    \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}
      \textit{\small#1} & \textit{\small #2} \\
    \end{tabular*}\vspace{-7pt}
}

\newcommand{\resumeProjectHeading}[2]{
    \item
    \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}
      \small#1 & #2 \\
    \end{tabular*}\vspace{-7pt}
}

\newcommand{\resumeSubItem}[1]{\resumeItem{#1}\vspace{-4pt}}

\renewcommand\labelitemii{$\vcenter{\hbox{\tiny$\bullet$}}$}

\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=0.15in, label={}]}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}
\newcommand{\resumeItemListStart}{\begin{itemize}}
\newcommand{\resumeItemListEnd}{\end{itemize}\vspace{-5pt}}

%-------------------------------------------
%%%%%%  RESUME STARTS HERE  %%%%%%%%%%%%%%%%%%%%%%%%%%%%


\begin{document}

%----------HEADING----------
% \begin{tabular*}{\textwidth}{l@{\extracolsep{\fill}}r}
%   \textbf{\href{http://sourabhbajaj.com/}{\Large Sourabh Bajaj}} & Email : \href{mailto:sourabh@sourabhbajaj.com}{sourabh@sourabhbajaj.com}\\
%   \href{http://sourabhbajaj.com/}{http://www.sourabhbajaj.com} & Mobile : +1-123-456-7890 \\
% \end{tabular*}

\begin{center}
    \textbf{\Huge \scshape Jake Ryan} \\ \vspace{1pt}
    \small 123-456-7890 $|$ \href{mailto:x@x.com}{\underline{jake@su.edu}} $|$ 
    \href{https://linkedin.com/in/...}{\underline{linkedin.com/in/jake}} $|$
    \href{https://github.com/...}{\underline{github.com/jake}}
\end{center}


%-----------EDUCATION-----------
\section{Education}
  \resumeSubHeadingListStart
    \resumeSubheading
      {Southwestern University}{Georgetown, TX}
      {Bachelor of Arts in Computer Science, Minor in Business}{Aug. 2018 -- May 2021}
    \resumeSubheading
      {Blinn College}{Bryan, TX}
      {Associate's in Liberal Arts}{Aug. 2014 -- May 2018}
  \resumeSubHeadingListEnd


%-----------EXPERIENCE-----------
\section{Experience}
  \resumeSubHeadingListStart

    \resumeSubheading
      {Undergraduate Research Assistant}{June 2020 -- Present}
      {Texas A\&M University}{College Station, TX}
      \resumeItemListStart
        \resumeItem{Developed a REST API using FastAPI and PostgreSQL to store data from learning management systems}
        \resumeItem{Developed a full-stack web application using Flask, React, PostgreSQL and Docker to analyze GitHub data}
        \resumeItem{Explored ways to visualize GitHub collaboration in a classroom setting}
      \resumeItemListEnd
      
% -----------Multiple Positions Heading-----------
%    \resumeSubSubheading
%     {Software Engineer I}{Oct 2014 - Sep 2016}
%     \resumeItemListStart
%        \resumeItem{Apache Beam}
%          {Apache Beam is a unified model for defining both batch and streaming data-parallel processing pipelines}
%     \resumeItemListEnd
%    \resumeSubHeadingListEnd
%-------------------------------------------

    \resumeSubheading
      {Information Technology Support Specialist}{Sep. 2018 -- Present}
      {Southwestern University}{Georgetown, TX}
      \resumeItemListStart
        \resumeItem{Communicate with managers to set up campus computers used on campus}
        \resumeItem{Assess and troubleshoot computer problems brought by students, faculty and staff}
        \resumeItem{Maintain upkeep of computers, classroom equipment, and 200 printers across campus}
    \resumeItemListEnd

    \resumeSubheading
      {Artificial Intelligence Research Assistant}{May 2019 -- July 2019}
      {Southwestern University}{Georgetown, TX}
      \resumeItemListStart
        \resumeItem{Explored methods to generate video game dungeons based off of \emph{The Legend of Zelda}}
        \resumeItem{Developed a game in Java to test the generated dungeons}
        \resumeItem{Contributed 50K+ lines of code to an established codebase via Git}
        \resumeItem{Conducted  a human subject study to determine which video game dungeon generation technique is enjoyable}
        \resumeItem{Wrote an 8-page paper and gave multiple presentations on-campus}
        \resumeItem{Presented virtually to the World Conference on Computational Intelligence}
      \resumeItemListEnd

  \resumeSubHeadingListEnd


%-----------PROJECTS-----------
\section{Projects}
    \resumeSubHeadingListStart
      \resumeProjectHeading
          {\textbf{Gitlytics} $|$ \emph{Python, Flask, React, PostgreSQL, Docker}}{June 2020 -- Present}
          \resumeItemListStart
            \resumeItem{Developed a full-stack web application using with Flask serving a REST API with React as the frontend}
            \resumeItem{Implemented GitHub OAuth to get data from user’s repositories}
            \resumeItem{Visualized GitHub data to show collaboration}
            \resumeItem{Used Celery and Redis for asynchronous tasks}
          \resumeItemListEnd
      \resumeProjectHeading
          {\textbf{Simple Paintball} $|$ \emph{Spigot API, Java, Maven, TravisCI, Git}}{May 2018 -- May 2020}
          \resumeItemListStart
            \resumeItem{Developed a Minecraft server plugin to entertain kids during free time for a previous job}
            \resumeItem{Published plugin to websites gaining 2K+ downloads and an average 4.5/5-star review}
            \resumeItem{Implemented continuous delivery using TravisCI to build the plugin upon new a release}
            \resumeItem{Collaborated with Minecraft server administrators to suggest features and get feedback about the plugin}
          \resumeItemListEnd
    \resumeSubHeadingListEnd



%
%-----------PROGRAMMING SKILLS-----------
\section{Technical Skills}
 \begin{itemize}[leftmargin=0.15in, label={}]
    \small{\item{
     \textbf{Languages}{: Java, Python, C/C++, SQL (Postgres), JavaScript, HTML/CSS, R} \\
     \textbf{Frameworks}{: React, Node.js, Flask, JUnit, WordPress, Material-UI, FastAPI} \\
     \textbf{Developer Tools}{: Git, Docker, TravisCI, Google Cloud Platform, VS Code, Visual Studio, PyCharm, IntelliJ, Eclipse} \\
     \textbf{Libraries}{: pandas, NumPy, Matplotlib}
    }}
 \end{itemize}


%-------------------------------------------
\end{document}"""


def _find_pdflatex():
    """Try to find pdflatex executable in PATH or common locations."""
    # Check PATH first
    try:
        result = subprocess.run(["pdflatex", "--version"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return "pdflatex"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Common Windows install locations
    common_paths = [
        "C:\\Program Files\\MiKTeX\\miktex\\bin\\x64\\pdflatex.exe",
        "C:\\Program Files (x86)\\MiKTeX\\miktex\\bin\\pdflatex.exe",
        "C:\\Program Files\\MiKTeX\\texmfs\\install\\miktex\\bin\\x64\\pdflatex.exe",
        os.path.expanduser("~\\AppData\\Local\\Programs\\MiKTeX\\miktex\\bin\\x64\\pdflatex.exe"),
    ]
    for path in common_paths:
        if os.path.isfile(path):
            return path

    return None


def _configure_miktex():
    """Configure MiKTeX to auto-install missing packages."""
    pdflatex_path = _find_pdflatex()
    if not pdflatex_path:
        return

    miktex_dir = os.path.dirname(pdflatex_path)
    initexmf = os.path.join(miktex_dir, "initexmf.exe")
    if os.path.isfile(initexmf):
        try:
            subprocess.run(
                [initexmf, "--set-config-value", "[MPM]AutoInstall=1"],
                capture_output=True, timeout=30
            )
        except Exception:
            pass


# Run MiKTeX configuration once at import time
_configure_miktex()


def _compile_latex_local(latex_source, output_dir):
    """Compile LaTeX locally using pdflatex."""
    pdflatex_path = _find_pdflatex()
    if not pdflatex_path:
        return None, "pdflatex not found. Install MiKTeX or restart after installation."

    tex_path = os.path.join(output_dir, "resume.tex")
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(latex_source)

    try:
        _is_miktex = "miktex" in pdflatex_path.lower() if pdflatex_path else False

        base_cmd = [
            pdflatex_path,
            "-interaction=nonstopmode",
            "-halt-on-error",
            "-output-directory", output_dir,
            tex_path
        ]

        if _is_miktex:
            base_cmd.insert(-1, "--enable-installer")

        for i in range(2):
            timeout = 300 if i == 0 else 120
            try:
                subprocess.run(
                    base_cmd, capture_output=True, text=True, timeout=timeout, cwd=output_dir
                )
                pdf_path = os.path.join(output_dir, "resume.pdf")
                if os.path.isfile(pdf_path) and os.path.getsize(pdf_path) > 100:
                    return pdf_path, None
            except subprocess.TimeoutExpired:
                if i == 0:
                    continue
                return None, "LaTeX compilation timed out."

        pdf_path = os.path.join(output_dir, "resume.pdf")
        if os.path.isfile(pdf_path) and os.path.getsize(pdf_path) > 100:
            return pdf_path, None

        log_path = os.path.join(output_dir, "resume.log")
        error_msg = "LaTeX compilation failed. Check your syntax."
        if os.path.isfile(log_path):
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                log_content = f.read()
                errors = re.findall(r"! (.*?)\n", log_content, re.MULTILINE)
                if errors:
                    error_msg = "LaTeX error: " + errors[0][:300]
        return None, error_msg

    except Exception as e:
        return None, f"Compilation error: {str(e)}"


def _compile_latex_online(latex_source):
    """Compile LaTeX using texlive.net API."""
    if not REQUESTS_AVAILABLE:
        return None, "'requests' library not available."

    try:
        files = [
            ('filecontents[]', ('document.tex', latex_source, 'text/plain')),
            ('filename[]', (None, 'document.tex')),
        ]
        data = {
            'engine': 'pdflatex',
            'return': 'pdf'
        }

        response = requests_lib.post(
            "https://texlive.net/cgi-bin/latexcgi",
            files=files,
            data=data,
            timeout=120
        )

        if response.status_code == 200 and len(response.content) > 500:
            if response.content[:4] == b"%PDF":
                pdf_path = os.path.join(tempfile.gettempdir(), f"resume_{uuid.uuid4().hex}.pdf")
                with open(pdf_path, "wb") as f:
                    f.write(response.content)
                return pdf_path, None

        content_type = response.headers.get("content-type", "")
        if "html" in content_type.lower():
            return None, "Online compilation failed. Check your LaTeX syntax."
        return None, f"Online compilation failed: {response.text[:300]}"


    except requests_lib.exceptions.Timeout:
        return None, "Online compilation timed out."
    except requests_lib.exceptions.ConnectionError:
        return None, "Could not reach the online compiler."
    except Exception as e:
        return None, f"Online compilation error: {str(e)}"


@app.route('/resume')
def resume_editor():
    """Resume LaTeX editor page."""
    return render_template('resume.html')


@app.route('/api/resume/compile', methods=['POST'])
def api_resume_compile():
    """Compile LaTeX source to PDF and return it."""
    try:
        data = request.get_json(force=True)
        latex_source = data.get("latex_source", "")

        if not latex_source or len(latex_source.strip()) < 10:
            return jsonify({"success": False, "error": "LaTeX source is too short or empty"}), 400

        output_dir = tempfile.mkdtemp(prefix="resume_compile_")

        pdf_path, error = _compile_latex_local(latex_source, output_dir)

        if pdf_path is None:
            pdf_path, error = _compile_latex_online(latex_source)

        if pdf_path is None:
            return jsonify({"success": False, "error": error}), 400

        with open(pdf_path, "rb") as f:
            pdf_data = f.read()

        try:
            import shutil
            shutil.rmtree(output_dir, ignore_errors=True)
            if pdf_path.startswith(tempfile.gettempdir()):
                os.unlink(pdf_path)
        except Exception:
            pass

        return Response(
            pdf_data,
            mimetype="application/pdf",
            headers={
                "Content-Disposition": "inline; filename=resume.pdf",
                "Content-Length": str(len(pdf_data)),
                "Cache-Control": "no-cache"
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/resume/default', methods=['GET'])
def api_resume_default():
    """Get the default LaTeX source."""
    return jsonify({
        "success": True,
        "latex_source": _default_resume_source
    })


@app.route('/api/resume/status', methods=['GET'])
def api_resume_status():
    """Check if pdflatex is available locally."""
    pdflatex_path = _find_pdflatex()
    return jsonify({
        "local_available": pdflatex_path is not None,
        "online_available": REQUESTS_AVAILABLE,
        "pdflatex_path": pdflatex_path
    })


# ============================================================================
# RESUME - AI Generation via OpenRouter
# ============================================================================

# Load the Jake's template for the AI prompt
_RESUME_TEMPLATE_PATH = Path(__file__).parent.parent / "Latex resume" / "resume-jake" / "resume.tex"
if _RESUME_TEMPLATE_PATH.exists():
    with open(_RESUME_TEMPLATE_PATH, "r") as f:
        _latex_template_reference = f.read()
else:
    _latex_template_reference = _default_resume_source

# The system prompt for the AI - tells it how to convert plain text to LaTeX
_AI_RESUME_SYSTEM_PROMPT = """You are an expert LaTeX resume generator. Your task is to convert plain text resume content into a properly formatted LaTeX document using the Jake's Resume template.

## TEMPLATE STRUCTURE (use these exact LaTeX commands):
The template uses these custom commands - you MUST use them:

1. HEADER: \\\\begin{{center}} block with name, phone, email, LinkedIn, GitHub
2. EDUCATION: \\\\section{{Education}} with \\\\resumeSubheading{{School}}{{Location}}{{Degree}}{{Dates}}
3. EXPERIENCE: \\\\section{{Experience}} with \\\\resumeSubheading{{JobTitle}}{{Dates}}{{Company}}{{Location}} then \\\\resumeItemListStart and \\\\resumeItem{{text}} for each bullet
4. PROJECTS: \\\\section{{Projects}} with \\\\resumeProjectHeading{{Name $|$ TechStack}}{{Dates}} then \\\\resumeItemListStart / \\\\resumeItem
5. TECHNICAL SKILLS: \\\\section{{Technical Skills}} with \\\\begin{{itemize}} using \\\\textbf{{Category}}{{: items}}

## RULES (strict - follow every one):
1. KEEP the EXACT preamble (everything before \\\\begin{{document}}) - do NOT modify or remove any packages or macros
2. ONLY modify the content between \\\\begin{{document}} and \\\\end{{document}}
3. Parse the user's plain text resume and extract these fields:
   - Name and Contact Info (phone, email, LinkedIn URL, GitHub URL)
   - Education entries (school, degree, dates, location)
   - Experience entries (company, job title, dates, location, bullet points)
   - Projects (name, tech stack, dates, description)
   - Technical Skills (languages, frameworks, tools, libraries)
4. Use \\\\href{{url}}{{text}} for all links (email, LinkedIn, GitHub)
5. Use \\\\textbf for job titles and company names in the Experience section
6. Use \\\\emph for tech stacks and degree names
7. For the Technical Skills section, use \\\\textbf{{Category}}{{: items}} format with \\\\\\\\ for line breaks between categories
8. If a section has no content, OMIT it entirely (don't include empty sections)
9. If the user's text doesn't specify a date, use a reasonable placeholder like "Date"
10. Output ONLY the complete LaTeX code wrapped in ```latex ... ``` code block
11. Do NOT include any explanations, notes, or commentary outside the code block
12. Ensure the output will compile WITHOUT errors - use proper escaping for special characters (&, %, $, #, _, {{, }}, ~, ^)

## EXAMPLE FORMAT (content section only):
\\\\begin{{document}}

\\\\begin{{center}}
    \\\\textbf{{\\\\Huge \\\\scshape John Doe}} \\\\\\\\ \\\\vspace{{1pt}}
    \\\\small +1-123-456-7890 $|$ \\\\href{{mailto:john@example.com}}{{\\\\underline{{john@example.com}}}} $|$
    \\\\href{{https://linkedin.com/in/johndoe}}{{\\\\underline{{linkedin.com/in/johndoe}}}} $|$
    \\\\href{{https://github.com/johndoe}}{{\\\\underline{{github.com/johndoe}}}}
\\\\end{{center}}

\\\\section{{Education}}
  \\\\resumeSubHeadingListStart
    \\\\resumeSubheading
      {{University of Example}}{{City, State}}
      {{Bachelor of Science in Computer Science, Minor in Math}}{{Aug. 2018 -- May 2022}}
  \\\\resumeSubHeadingListEnd

\\\\section{{Experience}}
  \\\\resumeSubHeadingListStart
    \\\\resumeSubheading
      {{Software Engineer}}{{June 2022 -- Present}}
      {{Tech Company Inc.}}{{San Francisco, CA}}
      \\\\resumeItemListStart
        \\\\resumeItem{{Developed REST APIs using Python and Flask serving 10K+ requests/day}}
        \\\\resumeItem{{Built real-time dashboards with React and D3.js for data visualization}}
      \\\\resumeItemListEnd
  \\\\resumeSubHeadingListEnd

\\\\end{{document}}

Now, convert the user's plain text resume below into a properly formatted LaTeX document following ALL of the above rules.
"""


def _call_openrouter(system_prompt, user_content):
    """Call OpenRouter API to generate LaTeX from plain text resume, with fallbacks."""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://roleboard.app",
        "X-OpenRouter-Title": "RoleBoard Resume Generator",
    }

    # Build list of models to try in order
    models_to_try = []
    
    # 1. Start with the configured model
    primary_model = OPENROUTER_MODEL or "google/gemma-4-31b-it:free"
    models_to_try.append(primary_model)
    
    # 2. Append the fallback models in order of ranking, avoiding duplicates
    for model in FALLBACK_MODELS:
        if model not in models_to_try:
            models_to_try.append(model)
            
    last_error = None
    
    for model in models_to_try:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.3,
            "max_tokens": 4096,
        }
        
        logging.info(f"Attempting to generate resume using OpenRouter model: {model}")
        
        try:
            response = requests_lib.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=120
            )
            
            # Check for non-200 responses
            if response.status_code != 200:
                error_detail = response.text[:500]
                last_error = f"Model {model} returned HTTP {response.status_code}: {error_detail}"
                logging.warning(last_error)
                continue
                
            try:
                result = response.json()
            except Exception:
                last_error = f"Model {model} returned invalid JSON: {response.text[:300]}"
                logging.warning(last_error)
                continue
                
            choices = result.get("choices")
            if not choices or not isinstance(choices, list) or len(choices) == 0:
                error_info = result.get("error", {})
                error_msg = error_info.get("message", "No choices returned") if isinstance(error_info, dict) else str(result)[:300]
                last_error = f"Model {model} returned no choices: {error_msg}"
                logging.warning(last_error)
                continue
                
            choice = choices[0]
            if not isinstance(choice, dict):
                last_error = f"Model {model} returned unexpected choice format"
                logging.warning(last_error)
                continue
                
            message = choice.get("message", {})
            if not isinstance(message, dict):
                last_error = f"Model {model} returned unexpected message format"
                logging.warning(last_error)
                continue
                
            content = message.get("content", "")
            if not content or not isinstance(content, str):
                last_error = f"Model {model} returned empty response content"
                logging.warning(last_error)
                continue
                
            # If we got here, we succeeded!
            logging.info(f"Successfully generated resume using model: {model}")
            return content, model
            
        except requests_lib.exceptions.Timeout:
            last_error = f"Model {model} request timed out"
            logging.warning(last_error)
            continue
        except requests_lib.exceptions.ConnectionError:
            last_error = f"Connection error while reaching model {model}"
            logging.warning(last_error)
            continue
        except Exception as e:
            last_error = f"Error with model {model}: {str(e)}"
            logging.warning(last_error)
            continue
            
    # If all models failed, raise the last error encountered
    raise Exception(f"All OpenRouter models failed to generate content. Last error: {last_error}")


def _clean_latex_output(raw_output):
    """Extract LaTeX code from AI output, handling various response formats."""
    if not raw_output or not isinstance(raw_output, str):
        raise Exception("AI returned empty output")

    # Strategy 1: Extract from ```latex ... ``` block
    latex_block = re.search(r"```latex\s*\n?(.*?)```", raw_output, re.DOTALL)
    if latex_block:
        result = latex_block.group(1).strip()
        if "\\begin{document}" in result:
            return result

    # Strategy 2: Extract from ``` ... ``` block (any language)
    code_block = re.search(r"```\s*\n?(.*?)```", raw_output, re.DOTALL)
    if code_block:
        result = code_block.group(1).strip()
        if result.startswith("\\documentclass") or "\\begin{document}" in result:
            return result

    # Strategy 3: Entire output starts with \documentclass
    stripped = raw_output.strip()
    if stripped.startswith("\\documentclass"):
        return stripped

    # Strategy 4: Find \documentclass anywhere in the output and extract
    docclass_match = re.search(r"(\\documentclass.*?\\end\{document\})", stripped, re.DOTALL)
    if docclass_match:
        return docclass_match.group(1).strip()

    # Strategy 5: Find \begin{document} to \end{document} block
    begin_end_match = re.search(r"(\\begin\{document\}.*?\\end\{document\})", stripped, re.DOTALL)
    if begin_end_match:
        # Reconstruct with a minimal preamble
        preamble = "\\documentclass[letterpaper,11pt]{article}\\n\\usepackage[empty]{fullpage}\\n\\usepackage{titlesec}\\n\\usepackage{hyperref}\\n\\usepackage{enumitem}\\n\\pagestyle{fancy}\\n\\fancyhf{}\\n\\fancyfoot{}\\n\\renewcommand{\\headrulewidth}{0pt}\\n\\renewcommand{\\footrulewidth}{0pt}\\n\\titleformat{\\section}{\\vspace{-4pt}\\scshape\\raggedright\\large}{}{0em}{}[\\color{black}\\titlerule \\vspace{-5pt}]"
        return preamble + "\n\n" + begin_end_match.group(1).strip()

    # Strategy 6: The output might be a simple error or message - return it as-is if it looks like reasonable text
    if len(stripped) > 100 and not stripped.startswith("<!DOCTYPE") and not stripped.startswith("{"):
        # Could be plain text with LaTeX commands - try wrapping it
        if "\\section" in stripped or "\\textbf" in stripped:
            preamble = "\\documentclass[letterpaper,11pt]{article}\\n\\usepackage[empty]{fullpage}\\n\\usepackage{titlesec}\\n\\usepackage{hyperref}\\n\\usepackage{enumitem}\\n\\pagestyle{fancy}\\n\\fancyhf{}\\n\\fancyfoot{}\\n\\renewcommand{\\headrulewidth}{0pt}\\n\\renewcommand{\\footrulewidth}{0pt}\\n\\begin{document}"
            return preamble + "\n\n" + stripped + "\n\n\\end{document}"

    raise Exception("Could not extract valid LaTeX from AI output. The model may have returned an unexpected format. Try again.")


@app.route('/api/resume/generate', methods=['POST'])
def api_resume_generate():
    """Use AI (OpenRouter) to convert plain text resume into LaTeX using Jake's template."""
    if not OPENROUTER_API_KEY:
        return jsonify({"success": False, "error": "OpenRouter API key not configured. Add OPENROUTER_API_KEY to .env"}), 400

    if not REQUESTS_AVAILABLE:
        return jsonify({"success": False, "error": "'requests' library required for AI generation"}), 400

    try:
        data = request.get_json(force=True)
        user_content = data.get("resume_content", "").strip()

        if not user_content or len(user_content) < 20:
            return jsonify({"success": False, "error": "Please paste your full resume content (at least 20 characters)"}), 400

        if len(user_content) > 15000:
            return jsonify({"success": False, "error": "Resume content is too long (max 15,000 characters)"}), 400

        # Extract the preamble from Jake's template to include in the AI prompt
        preamble_match = re.search(r"(.*?)\\begin\{document\}", _latex_template_reference, re.DOTALL)
        preamble = preamble_match.group(1) if preamble_match else _latex_template_reference

        # Build the full system prompt with the template preamble included
        system_prompt_with_template = (
            _AI_RESUME_SYSTEM_PROMPT
            + "\n\n## REFERENCE LATEX PREAMBLE (copy this EXACTLY into your output):\n```latex\n"
            + preamble
            + "\n```"
        )

        # Call OpenRouter with the enhanced system prompt that includes the template
        raw_output, success_model = _call_openrouter(system_prompt_with_template, user_content)

        # Clean and validate the output
        latex_source = _clean_latex_output(raw_output)

        # Basic validation
        if "\\begin{document}" not in latex_source:
            raise Exception("Generated LaTeX is missing \\\\begin{document}")

        if "\\end{document}" not in latex_source:
            raise Exception("Generated LaTeX is missing \\\\end{document}")

        return jsonify({
            "success": True,
            "latex_source": latex_source,
            "model": success_model,
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5001))
    debug = os.getenv('DEBUG', 'True').lower() == 'true'
    app.run(host=host, port=port, debug=debug)
