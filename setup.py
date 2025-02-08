from setuptools import setup, find_packages

setup(
    name="ai-pc-manager",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "aiohttp>=3.8.5",
    ],
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "ai-pc-manager=ai_pc_manager.cli:main",
        ],
    },
)