"""
Main application entry point.
Demonstrates authentication with SSO.
"""

import sys
from config import AuthConfig, setup_logging
from sso_integration import SSOAuthenticator, OAuthProvider, SAMLProvider


def main():
    """Run the authentication demo."""
    # Setup
    config = AuthConfig()
    setup_logging(config)

    print("=" * 60)
    print("Authentication System Demo")
    print("=" * 60)

    # Create SSO authenticator
    authenticator = SSOAuthenticator()

    # Register providers
    if config.enable_sso:
        oauth = OAuthProvider(config.oauth_client_id, config.oauth_client_secret)
        saml = SAMLProvider(config.saml_entity_id)

        authenticator.register_provider('oauth', oauth)
        authenticator.register_provider('saml', saml)

        print("\nSSO Providers registered:")
        print("  - OAuth 2.0")
        print("  - SAML 2.0")

    # Test OAuth authentication
    print("\n" + "-" * 60)
    print("Test 1: OAuth SSO Authentication")
    print("-" * 60)

    oauth_token = "oauth_test_token_12345"
    session_token = authenticator.authenticate_sso('oauth', oauth_token)

    if session_token:
        print(f"✓ OAuth authentication successful")
        print(f"  Session token: {session_token}")
    else:
        print("✗ OAuth authentication failed")
        return 1

    # Test SAML authentication
    print("\n" + "-" * 60)
    print("Test 2: SAML SSO Authentication")
    print("-" * 60)

    saml_token = "saml_test_token_67890"
    session_token = authenticator.authenticate_sso('saml', saml_token)

    if session_token:
        print(f"✓ SAML authentication successful")
        print(f"  Session token: {session_token}")
    else:
        print("✗ SAML authentication failed")
        return 1

    print("\n" + "=" * 60)
    print("All tests passed!")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
