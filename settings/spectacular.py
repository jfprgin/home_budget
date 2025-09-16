SPECTACULAR_SETTINGS = {
    "TITLE": "HomeBudget API",
    "DESCRIPTION": "API documentation for HomeBudget project",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,  # hide raw JSON in production
    "COMPONENT_SPLIT_REQUEST": True,
    "SECURITY_SCHEMES": {
        "TokenAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": "Enter your token prefixed with 'Token ', e.g. 'Token abc123...'"
        }
    },
    "SECURITY": [{"TokenAuth": []}],
}
