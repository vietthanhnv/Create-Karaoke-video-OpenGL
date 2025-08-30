"""
Setup script for Karaoke Subtitle Creator.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read requirements from requirements.txt
requirements_path = Path(__file__).parent / "requirements.txt"
with open(requirements_path, 'r', encoding='utf-8') as f:
    requirements = [
        line.strip() 
        for line in f 
        if line.strip() and not line.startswith('#') and not line.startswith('cupy') and not line.startswith('torch')
    ]

# Read README if it exists
readme_path = Path(__file__).parent / "README.md"
long_description = ""
if readme_path.exists():
    with open(readme_path, 'r', encoding='utf-8') as f:
        long_description = f.read()

setup(
    name="karaoke-subtitle-creator",
    version="1.0.0",
    author="Karaoke Subtitle Creator Team",
    description="Professional desktop application for creating karaoke videos with advanced text effects",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "karaoke-creator=main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Multimedia :: Video",
        "Topic :: Multimedia :: Graphics",
    ],
    include_package_data=True,
    package_data={
        "": ["*.glsl", "*.ttf", "*.otf", "*.png", "*.jpg"],
    },
)