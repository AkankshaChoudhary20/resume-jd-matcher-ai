from setuptools import find_packages, setup

setup(
    name="resume-jd-matcher",
    version="0.1.0",
    description=(
        "Compare a resume against a job description: score skill/keyword "
        "overlap, identify gaps, and optionally generate Claude-tailored "
        "resume bullet suggestions."
    ),
    packages=find_packages(exclude=["tests", "tests.*"]),
    install_requires=[
        "anthropic>=1.4.0",
        "scikit-learn>=1.9.0",
    ],
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "resume-jd-matcher=resume_jd_matcher.cli:main",
        ],
    },
)
