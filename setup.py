from setuptools import setup, find_packages

setup(
    name="shadowsip",
    version="0.1.0",
    description="Universal Open-Source SIP Softphone",
    author="ShadowPBX Project",
    license="GPL-3.0",
    url="https://github.com/dhirendralive9/shadowsip",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.10",
    install_requires=[
        "PySide6>=6.5",
    ],
    entry_points={
        "console_scripts": [
            "shadowsip=shadowsip.main:main",
        ],
    },
    package_data={
        "shadowsip": ["../../resources/**/*"],
    },
)
