from setuptools import setup, find_packages
VERSION = '0.0.1'
DESCRIPTION = 'Twitter and SERP Summarizer'

setup(
    name='scraper_summarizer_tool',
    version=VERSION,
    packages=find_packages(),
    description=DESCRIPTION,
    install_requires=[
        'pydantic~=2.6.4',
        'starlette~=0.37.2',
        'torch==2.1.0',
        'openai>=1.3.2',
        'requests==2.31.0',
        'Pillow==9.3.0',
        'aiohttp==3.9.0b0',
        'transformers==4.37.2',
        'scikit-learn==1.3.2',
        'datasets==2.17.0',
        'sentencepiece==0.1.99',
        'google-search-results==2.4.2',
        'urllib3==1.26.9',
        'wikipedia==1.4.0',
        'youtube-search==2.1.2',
        'accelerate==0.27.2',
        'setuptools~=69.1.1',
        'langchain~=0.1.14',
        'python-dotenv~=1.0.1'
    ],
)