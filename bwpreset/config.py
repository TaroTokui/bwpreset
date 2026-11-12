"""Find installed Bitwig resources without bundling vendor content."""

import os
from pathlib import Path


def installation():
    explicit = os.environ.get("BITWIG_HOME")
    roots = (
        [Path(explicit).expanduser()]
        if explicit
        else [
            Path("/Applications/Bitwig Studio.app/Contents"),
            Path("/opt/bitwig-studio"),
            Path(os.environ.get("PROGRAMFILES", "C:/Program Files")) / "Bitwig Studio",
        ]
    )
    for root in roots:
        if (root / "Contents").is_dir():
            root = root / "Contents"
        if root.is_dir():
            return root
    return roots[0]


def library_root(root=None):
    explicit = os.environ.get("BITWIG_LIBRARY_ROOT")
    if explicit:
        return Path(explicit).expanduser()
    root = installation() if root is None else Path(root)
    # Windows has the library at the top of the install folder, not under resources.
    for path in (root / "Resources/Library", root / "resources/Library", root / "resources/library", root / "Library"):
        if path.is_dir():
            return path
    return root / "Resources/Library"


def localization_root(root=None):
    """The folder of *-resources.properties: beside the library, except on Windows (resources/localization)."""
    root = installation() if root is None else Path(root)
    beside_library = library_root(root).parent / "localization"
    for path in (beside_library, root / "resources/localization"):
        if path.is_dir():
            return path
    return beside_library


def bitwig_jar():
    root = installation()
    for path in (root / "Java/bitwig.jar", root / "bin/bitwig.jar", root / "bitwig.jar"):
        if path.is_file():
            return path
    matches = list(root.glob("**/bitwig.jar")) if root.is_dir() else []
    if len(matches) == 1:
        return matches[0]
    raise FileNotFoundError("Bitwig's bitwig.jar was not found; set BITWIG_HOME to the installed application directory")
