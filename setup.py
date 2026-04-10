#!/usr/bin/env python3
"""
AgentSoul — Framework-agnostic agent persistence platform
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_path = Path(__file__).parent / "agent_soul_platform" / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

setup(
    name="agentsoul",
    version="1.0.0",
    author="AgentSoul Contributors",
    author_email="support@agentsoul.io",
    description="Framework-agnostic agent persistence platform with AES-256-GCM encryption",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/agentsoul/agentsoul",
    project_urls={
        "Bug Tracker": "https://github.com/agentsoul/agentsoul/issues",
        "Documentation": "https://github.com/agentsoul/agentsoul",
        "Source Code": "https://github.com/agentsoul/agentsoul",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
        "cryptography>=40.0.0",
        "pocketbase>=0.8.0",
    ],
    extras_require={
        "dev": ["pytest>=7.0", "pytest-cov>=4.0"],
        "rest": ["flask>=2.0"],
    },
)
