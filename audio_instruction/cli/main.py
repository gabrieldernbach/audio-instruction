"""Command line interface for audio instruction generation."""
import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, cast

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

from audio_instruction.core.validation import (
    ValidationError,
    validate_workout_instructions,
)
from audio_instruction.core.workout import generate_workout_guide_audio


def parse_workout_config(config_path: str) -> Dict[str, Any]:
    """Parse workout configuration from a file.
    
    Supports JSON, YAML, and plain text formats based on file extension.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Dictionary with 'instructions', 'language', and 'background_urls' keys
    """
    try:
        file_ext = os.path.splitext(config_path)[1].lower()
        
        # Default values
        config: Dict[str, Any] = {
            'instructions': [],
            'language': 'en',
            'background_urls': None
        }
        
        # Handle different file formats
        if file_ext == '.txt':
            # Plain text format - read as plain text
            with open(config_path, 'r') as f:
                text_content = f.read()
            
            # Parse plain text
            return parse_plain_text(text_content)
            
        elif file_ext in ['.yml', '.yaml']:
            # YAML format
            if not YAML_AVAILABLE:
                print("YAML support requires PyYAML. Install with: pip install pyyaml", file=sys.stderr)
                sys.exit(1)
                
            with open(config_path, 'r') as f:
                data = yaml.safe_load(f)
        else:
            # Assume JSON for all other extensions
            with open(config_path, 'r') as f:
                data = json.load(f)
        
        # Handle structured data (JSON/YAML)
        # Ensure data is a dictionary (object)
        if not isinstance(data, dict):
            raise ValueError("Configuration file must be an object with 'instructions' field")
        
        # Parse instructions
        if 'instructions' not in data:
            raise ValueError("Configuration must contain an 'instructions' field")
        
        if not isinstance(data['instructions'], list):
            raise ValueError("'instructions' field must be an array")
        
        parsed_instructions: List[Tuple[str, int]] = []
        for idx, item in enumerate(data['instructions']):
            if isinstance(item, str):
                # Simple string format - use default 30 seconds
                parsed_instructions.append((item, 30))
            elif isinstance(item, dict):
                # Full object format
                if 'text' not in item:
                    raise ValueError(f"Instruction {idx} missing 'text' field")
                
                if 'duration_seconds' not in item:
                    # Use default duration if not specified
                    text = item['text']
                    duration = 30
                else:
                    text = item['text']
                    duration = item['duration_seconds']
                
                if not isinstance(text, str):
                    raise ValueError(f"Instruction {idx} 'text' must be a string")
                
                if not isinstance(duration, int):
                    raise ValueError(f"Instruction {idx} 'duration_seconds' must be an integer")
                
                parsed_instructions.append((text, duration))
            else:
                raise ValueError(f"Instruction {idx} must be a string or an object")
        
        config['instructions'] = parsed_instructions
        
        # Parse language
        if 'language' in data:
            if not isinstance(data['language'], str):
                raise ValueError("'language' must be a string")
            config['language'] = data['language']
        
        # Parse background URLs
        if 'background_urls' in data:
            if isinstance(data['background_urls'], str):
                # Single URL as string
                config['background_urls'] = [data['background_urls']]
            elif isinstance(data['background_urls'], list):
                # List of URLs
                for idx, url in enumerate(data['background_urls']):
                    if not isinstance(url, str):
                        raise ValueError(f"Background URL {idx} must be a string")
                
                config['background_urls'] = data['background_urls']
            else:
                raise ValueError("'background_urls' must be a string or an array of strings")
        
        return config
    
    except (json.JSONDecodeError, yaml.YAMLError, ValueError) as e:
        print(f"Error parsing configuration file: {e}", file=sys.stderr)
        sys.exit(1)


def parse_plain_text(text_content: str) -> Dict[str, Any]:
    """Parse plain text workout format.
    
    Format:
    # Comments start with # and are ignored
    # language: en
    # background: https://youtube.com/watch?v=xyz
    
    Instruction text | duration_in_seconds
    Another instruction  # Uses default 30 seconds
    
    Args:
        text_content: The text content to parse
        
    Returns:
        Dictionary with 'instructions', 'language', and 'background_urls' keys
    """
    # Default values
    config: Dict[str, Any] = {
        'instructions': [],
        'language': 'en',
        'background_urls': None
    }
    
    # Split into lines and process
    lines = text_content.strip().split('\n')
    instructions: List[Tuple[str, int]] = []
    background_urls: List[str] = []
    
    for idx, line in enumerate(lines):
        line = line.strip()
        
        # Skip empty lines
        if not line:
            continue
            
        # Handle comment lines with special directives
        if line.startswith('#'):
            # Extract directives from comments (e.g. "# language: fr")
            line = line[1:].strip()  # Remove the # and trim whitespace
            
            if ':' in line:
                directive, value = [x.strip() for x in line.split(':', 1)]
                directive = directive.lower()
                
                if directive == 'language':
                    config['language'] = value
                elif directive in ['background', 'background_url', 'background_urls']:
                    background_urls.append(value)
            
            continue
        
        # Handle instruction lines
        if '|' in line:
            # Format: "Instruction text | duration"
            parts = line.split('|')
            if len(parts) != 2:
                raise ValueError(f"Line {idx+1} has invalid format. Use: 'Instruction text | duration'")
            
            text = parts[0].strip()
            try:
                # Handle comments in the duration part
                duration_part = parts[1].strip()
                if '#' in duration_part:
                    duration_part = duration_part.split('#')[0].strip()
                
                duration = int(duration_part)
            except ValueError:
                raise ValueError(f"Line {idx+1} has invalid duration: {parts[1].strip()}")
            
            instructions.append((text, duration))
        else:
            # Simple format with default 30 seconds duration
            # Handle inline comments
            if '#' in line:
                line = line.split('#')[0].strip()
            
            if line:  # Skip if line is empty after removing comment
                instructions.append((line, 30))
    
    # Set the parsed values in the config
    config['instructions'] = instructions
    
    # Only set background_urls if we found any
    if background_urls:
        config['background_urls'] = background_urls
    
    return config


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Generate workout audio guides with text-to-speech instructions."
    )
    
    parser.add_argument(
        "config_file",
        help="Path to configuration file (JSON, YAML, or TXT)"
    )
    
    parser.add_argument(
        "-o", "--output",
        help="Output MP3 file path (default: same as config file with .mp3 extension)"
    )
    
    args = parser.parse_args()
    
    # Parse configuration from file
    config = parse_workout_config(args.config_file)
    
    # Set default output path if not specified
    if not args.output:
        input_path = Path(args.config_file)
        output_path = str(input_path.with_suffix('.mp3'))
    else:
        output_path = args.output
    
    try:
        # Validate instructions
        validate_workout_instructions(config['instructions'])
        
        # Generate audio
        print(f"Generating workout guide with {len(config['instructions'])} instructions...")
        print(f"Language: {config['language']}")
        if config['background_urls']:
            print(f"Using {len(config['background_urls'])} background tracks")
        
        generate_workout_guide_audio(
            instructions=config['instructions'],
            lang=config['language'],
            background_urls=config['background_urls'],
            output_path=output_path
        )
        
        print(f"Workout guide saved to {os.path.abspath(output_path)}")
    except ValidationError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error generating audio: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main() 