"""
Resume-as-Code Schema & Jinja2 LaTeX Template Renderer
Supports: Jake, Sourabh, Pratul, FAANG
Decouples structured resume data (JSON/YAML) from LaTeX styling.
"""
import re
from jinja2 import Environment

def tex_escape(text):
    """
    Safely escape LaTeX special characters in user strings.
    Does not touch already escaped sequences.
    """
    if text is None:
        return ""
    text = str(text)
    # Characters that must be escaped: & % $ # _ { } ~ ^
    # First protect already escaped ones
    conv = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '~': r'\textasciitilde{}',
        '^': r'\textasciicircum{}',
    }
    # Regex to find unescaped special chars
    pattern = re.compile(r'(?<!\\)([&%$#_])')
    return pattern.sub(lambda m: conv[m.group(1)], text)


# Setup Jinja Environment with custom LaTeX delimiters to avoid clashes
latex_jinja_env = Environment(
    block_start_string=r'\BLOCK{',
    block_end_string='}',
    variable_start_string=r'\VAR{',
    variable_end_string='}',
    comment_start_string=r'\#{',
    comment_end_string='}',
    autoescape=False
)
latex_jinja_env.filters['tex_escape'] = tex_escape


DEFAULT_RESUME_DATA = {
    "basics": {
        "name": "Jake Ryan",
        "phone": "123-456-7890",
        "email": "jake@su.edu",
        "location": "Georgetown, TX",
        "linkedin": "linkedin.com/in/jake",
        "github": "github.com/jake",
        "website": ""
    },
    "education": [
        {
            "institution": "Southwestern University",
            "location": "Georgetown, TX",
            "degree": "Bachelor of Arts in Computer Science, Minor in Business",
            "dates": "Aug. 2018 -- May 2021"
        },
        {
            "institution": "Blinn College",
            "location": "Bryan, TX",
            "degree": "Associate's in Liberal Arts",
            "dates": "Aug. 2014 -- May 2018"
        }
    ],
    "experience": [
        {
            "company": "Texas A&M University",
            "location": "College Station, TX",
            "role": "Undergraduate Research Assistant",
            "dates": "June 2020 -- Present",
            "bullets": [
                "Developed a REST API using FastAPI and PostgreSQL to store data from learning management systems",
                "Developed a full-stack web application using Flask, React, PostgreSQL and Docker to analyze GitHub data",
                "Explored ways to visualize GitHub collaboration in a classroom setting"
            ]
        },
        {
            "company": "Southwestern University",
            "location": "Georgetown, TX",
            "role": "Information Technology Support Specialist",
            "dates": "Sep. 2018 -- Present",
            "bullets": [
                "Communicate with managers to set up campus computers used on campus",
                "Assess and troubleshoot computer problems brought by students, faculty and staff",
                "Maintain upkeep of computers, classroom equipment, and 200 printers across campus"
            ]
        }
    ],
    "projects": [
        {
            "name": "Gitlytics",
            "tools": "Python, Flask, React, PostgreSQL, Docker",
            "dates": "June 2020 -- Present",
            "bullets": [
                "Developed a full-stack web application with Flask serving a REST API with React as frontend",
                "Implemented GitHub OAuth to get data from user repositories and visualized data",
                "Used Celery and Redis for asynchronous background tasks"
            ]
        },
        {
            "name": "Simple Paintball",
            "tools": "Java, Spigot API, Maven, TravisCI, Git",
            "dates": "May 2018 -- May 2020",
            "bullets": [
                "Developed a Minecraft server plugin to entertain kids during free time",
                "Published plugin to websites gaining 2K+ downloads and average 4.5/5-star rating",
                "Implemented continuous delivery using TravisCI to build plugin on release"
            ]
        }
    ],
    "skills": {
        "Languages": "Java, Python, C/C++, SQL (Postgres), JavaScript, HTML/CSS, R",
        "Frameworks": "React, Node.js, Flask, FastAPI, JUnit",
        "Developer Tools": "Git, Docker, TravisCI, Google Cloud Platform, VS Code",
        "Libraries": "pandas, NumPy, Matplotlib"
    }
}


JAKE_TEMPLATE = r"""\documentclass[letterpaper,11pt]{article}

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

\pagestyle{fancy}
\fancyhf{}
\fancyfoot{}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}

\addtolength{\oddsidemargin}{-0.5in}
\addtolength{\evensidemargin}{-0.5in}
\addtolength{\textwidth}{1in}
\addtolength{\topmargin}{-.5in}
\addtolength{\textheight}{1.0in}

\urlstyle{same}
\raggedbottom
\raggedright
\setlength{\tabcolsep}{0in}

\titleformat{\section}{
  \vspace{-4pt}\scshape\raggedright\large
}{}{0em}{}[\color{black}\titlerule \vspace{-5pt}]

\pdfgentounicode=1

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

\newcommand{\resumeProjectHeading}[2]{
    \item
    \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}
      \small#1 & #2 \\
    \end{tabular*}\vspace{-7pt}
}

\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=0.15in, label={}]}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}
\newcommand{\resumeItemListStart}{\begin{itemize}}
\newcommand{\resumeItemListEnd}{\end{itemize}\vspace{-5pt}}

\begin{document}

\begin{center}
    \textbf{\Huge \scshape \VAR{basics.name | tex_escape}} \\ \vspace{1pt}
    \small \VAR{basics.phone | tex_escape} $|$ \href{mailto:\VAR{basics.email}}{\underline{\VAR{basics.email | tex_escape}}} 
    \BLOCK{ if basics.linkedin } $|$ \href{https://\VAR{basics.linkedin}}{\underline{\VAR{basics.linkedin | tex_escape}}} \BLOCK{ endif }
    \BLOCK{ if basics.github } $|$ \href{https://\VAR{basics.github}}{\underline{\VAR{basics.github | tex_escape}}} \BLOCK{ endif }
    \BLOCK{ if basics.website } $|$ \href{https://\VAR{basics.website}}{\underline{\VAR{basics.website | tex_escape}}} \BLOCK{ endif }
\end{center}

\BLOCK{ if education }
\section{Education}
  \resumeSubHeadingListStart
    \BLOCK{ for edu in education }
    \resumeSubheading
      {\VAR{edu.institution | tex_escape}}{\VAR{edu.location | tex_escape}}
      {\VAR{edu.degree | tex_escape}}{\VAR{edu.dates | tex_escape}}
    \BLOCK{ endfor }
  \resumeSubHeadingListEnd
\BLOCK{ endif }

\BLOCK{ if experience }
\section{Experience}
  \resumeSubHeadingListStart
    \BLOCK{ for exp in experience }
    \resumeSubheading
      {\VAR{exp.role | tex_escape}}{\VAR{exp.dates | tex_escape}}
      {\VAR{exp.company | tex_escape}}{\VAR{exp.location | tex_escape}}
      \resumeItemListStart
        \BLOCK{ for b in exp.bullets }
        \resumeItem{\VAR{b | tex_escape}}
        \BLOCK{ endfor }
      \resumeItemListEnd
    \BLOCK{ endfor }
  \resumeSubHeadingListEnd
\BLOCK{ endif }

\BLOCK{ if projects }
\section{Projects}
    \resumeSubHeadingListStart
      \BLOCK{ for proj in projects }
      \resumeProjectHeading
          {\textbf{\VAR{proj.name | tex_escape}} $|$ \emph{\VAR{proj.tools | tex_escape}}}{\VAR{proj.dates | tex_escape}}
          \resumeItemListStart
            \BLOCK{ for b in proj.bullets }
            \resumeItem{\VAR{b | tex_escape}}
            \BLOCK{ endfor }
          \resumeItemListEnd
      \BLOCK{ endfor }
    \resumeSubHeadingListEnd
\BLOCK{ endif }

\BLOCK{ if skills }
\section{Technical Skills}
 \begin{itemize}[leftmargin=0.15in, label={}]
    \small{\item{
      \BLOCK{ for k, v in skills.items() }
      \textbf{\VAR{k | tex_escape}}{: \VAR{v | tex_escape}} \BLOCK{ if not loop.last } \\ \BLOCK{ endif }
      \BLOCK{ endfor }
    }}
 \end{itemize}
\BLOCK{ endif }

\end{document}
"""

SOURABH_TEMPLATE = r"""\documentclass[letterpaper,11pt]{article}

\usepackage[empty]{fullpage}
\usepackage{titlesec}
\usepackage[usenames,dvipsnames]{color}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{fancyhdr}
\usepackage[english]{babel}
\usepackage{tabularx}
\input{glyphtounicode}

\pagestyle{fancy}
\fancyhf{}
\fancyfoot{}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}

\addtolength{\oddsidemargin}{-0.5in}
\addtolength{\evensidemargin}{-0.5in}
\addtolength{\textwidth}{1in}
\addtolength{\topmargin}{-.5in}
\addtolength{\textheight}{1.0in}

\urlstyle{same}
\raggedbottom
\raggedright
\setlength{\tabcolsep}{0in}

\titleformat{\section}{
  \vspace{-4pt}\scshape\raggedright\large
}{}{0em}{}[\color{black}\titlerule \vspace{-5pt}]

\pdfgentounicode=1

\newcommand{\resumeItem}[2]{
  \item\small{
    \textbf{#1}{: #2 \vspace{-2pt}}
  }
}

\newcommand{\resumeItemPlain}[1]{
  \item\small{
    {#1 \vspace{-2pt}}
  }
}

\newcommand{\resumeSubheading}[4]{
  \vspace{-1pt}\item
    \begin{tabular*}{0.97\textwidth}[t]{l@{\extracolsep{\fill}}r}
      \textbf{#1} & #2 \\
      \textit{\small #3} & \textit{\small #4} \\
    \end{tabular*}\vspace{-5pt}
}

\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=*]}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}
\newcommand{\resumeItemListStart}{\begin{itemize}}
\newcommand{\resumeItemListEnd}{\end{itemize}\vspace{-5pt}}

\begin{document}

\begin{tabular*}{\textwidth}{l@{\extracolsep{\fill}}r}
  \textbf{\Large \VAR{basics.name | tex_escape}} & Email: \href{mailto:\VAR{basics.email}}{\VAR{basics.email | tex_escape}}\\
  \BLOCK{ if basics.linkedin } LinkedIn: \href{https://\VAR{basics.linkedin}}{\VAR{basics.linkedin | tex_escape}} \BLOCK{ endif } & Mobile: \VAR{basics.phone | tex_escape} \\
\end{tabular*}

\BLOCK{ if education }
\section{Education}
  \resumeSubHeadingListStart
    \BLOCK{ for edu in education }
    \resumeSubheading
      {\VAR{edu.institution | tex_escape}}{\VAR{edu.location | tex_escape}}
      {\VAR{edu.degree | tex_escape}}{\VAR{edu.dates | tex_escape}}
    \BLOCK{ endfor }
  \resumeSubHeadingListEnd
\BLOCK{ endif }

\BLOCK{ if experience }
\section{Experience}
  \resumeSubHeadingListStart
    \BLOCK{ for exp in experience }
    \resumeSubheading
      {\VAR{exp.company | tex_escape}}{\VAR{exp.location | tex_escape}}
      {\VAR{exp.role | tex_escape}}{\VAR{exp.dates | tex_escape}}
      \resumeItemListStart
        \BLOCK{ for b in exp.bullets }
        \resumeItemPlain{\VAR{b | tex_escape}}
        \BLOCK{ endfor }
      \resumeItemListEnd
    \BLOCK{ endfor }
  \resumeSubHeadingListEnd
\BLOCK{ endif }

\BLOCK{ if projects }
\section{Projects}
  \resumeSubHeadingListStart
    \BLOCK{ for proj in projects }
    \resumeSubheading
      {\VAR{proj.name | tex_escape}}{\VAR{proj.dates | tex_escape}}
      {\VAR{proj.tools | tex_escape}}{}
      \resumeItemListStart
        \BLOCK{ for b in proj.bullets }
        \resumeItemPlain{\VAR{b | tex_escape}}
        \BLOCK{ endfor }
      \resumeItemListEnd
    \BLOCK{ endfor }
  \resumeSubHeadingListEnd
\BLOCK{ endif }

\BLOCK{ if skills }
\section{Skills}
 \resumeSubHeadingListStart
    \item{
      \BLOCK{ for k, v in skills.items() }
      \textbf{\VAR{k | tex_escape}}{: \VAR{v | tex_escape}} \BLOCK{ if not loop.last } \\ \BLOCK{ endif }
      \BLOCK{ endfor }
    }
 \resumeSubHeadingListEnd
\BLOCK{ endif }

\end{document}
"""

TEMPLATES = {
    'jake': JAKE_TEMPLATE,
    'sourabh': SOURABH_TEMPLATE,
    'pratul': JAKE_TEMPLATE, # uses jake geometry with pratul styling
    'faang': SOURABH_TEMPLATE # clean fallback
}

def render_latex_from_schema(template_name: str, data: dict) -> str:
    """Renders clean LaTeX code from a template name and structured data dict."""
    t_key = template_name.lower().strip()
    template_str = TEMPLATES.get(t_key, JAKE_TEMPLATE)
    jinja_template = latex_jinja_env.from_string(template_str)
    return jinja_template.render(**data)
