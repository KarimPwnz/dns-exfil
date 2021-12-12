import setuptools

with open("README.md", "r") as f:
    long_description = f.read()

setuptools.setup(
    name="dns-exfil",
    version="0.0.1",
    author="karimpwnz",
    author_email="karim@karimrahal.com",
    description="Open a DNS server that knows no records but records every request. Used for DNS exfiltration.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/karimpwnz/dns-exfil",
    project_urls={
        "Bug Tracker": "https://github.com/karimpwnz/dns-exfil/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Security",
        "Topic :: Internet :: Name Service (DNS)"
    ],
    packages=["dns_exfil"],
    entry_points={"console_scripts": ["dns-exfil = dns_exfil.__main__:main"]},
    python_requires=">=3.6",
    install_requires=[
        "dnslib >= 0.9.1"
    ],
)
