#!/usr/bin/env python3
"""
COINjecture Distribution Setup
Creates wheel packages for easy installation
"""

from setuptools import setup, find_packages
import os

# Read version from src/api/__init__.py
def get_version():
    with open('src/api/__init__.py', 'r') as f:
        for line in f:
            if line.startswith('__version__'):
                return line.split('=')[1].strip().strip('"').strip("'")
    return "3.3.1"

# Read long description from README
def get_long_description():
    with open('README.md', 'r', encoding='utf-8') as f:
        return f.read()

# Read requirements
def get_requirements():
    with open('requirements.txt', 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="coinjecture",
    version=get_version(),
    author="COINjecture Team",
    author_email="contact@coinjecture.org",
    description="Mathematical Proof-of-Work Blockchain with NP-Complete Problem Solving",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/beanapologist/COINjecture",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Mathematics",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Office/Business :: Financial",
    ],
    python_requires=">=3.9",
    install_requires=get_requirements(),
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.800",
        ],
        "api": [
            "Flask>=2.0.0",
            "Flask-CORS>=3.0.0",
            "Flask-Limiter>=2.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "coinjectured=src.cli:main",
            "coinjecture=src.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.json"],
    },
    keywords=[
        "blockchain",
        "proof-of-work",
        "np-complete",
        "mathematics",
        "cryptocurrency",
        "mining",
        "subset-sum",
        "computational-complexity",
    ],
    project_urls={
        "Bug Reports": "https://github.com/beanapologist/COINjecture/issues",
        "Source": "https://github.com/beanapologist/COINjecture",
        "Documentation": "https://github.com/beanapologist/COINjecture/blob/main/README.md",
    },
)
