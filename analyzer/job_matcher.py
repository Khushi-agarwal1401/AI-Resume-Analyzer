"""Job description matching module.

Extracts technical requirements and skills from a job description, compares them
with the candidate's resume skills, and calculates a transparent match score.
"""

import re
from typing import Dict, List, Optional, Set, Tuple

# Pre-defined list of skills and technical requirements.
# Reuses the core skills from skills_extractor and expands with standard tools/technologies.
JOB_SKILLS = [
    # Programming Languages
    "Python", "Java", "C++", "C", "C#", "JavaScript", "TypeScript",
    "Go", "Rust", "PHP", "Ruby", "Swift", "Kotlin", "R", "Scala",
    # Web & Frameworks
    "HTML", "CSS", "React", "Angular", "Vue", "Next.js", "Node.js",
    "Express", "Flask", "Django", "FastAPI", "Spring Boot", "ASP.NET",
    # Databases & Caching
    "SQL", "MySQL", "PostgreSQL", "MongoDB", "Redis", "SQLite",
    "Oracle", "Cassandra", "DynamoDB",
    # Cloud, DevOps & Tools
    "AWS", "Azure", "GCP", "Google Cloud", "Docker", "Kubernetes",
    "Git", "GitHub", "GitLab", "CI/CD", "Linux", "Terraform",
    # AI / ML & Data Science
    "Machine Learning", "Deep Learning", "NLP", "Computer Vision",
    "Data Analysis", "Pandas", "NumPy", "TensorFlow", "PyTorch", "Scikit-Learn",
    # Core Engineering & Concepts
    "REST API", "GraphQL", "Data Structures", "Algorithms", "OOP",
    "Microservices", "System Design", "Agile", "Scrum",
    # Soft & Professional Skills
    "Communication", "Problem Solving", "Teamwork", "Leadership"
]

# Aliases mapping variant skill terms to canonical skill names
SKILL_ALIASES: Dict[str, str] = {
    "js": "JavaScript",
    "ts": "TypeScript",
    "py": "Python",
    "react.js": "React",
    "reactjs": "React",
    "node": "Node.js",
    "nodejs": "Node.js",
    "vue.js": "Vue",
    "vuejs": "Vue",
    "golang": "Go",
    "postgres": "PostgreSQL",
    "mongo": "MongoDB",
    "k8s": "Kubernetes",
    "amazon web services": "AWS",
    "google cloud platform": "GCP",
    "ml": "Machine Learning",
    "dl": "Deep Learning",
    "natural language processing": "NLP",
    "restful api": "REST API",
    "restful apis": "REST API",
    "rest apis": "REST API",
    "rest": "REST API",
    "object oriented programming": "OOP",
    "object-oriented programming": "OOP",
}


def extract_job_skills(text: Optional[str]) -> List[str]:
    """Extract unique relevant skills and requirements from a job description text.

    Args:
        text: Raw text of the job description.

    Returns:
        Sorted list of unique detected canonical skills.
    """
    if not text or not text.strip():
        return []

    text_lower = text.lower()
    found: Set[str] = set()

    # 1. Match canonical skills
    for skill in JOB_SKILLS:
        skill_lower = skill.lower()
        # Word boundary pattern that safely handles skills with +, #, ., etc.
        pattern = r'(?<![\w#+])' + re.escape(skill_lower) + r'(?![\w#+])'
        if re.search(pattern, text_lower):
            found.add(skill)

    # 2. Match aliases
    for alias, canonical_name in SKILL_ALIASES.items():
        pattern = r'(?<![\w#+])' + re.escape(alias) + r'(?![\w#+])'
        if re.search(pattern, text_lower):
            found.add(canonical_name)

    return sorted(found, key=lambda s: s.lower())


def match_resume_to_job(
    resume_skills: List[str],
    job_description: Optional[str]
) -> Dict:
    """Compare extracted resume skills with job description requirements.

    Args:
        resume_skills: List of skills detected in the candidate's resume.
        job_description: Plain text job description pasted by the user.

    Returns:
        Structured dictionary containing:
        - matching_skills: List of skills found in both resume and job description.
        - missing_skills: List of required skills missing from the resume.
        - required_skills: List of all unique skills required by the job.
        - match_percentage: Integer percentage (0-100) of skill overlap.
        - total_required: Total count of unique required skills.
        - total_matching: Total count of matching skills.
        - has_job_description: Boolean indicating if a non-empty JD was provided.
        - explanation: Transparent explanation of the calculation formula.
    """
    is_empty_jd = not job_description or not job_description.strip()

    if is_empty_jd:
        return {
            "matching_skills": [],
            "missing_skills": [],
            "required_skills": [],
            "match_percentage": 0,
            "total_required": 0,
            "total_matching": 0,
            "has_job_description": False,
            "explanation": "No job description was provided for comparison."
        }

    # Extract requirements from the job description
    required = extract_job_skills(job_description)

    # Normalize resume skills for case-insensitive and alias-aware comparison
    resume_skills_canonical: Set[str] = set()
    for s in (resume_skills or []):
        s_clean = s.strip()
        if not s_clean:
            continue
        canonical = SKILL_ALIASES.get(s_clean.lower(), s_clean)
        # Find exact canonical title match if present in JOB_SKILLS
        matched_title = next(
            (js for js in JOB_SKILLS if js.lower() == canonical.lower()),
            canonical
        )
        resume_skills_canonical.add(matched_title)

    if not required:
        return {
            "matching_skills": [],
            "missing_skills": [],
            "required_skills": [],
            "match_percentage": 0,
            "total_required": 0,
            "total_matching": 0,
            "has_job_description": True,
            "explanation": (
                "No recognizable technical skills were detected in the provided job description. "
                "Try including specific tools, technologies or languages."
            )
        }

    # Map required skills and check intersection
    matching: List[str] = []
    missing: List[str] = []

    resume_skills_lower = {s.lower() for s in resume_skills_canonical}

    for req in required:
        if req.lower() in resume_skills_lower:
            matching.append(req)
        else:
            missing.append(req)

    total_required = len(required)
    total_matching = len(matching)

    # Calculate match percentage: (Matching / Required) * 100
    match_percentage = round((total_matching / total_required) * 100) if total_required > 0 else 0

    explanation = (
        f"Match percentage measures skill overlap: "
        f"({total_matching} matching / {total_required} required) × 100 = {match_percentage}%. "
        f"This score indicates keyword alignment and does not represent overall hiring probability."
    )

    return {
        "matching_skills": matching,
        "missing_skills": missing,
        "required_skills": required,
        "match_percentage": match_percentage,
        "total_required": total_required,
        "total_matching": total_matching,
        "has_job_description": True,
        "explanation": explanation
    }
