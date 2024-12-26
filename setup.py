# MIT License

# Copyright (c) 2024 Yuxuan Shao

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# Version: 0.3.3
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name='pyerm',
    version='0.3.3',
    author='Yuxuan Shao',
    author_email='yx_shao@qq.com',
    description='This project is an local experiment record manager for python based on SQLite DMS, suitable for recording experiment and analysing experiment data with a web UI, which can help you efficiently save your experiment settings and results for later analysis.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Mr-SGXXX/pyerm",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'pyerm_export_zip=pyerm.scripts.export_data:main',
            'pyerm_db_merge=pyerm.scripts.db_merge:main',
            'pyerm_webui=pyerm.scripts.erm_webui:main',
        ],
    },
    install_requires=[
        "pandas",
        "pillow",
        "xlsxwriter",
        "numpy",
        "matplotlib",
        "seaborn",
        "streamlit>=1.39.0"
    ],
    python_requires='>=3.9',
)
