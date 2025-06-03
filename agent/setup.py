# agent/setup.py

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="interview_ai_agent",
    version="0.1.0",
    author="AI面试评测团队",
    author_email="example@example.com",
    description="多模态面试评测智能体库",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/interview_ai_agent",
    package_dir={'': 'src'},
    packages=find_packages(where='src', include=['*', 'analyzers.*', 'core.*', 'learning.*', 'nodes.*', 'services.*', 'utils.*', 'scenarios.*']),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "numpy",
        "opencv-python",
        "librosa",
        "torch",
        "transformers",
        "requests",
    ],
)