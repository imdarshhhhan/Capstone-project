import os
from dotenv import load_dotenv

# Instruct Python to search for and parse the local .env variables
load_dotenv()

class AppSettings:
    """
    [SECURITY ARCHITECTURE LAYER]:
    Extracts critical configuration parameters from environment memory buckets,
    ensuring infrastructure passwords never sit hardcoded in the codebase.
    """
    # Database Portal Connection String Configuration
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres:postgres@localhost:5432/quiz_platform" # Safe generic fallback default
    )
    
    # Cryptographic JWT Signing Variable Configuration
    JWT_SECRET: str = os.getenv(
        "JWT_SECRET_KEY", 
        "fallback_default_development_secret_signing_key_matrix"
    )

# Instantiate a single accessible settings tracking configuration object
settings = AppSettings()
