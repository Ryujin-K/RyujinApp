import os
import sys

def get_posix_candidates() -> list[str]:
    posix_candidates = [
        os.path.join(path, subitem)
        for path in os.environ.get("PATH", "").split(os.pathsep)
        for subitem in (
            "google-chrome",
            "chromium",
            "chromium-browser",
            "chrome",
            "google-chrome-stable",
        )
    ]
    if "darwin" in sys.platform:
        posix_candidates += [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
        ]
    return posix_candidates

def get_windows_candidates() -> list[str]:
    """
    Get all possible Chrome executable paths on Windows.
    Using os.path.join for proper path handling.
    """
    windows_candidates = []
    
    # Standard environment variables
    for item in map(
        os.environ.get,
        ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA", "PROGRAMW6432"),
    ):
        if item:
            # Use proper path separators for Windows
            chrome_paths = [
                os.path.join(item, "Google", "Chrome", "Application", "chrome.exe"),
                os.path.join(item, "Google", "Chrome Beta", "Application", "chrome.exe"),
                os.path.join(item, "Google", "Chrome Canary", "Application", "chrome.exe"),
            ]
            windows_candidates.extend(chrome_paths)
    
    # Additional common paths
    username = os.environ.get('USERNAME', '')
    if username:
        additional_paths = [
            rf"C:\Users\{username}\AppData\Local\Google\Chrome\Application\chrome.exe",
        ]
        windows_candidates.extend(additional_paths)
    
    return windows_candidates

def find_chrome_executable() -> str | None:
    """
    Find a valid Chrome/Chromium executable on the system.
    """
    is_frozen = getattr(sys, 'frozen', False)
    
    if is_frozen:
        is_posix = sys.platform.startswith(("darwin", "cygwin", "linux", "linux2"))
    else:
        is_posix = os.name == 'posix'

    candidates = get_posix_candidates() if is_posix else get_windows_candidates()

    # Find valid executables
    valid_candidates = []
    for candidate in candidates:
        try:
            if os.path.exists(candidate) and os.access(candidate, os.X_OK):
                valid_candidates.append(candidate)
        except (OSError, PermissionError):
            continue
    
    if valid_candidates:
        result = os.path.normpath(min(valid_candidates, key=len))
        print(f"[CHROME] Found: {result}")
        return result

    print("[CHROME] No executable found")
    return None
