import re
import logging
import os
import spacy
from typing import List, Dict, Any, Tuple, Optional

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class CityAnalyzer:
    """Class for analyzing text and identifying mentioned cities"""
    
    def __init__(self):
        """
        Initialize the city analyzer
        
        Loads Spacy models for English language
        for named entity recognition (NER)
        """
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Dictionary of known cities with coordinates (latitude, longitude)
        # This is a small subset for example
        self.known_cities = {
            # Russia
            "moscow": (55.7558, 37.6173),
            "saint petersburg": (59.9343, 30.3351),
            "novosibirsk": (55.0084, 82.9357),
            "yekaterinburg": (56.8389, 60.6057),
            "kazan": (55.7879, 49.1233),
            "nizhny novgorod": (56.3287, 44.002),
            "chelyabinsk": (55.1644, 61.4368),
            "omsk": (54.9884, 73.3242),
            "samara": (53.1959, 50.1001),
            "rostov-on-don": (47.2357, 39.7015),
            "ufa": (54.7431, 55.9678),
            "krasnoyarsk": (56.0184, 92.8672),
            "perm": (58.0105, 56.2502),
            "voronezh": (51.6755, 39.2088),
            "volgograd": (48.7080, 44.5133),
            
            # USA
            "new york": (40.7128, -74.0060),
            "los angeles": (34.0522, -118.2437),
            "chicago": (41.8781, -87.6298),
            "houston": (29.7604, -95.3698),
            "phoenix": (33.4484, -112.0740),
            "philadelphia": (39.9526, -75.1652),
            "san antonio": (29.4241, -98.4936),
            "san diego": (32.7157, -117.1611),
            "dallas": (32.7767, -96.7970),
            "san jose": (37.3382, -121.8863),
            
            # Europe
            "london": (51.5074, -0.1278),
            "paris": (48.8566, 2.3522),
            "berlin": (52.5200, 13.4050),
            "madrid": (40.4168, -3.7038),
            "rome": (41.9028, 12.4964),
            "barcelona": (41.3851, 2.1734),
            "vienna": (48.2082, 16.3738),
            "amsterdam": (52.3676, 4.9041),
            "brussels": (50.8503, 4.3517),
            "stockholm": (59.3293, 18.0686),
            
            # Asia
            "tokyo": (35.6762, 139.6503),
            "beijing": (39.9042, 116.4074),
            "shanghai": (31.2304, 121.4737),
            "delhi": (28.6139, 77.2090),
            "seoul": (37.5665, 126.9780),
            "mumbai": (19.0760, 72.8777),
            "singapore": (1.3521, 103.8198),
            "bangkok": (13.7563, 100.5018),
            "dubai": (25.2048, 55.2708),
            "hong kong": (22.3193, 114.1694)
        }
        
        # Load NLP models
        try:
            self.nlp_en = spacy.load("en_core_web_sm")
            self.logger.info("English NLP model loaded successfully")
        except Exception as e:
            self.logger.error(f"Error loading English model: {str(e)}")
            self.nlp_en = None
        
        try:
            self.nlp_ru = None  # We don't need Russian model anymore
        except Exception as e:
            self.logger.error(f"Error loading model: {str(e)}")
            self.nlp_ru = None
    
    def extract_cities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract city mentions from text
        
        Args:
            text (str): Text to analyze
            
        Returns:
            List[Dict[str, Any]]: List of cities with additional information
        """
        if not text:
            return []
            
        cities = []
        
        # Extract cities using SpaCy
        spacy_cities = self._extract_cities_with_spacy(text)
        cities.extend(spacy_cities)
        
        # Additional search for cities from our list of known cities
        known_cities = self._extract_known_cities(text)
        
        # Combine results and remove duplicates
        cities_set = {city["city"].lower() for city in cities}
        for city in known_cities:
            if city["city"].lower() not in cities_set:
                cities.append(city)
                cities_set.add(city["city"].lower())
        
        # Sort cities by confidence (descending)
        cities.sort(key=lambda x: x["confidence"], reverse=True)
        
        return cities
    
    def _extract_cities_with_spacy(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract cities from text using SpaCy
        
        Args:
            text (str): Text to analyze
            
        Returns:
            List[Dict[str, Any]]: List of found cities
        """
        cities = []
        
        try:
            # Use English model
            nlp = self.nlp_en
            if not nlp:
                self.logger.warning("NLP model not available")
                return []
            
            # Process text
            doc = nlp(text)
            
            # Extract cities
            for ent in doc.ents:
                if ent.label_ == "GPE":
                    city_name = ent.text
                    
                    # Check if it's likely a city
                    if self._is_likely_city(city_name):
                        # Coordinates from our list or None
                        coordinates = self.known_cities.get(city_name.lower())
                        
                        # Use fixed confidence value (85%)
                        # as not all models have trf_score attribute
                        confidence = 85
                        
                        cities.append({
                            "city": city_name,
                            "confidence": confidence,
                            "coordinates": coordinates,
                            "source": "spacy"
                        })
        
        except Exception as e:
            self.logger.error(f"Error extracting cities with SpaCy: {str(e)}")
        
        return cities
    
    def _extract_known_cities(self, text: str) -> List[Dict[str, Any]]:
        """
        Search for known cities from predefined list in text
        
        Args:
            text (str): Text to analyze
            
        Returns:
            List[Dict[str, Any]]: List of found cities
        """
        cities = []
        lower_text = text.lower()
        
        for city, coordinates in self.known_cities.items():
            # Search for the city in text with word boundaries
            city_pattern = r'\b' + city + r'[a-z]*\b'
            matches = re.findall(city_pattern, lower_text)
            
            if matches:
                # Base confidence score - 75%
                confidence = 75
                
                # Increase confidence if city is mentioned multiple times
                if len(matches) > 1:
                    confidence += min(len(matches) * 5, 20)  # Maximum +20%
                
                cities.append({
                    "city": city.title(),  # Convert to "New York" format
                    "confidence": confidence,
                    "coordinates": coordinates,
                    "source": "dictionary",
                    "mentions": len(matches)
                })
        
        return cities
    
    def _is_likely_city(self, name: str) -> bool:
        """
        Determine if the name is likely a city
        
        Args:
            name (str): Place name
            
        Returns:
            bool: True if the place is likely a city
        """
        lower_name = name.lower()
        
        # Check if it's in our list of known cities
        if lower_name in self.known_cities:
            return True
            
        # Simple heuristics for English language
        non_city_words = ["county", "state", "province", "territory", "republic", "kingdom"]
        if any(word in lower_name for word in non_city_words):
            return False
        
        return True

# Testing
if __name__ == "__main__":
    analyzer = CityAnalyzer()
    
    # Test text
    test_text = """
    The G7 summit was held in London this week. Representatives from Paris, Berlin, 
    and Rome discussed climate change and economic issues. The next meeting is planned 
    in New York in December.
    """
    
    print("=== City Analysis Test ===")
    cities = analyzer.extract_cities(test_text)
    for city in cities:
        print(f"{city['city']}: {city['confidence']}%") 