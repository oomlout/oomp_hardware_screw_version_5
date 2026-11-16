"""Refresh documentation from existing assets without rebuilding parts."""
from pathlib import Path
from oomp_documentation import generate

def main(**kwargs):
    return generate(Path(__file__).resolve().parent)

if __name__ == "__main__":
    print(main())
