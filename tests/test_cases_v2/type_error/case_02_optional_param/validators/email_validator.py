"""Email validation with strict mode."""
import re


class EmailValidationError(Exception):
    """Raised when email validation fails."""
    pass


def validate_email(email, strict):
    """
    Validate email address with configurable strictness.

    Args:
        email: The email address to validate
        strict: Whether to use strict validation (REQUIRED parameter)
                - True: RFC 5322 compliant validation
                - False: Simple format check

    Returns:
        dict: Validation result with 'valid' and 'message' keys

    Raises:
        EmailValidationError: If validation fails in strict mode

    Note:
        This parameter was changed from optional to required to enforce
        explicit validation mode selection for security compliance.
        Old signature: validate_email(email, strict=False)
        New signature: validate_email(email, strict)
    """
    if not email:
        result = {"valid": False, "message": "Email cannot be empty"}
        if strict:
            raise EmailValidationError(result["message"])
        return result

    if strict:
        # Strict RFC 5322 validation
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        # Additional strict checks
        if email.count('@') != 1:
            raise EmailValidationError("Email must contain exactly one @ symbol")

        local_part, domain = email.split('@')

        # Check local part
        if not local_part or len(local_part) > 64:
            raise EmailValidationError("Invalid local part length")

        if local_part.startswith('.') or local_part.endswith('.'):
            raise EmailValidationError("Local part cannot start or end with a dot")

        if '..' in local_part:
            raise EmailValidationError("Local part cannot contain consecutive dots")

        # Check domain
        if not domain or len(domain) > 255:
            raise EmailValidationError("Invalid domain length")

        if domain.startswith('.') or domain.endswith('.'):
            raise EmailValidationError("Domain cannot start or end with a dot")

        if not re.match(pattern, email):
            raise EmailValidationError(f"Email '{email}' does not match RFC 5322 format")

        return {"valid": True, "message": "Email is valid (strict)"}
    else:
        # Simple validation - just check for @ and dot
        if '@' not in email:
            return {"valid": False, "message": "Email must contain @ symbol"}

        if '.' not in email.split('@')[1]:
            return {"valid": False, "message": "Domain must contain a dot"}

        return {"valid": True, "message": "Email is valid (simple)"}


def validate_email_domain(email, allowed_domains):
    """
    Check if email domain is in allowed list.

    Args:
        email: The email address to check
        allowed_domains: List of allowed domain names

    Returns:
        bool: True if domain is allowed, False otherwise
    """
    if '@' not in email:
        return False

    domain = email.split('@')[1].lower()
    return domain in [d.lower() for d in allowed_domains]


def validate_email_format_bulk(emails, strict):
    """
    Validate multiple email addresses.

    Args:
        emails: List of email addresses
        strict: Validation strictness level (required)

    Returns:
        dict: Mapping of email to validation result
    """
    results = {}
    for email in emails:
        try:
            result = validate_email(email, strict)
            results[email] = result
        except EmailValidationError as e:
            results[email] = {"valid": False, "message": str(e)}

    return results
