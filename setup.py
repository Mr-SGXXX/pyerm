from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name='pyerm',
    version='0.1.3',
    author='Yuxuan Shao',
    author_email='yx_shao@qq.com',
    description='This project is an experiment record manager for python based on SQLite DMS, which can help you efficiently save your experiment settings and results for latter analysis.',
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
)
