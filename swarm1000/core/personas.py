"""Persona generation for 1000 logical agents."""

import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path

from .logger import logger


@dataclass
class Persona:
    """Agent persona with role, skills, and constraints."""
    id: str
    role: str
    seniority: str
    stack: list[str]
    style: str
    constraints: list[str]
    review_skill: int  # 1-10


# Role distribution according to requirements
ROLE_DISTRIBUTION = {
    "PM-Chief": 1,
    "PM": 3,
    "Tech Lead": 10,
    "Backend Engineer": 250,
    "Frontend Engineer": 250,
    "Rust/Protocol Engineer": 150,
    "DevOps/SRE": 100,
    "QA/Automation": 120,
    "Security/Performance": 80,
    "Design/UX/Copywriting": 36,
}

SENIORITY_LEVELS = ["Junior", "Mid", "Senior", "Staff", "Principal"]

BACKEND_STACKS = [
    ["Python", "FastAPI", "PostgreSQL"],
    ["Python", "Django", "Redis"],
    ["Node.js", "Express", "MongoDB"],
    ["Go", "gRPC", "Kafka"],
    ["Java", "Spring Boot", "MySQL"],
]

FRONTEND_STACKS = [
    ["React", "TypeScript", "Vite"],
    ["Vue", "TypeScript", "Tailwind"],
    ["Svelte", "JavaScript", "CSS"],
    ["Next.js", "React", "TypeScript"],
    ["Angular", "TypeScript", "RxJS"],
]

RUST_STACKS = [
    ["Rust", "Tokio", "async"],
    ["Rust", "actix-web", "PostgreSQL"],
    ["Rust", "WebAssembly", "WASI"],
    ["Rust", "embedded", "no_std"],
]

DEVOPS_STACKS = [
    ["Kubernetes", "Terraform", "AWS"],
    ["Docker", "GitLab CI", "GCP"],
    ["Ansible", "GitHub Actions", "Azure"],
    ["Helm", "ArgoCD", "Prometheus"],
]

QA_STACKS = [
    ["Selenium", "Python", "pytest"],
    ["Cypress", "JavaScript", "Mocha"],
    ["Playwright", "TypeScript", "Jest"],
    ["JMeter", "Gatling", "K6"],
]

SECURITY_STACKS = [
    ["OWASP", "Burp Suite", "Nmap"],
    ["CodeQL", "Snyk", "SonarQube"],
    ["Penetration Testing", "Metasploit"],
    ["Security Audit", "Compliance"],
]

DESIGN_STACKS = [
    ["Figma", "UI/UX", "Design Systems"],
    ["Adobe XD", "Prototyping"],
    ["Copywriting", "Content Strategy"],
    ["Accessibility", "WCAG"],
]

CODING_STYLES = [
    "pragmatic",
    "test-driven",
    "clean-code-focused",
    "performance-oriented",
    "security-first",
    "documentation-heavy",
]

COMMON_CONSTRAINTS = [
    "Follow PEP 8 for Python",
    "Use type hints",
    "Write comprehensive tests",
    "Document all public APIs",
    "Security audit before commit",
    "Performance profiling on critical paths",
    "Accessibility compliance",
    "Energy-efficient code",
]


def generate_personas(count: int = 1000) -> list[Persona]:
    """
    Generate personas according to role distribution.

    Args:
        count: Total number of personas to generate (default 1000)

    Returns:
        List of Persona objects
    """
    personas = []
    persona_id = 1

    for role, role_count in ROLE_DISTRIBUTION.items():
        for _ in range(role_count):
            # Determine seniority
            if role in ["PM-Chief", "PM"]:
                seniority = "Principal"
            elif role == "Tech Lead":
                # Tech Leads should be senior - weighted towards Staff/Principal
                weights = [0.2, 0.5, 0.3]  # Senior, Staff, Principal
                seniority = random.choices(["Senior", "Staff", "Principal"], weights=weights)[0]
            else:
                weights = [0.2, 0.35, 0.3, 0.1, 0.05]  # Junior to Principal
                seniority = random.choices(SENIORITY_LEVELS, weights=weights)[0]

            # Determine stack
            if "Backend" in role:
                stack = random.choice(BACKEND_STACKS)
            elif "Frontend" in role:
                stack = random.choice(FRONTEND_STACKS)
            elif "Rust" in role or "Protocol" in role:
                stack = random.choice(RUST_STACKS)
            elif "DevOps" in role or "SRE" in role:
                stack = random.choice(DEVOPS_STACKS)
            elif "QA" in role or "Automation" in role:
                stack = random.choice(QA_STACKS)
            elif "Security" in role or "Performance" in role:
                stack = random.choice(SECURITY_STACKS)
            elif "Design" in role or "UX" in role or "Copywriting" in role:
                stack = random.choice(DESIGN_STACKS)
            else:
                stack = ["General", "Agile", "Communication"]

            # Determine style
            style = random.choice(CODING_STYLES)

            # Determine constraints (2-4 random constraints)
            constraints = random.sample(COMMON_CONSTRAINTS, k=random.randint(2, 4))

            # Review skill based on seniority
            review_skill_map = {
                "Junior": random.randint(3, 5),
                "Mid": random.randint(5, 7),
                "Senior": random.randint(7, 9),
                "Staff": random.randint(8, 10),
                "Principal": random.randint(9, 10),
            }
            review_skill = review_skill_map.get(seniority, 5)

            persona = Persona(
                id=f"agent-{persona_id:04d}",
                role=role,
                seniority=seniority,
                stack=stack,
                style=style,
                constraints=constraints,
                review_skill=review_skill,
            )
            personas.append(persona)
            persona_id += 1

    # Fill remaining slots with balanced mix if needed
    while len(personas) < count:
        role = random.choice(list(ROLE_DISTRIBUTION.keys()))
        seniority = random.choice(SENIORITY_LEVELS)
        stack = ["General", "Multi-domain"]
        style = random.choice(CODING_STYLES)
        constraints = random.sample(COMMON_CONSTRAINTS, k=3)
        review_skill = random.randint(5, 8)

        persona = Persona(
            id=f"agent-{persona_id:04d}",
            role=role,
            seniority=seniority,
            stack=stack,
            style=style,
            constraints=constraints,
            review_skill=review_skill,
        )
        personas.append(persona)
        persona_id += 1

    return personas[:count]


def save_personas_jsonl(personas: list[Persona], output_path: Path) -> None:
    """
    Save personas to JSONL file.

    Args:
        personas: List of personas to save
        output_path: Path to output JSONL file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        for persona in personas:
            f.write(json.dumps(asdict(persona)) + '\n')

    logger.info(f"Saved {len(personas)} personas to {output_path}")


def load_personas_jsonl(input_path: Path) -> list[Persona]:
    """
    Load personas from JSONL file.

    Args:
        input_path: Path to JSONL file

    Returns:
        List of Persona objects
    """
    personas = []
    with open(input_path) as f:
        for line in f:
            data = json.loads(line)
            personas.append(Persona(**data))

    logger.info(f"Loaded {len(personas)} personas from {input_path}")
    return personas
