from setuptools import setup, find_packages

setup(
    name="dictwhisperer",
    version="0.1.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "dictwhisperer = dictwhisperer.dictwhisperer:main",
        ],
    },
    install_requires=[
        "openai-whisper",
        "sounddevice",
        "numpy",
    ],
    author="Your Name",
    author_email="your.email@example.com",
    description="Real-time voice dictation to Obsidian using OpenAI Whisper.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/dictwhisperer",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.10, <3.14',
)
