from __future__ import annotations
from typing import Dict, List, Optional
import re
import pandas as pd

# Canonical fields expected by schema.validate_and_normalize
REQUIRED_CANONICAL = [
    "issue_id", "issue_type", "status", "story_points",
    "created", "sprint_id", "sprint_start", "sprint_end",
]
OPTIONAL_CANONICAL = [
    "updated", "resolved", "assignee", "reporter", "sprint_name",
    "parent_id", "labels", "priority",
]

# Common header synonyms seen across Jira/Trello/CSV exports
_SYNONYMS: Dict[str, List[str]] = {
    "issue_id": ["issue id", "key", "ticket", "ticket key", "id"],
    "issue_type": ["issue type", "type", "issuetype"],
    "status": ["status", "state", "workflow status"],
    "story_points": ["story points", "points", "sp", "estimate", "storypoints"],
    "created": ["created", "created date", "created on", "creation date"],
    "updated": ["updated", "updated date", "last updated"],
    "resolved": ["resolved", "resolution date", "done date", "completed"],
    "sprint_id": ["sprint", "sprint id", "sprint key", "iteration", "sprint name"],
    "sprint_name": ["sprint name", "sprint title", "iteration name"],
    "sprint_start": ["sprint start", "start", "start date", "sprint start date", "iteration start"],
    "sprint_end": ["sprint end", "end", "end date", "sprint end date", "iteration end"],
    "assignee": ["assignee", "owner"],
    "reporter": ["reporter", "created by"],
    "parent_id": ["parent", "parent id", "epic link", "parent key"],
    "labels": ["labels", "tags", "tag"],
    "priority": ["priority", "prio"],
}

def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(s).strip().lower()).strip()

def infer_mapping(df: pd.DataFrame) -> Dict[str, Optional[str]]:
    """Best-effort mapping from uploaded headers to canonical headers."""
    src_cols_norm = {c: _norm(c) for c in df.columns}
    mapping: Dict[str, Optional[str]] = {k: None for k in REQUIRED_CANONICAL + OPTIONAL_CANONICAL}

    # 1) exact or normalized match
    rev = {v: k for k, v in src_cols_norm.items()}
    for target, syns in _SYNONYMS.items():
        for s in syns + [target.replace("_", " ")]:  # include canonical as phrase
            ns = _norm(s)
            # direct normalized hit
            for src, nsrc in src_cols_norm.items():
                if nsrc == ns:
                    mapping[target] = src
                    break
            if mapping[target]:
                break

    # 2) heuristics for sprint fields inside a single "sprint" text column
    # keep None; UI will allow manual selection
    return mapping

def apply_mapping(df: pd.DataFrame, mapping: Dict[str, Optional[str]]) -> pd.DataFrame:
    """Return DataFrame with canonical headers, selecting mapped source columns.
       Unmapped optional columns are created as None; required ones must be mapped."""
    out = pd.DataFrame()
    # Validate required are mapped
    missing = [k for k in REQUIRED_CANONICAL if not mapping.get(k)]
    if missing:
        raise ValueError(f"Required fields not mapped: {missing}")

    # Copy required
    for k in REQUIRED_CANONICAL:
        out[k] = df[mapping[k]]

    # Copy optionals if mapped, else None
    for k in OPTIONAL_CANONICAL:
        if mapping.get(k):
            out[k] = df[mapping[k]]
        else:
            out[k] = None

    return out
