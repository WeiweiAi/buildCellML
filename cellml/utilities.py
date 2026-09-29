import urllib.request
import urllib.error
from urllib.parse import ParseResult, urlparse
from pathlib import Path
from typing import Optional

def is_web_url(file_path: str) -> Optional[ParseResult]:
    """
    Safely checks if a provided string is a valid HTTP/HTTPS web URL.
    
    Args:
        file_path (str): The file path or URL to check.
        
    Returns:
        Optional[ParseResult]: The parsed URL object if it's a valid web URL, None otherwise.
        The object includes: scheme, netloc, path, params, query, fragment
    """
    clean_path = file_path.strip()    
    try:
        # Parse the URL into its core components (scheme, network location, etc.)
        result = urlparse(clean_path)
        # Ensure it has both an acceptable web protocol and a domain name
        if result.scheme in ['http', 'https'] and bool(result.netloc):
            return result
    except ValueError:
        # Catch cases where the string is completely malformed
        raise ValueError(f"Invalid URL format: {clean_path}")

    return None

def get_file(file_path: str, timeout_seconds: int = 15) -> str | None:
    """
    Takes a URL or a local file path and loads its contents into a reusable 
    in-memory byte buffer. 
    
    Args:
        file_path (str): The local file path or remote URL.
        timeout_seconds (int): Maximum time to wait for a web response.
        
    Returns:
        str | None: The contents of the file, or None if an error occurs.
    """
    clean_path = file_path.strip()
    
    if is_web_url(clean_path):
        print(f"Downloading {clean_path}...")
        try:
            # Added a timeout to prevent the script from hanging on unresponsive servers
            with urllib.request.urlopen(clean_path, timeout=timeout_seconds) as response:
                return response.read().decode('utf-8')
        except urllib.error.URLError as e:
            print(f"Network error while downloading {clean_path}: {e}")
        except Exception as e:
            print(f"Unexpected error occurred while downloading {clean_path}: {e}")
        return None    
    else:
        # If it is not a web URL, treat it as a local file path
        try:
            with open(Path(clean_path), 'r') as f:
                return f.read()
        except FileNotFoundError:
            print(f"Error: Local file not found - {clean_path}")
        except PermissionError:
            print(f"Error: Permission denied when trying to read - {clean_path}")
        except Exception as e:
            print(f"Unexpected error occurred while reading {clean_path}: {e}")
        return None

def validate_file_path(file_path: str) -> Path | None:
    """
    Validates whether the provided file path is a valid.
    
    Args:
        file_path (str): The file path .
        
    Returns:
        Path | None: The validated file path, or None if it is invalid.
    """
    file_path_ = Path(file_path.strip())

    if file_path_.exists():
        # ask user if they want to overwrite the file
        overwrite = input(f"Warning: '{file_path_}' already exists! Do you want to overwrite it? (y/n): ").strip().lower()
        if overwrite != 'y':
            print("Operation cancelled by user.")
            return None
    else:
        # Check if the parent directory exists; if not, create it
        if not file_path_.parent.exists():
            try:
                file_path_.parent.mkdir(parents=True, exist_ok=True)
                print(f"Created missing directory: {file_path_.parent}")
            except Exception as e:
                print(f"Error creating directory '{file_path_.parent}': {e}")
                return None
    return file_path_
    
    