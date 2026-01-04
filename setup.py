from setuptools import setup, find_packages

def read_file(filename):
    with open(filename, encoding="utf-8") as f:
        return f.read()

setup(
    name="dictwhisperer",
    version="1.0.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "dictwhisperer = dictwhisperer.cli:main",
        ],
    },
    install_requires=[
        "openai-whisper",
        "sounddevice",
        "numpy",
    ],
    author="80nF1R3H34D",
    author_email="",  # Update if you have a public email
    description="Real-time voice dictation to Obsidian using OpenAI Whisper.",
    long_description=read_file("README.md"),
    long_description_content_type="text/markdown",
    url="https://github.com/80nF1R3H34D/Dict_Whisperer",
    project_urls={
        "Bug Tracker": "https://github.com/80nF1R3H34D/Dict_Whisperer/issues",
        "Source Code": "https://github.com/80nF1R3H34D/Dict_Whisperer",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "Topic :: Text Processing :: Linguistic",
    ],
    python_requires='>=3.10, <3.14',
    keywords="whisper, obsidian, dictation, speech-to-text, ai",
)
