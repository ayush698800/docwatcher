from setuptools import setup, find_packages

setup(
    name='docdrift',
    version='2.0.0',
    author='ayush698800',
    description='Finds stale documentation and fixes it automatically using AI',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/ayush698800/docwatcher',
    packages=find_packages(),
    install_requires=[
        'click>=8.0',
        'gitpython>=3.1',
        'rich>=13.0',
        'tree-sitter>=0.21',
        'tree-sitter-python>=0.21',
        'tree-sitter-javascript>=0.21',
        'chromadb>=0.4',
        'sentence-transformers>=2.2',
        'groq>=0.4',
        'requests>=2.28',
    ],
    entry_points={
        'console_scripts': [
            'docdrift=docwatcher.cli:cli',
        ],
    },
    python_requires='>=3.11',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)