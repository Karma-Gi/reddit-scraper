#!/usr/bin/env python3
"""
Setup script for the Reddit Study Abroad Data Scraper
"""

from setuptools import setup, find_packages
import os

# Read README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="reddit-study-abroad-scraper",
    version="1.0.0",
    author="Data Science Intern",
    author_email="intern@perfects.ai",
    description="Reddit scraper for study abroad discussion data mining and processing",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/perfects-ai/reddit-study-abroad-scraper",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Text Processing :: Linguistic",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],
        "ml": [
            "openai>=1.0.0",
            "anthropic>=0.7.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "reddit-scraper=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.yml", "*.txt", "*.md"],
    },
    project_urls={
        "Bug Reports": "https://github.com/perfects-ai/reddit-study-abroad-scraper/issues",
        "Source": "https://github.com/perfects-ai/reddit-study-abroad-scraper",
        "Documentation": "https://github.com/perfects-ai/reddit-study-abroad-scraper/blob/main/README.md",
    },
)
