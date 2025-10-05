"""
Input validation utilities.
"""

import re
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse
import magic


def validate_email(email: str) -> bool:
    """Validate email address format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password_strength(password: str) -> Dict[str, Union[bool, List[str]]]:
    """Validate password strength and return detailed feedback."""
    errors = []
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    
    if len(password) > 128:
        errors.append("Password must be less than 128 characters")
    
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")
    
    if not re.search(r'\d', password):
        errors.append("Password must contain at least one number")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Password must contain at least one special character")
    
    # Check for common weak passwords
    weak_patterns = [
        r'12345',
        r'password',
        r'qwerty',
        r'abc123',
        r'admin',
    ]
    
    for pattern in weak_patterns:
        if re.search(pattern, password.lower()):
            errors.append("Password contains common weak patterns")
            break
    
    return {
        'is_valid': len(errors) == 0,
        'errors': errors
    }


def validate_filename(filename: str) -> bool:
    """Validate filename for safety."""
    if not filename or len(filename) > 255:
        return False
    
    # Check for dangerous characters
    dangerous_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|', '\0']
    if any(char in filename for char in dangerous_chars):
        return False
    
    # Check for reserved names (Windows)
    reserved_names = [
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    ]
    
    name_without_ext = filename.split('.')[0].upper()
    if name_without_ext in reserved_names:
        return False
    
    return True


def validate_image_file(file_bytes: bytes, allowed_types: Optional[List[str]] = None) -> Dict[str, Union[bool, str]]:
    """Validate image file type and content."""
    if allowed_types is None:
        allowed_types = ['image/jpeg', 'image/png', 'image/webp']
    
    try:
        # Use python-magic to detect file type
        mime_type = magic.from_buffer(file_bytes, mime=True)
        
        if mime_type not in allowed_types:
            return {
                'is_valid': False,
                'error': f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
            }
        
        # Check file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if len(file_bytes) > max_size:
            return {
                'is_valid': False,
                'error': f"File too large. Maximum size is {max_size // (1024*1024)}MB"
            }
        
        return {'is_valid': True, 'mime_type': mime_type}
        
    except Exception as e:
        return {
            'is_valid': False,
            'error': f"Invalid file: {str(e)}"
        }


def validate_url(url: str, allowed_schemes: Optional[List[str]] = None) -> bool:
    """Validate URL format and scheme."""
    if allowed_schemes is None:
        allowed_schemes = ['http', 'https']
    
    try:
        parsed = urlparse(url)
        return (
            parsed.scheme in allowed_schemes and
            bool(parsed.netloc) and
            len(url) <= 2048
        )
    except Exception:
        return False


def validate_tags(tags: List[str], max_tags: int = 10, max_tag_length: int = 50) -> Dict[str, Union[bool, List[str]]]:
    """Validate tags list."""
    if len(tags) > max_tags:
        return {
            'is_valid': False,
            'error': f"Too many tags. Maximum {max_tags} allowed"
        }
    
    cleaned_tags = []
    for tag in tags:
        if not isinstance(tag, str):
            return {
                'is_valid': False,
                'error': "All tags must be strings"
            }
        
        cleaned_tag = tag.strip()
        if not cleaned_tag:
            continue
        
        if len(cleaned_tag) > max_tag_length:
            return {
                'is_valid': False,
                'error': f"Tag '{cleaned_tag}' is too long. Maximum {max_tag_length} characters"
            }
        
        if not re.match(r'^[a-zA-Z0-9_-]+$', cleaned_tag):
            return {
                'is_valid': False,
                'error': f"Tag '{cleaned_tag}' contains invalid characters. Use only letters, numbers, hyphens, and underscores"
            }
        
        cleaned_tags.append(cleaned_tag.lower())
    
    # Remove duplicates while preserving order
    seen = set()
    unique_tags = []
    for tag in cleaned_tags:
        if tag not in seen:
            seen.add(tag)
            unique_tags.append(tag)
    
    return {
        'is_valid': True,
        'cleaned_tags': unique_tags
    }


def validate_text_input(
    text: str,
    min_length: int = 0,
    max_length: int = 1000,
    allow_empty: bool = True,
    strip_html: bool = True
) -> Dict[str, Union[bool, str]]:
    """Validate text input with configurable constraints."""
    if not isinstance(text, str):
        return {
            'is_valid': False,
            'error': "Input must be a string"
        }
    
    # Strip HTML if requested
    if strip_html:
        text = re.sub(r'<[^>]*>', '', text)
    
    # Strip whitespace
    text = text.strip()
    
    # Check if empty is allowed
    if not text and not allow_empty:
        return {
            'is_valid': False,
            'error': "Input cannot be empty"
        }
    
    # Check length constraints
    if len(text) < min_length:
        return {
            'is_valid': False,
            'error': f"Input must be at least {min_length} characters long"
        }
    
    if len(text) > max_length:
        return {
            'is_valid': False,
            'error': f"Input must be no more than {max_length} characters long"
        }
    
    return {
        'is_valid': True,
        'cleaned_text': text
    }


def validate_pagination_params(page: int, per_page: int, max_per_page: int = 100) -> Dict[str, Union[bool, str, int]]:
    """Validate pagination parameters."""
    if not isinstance(page, int) or page < 1:
        return {
            'is_valid': False,
            'error': "Page must be a positive integer"
        }
    
    if not isinstance(per_page, int) or per_page < 1:
        return {
            'is_valid': False,
            'error': "Per page must be a positive integer"
        }
    
    if per_page > max_per_page:
        return {
            'is_valid': False,
            'error': f"Per page cannot exceed {max_per_page}"
        }
    
    return {
        'is_valid': True,
        'page': page,
        'per_page': per_page
    }


def validate_sort_params(
    sort_by: str,
    sort_order: str,
    allowed_fields: List[str]
) -> Dict[str, Union[bool, str]]:
    """Validate sorting parameters."""
    if sort_by not in allowed_fields:
        return {
            'is_valid': False,
            'error': f"Invalid sort field. Allowed fields: {', '.join(allowed_fields)}"
        }
    
    if sort_order.lower() not in ['asc', 'desc']:
        return {
            'is_valid': False,
            'error': "Sort order must be 'asc' or 'desc'"
        }
    
    return {
        'is_valid': True,
        'sort_by': sort_by,
        'sort_order': sort_order.lower()
    }


def sanitize_search_query(query: str, max_length: int = 100) -> str:
    """Sanitize search query for safe database operations."""
    if not query:
        return ""
    
    # Remove special characters that could be used for injection
    query = re.sub(r'[^\w\s\-_]', ' ', query)
    
    # Normalize whitespace
    query = ' '.join(query.split())
    
    # Truncate if too long
    if len(query) > max_length:
        query = query[:max_length].strip()
    
    return query


def validate_uuid(uuid_string: str) -> bool:
    """Validate UUID string format."""
    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    return bool(re.match(uuid_pattern, uuid_string.lower()))


def validate_json_data(data: Any, required_fields: List[str]) -> Dict[str, Union[bool, str]]:
    """Validate JSON data contains required fields."""
    if not isinstance(data, dict):
        return {
            'is_valid': False,
            'error': "Data must be a JSON object"
        }
    
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return {
            'is_valid': False,
            'error': f"Missing required fields: {', '.join(missing_fields)}"
        }
    
    return {'is_valid': True}
