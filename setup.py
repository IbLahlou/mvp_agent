from setuptools import setup, find_packages

setup(
    name="lang_stack_proj",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "python-dotenv",
        "langchain",
        "redis",
        "openai",
        "pydantic",
        "pydantic-settings"
    ],
)