from pathlib import Path

from setuptools import find_packages, setup

README = Path(__file__).with_name("README.md").read_text(encoding="utf-8")

setup(
    name="docdrift",
    version="2.1.0",
    author="ayush698800",
    description="Detect and fix stale documentation before it reaches your next commit.",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/ayush698800/docwatcher",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "click>=8.1",
        "gitpython>=3.1",
        "rich>=13.0",
        "tree-sitter>=0.21",
        "tree-sitter-python>=0.21",
        "tree-sitter-javascript>=0.21",
        "tree-sitter-typescript>=0.21",
        "chromadb>=0.4",
        "sentence-transformers>=2.2",
        "groq>=0.4",
        "requests>=2.28",
    ],
    entry_points={
        "console_scripts": [
            "docdrift=docwatcher.cli:cli",
        ],
    },
    python_requires=">=3.11",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Documentation",
        "Topic :: Software Development :: Quality Assurance",
    ],
)
