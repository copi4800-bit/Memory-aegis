import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from aegis_py.storage.models import Memory, MemoryLink

def generate_random_content(tag: str, index: int) -> str:
    topics = ["React", "Python", "SQLite", "Memory", "AI", "Agent", "OpenClaw", "Aegis", "TypeScript", "System"]
    actions = ["build", "fix", "update", "deploy", "verify", "rebuild", "clean", "scan", "search", "store"]
    topic = random.choice(topics)
    action = random.choice(actions)
    return f"[{tag} #{index}] {action.capitalize()} the {topic} system. This is an important piece of data for stress testing."

def generate_dataset_a(count: int = 10000) -> List[Memory]:
    """Dataset A: Clean realistic (10k)"""
    memories = []
    projects = ["P1", "P2", "P3", "P4", "P5"]
    scopes = ["user", "global", "project", "session"]
    types = ["semantic", "episodic", "working", "procedural"]
    
    for i in range(count):
        m_type = random.choice(types)
        scope_type = random.choice(scopes)
        scope_id = random.choice(projects)
        content = generate_random_content("A", i)
        
        memories.append(Memory(
            id=str(uuid.uuid4()),
            type=m_type,
            scope_type=scope_type,
            scope_id=scope_id,
            content=content,
            source_kind="manual" if i % 2 == 0 else "message",
            subject=f"tech.{random.choice(['infra', 'app', 'core', 'ui'])}",
            summary=f"Summary of clean record {i}",
            created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 30))
        ))
    return memories

def generate_dataset_b(count: int = 10000) -> List[Memory]:
    """Dataset B: Conflict-heavy (10k, 20% conflicts)"""
    memories = []
    conflict_count = int(count * 0.2)
    
    # Generate base memories
    for i in range(count - conflict_count):
        memories.append(Memory(
            id=f"B-base-{i}",
            type="semantic",
            scope_type="project",
            scope_id="CONFLICT_WALKER",
            content=f"User likes {i} as a favorite number.",
            source_kind="manual",
            subject=f"user.preference.{i}"
        ))
    
    # Generate conflicting memories
    for i in range(conflict_count):
        # Conflicts with base-i
        memories.append(Memory(
            id=f"B-conflict-{i}",
            type="semantic",
            scope_type="project",
            scope_id="CONFLICT_WALKER",
            content=f"User strictly hates {i} and never uses it as a favorite number.",
            source_kind="message",
            subject=f"user.preference.{i}"
        ))
    return memories

def generate_dataset_c(count: int = 20000) -> List[Memory]:
    """Dataset C: Duplicate & noisy (20k)"""
    memories = []
    for i in range(count // 2):
        content = f"The value of pi is approximately 3.14159, used in project CIRCLE."
        # Original
        memories.append(Memory(
            id=f"C-orig-{i}",
            type="semantic",
            scope_type="project",
            scope_id="NOISY",
            content=content,
            source_kind="manual",
            subject="math.pi"
        ))
        # Near duplicate
        memories.append(Memory(
            id=f"C-dup-{i}",
            type="semantic",
            scope_type="project",
            scope_id="NOISY",
            content=content + " (This is a noisy duplicate entry)",
            source_kind="message",
            subject="math.pi.alias"
        ))
    return memories

def generate_dataset_d(count: int = 2000) -> List[Memory]:
    """Dataset D: Procedure-heavy (2k)"""
    memories = []
    for i in range(count):
        memories.append(Memory(
            id=f"D-proc-{i}",
            type="procedural",
            scope_type="project",
            scope_id="PROC_STORM",
            content=f"# Workflow {i}: 1. Step A, 2. Step B, 3. Success.",
            source_kind="manual",
            subject=f"workflow.step.{i % 10}" # Many share the same subject
        ))
    return memories

def generate_dataset_f(count: int = 100000) -> List[Memory]:
    """Dataset F: Monster mixed (100k)"""
    # For speed, we just mix chunks of other generators
    mems = []
    mems.extend(generate_dataset_a(count // 2))
    mems.extend(generate_dataset_b(count // 4))
    mems.extend(generate_dataset_c(count // 4))
    return mems[:count]

if __name__ == "__main__":
    import sys
    if "--dry-run" in sys.argv:
        print("Dataset A:", len(generate_dataset_a()))
        print("Dataset B:", len(generate_dataset_b()))
        print("Dataset C:", len(generate_dataset_c()))
        print("Dataset D:", len(generate_dataset_d()))
        print("Dataset F:", len(generate_dataset_f()))
