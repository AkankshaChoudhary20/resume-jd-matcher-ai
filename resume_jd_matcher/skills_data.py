"""
A curated, extendable list of common tech/professional skill keywords used by
the term-extraction step in matching.py.

This is deliberately a plain Python list (not a package dependency) so it's
easy to extend: add new terms as lowercase strings. Multi-word skills are
matched as exact phrases; extraction in matching.py handles word-boundary
matching so substrings inside unrelated words won't false-positive.

This list is NOT exhaustive -- it's a reasonable starting point covering
common software engineering / data / product skill vocabulary. Extend it for
your own domain (e.g. add marketing, legal, healthcare terms) as needed.
"""

KNOWN_SKILLS = [
    # Programming languages
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "golang",
    "rust", "ruby", "php", "swift", "kotlin", "scala", "r", "matlab", "perl",
    "bash", "shell scripting", "sql", "html", "css", "objective-c",

    # Web / backend frameworks
    "django", "flask", "fastapi", "react", "react.js", "angular", "vue",
    "vue.js", "node.js", "express", "spring", "spring boot", "rails",
    "ruby on rails", "asp.net", ".net", "graphql", "rest", "rest api",
    "restful api", "microservices", "next.js", "svelte",

    # Data / ML
    "machine learning", "deep learning", "artificial intelligence",
    "natural language processing", "nlp", "computer vision", "data science",
    "data analysis", "data engineering", "data visualization", "pandas",
    "numpy", "scikit-learn", "tensorflow", "pytorch", "keras", "spark",
    "apache spark", "hadoop", "airflow", "etl", "tableau", "power bi",
    "statistics", "a/b testing", "predictive modeling", "llm",
    "large language models", "generative ai", "prompt engineering",

    # Cloud / DevOps
    "aws", "amazon web services", "azure", "gcp", "google cloud platform",
    "docker", "kubernetes", "terraform", "ansible", "jenkins", "ci/cd",
    "devops", "linux", "unix", "nginx", "load balancing", "serverless",
    "lambda", "cloudformation", "helm", "prometheus", "grafana",

    # Databases
    "postgresql", "postgres", "mysql", "mongodb", "redis", "sqlite",
    "elasticsearch", "dynamodb", "cassandra", "oracle", "nosql",
    "database design", "data modeling",

    # Tools / practices
    "git", "github", "gitlab", "jira", "confluence", "agile", "scrum",
    "kanban", "unit testing", "test driven development", "tdd",
    "continuous integration", "continuous deployment", "api design",
    "system design", "object oriented programming", "oop",
    "design patterns", "code review", "debugging",

    # Product / soft skills (still concrete/matchable)
    "project management", "product management", "stakeholder management",
    "cross-functional collaboration", "technical writing", "mentoring",
    "leadership", "communication", "problem solving", "team leadership",
    "roadmap planning", "requirements gathering",

    # Security
    "cybersecurity", "penetration testing", "encryption", "oauth",
    "authentication", "authorization", "security auditing",

    # Mobile
    "ios", "android", "react native", "flutter", "mobile development",

    # Other common business/analytics terms
    "excel", "salesforce", "sap", "erp", "crm", "seo", "sem",
    "google analytics", "marketing automation",
]
