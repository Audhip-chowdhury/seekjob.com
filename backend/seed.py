"""
Seed SQLite with realistic test data. Run from backend/: python seed.py
"""
import os
import random
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta

from fpdf import FPDF
from sqlalchemy.orm import Session

from auth import hash_password
from database import Base, SessionLocal, engine
from models import (
    Applicant,
    Application,
    AuthorType,
    Company,
    Discussion,
    JobPosting,
    JobType,
)

BASE = os.path.dirname(os.path.abspath(__file__))
UPLOAD = os.path.join(BASE, "uploads")
random.seed(42)

MINIMAL_JPEG = bytes(
    [
        0xFF,
        0xD8,
        0xFF,
        0xE0,
        0x00,
        0x10,
        0x4A,
        0x46,
        0x49,
        0x46,
        0x00,
        0x01,
        0x01,
        0x00,
        0x00,
        0x01,
        0x00,
        0x01,
        0x00,
        0x00,
        0xFF,
        0xDB,
        0x00,
        0x43,
        0x00,
        0xFF,
        0xC0,
        0x00,
        0x0B,
        0x08,
        0x00,
        0x01,
        0x00,
        0x01,
        0x01,
        0x01,
        0x11,
        0x00,
        0xFF,
        0xC4,
        0x00,
        0x1F,
        0x00,
        0x00,
        0x01,
        0x05,
        0x01,
        0x01,
        0x01,
        0x01,
        0x01,
        0x01,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x01,
        0x02,
        0x03,
        0x04,
        0x05,
        0x06,
        0x07,
        0x08,
        0x09,
        0x0A,
        0x0B,
        0xFF,
        0xDA,
        0x00,
        0x08,
        0x01,
        0x01,
        0x00,
        0x00,
        0x3F,
        0x00,
        0xFB,
        0xD5,
        0xDB,
        0x20,
        0xFF,
        0xD9,
    ]
)


def ensure_upload_dirs():
    for sub in ("logos", "pictures", "cvs"):
        os.makedirs(os.path.join(UPLOAD, sub), exist_ok=True)


def download_url(url: str, dest_path: str, min_bytes: int = 500) -> bool:
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; SeekJobSeed/1.0)"},
        )
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = resp.read()
        if len(data) < min_bytes:
            return False
        with open(dest_path, "wb") as f:
            f.write(data)
        return True
    except (urllib.error.URLError, OSError, TimeoutError, ValueError):
        return False


LOGO_BG_COLORS = ["2563eb", "047857", "b45309", "b91c1c", "6d28d9", "be185d", "0f766e"]


def write_applicant_cv_pdf(path: str, name: str, email: str, headline: str, skills: str) -> None:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 10, name, ln=1)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, email, ln=1)
    pdf.set_font("Helvetica", "I", 10)
    pdf.cell(0, 7, "Nova Meridian", ln=1)
    pdf.ln(6)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Professional summary", ln=1)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5, headline)
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Core skills", ln=1)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5, skills)
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Experience", ln=1)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(
        0,
        5,
        "Senior Consultant, Summit Advisory NM (2021-Present)\n"
        "- Led cross-functional workstreams for public-sector digital programs.\n"
        "- Owned stakeholder updates, risk registers, and delivery milestones.\n\n"
        "Analyst, Harborline Shared Services (2018-2021)\n"
        "- Built reporting pipelines and supported regulatory filing cycles.\n"
        "- Partnered with HR and Ops on process documentation.",
    )
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Education", ln=1)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(
        0,
        5,
        "M.Sc. Information Systems - Nova Meridian Institute of Technology\n"
        "B.A. Economics - City University of Nova Meridian",
    )
    pdf.output(path)


COMPANIES_DATA = [
    {
        "name": "Meridian Tech Labs",
        "location": "Nova Meridian — Tech District",
        "email": "careers@meridiantech.nm",
    },
    {
        "name": "Harborline Financial Group",
        "location": "Nova Meridian — Harbor Plaza",
        "email": "talent@harborline.nm",
    },
    {
        "name": "Crescent Logistics Co.",
        "location": "Nova Meridian — Industrial Belt",
        "email": "hr@crescentlogistics.nm",
    },
    {
        "name": "Willowbrook Healthcare Systems",
        "location": "Nova Meridian — Medical Quarter",
        "email": "recruiting@willowbrook.nm",
    },
    {
        "name": "Summit Consulting Partners",
        "location": "Nova Meridian — Central Business District",
        "email": "jobs@summitcp.nm",
    },
    {
        "name": "Pulse Media Network",
        "location": "Nova Meridian — Creative Wharf",
        "email": "people@pulsemedia.nm",
    },
    {
        "name": "Aurora Energy Grid",
        "location": "Nova Meridian — Power & Grid Hub",
        "email": "careers@auroraenergygrid.nm",
    },
]

# One "About {company}" paragraph per company index (used inside jd_block)
COMPANY_ABOUT = [
    "Meridian Tech Labs builds secure, observable software for Nova Meridian's public agencies and growth-stage startups. "
    "We invest in platform engineering, developer experience, and pragmatic AI where it reduces toil. "
    "Our teams work in squads with clear ownership, strong documentation culture, and blameless postmortems.",
    "Harborline Financial Group provides wealth management, corporate banking, and risk services across the metro region. "
    "We operate under strict regulatory standards and value precision, auditability, and client trust. "
    "Technology and operations partner tightly to deliver resilient, compliant systems at scale.",
    "Crescent Logistics Co. runs warehousing, last-mile distribution, and fleet coordination for retail and industrial clients. "
    "Safety, on-time performance, and cost discipline define how we work. "
    "We are modernizing planning systems while keeping frontline teams empowered with clear SOPs.",
    "Willowbrook Healthcare Systems operates hospitals, clinics, and digital care pathways for Nova Meridian residents. "
    "Patient safety, clinical quality, and data privacy are non-negotiable. "
    "We collaborate across clinical, IT, and operations to ship improvements that clinicians actually adopt.",
    "Summit Consulting Partners advises enterprises and public institutions on strategy, transformation, and delivery. "
    "Our engagements blend analysis, facilitation, and hands-on execution. "
    "Consultants are expected to communicate crisply, manage ambiguity, and develop junior teammates.",
    "Pulse Media Network produces streaming content, live events, and brand partnerships for regional and national audiences. "
    "Creativity meets operational rigor: we ship on schedule, protect IP, and iterate using audience data. "
    "Cross-functional pods include production, engineering, and growth.",
    "Aurora Energy Grid operates transmission, distribution planning, and smart-meter programs for Nova Meridian. "
    "Reliability and worker safety come first; we invest in SCADA modernization, outage analytics, and storm response. "
    "Engineering and field teams collaborate under NERC-style discipline with transparent incident learning.",
]

OFFER_EXTRAS = [
    "Employee stock purchase plan and annual merit cycles tied to clear competencies.",
    "Employer-matched pension contributions and financial wellness coaching.",
    "Safety bonuses, certified training paths, and union-aligned benefits where applicable.",
    "Clinical education stipend, mental health support, and flexible shift swap tools.",
    "Performance bonuses on client outcomes and sponsored MBA pathways for senior staff.",
    "Festival passes, creative sabbaticals, and equipment budgets for remote editors.",
    "Grid safety certifications, hazard pay for field rotations, and union-negotiated overtime rules.",
]


def jd_block(
    role: str,
    skills: str,
    company_name: str,
    job_type: JobType,
    co_idx: int,
    job_index: int,
) -> str:
    about = COMPANY_ABOUT[co_idx % len(COMPANY_ABOUT)]
    offer_extra = OFFER_EXTRAS[co_idx % len(OFFER_EXTRAS)]
    salary_low = 42_000 + (job_index * 1_373) % 38_000
    salary_high = salary_low + 18_000 + (job_index * 911) % 22_000
    skills_bits = [s.strip() for s in skills.split(",") if s.strip()]

    if job_type == JobType.SOFTWARE_DEV:
        role_para = (
            f"As a {role}, you will own features and services end to end—from design discussion through deployment and monitoring. "
            f"You will work closely with product and peers to keep the stack healthy, with emphasis on {skills_bits[0] if skills_bits else 'modern tooling'} "
            "and sustainable delivery practices."
        )
        do_lines = [
            f"Design, implement, and test software using {skills}.",
            "Review code, document APIs, and improve reliability and performance where it matters to users.",
            "Collaborate in agile ceremonies; break work into shippable increments with clear acceptance criteria.",
            "Participate in on-call or incident response rotations where applicable; write actionable runbooks.",
            "Partner with security and platform teams on secrets handling, access patterns, and observability.",
            "Mentor junior engineers through pairing and crisp feedback.",
        ]
        req_lines = [
            f"4+ years of professional software experience (or equivalent depth for senior titles) with strong fundamentals.",
            f"Hands-on experience with: {skills}.",
            "Comfortable owning a service or subsystem and communicating trade-offs to non-engineers.",
            "Pragmatic testing habits; you know when unit, contract, or e2e tests earn their keep.",
            "Written English strong enough for design docs, RFCs, and async updates.",
            "Experience in cloud-native or distributed systems is a strong plus.",
        ]
    elif job_type == JobType.HR:
        role_para = (
            f"In this {role} position, you will support people programs that scale with the business while staying fair and compliant. "
            "You will balance empathy for employees with clear policy application and measurable outcomes."
        )
        do_lines = [
            "Partner with managers on hiring, performance, and employee relations cases with consistency.",
            "Maintain accurate records in HRIS; support audits and reporting cycles.",
            "Improve processes for onboarding, benefits, and policy communications.",
            "Facilitate training and engagement initiatives aligned to leadership priorities.",
            "Coordinate with legal and compliance on sensitive matters and documentation.",
            "Use data to spot trends in turnover, hiring funnel health, and survey feedback.",
        ]
        req_lines = [
            "3+ years in HR, people operations, or talent in mid-size or larger organizations.",
            f"Subject matter familiarity relevant to this role, including {skills}.",
            "Strong stakeholder management and discretion with confidential information.",
            "Experience with ATS/HRIS tools and structured interview practices.",
            "Knowledge of regional employment regulations; willingness to escalate appropriately.",
            "Excellent organizational skills and calm communication under pressure.",
        ]
    elif job_type == JobType.OPS:
        role_para = (
            f"As {role}, you will tighten how work flows through the organization—metrics, vendors, and frontline execution. "
            "You will translate leadership goals into operating plans teams can run week to week."
        )
        do_lines = [
            "Own KPI dashboards and weekly operating reviews with clear actions and owners.",
            "Improve SOPs, playbooks, and handoffs between teams and external partners.",
            f"Apply analytical and tooling skills across areas such as {skills}.",
            "Lead or support cross-functional projects with realistic timelines and risk buffers.",
            "Identify bottlenecks in supply, service delivery, or internal workflows and drive fixes.",
            "Ensure vendor contracts and SLAs are tracked and renewed deliberately.",
        ]
        req_lines = [
            "3+ years in operations, business operations, or supply chain roles.",
            f"Demonstrated use of: {skills} in a professional context.",
            "Comfort with spreadsheets, basic data storytelling, and process mapping.",
            "Track record of finishing improvement projects, not only proposing them.",
            "Ability to influence without authority across departments.",
            "Experience in regulated or high-volume environments is a plus.",
        ]
    else:  # MANAGEMENT
        role_para = (
            f"As {role}, you will set direction for a team or portfolio while staying close to delivery realities. "
            "You will align stakeholders, allocate capacity, and uphold quality and people standards."
        )
        do_lines = [
            "Define goals, priorities, and success metrics; align teams and partners around them.",
            "Coach and develop direct reports; handle performance conversations with clarity and respect.",
            "Oversee budgets, forecasts, or resource plans within governance guardrails.",
            f"Steer initiatives that depend on expertise in {skills}.",
            "Represent the function in executive forums with concise narratives and options.",
            "Build hiring plans and succession depth for critical roles.",
        ]
        req_lines = [
            "5+ years of progressive experience including people leadership or large program ownership.",
            f"Depth in areas reflected by: {skills}.",
            "Proven ability to deliver business outcomes, not only manage activity.",
            "Excellent judgment on risk, compliance, and reputational exposure.",
            "Strong written and verbal communication for boards, clients, or regulators as needed.",
            "Experience leading through change and ambiguous mandates.",
        ]

    do_bullets = "\n".join(f"- {line}" for line in do_lines)
    req_bullets = "\n".join(f"- {line}" for line in req_lines)

    return (
        f"{company_name} — {role}\n\n"
        f"About {company_name}\n"
        f"{about}\n\n"
        f"The Role\n"
        f"{role_para}\n\n"
        f"What you'll do\n"
        f"{do_bullets}\n\n"
        f"What we're looking for\n"
        f"{req_bullets}\n\n"
        f"What we offer\n"
        f"- Competitive package: NM$ {salary_low:,} – NM$ {salary_high:,} depending on experience and level.\n"
        f"- Hybrid and remote-friendly arrangements where the role allows; core collaboration hours in Nova Meridian time.\n"
        f"- Health and dental coverage, parental leave, and an annual learning budget.\n"
        f"- 25 days paid annual leave plus public holidays; sick leave per policy.\n"
        f"- {offer_extra}"
    )


def fetch_media_and_cv_paths():
    """Download logos and portraits where possible; generate CV PDFs. Returns same shape as old write_placeholder_files."""
    paths: dict = {}
    ensure_upload_dirs()

    for i, c in enumerate(COMPANIES_DATA):
        q = urllib.parse.quote(c["name"])
        bg = LOGO_BG_COLORS[i % len(LOGO_BG_COLORS)]
        url = (
            f"https://ui-avatars.com/api/?name={q}&size=256&background={bg}&color=fff&format=png"
        )
        png_path = os.path.join(UPLOAD, "logos", f"logo_seed_{i}.png")
        jpg_fallback = os.path.join(UPLOAD, "logos", f"logo_seed_{i}.jpg")
        if download_url(url, png_path):
            paths[f"co{i}"] = f"logos/logo_seed_{i}.png"
        else:
            with open(jpg_fallback, "wb") as f:
                f.write(MINIMAL_JPEG)
            paths[f"co{i}"] = f"logos/logo_seed_{i}.jpg"

    applicant_headlines = [
        "Product-minded engineer focused on reliable APIs and clear developer experience.",
        "Full-stack builder who enjoys shipping UI polish and pragmatic backend design.",
        "Mobile specialist with a passion for performance, accessibility, and CI quality gates.",
        "Data and platform engineer comfortable owning pipelines and stakeholder reporting.",
        "People partner who scales fair processes and trusted manager relationships.",
        "Operator who loves turning messy workflows into measurable, repeatable systems.",
        "Consultant-style leader bridging strategy decks and on-the-ground delivery.",
        "Creative technologist blending storytelling with disciplined production schedules.",
        "Security-conscious developer advocating for safe defaults and threat modeling.",
        "Generalist engineer eager to grow breadth while deepening in high-impact areas.",
    ]
    applicant_skills = [
        "Python, FastAPI, PostgreSQL, Docker, AWS basics",
        "React, TypeScript, Node.js, REST, Git",
        "Swift, Kotlin, mobile CI, instrumentation",
        "SQL, Spark, Airflow, data modeling, visualization",
        "Workday, ATS administration, ER case handling, surveys",
        "Excel, SQL-light, process mapping, vendor management",
        "Stakeholder management, workshops, OKRs, governance",
        "Premiere, After Effects, DAM workflows, codecs",
        "AppSec, OAuth/OIDC, secure SDLC, logging",
        "Go, gRPC, Kubernetes fundamentals, observability",
    ]

    for i in range(10):
        gender = "men" if i % 2 == 0 else "women"
        pic_idx = (i // 2) % 99
        pic_url = f"https://randomuser.me/api/portraits/{gender}/{pic_idx}.jpg"
        pic_rel = f"pictures/pic_seed_{i}.jpg"
        pic_abs = os.path.join(UPLOAD, pic_rel)
        if not download_url(pic_url, pic_abs):
            with open(pic_abs, "wb") as f:
                f.write(MINIMAL_JPEG)

        name, email = APPLICANTS_DATA[i]
        cv_rel = f"cvs/cv_seed_{i}.pdf"
        cv_abs = os.path.join(UPLOAD, cv_rel)
        write_applicant_cv_pdf(
            cv_abs,
            name,
            email,
            applicant_headlines[i],
            applicant_skills[i],
        )
        paths[f"ap{i}"] = (pic_rel, cv_rel)

    return paths


JOB_BLUEPRINTS = [
    ("Senior Backend Engineer", JobType.SOFTWARE_DEV, "Python, FastAPI, PostgreSQL, AWS"),
    ("Full Stack Developer", JobType.SOFTWARE_DEV, "React, TypeScript, Node.js, REST APIs"),
    ("Mobile Engineer (iOS/Android)", JobType.SOFTWARE_DEV, "Swift, Kotlin, CI/CD"),
    ("DevOps Engineer", JobType.SOFTWARE_DEV, "Kubernetes, Terraform, observability"),
    ("QA Automation Lead", JobType.SOFTWARE_DEV, "Selenium, Pytest, test strategy"),
    ("Data Engineer", JobType.SOFTWARE_DEV, "Spark, Airflow, SQL, data modeling"),
    ("Security Engineer", JobType.SOFTWARE_DEV, "AppSec, threat modeling, SOC2"),
    ("Frontend Engineer", JobType.SOFTWARE_DEV, "React, accessibility, design systems"),
    ("Machine Learning Engineer", JobType.SOFTWARE_DEV, "PyTorch, ML ops, experimentation"),
    ("Site Reliability Engineer", JobType.SOFTWARE_DEV, "On-call, SLOs, incident response"),
    ("Software Engineer II", JobType.SOFTWARE_DEV, "Go, microservices, gRPC"),
    ("Platform Engineer", JobType.SOFTWARE_DEV, "Internal tooling, developer experience"),
    ("Engineering Manager", JobType.MANAGEMENT, "People leadership, delivery, roadmap"),
    ("Product Engineer", JobType.SOFTWARE_DEV, "Feature ownership, metrics, UX"),
    ("Cloud Architect", JobType.SOFTWARE_DEV, "Multi-region design, cost optimization"),
    ("HR Business Partner", JobType.HR, "Employee relations, policies, ER cases"),
    ("Talent Acquisition Specialist", JobType.HR, "Sourcing, interviewing, employer brand"),
    ("HR Operations Analyst", JobType.HR, "HRIS, audits, compliance"),
    ("Learning & Development Coordinator", JobType.HR, "Curriculum design, LMS"),
    ("Compensation Analyst", JobType.HR, "Benchmarking, surveys, equity"),
    ("People Operations Manager", JobType.HR, "Onboarding, HR programs"),
    ("Recruiter (Contract)", JobType.HR, "High-volume hiring, scheduling"),
    ("HR Generalist", JobType.HR, "Full-cycle HR support"),
    ("Diversity & Inclusion Lead", JobType.HR, "Programs, reporting, partnerships"),
    ("HRIS Administrator", JobType.HR, "Workday, integrations, reporting"),
    ("Employee Experience Manager", JobType.HR, "Engagement surveys, culture"),
    ("HR Compliance Specialist", JobType.HR, "Labor law, documentation"),
    ("Operations Manager", JobType.OPS, "Process improvement, KPIs, vendor mgmt"),
    ("Supply Chain Analyst", JobType.OPS, "Forecasting, inventory, logistics"),
    ("Business Operations Associate", JobType.OPS, "Cross-functional projects, reporting"),
    ("Facilities Coordinator", JobType.OPS, "Office ops, vendor contracts"),
    ("Program Operations Lead", JobType.OPS, "Stakeholder alignment, timelines"),
    ("General Manager", JobType.MANAGEMENT, "P&L ownership, strategy, teams"),
    ("Project Director", JobType.MANAGEMENT, "Large programs, governance, risk"),
    ("Head of Customer Success", JobType.MANAGEMENT, "Retention, playbooks, leadership"),
    ("Regional Operations Head", JobType.MANAGEMENT, "Multi-site leadership, audits"),
    ("Director of Strategy", JobType.MANAGEMENT, "Market analysis, OKRs, planning"),
    ("Chief of Staff", JobType.MANAGEMENT, "Exec comms, initiatives, prioritization"),
    ("Associate Director — Finance Ops", JobType.MANAGEMENT, "Budgeting, forecasting, controls"),
    ("Practice Lead (Consulting)", JobType.MANAGEMENT, "Client delivery, hiring, sales support"),
    ("Studio Producer", JobType.MANAGEMENT, "Production schedules, budgets, teams"),
    ("Head of Partnerships", JobType.MANAGEMENT, "BD pipeline, alliances, contracts"),
    ("Junior Software Engineer", JobType.SOFTWARE_DEV, "CS fundamentals, mentorship, code reviews"),
    ("Integration Engineer", JobType.SOFTWARE_DEV, "APIs, partner integrations, debugging"),
    ("Technical Writer (Engineering)", JobType.SOFTWARE_DEV, "Docs, developer guides, DX"),
    ("HR Coordinator", JobType.HR, "Scheduling, ATS hygiene, candidate comms"),
    ("Recruiting Operations Specialist", JobType.HR, "Metrics, tooling, process"),
    ("Warehouse Operations Lead", JobType.OPS, "3PL coordination, safety, throughput"),
    ("IT Operations Analyst", JobType.OPS, "Endpoints, access, service desk metrics"),
    ("Product Manager — Growth", JobType.MANAGEMENT, "Roadmaps, experiments, stakeholder alignment"),
]

APPLICANTS_DATA = [
    ("Priya Sharma", "priya.sharma@email.nm"),
    ("James Okonkwo", "james.okonkwo@email.nm"),
    ("Elena Vasquez", "elena.vasquez@email.nm"),
    ("Arjun Mehta", "arjun.mehta@email.nm"),
    ("Sofia Lindberg", "sofia.lindberg@email.nm"),
    ("Marcus Chen", "marcus.chen@email.nm"),
    ("Fatima Al-Rashid", "fatima.rashid@email.nm"),
    ("Oliver Grant", "oliver.grant@email.nm"),
    ("Ananya Iyer", "ananya.iyer@email.nm"),
    ("Diego Fernandez", "diego.fernandez@email.nm"),
]

DISCUSSION_TITLES = [
    "Interview experience at Meridian Tech — what to expect?",
    "Harborline case study round — tips?",
    "Salary bands for Software Dev in Nova Meridian (2025)",
    "How long does Crescent Logistics take to reply?",
    "Willowbrook onsite: parking and dress code",
    "Summit Consulting behavioral questions thread",
    "Pulse Media portfolio review — feedback welcome",
    "Switching from HR to People Ops — advice",
    "Ops manager interview: metrics they care about",
    "Rejected after final round — stay in touch?",
    "Meridian Tech culture — honest takes",
    "Preparing for technical system design in NM market",
    "Certifications worth it for DevOps roles here?",
    "Part-time vs contract: experiences in NM",
    "Recruiter ghosting — how long before follow-up?",
]


def seed():
    ensure_upload_dirs()
    file_paths = fetch_media_and_cv_paths()
    pw = hash_password("password123")

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    companies: list[Company] = []
    for i, c in enumerate(COMPANIES_DATA):
        co = Company(
            name=c["name"],
            location=c["location"],
            email=c["email"],
            password_hash=pw,
            logo_path=file_paths[f"co{i}"],
        )
        db.add(co)
        companies.append(co)
    db.commit()
    for c in companies:
        db.refresh(c)

    jobs: list[JobPosting] = []
    base_date = datetime.utcnow() - timedelta(days=120)
    for idx, (role, jt, skills) in enumerate(JOB_BLUEPRINTS):
        co = companies[idx % len(companies)]
        co_idx = idx % len(companies)
        created = base_date + timedelta(days=idx * 2, hours=(idx % 7) * 3)
        job = JobPosting(
            company_id=co.id,
            job_role=role,
            job_type=jt,
            location=random.choice(
                [
                    "On-site — Nova Meridian",
                    "Hybrid — Nova Meridian",
                    "Remote — Nova Meridian metro",
                ]
            ),
            description=jd_block(role, skills, co.name, jt, co_idx, idx),
            skills_required=skills,
            created_at=created,
            is_active=True,
        )
        db.add(job)
        jobs.append(job)
    db.commit()
    for j in jobs:
        db.refresh(j)

    applicants: list[Applicant] = []
    for i, (name, email) in enumerate(APPLICANTS_DATA):
        pic, cv = file_paths[f"ap{i}"]
        ap = Applicant(
            name=name,
            email=email,
            password_hash=pw,
            picture_path=pic,
            cv_path=cv,
        )
        db.add(ap)
        applicants.append(ap)
    db.commit()
    for a in applicants:
        db.refresh(a)

    pairs = []
    job_ids = [j.id for j in jobs]
    app_ids = [a.id for a in applicants]
    for _ in range(50):
        pairs.append((random.choice(job_ids), random.choice(app_ids)))
    seen = set()
    unique = []
    for p in pairs:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    while len(unique) < 50:
        p = (random.choice(job_ids), random.choice(app_ids))
        if p not in seen:
            seen.add(p)
            unique.append(p)

    statuses = ["Applied", "Interview", "Accepted", "Rejected"]
    weights = [0.35, 0.25, 0.15, 0.25]
    for i, (jid, aid) in enumerate(unique[:50]):
        st = random.choices(statuses, weights=weights, k=1)[0]
        applied = base_date + timedelta(days=i, hours=i % 12)
        db.add(
            Application(
                job_id=jid,
                applicant_id=aid,
                status=st,
                applied_at=applied,
                updated_at=applied,
            )
        )
    db.commit()

    roots: list[Discussion] = []
    for i in range(18):
        title = DISCUSSION_TITLES[i % len(DISCUSSION_TITLES)]
        job = jobs[i % len(jobs)]
        co = companies[i % len(companies)]
        author_ap = applicants[i % len(applicants)]
        d = Discussion(
            title=title,
            body=(
                f"Starting a thread about {title.lower()}. "
                f"Tagging @{co.name.split()[0]} — anyone recently go through this process?"
            ),
            job_id=job.id if i % 3 != 0 else None,
            company_id=co.id if i % 2 == 0 else None,
            author_id=author_ap.id,
            author_type=AuthorType.APPLICANT,
            parent_id=None,
            created_at=base_date + timedelta(days=i),
        )
        db.add(d)
        roots.append(d)
    db.commit()
    for r in roots:
        db.refresh(r)

    disc_count = 18
    reply_idx = 0
    while disc_count < 50:
        non_root = db.query(Discussion).filter(Discussion.parent_id.isnot(None)).all()
        pool = roots + non_root if (disc_count > 28 and non_root) else roots
        parent = random.choice(pool)
        use_company = random.random() < 0.15 and parent.parent_id is None
        author_id = companies[reply_idx % len(companies)].id if use_company else applicants[reply_idx % len(applicants)].id
        atype = AuthorType.COMPANY if use_company else AuthorType.APPLICANT
        pid = parent.id
        d = Discussion(
            title=None,
            body=(
                "Thanks for sharing — I had a similar experience. "
                "Happy to compare notes on timeline and interview format."
            ),
            job_id=parent.job_id,
            company_id=parent.company_id,
            author_id=author_id,
            author_type=atype,
            parent_id=pid,
            created_at=parent.created_at + timedelta(hours=reply_idx + 1),
        )
        db.add(d)
        disc_count += 1
        reply_idx += 1
    db.commit()

    db.close()
    print("Seed complete: 7 companies, 50 jobs, 10 applicants, 50 applications, 50 discussion rows.")
    print("Test login password for all seeded users: password123")


if __name__ == "__main__":
    seed()
