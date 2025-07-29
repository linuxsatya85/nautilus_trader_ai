#!/usr/bin/env python3
"""
AI Nautilus Trader - Complete AI-Enhanced Trading Backend
=========================================================

A production-ready AI trading system that integrates CrewAI and Nautilus Trader
frameworks with custom adapters for intelligent trading operations.

Features:
- Complete CrewAI framework integration
- Complete Nautilus Trader framework integration  
- Custom integration adapters
- Production-ready API endpoints
- Comprehensive testing suite
- Zero-configuration setup

Author: AI Trading Systems
License: MIT
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="ai-nautilus-trader",
    version="1.0.0",
    author="AI Trading Systems",
    author_email="contact@aitradingsystems.com",
    description="Complete AI-Enhanced Trading Backend with CrewAI and Nautilus Trader",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/linuxsatya85/nautilus_trader_ai",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Office/Business :: Financial :: Investment",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
        ],
        "docs": [
            "sphinx>=4.0.0",
            "sphinx-rtd-theme>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "ai-nautilus-trader=ai_nautilus_trader.cli:main",
            "ant-server=ai_nautilus_trader.server:run_server",
            "ant-test=ai_nautilus_trader.tests:run_tests",
        ],
    },
    include_package_data=True,
    package_data={
        "ai_nautilus_trader": [
            "config/*.yaml",
            "config/*.json",
            "templates/*.html",
            "static/*",
        ],
    },
    zip_safe=False,
)
