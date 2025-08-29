# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from setuptools import setup, find_packages

setup(
    name="proteingo",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.31.0",
        "numpy>=1.24.0",
        "pandas>=2.0.0",
        "python-dotenv>=1.0.0",
        "pytest>=7.4.0",
        "tqdm>=4.65.0",
        "biopython>=1.81",
        "scikit-learn>=1.3.0",
    ],
    entry_points={
        'console_scripts': [
            'proteingo=src.main:main',
        ],
    },
) 