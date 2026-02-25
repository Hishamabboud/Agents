#!/usr/bin/env python3
"""Generate a professional CV PDF from resume data using reportlab."""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def main():
    output_path = "/home/user/Agents/profile/Hisham Abboud CV.pdf"
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        topMargin=15*mm,
        bottomMargin=15*mm,
        leftMargin=20*mm,
        rightMargin=20*mm,
    )

    styles = getSampleStyleSheet()
    blue = HexColor("#1E3C78")

    name_style = ParagraphStyle("Name", parent=styles["Title"], fontSize=22, spaceAfter=2, textColor=HexColor("#000000"), alignment=1)
    contact_style = ParagraphStyle("Contact", parent=styles["Normal"], fontSize=10, spaceAfter=6, alignment=1, textColor=HexColor("#444444"))
    section_style = ParagraphStyle("Section", parent=styles["Heading2"], fontSize=13, textColor=blue, spaceAfter=2, spaceBefore=10)
    job_style = ParagraphStyle("Job", parent=styles["Normal"], fontSize=11, spaceAfter=1, textColor=HexColor("#000000"))
    job_sub_style = ParagraphStyle("JobSub", parent=styles["Normal"], fontSize=10, spaceAfter=3, textColor=HexColor("#666666"))
    bullet_style = ParagraphStyle("Bullet", parent=styles["Normal"], fontSize=10, leftIndent=10, spaceAfter=2, bulletIndent=0)
    skill_style = ParagraphStyle("Skill", parent=styles["Normal"], fontSize=10, spaceAfter=2)

    story = []

    # Name
    story.append(Paragraph("Hisham Abboud", name_style))
    story.append(Paragraph("+31 06 4841 2838  |  hiaham123@hotmail.com  |  Eindhoven, Netherlands", contact_style))
    story.append(HRFlowable(width="100%", thickness=1, color=HexColor("#555555"), spaceAfter=8))

    # Professional Experience
    story.append(Paragraph("PROFESSIONAL EXPERIENCE", section_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=blue, spaceAfter=6))

    story.append(Paragraph("<b>Software Service Engineer</b>", job_style))
    story.append(Paragraph("<i>Actemium (VINCI Energies), Eindhoven  |  July 2025 — Present</i>", job_sub_style))
    for b in [
        "Provide full-stack development and technical support for Manufacturing Execution Systems (MES) across industrial clients",
        "Build and maintain applications using .NET, C#, ASP.NET, Python/Flask, and JavaScript",
        "Develop custom software solutions and integrations for manufacturing processes, including API connections and database optimizations",
        "Troubleshoot and resolve complex technical issues in production environments for clients in diverse industries",
    ]:
        story.append(Paragraph(f"• {b}", bullet_style))
    story.append(Spacer(1, 4))

    story.append(Paragraph("<b>Python Developer Intern</b>", job_style))
    story.append(Paragraph("<i>ASML, Veldhoven  |  Aug 2023 — Feb 2024</i>", job_sub_style))
    for b in [
        "Developed Python test suite using Locust and Pytest for high-efficiency performance and regression testing",
        "Collaborated in an agile environment using Azure, Jira, and Kubernetes for continuous integration and deployment",
    ]:
        story.append(Paragraph(f"• {b}", bullet_style))
    story.append(Spacer(1, 4))

    story.append(Paragraph("<b>Software Developer &amp; IT Admin Intern</b>", job_style))
    story.append(Paragraph("<i>Delta Electronics, Helmond  |  Feb 2022 — Feb 2023</i>", job_sub_style))
    for b in [
        "Developed web application for HR to manage salary adjustments and quarterly budgets across multiple branches",
        "Migrated legacy codebase from Visual Basic to C# to improve maintainability and performance",
        "Managed Active Directory and provided cross-departmental technical support; mentored new IT interns",
    ]:
        story.append(Paragraph(f"• {b}", bullet_style))
    story.append(Spacer(1, 4))

    # Projects
    story.append(Paragraph("PROJECTS", section_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=blue, spaceAfter=6))

    story.append(Paragraph("<b>CogitatAI — AI Customer Support Platform</b>", job_style))
    story.append(Paragraph("<i>Founder &amp; Developer  |  2024 — Present</i>", job_sub_style))
    for b in [
        "Building an AI-powered chatbot platform with personality-adaptive responses and multi-task sentiment analysis",
        "Architected full-stack solution using Python/Flask backend and modern frontend, deployed on cloud infrastructure",
    ]:
        story.append(Paragraph(f"• {b}", bullet_style))
    story.append(Spacer(1, 4))

    story.append(Paragraph("<b>GDPR Data Anonymization Solution</b>", job_style))
    story.append(Paragraph("<i>Fontys ICT Cyber Security Research Group  |  Sep 2024 — Feb 2025</i>", job_sub_style))
    story.append(Paragraph("• Developed a GDPR-compliant data anonymization pipeline enabling secure cross-organization data sharing", bullet_style))
    story.append(Spacer(1, 4))

    # Education
    story.append(Paragraph("EDUCATION", section_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=blue, spaceAfter=6))

    story.append(Paragraph("<b>Bachelor of Science in Software Engineering</b>", job_style))
    story.append(Paragraph("<i>Fontys University of Applied Sciences, Eindhoven  |  2020 — 2024</i>", job_sub_style))
    story.append(Paragraph("• Thesis: GDPR-compliant data anonymization for secure data sharing", bullet_style))
    story.append(Spacer(1, 4))

    # Skills
    story.append(Paragraph("SKILLS", section_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=blue, spaceAfter=6))

    story.append(Paragraph("<b>Languages:</b>  Python, C#, JavaScript, SQL, Visual Basic", skill_style))
    story.append(Paragraph("<b>Frameworks:</b>  .NET, ASP.NET, React, Flask, Locust, Pytest", skill_style))
    story.append(Paragraph("<b>Tools:</b>  Azure, Jira, Kubernetes, Git, Active Directory, Docker", skill_style))
    story.append(Paragraph("<b>Domains:</b>  MES, Agile/Scrum, GDPR, REST API Development, CI/CD", skill_style))
    story.append(Spacer(1, 4))

    # Spoken Languages
    story.append(Paragraph("SPOKEN LANGUAGES", section_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=blue, spaceAfter=6))
    story.append(Paragraph("English (fluent)  |  Dutch (fluent)  |  Arabic (fluent)  |  Persian (fluent)", skill_style))

    doc.build(story)
    print(f"CV PDF generated successfully: {output_path}")

if __name__ == "__main__":
    main()
