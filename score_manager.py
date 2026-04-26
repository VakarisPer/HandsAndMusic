"""Score management with file I/O"""

import json
from pathlib import Path
from datetime import datetime

class ScoreManager:
    """Manages game scores with persistence (Composition pattern)"""
    
    def __init__(self, filepath: str = "scores.json"):
        self.filepath = Path(filepath)
        self.scores = self._load_scores()
    
    def _load_scores(self) -> list:
        if self.filepath.exists():
            try:
                with open(self.filepath, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []
        return []
    
    def add_score(self, score: int, player_name: str = "Player") -> None:
        """Add a new score to the list and save"""
        new_entry = {
            "score": score,
            "player": player_name,
            "timestamp": datetime.now().isoformat()
        }
        self.scores.append(new_entry)
        self.scores.sort(key=lambda x: x["score"], reverse=True)
        self._save_scores()
    
    def _save_scores(self) -> None:
        try:
            with open(self.filepath, 'w') as f:
                json.dump(self.scores, f, indent=2)
        except IOError as e:
            print(f"Error saving scores: {e}")
    
    def get_high_scores(self, limit: int = 5) -> list:
        """Get top scores"""
        return self.scores[:limit]
    
    def clear_scores(self) -> None:
        """Clear all scores"""
        self.scores = []
        self._save_scores()
