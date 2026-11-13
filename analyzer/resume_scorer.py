
import re


def calculate_resume_score(text):

    text_lower = text.lower()
    score = 0
    breakdown = {}

    # 1. Contact Information (10 Marks)
    contact_score = 0

    email = re.search(
        r'[\w.+-]+@[\w-]+\.[\w.-]+',
        text
    )

    phone = re.search(
        r'(?<!\w)(?:\+?\d[\d\s()-]{8,}\d)(?!\w)',
        text
    )

    if email:
        contact_score += 5

    if phone:
        contact_score += 5

    breakdown["Contact Information"] = contact_score
    score += contact_score

    # 2. Professional Summary (10 Marks)
    summary_keywords = [
        "professional summary",
        "career objective",
        "profile summary",
        "about me"
    ]

    summary_score = 10 if any(
        keyword in text_lower
        for keyword in summary_keywords
    ) else 0

    breakdown["Professional Summary"] = summary_score
    score += summary_score

    # 3. Technical Skills (20 Marks)
    technical_skills = [
        "python", "java", "c++", "c",
        "javascript", "html", "css", "sql",
        "machine learning", "deep learning",
        "flask", "django", "react",
        "mongodb", "mysql", "git", "github",
        "tensorflow", "pandas", "numpy"
    ]

    detected_skills = []

    for skill in technical_skills:

        pattern = (
            r'(?<!\w)' +
            re.escape(skill) +
            r'(?!\w)'
        )

        if re.search(pattern, text_lower):
            detected_skills.append(skill)

    skills_score = min(
        len(detected_skills) * 2,
        20
    )

    breakdown["Technical Skills"] = skills_score
    score += skills_score

    # 4. Education (15 Marks)
    education_keywords = [
        "education",
        "b.tech",
        "bachelor",
        "degree",
        "university",
        "college"
    ]

    education_score = 15 if any(
        keyword in text_lower
        for keyword in education_keywords
    ) else 0

    breakdown["Education"] = education_score
    score += education_score

    # 5. Experience (15 Marks)
    experience_keywords = [
        "experience",
        "internship",
        "intern",
        "work history"
    ]

    experience_score = 15 if any(
        keyword in text_lower
        for keyword in experience_keywords
    ) else 0

    breakdown["Experience"] = experience_score
    score += experience_score

    # 6. Projects (20 Marks)
    project_keywords = [
        "projects",
        "project",
        "github repository"
    ]

    project_score = 20 if any(
        keyword in text_lower
        for keyword in project_keywords
    ) else 0

    breakdown["Projects"] = project_score
    score += project_score

    # 7. Readability (10 Marks)
    readability_score = 0

    word_count = len(text.split())

    if word_count >= 100:
        readability_score += 5

    headings = [
        "education",
        "skills",
        "projects",
        "experience",
        "summary"
    ]

    heading_count = sum(
        1 for heading in headings
        if heading in text_lower
    )

    if heading_count >= 3:
        readability_score += 5

    breakdown["Readability"] = readability_score
    score += readability_score

    # Final Result
    return {
        "score": score,
        "breakdown": breakdown,
        "detected_skills": detected_skills,
        "word_count": word_count
    }

