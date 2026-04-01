import os
import asyncio
import time
import json
import argparse
import random
import uuid
from typing import List, Any, Dict
from datetime import datetime, timezone, timedelta

from aegis_py.storage.manager import StorageManager
from aegis_py.memory.core import MemoryManager
from aegis_py.retrieval.search import SearchPipeline
from aegis_py.retrieval.models import SearchQuery, SearchResult
from aegis_py.storage.models import Memory
from aegis_py.surface import serialize_search_result

class V9ExtremeGauntlet:
    def __init__(self, db_path: str, noise_count: int, scope_count: int, conflict_count: int, compare_v8: bool):
        self.db_path = db_path
        self.noise_count = noise_count
        self.scope_count = scope_count
        self.conflict_count = conflict_count
        self.compare_v8 = compare_v8
        
        if os.path.exists(db_path):
            os.remove(db_path)
            
        self.storage = StorageManager(db_path)
        self.manager = MemoryManager(self.storage)
        self.pipeline = SearchPipeline(self.storage)
        self.scenarios = []
        self.stats = {"pass": 0, "fail": 0, "v9_latencies": [], "v8_latencies": []}

    def log(self, msg: str):
        print(f"[*] {msg}")

    def populate_noise(self):
        self.log(f"Injecting {self.noise_count} noise memories across {self.scope_count} scopes...")
        subjects = ["weather", "news", "random_fact", "history", "config", "log"]
        for i in range(self.noise_count):
            scope_id = f"scope_{i % self.scope_count}"
            sub = random.choice(subjects)
            m = Memory(
                id=f"noise_{i}",
                type="semantic",
                content=f"Random noise data {uuid.uuid4().hex} about {sub}",
                subject=f"{sub}_{i}",
                confidence=random.uniform(0.1, 0.8),
                source_kind="ingest",
                source_ref="gauntlet",
                scope_type="test",
                scope_id=scope_id,
                created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 100))
            )
            self.manager.store(m)
            # Fast FTS sync
            self.storage.execute("INSERT INTO memories_fts(rowid, content, subject) VALUES ((SELECT rowid FROM memories WHERE id = ?), ?, ?)", (m.id, m.content, m.subject))
        self.log("Noise injection complete.")

    def setup_scenarios(self):
        now_str = datetime.now(timezone.utc).isoformat()
        
        # 1. Truth Alignment Storm (Deep Correction Chain)
        self.log("Setting up Truth Alignment Storm...")
        subject = "hq_location"
        for i in range(10):
            status = "superseded" if i < 9 else "active"
            m = Memory(
                id=f"loc_{i}", type="semantic", content=f"HQ is at Floor {i+1}", subject=subject, 
                confidence=0.5 + (i * 0.05), source_kind="manual", source_ref="chain",
                scope_type="agent", scope_id="main", status=status,
                metadata={"is_winner": (i == 9)}
            )
            self.manager.store(m)
            self.storage.execute("INSERT INTO memories_fts(rowid, content, subject) VALUES ((SELECT rowid FROM memories WHERE id = ?), ?, ?)", (m.id, m.content, m.subject))
        self.scenarios.append({
            "name": "Truth Storm", "query": "HQ floor location", "expected_top": "loc_9", 
            "scope": ("agent", "main"), "check": "id"
        })

        # 2. Conflict Storm (Complex network)
        self.log("Setting up Conflict Storm...")
        for i in range(self.conflict_count):
            m_a = Memory(id=f"c_a_{i}", type="semantic", content=f"Value is {i}", subject=f"conflict_{i}", confidence=0.7, source_kind="manual", scope_type="agent", scope_id="main")
            m_b = Memory(id=f"c_b_{i}", type="semantic", content=f"Value is {i+100}", subject=f"conflict_{i}", confidence=0.7, source_kind="manual", scope_type="agent", scope_id="main")
            self.manager.store(m_a)
            self.manager.store(m_b)
            self.storage.execute("INSERT INTO conflicts (id, subject_key, memory_a_id, memory_b_id, score, status, created_at) VALUES (?, ?, ?, ?, 0.9, 'open', ?)", (f"conf_{i}", f"conflict_{i}", m_a.id, m_b.id, now_str))
            self.storage.execute("INSERT INTO memories_fts(rowid, content, subject) VALUES ((SELECT rowid FROM memories WHERE id = ?), ?, ?)", (m_a.id, m_a.content, m_a.subject))
            self.storage.execute("INSERT INTO memories_fts(rowid, content, subject) VALUES ((SELECT rowid FROM memories WHERE id = ?), ?, ?)", (m_b.id, m_b.content, m_b.subject))
        self.scenarios.append({
            "name": "Conflict Storm", "query": "Value is", "expected_action": "suppress_all", 
            "scope": ("agent", "main"), "check": "suppression"
        })

        # 3. Bias Fairness (Flashy vs Truth)
        self.log("Setting up Bias Fairness scenario...")
        # Add a common keyword 'status_check' to both
        m_flashy = Memory(id="bias_flashy", type="semantic", content="URGENT: SYSTEM IS DOWN!! ERROR 500!! status_check", subject="sys_status", confidence=0.1, source_kind="ingest", scope_type="agent", scope_id="main", metadata={"is_winner": False})
        m_truth = Memory(id="bias_truth", type="semantic", content="System maintenance is scheduled. Status: nominal. status_check", subject="sys_status", confidence=0.9, source_kind="verified", scope_id="main", scope_type="agent", metadata={"is_winner": True})
        self.manager.store(m_flashy)
        self.manager.store(m_truth)
        self.storage.execute("INSERT INTO memories_fts(rowid, content, subject) VALUES ((SELECT rowid FROM memories WHERE id = 'bias_flashy'), ?, ?)", (m_flashy.content, m_flashy.subject))
        self.storage.execute("INSERT INTO memories_fts(rowid, content, subject) VALUES ((SELECT rowid FROM memories WHERE id = 'bias_truth'), ?, ?)", (m_truth.content, m_truth.subject))
        self.scenarios.append({
            "name": "Bias Fairness", "query": "status_check", "expected_top": "bias_truth", 
            "scope": ("agent", "main"), "check": "id"
        })

    async def run(self):
        self.populate_noise()
        self.setup_scenarios()
        
        print(f"\n{'Scenario':<25} | {'v8 Rank':<10} | {'v9 Rank':<10} | {'v9 Score':<8} | {'Status'}")
        print("-" * 85)
        
        report = []

        for s in self.scenarios:
            # 1. Run v9
            q_v9 = SearchQuery(query=s["query"], scope_type=s["scope"][0], scope_id=s["scope"][1], min_score=-10.0)
            setattr(q_v9, "scoring_mode", "v9_primary")
            
            t0 = time.perf_counter()
            res_v9 = self.pipeline.search(q_v9)
            lat_v9 = (time.perf_counter() - t0) * 1000
            self.stats["v9_latencies"].append(lat_v9)

            # 2. Run v8 (if requested)
            lat_v8 = 0
            v8_top = "N/A"
            if self.compare_v8:
                q_v8 = SearchQuery(query=s["query"], scope_type=s["scope"][0], scope_id=s["scope"][1], min_score=-10.0)
                setattr(q_v8, "scoring_mode", "v8_primary")
                t0 = time.perf_counter()
                res_v8 = self.pipeline.search(q_v8)
                lat_v8 = (time.perf_counter() - t0) * 1000
                self.stats["v8_latencies"].append(lat_v8)
                v8_top = res_v8[0].memory.id if res_v8 else "None"

            v9_top = res_v9[0].memory.id if res_v9 else "None"
            v9_score = res_v9[0].v9_score if res_v9 else 0
            
            success = False
            if s["check"] == "id":
                success = (v9_top == s["expected_top"])
            elif s["check"] == "suppression":
                # High-severity conflicts should be pushed down (negative or low score)
                success = (v9_score < 0)

            status_mark = "✅ PASS" if success else "❌ FAIL"
            print(f"{s['name']:<25} | {v8_top:<10} | {v9_top:<10} | {v9_score:<8.2f} | {status_mark}")
            
            if success: self.stats["pass"] += 1
            else: self.stats["fail"] += 1
            
            if not success and res_v9:
                ser = serialize_search_result(res_v9[0])
                print(f"   [!] Audit: {ser['human_reason']}")
                print(f"   [!] Trace: {ser['v9_audit']['factors']}")

            report.append({
                "name": s["name"], "success": success, "v9_top": v9_top, "v8_top": v8_top,
                "v9_score": v9_score, "lat_v9": lat_v9, "lat_v8": lat_v8
            })

        # Summary
        print("-" * 85)
        print(f"TOTAL: {self.stats['pass']} PASS, {self.stats['fail']} FAIL")
        p50 = sorted(self.stats["v9_latencies"])[len(self.stats["v9_latencies"])//2]
        print(f"Latency p50: {p50:.2f}ms")
        
        return report

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--noise-memories", type=int, default=100)
    parser.add_argument("--scopes", type=int, default=2)
    parser.add_argument("--conflict-pairs", type=int, default=5)
    parser.add_argument("--compare-v8", action="store_true", default=True)
    parser.add_argument("--json-out", type=str, default=None)
    args = parser.parse_args()

    gauntlet = V9ExtremeGauntlet(
        "/home/hali/.openclaw/extensions/memory-aegis-v7/extreme_gauntlet.db",
        args.noise_memories, args.scopes, args.conflict_pairs, args.compare_v8
    )
    
    results = asyncio.run(gauntlet.run())
    
    if args.json_out:
        with open(args.json_out, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\n[+] Results saved to {args.json_out}")
    
    os.remove("/home/hali/.openclaw/extensions/memory-aegis-v7/extreme_gauntlet.db")
    exit(0 if gauntlet.stats["fail"] == 0 else 1)
