"""
HERPath AI - Health Library & Educational Resource Module
recHERsion 2026 | PS1: Women's Healthcare
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from config import RESOURCES_FILE_PATH


class HealthLibrary:
    """Provides categorized, searchable, evidence-based educational resources."""

    def __init__(self, resources_path: Optional[str] = None):
        self.resources_path = resources_path or RESOURCES_FILE_PATH
        self._resources: List[Dict[str, Any]] = []
        self._load_resources()

    def _load_resources(self) -> None:
        """Loads curated resources from JSON with safe fallback."""
        try:
            path = Path(self.resources_path)
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    self._resources = json.load(f)
            else:
                self._resources = self._fallback_resources()
        except Exception:
            self._resources = self._fallback_resources()

    def get_all_resources(self) -> List[Dict[str, Any]]:
        """Returns all available educational resources."""
        return self._resources

    def get_categories(self) -> List[str]:
        """Returns sorted unique category list."""
        categories = sorted(list(set(r.get("category", "General") for r in self._resources)))
        return ["All Categories"] + categories

    def get_resource_by_id(self, resource_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single resource by its ID."""
        for r in self._resources:
            if r.get("id") == resource_id:
                return r
        return None

    def search_resources(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Filters resources by search keyword and category."""
        results = self._resources

        # Category Filter
        if category and category != "All Categories":
            results = [r for r in results if r.get("category") == category]

        # Keyword Filter
        if query and query.strip():
            q = query.strip().lower()
            filtered = []
            for r in results:
                title = r.get("title", "").lower()
                summary = r.get("summary", "").lower()
                cat = r.get("category", "").lower()
                org = r.get("source_org", "").lower()
                points = " ".join(r.get("key_points", [])).lower()
                
                if (q in title or q in summary or q in cat or q in org or q in points):
                    filtered.append(r)
            results = filtered

        return results

    def get_recommended_resources_for_symptom(self, symptom_category: str) -> List[Dict[str, Any]]:
        """Finds recommended educational readings mapped to a specific symptom category."""
        category_map = {
            "Pelvic & Menstrual": ["PCOS Education", "Endometriosis Education", "Menstrual Health"],
            "Systemic & Energy": ["Anemia & Iron Deficiency", "General Wellbeing & Sleep", "Menopause"],
            "Neurological & Head": ["Neurological & Head", "General Wellbeing & Sleep"],
            "Breast Health": ["Breast Health"],
            "Gastrointestinal & Abdominal": ["Endometriosis Education", "PCOS Education"],
            "Urinary & Pelvic Floor": ["Urinary Health", "Endometriosis Education"],
            "Mood & Sleep": ["Stress & Mental Wellbeing", "General Wellbeing & Sleep", "Menopause"]
        }
        target_cats = category_map.get(symptom_category, ["General Wellbeing & Sleep"])
        matches = [r for r in self._resources if r.get("category") in target_cats]
        return matches[:3]

    def _fallback_resources(self) -> List[Dict[str, Any]]:
        """Embedded fallback in case of missing file."""
        return [
            {
                "id": "res-fallback-01",
                "title": "Evidence-Based Women's Health Education",
                "category": "General Wellbeing",
                "summary": "Accessing validated medical literature and tracking personal patterns helps empower informed clinical consultations.",
                "key_points": [
                    "Always consult licensed healthcare providers for diagnostic evaluations.",
                    "Keep detailed symptom diaries to share with your physician."
                ],
                "source_org": "World Health Organization (WHO)",
                "source_title": "Women's Health",
                "source_url": "https://www.who.int/health-topics/women-s-health",
                "last_reviewed": "2024-01-01"
            }
        ]
