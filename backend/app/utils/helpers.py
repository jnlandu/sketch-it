"""
General helper functions and utilities.
"""

import uuid
import hashlib
import secrets
import string
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
import re
import os
from urllib.parse import urlparse


def generate_uuid() -> str:
    """Generate a new UUID string."""
    return str(uuid.uuid4())


def generate_secure_token(length: int = 32) -> str:
    """Generate a secure random token."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_filename(original_filename: str, prefix: str = "") -> str:
    """Generate a unique filename while preserving extension."""
    name, ext = os.path.splitext(original_filename)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    unique_id = generate_secure_token(8)
    
    if prefix:
        return f"{prefix}_{timestamp}_{unique_id}{ext}"
    return f"{timestamp}_{unique_id}{ext}"


def calculate_file_hash(file_bytes: bytes, algorithm: str = "sha256") -> str:
    """Calculate hash of file bytes."""
    if algorithm == "md5":
        return hashlib.md5(file_bytes).hexdigest()
    elif algorithm == "sha1":
        return hashlib.sha1(file_bytes).hexdigest()
    elif algorithm == "sha256":
        return hashlib.sha256(file_bytes).hexdigest()
    else:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    return f"{size:.1f} {size_names[i]}"


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """Sanitize filename for safe storage."""
    # Remove directory separators and null bytes
    filename = re.sub(r'[/\\:\*\?"<>\|]', '_', filename)
    filename = filename.replace('\0', '')
    
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    
    # Limit length
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        max_name_length = max_length - len(ext)
        filename = name[:max_name_length] + ext
    
    # Ensure it's not empty
    if not filename:
        filename = "unnamed_file"
    
    return filename


def validate_url(url: str) -> bool:
    """Validate if string is a valid URL."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def clean_html_tags(text: str) -> str:
    """Remove HTML tags from text."""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to specified length."""
    if len(text) <= max_length:
        return text
    
    truncated = text[:max_length - len(suffix)].rstrip()
    return truncated + suffix


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format datetime to string."""
    return dt.strftime(format_str)


def parse_datetime(dt_str: str) -> Optional[datetime]:
    """Parse datetime string with common formats."""
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%d",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue
    
    return None


def get_time_ago(dt: datetime) -> str:
    """Get human readable time ago string."""
    now = datetime.utcnow()
    diff = now - dt
    
    if diff.days > 365:
        years = diff.days // 365
        return f"{years} year{'s' if years != 1 else ''} ago"
    elif diff.days > 30:
        months = diff.days // 30
        return f"{months} month{'s' if months != 1 else ''} ago"
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    else:
        return "Just now"


def paginate_query_params(
    page: int = 1,
    per_page: int = 20,
    max_per_page: int = 100
) -> Dict[str, int]:
    """Validate and normalize pagination parameters."""
    page = max(1, page)
    per_page = min(max(1, per_page), max_per_page)
    offset = (page - 1) * per_page
    
    return {
        'page': page,
        'per_page': per_page,
        'offset': offset,
        'limit': per_page
    }


def build_pagination_response(
    items: List[Any],
    total: int,
    page: int,
    per_page: int
) -> Dict[str, Any]:
    """Build standardized pagination response."""
    total_pages = (total + per_page - 1) // per_page
    
    return {
        'items': items,
        'pagination': {
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1,
            'next_page': page + 1 if page < total_pages else None,
            'prev_page': page - 1 if page > 1 else None
        }
    }


def extract_tags_from_text(text: str, max_tags: int = 10) -> List[str]:
    """Extract hashtags from text."""
    if not text:
        return []
    
    # Find hashtags
    hashtags = re.findall(r'#(\w+)', text.lower())
    
    # Remove duplicates while preserving order
    seen = set()
    unique_tags = []
    for tag in hashtags:
        if tag not in seen and len(tag) >= 2:
            seen.add(tag)
            unique_tags.append(tag)
    
    return unique_tags[:max_tags]


def is_safe_redirect_url(url: str, allowed_hosts: List[str]) -> bool:
    """Check if URL is safe for redirect."""
    try:
        parsed = urlparse(url)
        
        # Only allow relative URLs or URLs to allowed hosts
        if not parsed.netloc:  # Relative URL
            return True
        
        return parsed.netloc in allowed_hosts
    except Exception:
        return False


def mask_email(email: str) -> str:
    """Mask email address for privacy."""
    try:
        username, domain = email.split('@')
        if len(username) <= 2:
            masked_username = username[0] + '*' * (len(username) - 1)
        else:
            masked_username = username[0] + '*' * (len(username) - 2) + username[-1]
        return f"{masked_username}@{domain}"
    except Exception:
        return email


def get_client_ip(headers: Dict[str, str]) -> str:
    """Extract client IP from request headers."""
    # Check common proxy headers
    ip_headers = [
        'x-forwarded-for',
        'x-real-ip',
        'x-client-ip',
        'cf-connecting-ip',
        'true-client-ip'
    ]
    
    for header in ip_headers:
        if header in headers:
            ip = headers[header].split(',')[0].strip()
            if ip and ip != 'unknown':
                return ip
    
    return 'unknown'


def create_error_response(
    message: str,
    error_code: str = "UNKNOWN_ERROR",
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create standardized error response."""
    response = {
        'error': True,
        'message': message,
        'error_code': error_code,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if details:
        response['details'] = details
    
    return response


def create_success_response(
    data: Any = None,
    message: str = "Success"
) -> Dict[str, Any]:
    """Create standardized success response."""
    response = {
        'success': True,
        'message': message,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if data is not None:
        response['data'] = data
    
    return response
