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
            
        # 4. Vietnamese Honorifics (xưng hô)
        signals.extend(self.extract_honorifics(content, session_id, scope_id, scope_type))
            
        return signals

    def extract_honorifics(self, content: str, session_id: str, scope_id: str, scope_type: str) -> List[StyleSignal]:
        """
        Detects persona identity (honorifics) from explicit user assignment.
        Follows a Zero-Locking strategy: no hardcoded lists of pronouns or verbs.
        """
        signals = []
        low_content = content.lower()
        
        # 1. Explicit Identification: "Gọi [X] là [Y]" 
        # Captures the identity 'Y' specifically as the user's preferred label.
        match = re.search(r"gọi\s+.+?\s+là\s+([\w\s]+)", low_content)
        if match:
            val = match.group(1).split()[0] # Take first word of the label
            signals.append(StyleSignal(
                id=f"sig_uh_{session_id[:6]}_{val}",
                session_id=session_id,
                scope_id=scope_id,
                scope_type=scope_type,
                signal_key="user_honorific",
                signal_value=val
            ))

        # 2. Explicit Identity: "Xưng là [Y]"
        # Captures how the user wants the assistant to refer to itself.
        match = re.search(r"xưng\s+là\s+([\w\s]+)", low_content)
        if match:
            val = match.group(1).split()[0]
            signals.append(StyleSignal(
                id=f"sig_ah_{session_id[:6]}_{val}",
                session_id=session_id,
                scope_id=scope_id,
                scope_type=scope_type,
                signal_key="assistant_honorific",
                signal_value=val
            ))
            
        return signals

    def _make_assistant_signal(self, val: str, sid: str, scid: str, sct: str) -> StyleSignal:
        return StyleSignal(
            id=f"sig_ah_{sid[:6]}_{val}",
            session_id=sid,
            scope_id=scid,
            scope_type=sct,
            signal_key="assistant_honorific",
            signal_value=val
        )
