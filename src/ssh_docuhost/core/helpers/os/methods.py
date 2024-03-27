import sys


def get_host_os() -> str:
    VALID_PLATFORMS: list[str] = ["linux", "win32", "darwin"]
    return_map: dict[str, str] = {"linux": "linux", "win32": "windows", "darwin": "mac"}

    _platform = sys.platform

    assert _platform in VALID_PLATFORMS, ValueError(
        f"Unknown platform: {_platform}. Expected one of {VALID_PLATFORMS}"
    )

    return_val = return_map[_platform]
    assert return_val, ValueError("return_val should not be None")

    return return_val
