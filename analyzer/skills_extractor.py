"""Skill extraction from resume text.

All skills live in SKILL_CATEGORIES:

    category -> { "Canonical Name": ["alias", "another alias"] }

The canonical name is what the app shows and returns. Aliases are the other
ways people write the same skill (for example "JS" or "Javascript" for
"JavaScript"). Matching ignores upper/lower case, so there is no need to add
aliases that only differ by case.

To add a skill, add one line to the right category below. The canonical names
should match the ones in job_matcher.JOB_SKILLS so job matching keeps working.
"""

import re

SKILL_CATEGORIES = {
    "Programming Languages": {
        "Python": ["python3"],
        "Java": [],
        "C++": ["cpp"],
        "C": ["c programming", "c language"],
        "C#": ["csharp", "c sharp"],
        "JavaScript": ["js", "ecmascript", "es6"],
        "TypeScript": [],
        "Go": ["golang"],
        "Rust": [],
        "PHP": [],
        "Ruby": [],
        "Swift": [],
        "Kotlin": [],
        "R": ["r programming"],
        "Scala": [],
    },
    "Web Development": {
        "HTML": ["html5"],
        "CSS": ["css3"],
        "React": ["react.js", "reactjs", "react js"],
        "Angular": ["angularjs", "angular.js", "angular js"],
        "Vue": ["vue.js", "vuejs", "vue js"],
        "Next.js": ["nextjs", "next js"],
        "Node.js": ["nodejs", "node js", "node"],
        "Express": ["express.js", "expressjs", "express js"],
        "Flask": [],
        "Django": [],
        "FastAPI": ["fast api"],
        "Spring Boot": ["springboot"],
        "ASP.NET": ["asp net"],
        "Bootstrap": [],
        "Tailwind CSS": ["tailwind", "tailwindcss"],
    },
    "Databases": {
        "SQL": ["plsql"],
        "MySQL": [],
        "PostgreSQL": ["postgres", "postgre sql"],
        "MongoDB": ["mongo", "mongo db"],
        "Redis": [],
        "SQLite": [],
        "Oracle": ["oracle db", "oracle database"],
        "Cassandra": [],
        "DynamoDB": ["dynamo db"],
    },
    "Cloud & DevOps": {
        "AWS": ["amazon web services"],
        "Azure": ["microsoft azure"],
        "GCP": ["google cloud platform"],
        "Google Cloud": [],
        "Docker": [],
        "Kubernetes": ["k8s"],
        "Git": [],
        "GitHub": [],
        "GitLab": [],
        "CI/CD": ["cicd", "ci cd", "continuous integration"],
        "Linux": [],
        "Terraform": [],
    },
    "Data Science & AI": {
        "Machine Learning": ["ml"],
        "Deep Learning": ["dl"],
        "Artificial Intelligence": [],
        "NLP": ["natural language processing"],
        "Computer Vision": [],
        "Data Analysis": ["data analytics"],
        "Pandas": [],
        "NumPy": [],
        "Matplotlib": [],
        "TensorFlow": [],
        "PyTorch": [],
        "Keras": [],
        "Scikit-Learn": ["sklearn"],
        "OpenCV": [],
    },
    "Tools": {
        "Excel": ["microsoft excel", "ms excel", "advanced excel"],
        "Tableau": [],
        "Power BI": ["powerbi"],
        "Jira": [],
        "Postman": [],
        "Selenium": [],
    },
    "Core Concepts": {
        "REST API": ["rest apis", "restful api", "restful apis", "restful"],
        "GraphQL": [],
        "Data Structures": ["data structure", "dsa"],
        "Algorithms": ["algorithm"],
        "OOP": ["oops", "object oriented programming", "object oriented"],
        "Microservices": ["microservice"],
        "System Design": [],
        "Agile": [],
        "Scrum": [],
    },
    "Soft Skills": {
        "Communication": [],
        "Problem Solving": ["problem solver"],
        "Teamwork": ["team work", "team player"],
        "Leadership": [],
    },
}

# Flat list of every canonical skill name, in the order shown above.
SKILLS = [
    skill
    for group in SKILL_CATEGORIES.values()
    for skill in group
]

# These words are also normal English words or single letters ("C", "Go",
# "Swift", "Express", "Excel"...). They only count when they clearly stand as
# a skill, for example in a list: "Python, C, Go" or "proficient in C and C++".
# This stops "Plan C", "Vitamin C" or "to express interest" from matching.
AMBIGUOUS_TERMS = {
    "c", "r", "go", "node", "express", "swift", "oracle", "excel",
}

# "Node JS" or "React JS" are written with a space, so the alias "js" must not
# count them as the JavaScript skill.
JS_FRAMEWORK_WORDS = ["node", "react", "vue", "express", "next", "angular"]

# Whitespace except a line break (PDF text can contain odd spaces).
_SPACE = r"[^\S\n]"

# What may stand directly before / after an ambiguous skill name.
_BEFORE_AMBIGUOUS = (
    r"(?:^|[,;:|/•·●▪*(\[–-]|\b(?:in|of|with|using|and|or)\b|&)"
    + _SPACE + r"*"
)
_AFTER_AMBIGUOUS = (
    r"(?=" + _SPACE + r"*(?:$|[,;:|/•·●▪)\]]|\.(?:\s|$))"
    r"|" + _SPACE + r"+(?:and|or|&)" + _SPACE + r")"
)


def _term_to_regex(term):
    """Turn a skill name into regex text.

    A space or hyphen in the name matches any space, hyphen or line break, so
    "machine learning" also finds "Machine-Learning" and text that PDF
    extraction split over two lines.
    """
    parts = re.split(r"[\s-]+", term.lower().strip())
    return r"[\s\-]+".join(re.escape(part) for part in parts)


def _compile_term(term):
    """Build the regex that finds one skill name (or alias) in text."""
    body = _term_to_regex(term)

    if term.lower() in AMBIGUOUS_TERMS:
        return re.compile(
            _BEFORE_AMBIGUOUS + body + _AFTER_AMBIGUOUS,
            re.IGNORECASE | re.MULTILINE,
        )

    if term.lower() == "js":
        blockers = "".join(rf"(?<!{word}\s)" for word in JS_FRAMEWORK_WORDS)
        body = blockers + body

    # Not inside another word ("MySQL" is not "SQL") and not after a dot
    # (the "js" in "Node.js" is not JavaScript).
    return re.compile(r"(?<![\w.])" + body + r"(?!\w)", re.IGNORECASE)


# Built once when the module loads: [(canonical skill, [regex, ...]), ...]
_SKILL_PATTERNS = [
    (skill, [_compile_term(term) for term in [skill] + aliases])
    for group in SKILL_CATEGORIES.values()
    for skill, aliases in group.items()
]


def extract_skills(resume_text):
    """Return the canonical names of the skills found in the resume text.

    Every skill appears once, even if it is written in several ways
    ("JavaScript", "JS", "javascript"). The list follows the order of
    SKILL_CATEGORIES.
    """
    text = resume_text or ""

    found_skills = []

    for skill, patterns in _SKILL_PATTERNS:
        if any(pattern.search(text) for pattern in patterns):
            found_skills.append(skill)

    return found_skills


def get_suggestions(found_skills):

    suggestions = []

    if "Python" not in found_skills:
        suggestions.append("Consider adding Python skills if you have experience.")

    if "SQL" not in found_skills:
        suggestions.append("Consider learning SQL for database management.")

    if "Git" not in found_skills and "GitHub" not in found_skills:
        suggestions.append("Add Git and GitHub experience if applicable.")

    if "Machine Learning" not in found_skills:
        suggestions.append("Explore Machine Learning fundamentals.")

    if "Communication" not in found_skills:
        suggestions.append("Highlight your communication skills if relevant.")

    if not suggestions:
        suggestions.append("Your listed skills cover several useful technical areas. Keep your skills updated.")

    return suggestions


if __name__ == "__main__":

    sample = """
    Python, C++, JavaScript, SQL,
    HTML, CSS, Git, Machine Learning
    """

    result = extract_skills(sample)

    print("Detected Skills:", result)