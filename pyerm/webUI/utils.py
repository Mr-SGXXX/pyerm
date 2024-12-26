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

# Version: 0.3.2

import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import io
import os

class LanguageManager:
    def __init__(self, default_language="English"):
        self.translations_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "language_data")
        self.language = default_language
        self.default_translations = self.load_language("English")
        self.translations = self.load_language(default_language)

    def load_language(self, language):
        file_path = os.path.join(self.translations_dir, f"string_{language}.xml")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Language file not found: {file_path}")
        return load_language_file(file_path)

    def set_language(self, language):
        self.language = language
        self.translations = self.load_language(language)

    def translate(self, key):
        keys = key.split(".")
        try:
            template = self.translations
            for k in keys:
                template = template[k]
        except KeyError:
            template = self.default_translations
            for k in keys:
                template = template[k]
        
        return template
    
    def __getitem__(self, key):
        return self.translate(key)

def detect_languages():
    translations_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "language_data")
    languages = []
    for file in os.listdir(translations_dir):
        if file.startswith("string_") and file.endswith(".xml"):
            languages.append(file[7:-4])
    return languages

def parse_xml_to_dict(element):
    translations = {}
    for child in element:
        if len(child):
            translations[child.tag] = parse_xml_to_dict(child)
        else:
            translations[child.tag] = child.text
    return translations

def load_language_file(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    return parse_xml_to_dict(root)

def boxplot(df:pd.DataFrame, x:str, y:str, title:str='', figsize=(10, 6), **additional_params_dict):
    fig, ax = plt.subplots(figsize=figsize)
    if 'palette' not in additional_params_dict:
        additional_params_dict['palette'] = 'Set2'
    if 'linewidth' not in additional_params_dict:
        additional_params_dict['linewidth'] = 2.5
    sns.boxplot(data=df, hue=x, x=x, y=y, ax=ax, **additional_params_dict)
    if title != '':
        ax.set_title(title, fontsize=16)
    ax.set_xlabel(x, fontsize=14)
    ax.set_ylabel(y, fontsize=14)
    ax.grid(True, linestyle='--', alpha=0.7)
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    return buf

def violinplot(df:pd.DataFrame, x:str, y:str, title:str='', figsize=(10, 6), **additional_params_dict):
    fig, ax = plt.subplots(figsize=figsize)
    if 'palette' not in additional_params_dict:
        additional_params_dict['palette'] = 'Set2'
    if 'linewidth' not in additional_params_dict:
        additional_params_dict['linewidth'] = 2.5
    sns.violinplot(data=df, hue=x, x=x, y=y, ax=ax, **additional_params_dict)
    if title != '':
        ax.set_title(title, fontsize=16)
    ax.set_xlabel(x, fontsize=14)
    ax.set_ylabel(y, fontsize=14)
    ax.grid(True, linestyle='--', alpha=0.7)
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    return buf

def lineplot(df:pd.DataFrame, x:str, y:str, title:str='', figsize=(10, 6), **additional_params_dict):
    fig, ax = plt.subplots(figsize=figsize)
    if 'palette' not in additional_params_dict:
        additional_params_dict['palette'] = 'Set2'
    if 'linewidth' not in additional_params_dict:
        additional_params_dict['linewidth'] = 2.5
    sns.lineplot(data=df, x=x, y=y, ax=ax, **additional_params_dict)
    if title != '':
        ax.set_title(title, fontsize=16)
    ax.set_xlabel(x, fontsize=14)
    ax.set_ylabel(y, fontsize=14)
    ax.grid(True, linestyle='--', alpha=0.7)
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    return buf

def barplot(df:pd.DataFrame, x:str, y:str, title:str='', figsize=(10, 6), **additional_params_dict):
    fig, ax = plt.subplots(figsize=figsize)
    if 'palette' not in additional_params_dict:
        additional_params_dict['palette'] = 'Set2'
    if 'linewidth' not in additional_params_dict:
        additional_params_dict['linewidth'] = 2.5
    sns.barplot(data=df, hue=x, x=x, y=y, ax=ax, **additional_params_dict)
    if title != '':
        ax.set_title(title, fontsize=16)
    ax.set_xlabel(x, fontsize=14)
    ax.set_ylabel(y, fontsize=14)
    ax.grid(True, linestyle='--', alpha=0.7)
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    return buf

