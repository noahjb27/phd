import re

class StationNameCleaner:
    """Standardizes station names according to Berlin transport conventions."""
    
    ABBREVIATION_MAP = {
        'str': 'strasse',
        'Str': 'strasse',
        'Str.': 'strasse',
        'S+U': 'S-U',
        'S + U': 'S-U',
        'Bhf': 'Bahnhof',
        'Bhf.': 'Bahnhof',
        'U-Bhf': 'U-Bahnhof',
        'S-Bhf': 'S-Bahnhof',
    }
    
    DIRECTION_MAP = {
        'Nord': 'N',
        'Süd': 'S',
        'Ost': 'O',
        'West': 'W'
    }

    @classmethod
    def standardize_name(cls, name: str) -> str:
        """
        Standardize a station name according to conventions.
        
        Args:
            name: Raw station name
            
        Returns:
            Standardized station name
        """
        # Convert to title case first
        name = name.title()
        
        # Replace common abbreviations
        for abbr, full in cls.ABBREVIATION_MAP.items():
            name = re.sub(rf'\b{abbr}\b', full, name)
            
        # Attach 'strasse' to previous word
        name = re.sub(r'(\w+)\s+strasse', r'\1strasse', name)
        
        # Standardize directional indicators
        for direction, abbr in cls.DIRECTION_MAP.items():
            name = name.replace(f" {direction} ", f" {abbr} ")
            
        return name.strip()