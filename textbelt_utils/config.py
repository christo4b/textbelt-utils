"""Configuration module for textbelt-utils."""
import os
from typing import Optional
from dotenv import load_dotenv

def load_config(env_file: Optional[str] = None) -> None:
    """Load environment configuration.
    
    Args:
        env_file: Optional path to specific .env file. If not provided,
                 will look for .env in current directory.
    """
    # Load environment variables from file
    load_dotenv(dotenv_path=env_file)

def get_env_var(var_name: str, default: Optional[str] = None) -> str:
    """Get environment variable or raise error with helpful message.
    
    Args:
        var_name: Name of the environment variable
        default: Optional default value if not set
        
    Returns:
        The environment variable value
        
    Raises:
        ValueError: If the variable is not set and no default is provided
    """
    value = os.getenv(var_name, default)
    if value is None:
        raise ValueError(
            f"Please set {var_name} environment variable\n"
            f"Example: export {var_name}=your_{var_name.lower()}_here"
        )
    return value

# Load configuration on module import
load_config() 