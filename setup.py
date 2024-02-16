from setuptools import setup

setup(
    name='my_climate_dashboard_backend',
    version='0.0.0',
    description='Backend for my climate dashboard',
    long_description=open('README.md').read(),
    author='Natalie Grefenstette, Ridhee Gupta, Helen Li, Christine Madden',
    license=open('LICENSE').read(),
    author_email='',
    packages=['my_climate_dashboard_backend'],
    install_requires=[
        "flask",
        "flask-restful",
        "gunicorn",
        "pandas",
        "matplotlib",
        "requests",
        "google-api-python-client",
        "google-auth-httplib2 google-auth-oauthlib",
    ],
    extras_require={
            "dev": [
                "black",  # lint & formatting helper
                "flake8",  # lint & formatting helper
                "isort",  # lint & formatting helper
                "sphinx",  # documentation
                "sphinx-autoapi",  # documentation
                "sphinx-mdinclude",  # documentation
                "sphinx-rtd-theme",  # read-the-docs theme
                "docstr-coverage",  # doc string coverage
                "wily",
                "coverage",
                "coverage-badge",
                "docstr-coverage",
                "pybadges",
                "pylint",
                "pytest",
        ],
    },
    entry_points={
        'console_scripts':
        [
            'my_climate_dashboard_backend = my_climate_dashboard_backend.__main__:main',
        ]
    }
)
