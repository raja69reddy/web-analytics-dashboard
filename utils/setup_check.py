"""Verify all required packages are importable. Run after pip install -r requirements.txt."""
import sys


def check():
    packages = [
        ("psycopg2",       "psycopg2-binary"),
        ("sqlalchemy",     "sqlalchemy"),
        ("pandas",         "pandas"),
        ("dotenv",         "python-dotenv"),
        ("numpy",          "numpy"),
        ("streamlit",      "streamlit"),
        ("plotly",         "plotly"),
        ("altair",         "altair"),
        ("requests",       "requests"),
        ("bs4",            "beautifulsoup4"),
        ("user_agents",    "user-agents"),
        ("tqdm",           "tqdm"),
        ("click",          "click"),
        ("dateutil",       "python-dateutil"),
        ("faker",          "Faker"),
    ]

    failed = []
    for module, pkg in packages:
        try:
            __import__(module)
        except ImportError:
            failed.append(pkg)

    if failed:
        print(f"MISSING packages: {', '.join(failed)}")
        print("Run: pip install -r requirements.txt")
        sys.exit(1)
    else:
        print("All packages OK")


if __name__ == "__main__":
    check()
