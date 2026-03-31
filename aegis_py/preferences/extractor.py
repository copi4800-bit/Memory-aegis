import re
from typing import List, Optional
from ..storage.models import StyleSignal

class SignalExtractor:
    """Extracts style signals (verbosity, technicality, etc.) from message content."""
    
    def extract_signals(self, content: str, session_id: str, scope_id: str, scope_type: str) -> List[StyleSignal]:
        signals = []
        
        # 1. Verbosity (0.0 = terse, 1.0 = verbose)
        length = len(content)
        verbosity = 0.5
        if length < 50: verbosity = 0.1
        elif length > 1000: verbosity = 0.9
        
        signals.append(StyleSignal(
            id=f"sig_v_{session_id[:6]}_{length}",
            session_id=session_id,
            scope_id=scope_id,
            scope_type=scope_type,
            signal_key="verbosity",
            signal_value=verbosity
        ))
        
        # 2. Format Preference (Categorical)
        if "```json" in content.lower():
            signals.append(StyleSignal(
                id=f"sig_f_{session_id[:6]}_json",
                session_id=session_id,
                scope_id=scope_id,
                scope_type=scope_type,
                signal_key="preferred_format",
                signal_value="json"
            ))
        elif "```markdown" in content.lower() or "##" in content:
            signals.append(StyleSignal(
                id=f"sig_f_{session_id[:6]}_md",
                session_id=session_id,
                scope_id=scope_id,
                scope_type=scope_type,
                signal_key="preferred_format",
                signal_value="markdown"
            ))
            
        # 3. Technical Level (0.0 = simple, 1.0 = expert)
        if "```" in content or "import " in content or "def " in content:
            signals.append(StyleSignal(
                id=f"sig_t_{session_id[:6]}_tech",
                session_id=session_id,
                scope_id=scope_id,
                scope_type=scope_type,
                signal_key="technical_level",
                signal_value=1.0
            ))
            
        return signals
