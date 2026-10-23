"""
Setup script for Payment Sharding Network with ZK Privacy
"""

from setuptools import setup, find_packages

setup(
    name="payment-sharding-network",
    version="1.0.0",
    description="Sharded payment settlement network with zero-knowledge privacy for digital currencies",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Payment Research Team",
    author_email="contact@technograte.com.au",
    url="https://github.com/engr-dr-ammad/Claude",
    license="MIT",
    python_requires=">=3.8",
    py_modules=["simulator", "zk_aggregation", "analysis", "cli"],
    entry_points={
        "console_scripts": [
            "payment-shard=cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Office/Business :: Financial",
        "Topic :: Security :: Cryptography",
    ],
    keywords="blockchain sharding zero-knowledge privacy cbdc payments settlement",
)
