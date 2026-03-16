import re
from typing import List

def _split_into_words(text: str) -> List[str]:
    if not text:
        return []
    
    words = re.split(r'[-_\s]+', text)
    words = [w for w in words if w]
    
    if not words:
        return []
    
    all_words = []
    for word in words:
        word = re.sub(r'([a-z0-9])([A-Z])', r'\1 \2', word)        
        word = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1 \2', word)
        all_words.extend(word.split())
    
    return all_words


def to_camel(text: str) -> str:
    words = _split_into_words(text)
    
    if not words:
        return text

    result = words[0].lower()

    for word in words[1:]:
        result += word.capitalize()
    
    return result


def to_pascal(text: str) -> str:
    words = _split_into_words(text)
    
    if not words:
        return text
    
    return ''.join(word.capitalize() for word in words)


def to_snake(text: str) -> str:
    words = _split_into_words(text)
    
    if not words:
        return text
    
    return '_'.join(word.lower() for word in words)


def to_upper_snake(text: str) -> str:
    words = _split_into_words(text)
    
    if not words:
        return text
    
    return '_'.join(word.upper() for word in words)