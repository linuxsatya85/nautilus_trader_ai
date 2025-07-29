"""
Shared Memory System for AI Nautilus Trader
Extends existing CrewAI SQLite and Nautilus Trader storage systems
"""

import json
import sqlite3
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, asdict
import pandas as pd

from crewai.memory.storage.ltm_sqlite_storage import LTMSQLiteStorage
from crewai.utilities.paths import db_storage_path


@dataclass
class SharedMemoryEntry:
    """Unified memory entry for both CrewAI and Nautilus Trader"""
    id: Optional[str] = None
    source: str = ""  # 'crewai' or 'nautilus'
    data_type: str = ""  # 'market_data', 'agent_decision', 'trade_signal', etc.
    content: Dict[str, Any] = None
    metadata: Dict[str, Any] = None
    timestamp: str = ""
    score: float = 0.0
    tags: List[str] = None

    def __post_init__(self):
        if self.content is None:
            self.content = {}
        if self.metadata is None:
            self.metadata = {}
        if self.tags is None:
            self.tags = []
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class SharedMemoryStorage:
    """
    Shared memory storage that extends CrewAI's SQLite system
    and integrates with Nautilus Trader's data persistence
    """
    
    def __init__(self, db_path: Optional[str] = None):
        # Use CrewAI's existing database path structure
        if db_path is None:
            db_path = str(Path(db_storage_path()) / "shared_memory_storage.db")
        
        self.db_path = db_path
        self._lock = threading.RLock()
        
        # Initialize CrewAI's existing LTM storage
        self.crewai_storage = LTMSQLiteStorage(
            str(Path(db_storage_path()) / "crewai_shared_memory.db")
        )
        
        # Ensure parent directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._initialize_shared_db()
    
    def _initialize_shared_db(self):
        """Initialize shared memory database with extended tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Shared memory table for both frameworks
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS shared_memories (
                        id TEXT PRIMARY KEY,
                        source TEXT NOT NULL,
                        data_type TEXT NOT NULL,
                        content TEXT NOT NULL,
                        metadata TEXT,
                        timestamp TEXT NOT NULL,
                        score REAL DEFAULT 0.0,
                        tags TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Market data cache for Nautilus Trader
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS market_data_cache (
                        id TEXT PRIMARY KEY,
                        instrument_id TEXT NOT NULL,
                        data_type TEXT NOT NULL,
                        data TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Agent decisions cache for CrewAI
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS agent_decisions_cache (
                        id TEXT PRIMARY KEY,
                        agent_id TEXT NOT NULL,
                        task_id TEXT,
                        decision_type TEXT NOT NULL,
                        decision_data TEXT NOT NULL,
                        confidence REAL DEFAULT 0.0,
                        timestamp TEXT NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Cross-framework events
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS cross_framework_events (
                        id TEXT PRIMARY KEY,
                        event_type TEXT NOT NULL,
                        source_framework TEXT NOT NULL,
                        target_framework TEXT,
                        event_data TEXT NOT NULL,
                        processed BOOLEAN DEFAULT FALSE,
                        timestamp TEXT NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes for performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_shared_source ON shared_memories(source)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_shared_type ON shared_memories(data_type)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_shared_timestamp ON shared_memories(timestamp)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_market_instrument ON market_data_cache(instrument_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_agent_decisions ON agent_decisions_cache(agent_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_processed ON cross_framework_events(processed)")
                
                conn.commit()
                
        except sqlite3.Error as e:
            print(f"Error initializing shared memory database: {e}")
    
    def save_shared_memory(self, entry: SharedMemoryEntry) -> bool:
        """Save a shared memory entry accessible to both frameworks"""
        try:
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    # Generate ID if not provided
                    if not entry.id:
                        entry.id = f"{entry.source}_{entry.data_type}_{int(time.time() * 1000)}"
                    
                    cursor.execute("""
                        INSERT OR REPLACE INTO shared_memories 
                        (id, source, data_type, content, metadata, timestamp, score, tags, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (
                        entry.id,
                        entry.source,
                        entry.data_type,
                        json.dumps(entry.content),
                        json.dumps(entry.metadata),
                        entry.timestamp,
                        entry.score,
                        json.dumps(entry.tags)
                    ))
                    
                    conn.commit()
                    return True
                    
        except Exception as e:
            print(f"Error saving shared memory: {e}")
            return False
    
    def load_shared_memories(
        self, 
        source: Optional[str] = None,
        data_type: Optional[str] = None,
        limit: int = 100,
        min_score: float = 0.0
    ) -> List[SharedMemoryEntry]:
        """Load shared memories with filtering"""
        try:
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    query = """
                        SELECT id, source, data_type, content, metadata, timestamp, score, tags
                        FROM shared_memories 
                        WHERE score >= ?
                    """
                    params = [min_score]
                    
                    if source:
                        query += " AND source = ?"
                        params.append(source)
                    
                    if data_type:
                        query += " AND data_type = ?"
                        params.append(data_type)
                    
                    query += " ORDER BY timestamp DESC, score DESC LIMIT ?"
                    params.append(limit)
                    
                    cursor.execute(query, params)
                    rows = cursor.fetchall()
                    
                    entries = []
                    for row in rows:
                        entry = SharedMemoryEntry(
                            id=row[0],
                            source=row[1],
                            data_type=row[2],
                            content=json.loads(row[3]),
                            metadata=json.loads(row[4]) if row[4] else {},
                            timestamp=row[5],
                            score=row[6],
                            tags=json.loads(row[7]) if row[7] else []
                        )
                        entries.append(entry)
                    
                    return entries
                    
        except Exception as e:
            print(f"Error loading shared memories: {e}")
            return []

    def save_market_data(self, instrument_id: str, data_type: str, data: Dict[str, Any]) -> bool:
        """Save market data for Nautilus Trader integration"""
        try:
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()

                    data_id = f"market_{instrument_id}_{data_type}_{int(time.time() * 1000)}"
                    timestamp = datetime.now().isoformat()

                    cursor.execute("""
                        INSERT INTO market_data_cache
                        (id, instrument_id, data_type, data, timestamp)
                        VALUES (?, ?, ?, ?, ?)
                    """, (data_id, instrument_id, data_type, json.dumps(data), timestamp))

                    conn.commit()
                    return True

        except Exception as e:
            print(f"Error saving market data: {e}")
            return False

    def save_agent_decision(self, agent_id: str, decision_type: str,
                          decision_data: Dict[str, Any], confidence: float = 0.0,
                          task_id: Optional[str] = None) -> bool:
        """Save agent decision for CrewAI integration"""
        try:
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()

                    decision_id = f"decision_{agent_id}_{decision_type}_{int(time.time() * 1000)}"
                    timestamp = datetime.now().isoformat()

                    cursor.execute("""
                        INSERT INTO agent_decisions_cache
                        (id, agent_id, task_id, decision_type, decision_data, confidence, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (decision_id, agent_id, task_id, decision_type,
                          json.dumps(decision_data), confidence, timestamp))

                    conn.commit()
                    return True

        except Exception as e:
            print(f"Error saving agent decision: {e}")
            return False

    def get_market_data(self, instrument_id: str, data_type: Optional[str] = None,
                       limit: int = 100) -> List[Dict[str, Any]]:
        """Get market data for specific instrument"""
        try:
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()

                    query = """
                        SELECT data, timestamp FROM market_data_cache
                        WHERE instrument_id = ?
                    """
                    params = [instrument_id]

                    if data_type:
                        query += " AND data_type = ?"
                        params.append(data_type)

                    query += " ORDER BY timestamp DESC LIMIT ?"
                    params.append(limit)

                    cursor.execute(query, params)
                    rows = cursor.fetchall()

                    return [
                        {
                            "data": json.loads(row[0]),
                            "timestamp": row[1]
                        }
                        for row in rows
                    ]

        except Exception as e:
            print(f"Error getting market data: {e}")
            return []

    def get_agent_decisions(self, agent_id: str, decision_type: Optional[str] = None,
                          limit: int = 100) -> List[Dict[str, Any]]:
        """Get agent decisions for specific agent"""
        try:
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()

                    query = """
                        SELECT decision_data, confidence, timestamp FROM agent_decisions_cache
                        WHERE agent_id = ?
                    """
                    params = [agent_id]

                    if decision_type:
                        query += " AND decision_type = ?"
                        params.append(decision_type)

                    query += " ORDER BY timestamp DESC LIMIT ?"
                    params.append(limit)

                    cursor.execute(query, params)
                    rows = cursor.fetchall()

                    return [
                        {
                            "decision_data": json.loads(row[0]),
                            "confidence": row[1],
                            "timestamp": row[2]
                        }
                        for row in rows
                    ]

        except Exception as e:
            print(f"Error getting agent decisions: {e}")
            return []

    def create_cross_framework_event(self, event_type: str, source_framework: str,
                                   event_data: Dict[str, Any],
                                   target_framework: Optional[str] = None) -> bool:
        """Create event for cross-framework communication"""
        try:
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()

                    event_id = f"event_{source_framework}_{event_type}_{int(time.time() * 1000)}"
                    timestamp = datetime.now().isoformat()

                    cursor.execute("""
                        INSERT INTO cross_framework_events
                        (id, event_type, source_framework, target_framework, event_data, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (event_id, event_type, source_framework, target_framework,
                          json.dumps(event_data), timestamp))

                    conn.commit()
                    return True

        except Exception as e:
            print(f"Error creating cross-framework event: {e}")
            return False

    def get_unprocessed_events(self, target_framework: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get unprocessed cross-framework events"""
        try:
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()

                    query = """
                        SELECT id, event_type, source_framework, event_data, timestamp
                        FROM cross_framework_events
                        WHERE processed = FALSE
                    """
                    params = []

                    if target_framework:
                        query += " AND (target_framework = ? OR target_framework IS NULL)"
                        params.append(target_framework)

                    query += " ORDER BY timestamp ASC"

                    cursor.execute(query, params)
                    rows = cursor.fetchall()

                    return [
                        {
                            "id": row[0],
                            "event_type": row[1],
                            "source_framework": row[2],
                            "event_data": json.loads(row[3]),
                            "timestamp": row[4]
                        }
                        for row in rows
                    ]

        except Exception as e:
            print(f"Error getting unprocessed events: {e}")
            return []

    def mark_event_processed(self, event_id: str) -> bool:
        """Mark an event as processed"""
        try:
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE cross_framework_events
                        SET processed = TRUE
                        WHERE id = ?
                    """, (event_id,))
                    conn.commit()
                    return True

        except Exception as e:
            print(f"Error marking event as processed: {e}")
            return False

    def cleanup_old_data(self, days_to_keep: int = 7) -> bool:
        """Clean up old data to prevent database bloat"""
        try:
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()

                    cutoff_date = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
                    cutoff_iso = datetime.fromtimestamp(cutoff_date).isoformat()

                    # Clean up old market data
                    cursor.execute("""
                        DELETE FROM market_data_cache
                        WHERE timestamp < ?
                    """, (cutoff_iso,))

                    # Clean up old processed events
                    cursor.execute("""
                        DELETE FROM cross_framework_events
                        WHERE processed = TRUE AND timestamp < ?
                    """, (cutoff_iso,))

                    conn.commit()
                    return True

        except Exception as e:
            print(f"Error cleaning up old data: {e}")
            return False
