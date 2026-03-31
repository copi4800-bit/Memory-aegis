import re

class WorthyFilter:
    """Decides if context is worth storing as a long-term memory."""
    
    NOISE_KEYWORDS = {
        "ok", "hello", "hi", "bye", "thanks", "thank you", "no", "yes",
        "clear", "cls", "wait", "hold on", "stop", "start"
    }
    
    MIN_CONTENT_LENGTH = 10
    
    def is_worthy(self, content: str) -> bool:
        content = content.strip()
        if not content:
            return False
        
        # 1. Length check
        if len(content) < self.MIN_CONTENT_LENGTH:
            # Special case: allow short explicit style preferences like "I prefer JSON"
            if "prefer" not in content.lower():
                return False
        
        # 2. Noise keyword check (for very short strings)
        if len(content.split()) <= 2:
            clean = re.sub(r'[^\w\s]', '', content).lower()
            if clean in self.NOISE_KEYWORDS:
                return False
        
        # 3. System command check (simulated)
        if content.startswith("/") or content.startswith("@"):
            return False
            
        return True
