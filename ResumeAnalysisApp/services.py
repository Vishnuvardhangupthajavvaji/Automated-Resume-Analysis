import re

import docx2txt
from pdfminer.high_level import extract_text as extract_pdf_text


def extract_resume_text(path):
    suffix = str(path).lower().rsplit(".", 1)[-1]
    if suffix == "pdf":
        return extract_pdf_text(path) or ""
    if suffix == "docx":
        return docx2txt.process(path) or ""
    raise ValueError("Unsupported resume format.")


def calculate_match(required_skills, resume_text):
    required = {skill.strip().casefold() for skill in required_skills if skill.strip()}
    normalized_text = re.sub(r"\s+", " ", resume_text.casefold())
    matched = sorted(skill for skill in required if skill in normalized_text)
    score = round((len(matched) / len(required)) * 100, 2) if required else 0
    return score, matched
