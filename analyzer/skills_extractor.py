
import re

SKILLS = [
    "Python", "Java", "C++", "C", "JavaScript",
    "HTML", "CSS", "SQL", "Flask", "Django",
    "React", "Node.js", "MongoDB", "MySQL",
    "Machine Learning", "Deep Learning", "NLP",
    "Data Analysis", "Pandas", "NumPy",
    "TensorFlow", "PyTorch", "Git", "GitHub",
    "REST API", "Data Structures", "OOP",
    "Communication", "Problem Solving"
]


def extract_skills(resume_text):

    found_skills = []

    text = resume_text.lower()

    for skill in SKILLS:
        pattern = r'(?<!\w)' + re.escape(skill.lower()) + r'(?!\w)'

        if re.search(pattern, text):
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