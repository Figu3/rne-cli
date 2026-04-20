from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("rne-cli")
except PackageNotFoundError:
    __version__ = "unknown"
