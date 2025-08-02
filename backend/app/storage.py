"""
Storage and history management for the research brief generator.
"""

import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import sqlite3
import os
from pathlib import Path

from app.schemas import FinalBrief, BriefRequest
from app.config import settings

logger = logging.getLogger(__name__)


class BriefStorage:
    """Storage manager for research briefs and user history."""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.DATABASE_URL.replace("sqlite:///", "")
        self._init_database()
    
    def _init_database(self):
        """Initialize the database with required tables."""
        try:
            # Ensure directory exists
            db_dir = Path(self.db_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create users table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id TEXT PRIMARY KEY,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create briefs table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS briefs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        topic TEXT NOT NULL,
                        depth TEXT NOT NULL,
                        is_follow_up BOOLEAN NOT NULL,
                        brief_data TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                """)
                
                # Create conversations table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS conversations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        user_input TEXT NOT NULL,
                        bot_response TEXT NOT NULL,
                        interaction_type TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                """)
                
                # Create indexes
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_briefs_user_id 
                    ON briefs (user_id)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_briefs_created_at 
                    ON briefs (created_at)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_conversations_user_id 
                    ON conversations (user_id)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_conversations_created_at 
                    ON conversations (created_at)
                """)
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def save_brief(self, user_id: str, request: BriefRequest, brief: FinalBrief) -> bool:
        """
        Save a research brief to storage.
        
        Args:
            user_id: User identifier
            request: Original request
            brief: Generated brief
            
        Returns:
            True if saved successfully
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Ensure user exists
                cursor.execute("""
                    INSERT OR IGNORE INTO users (user_id) VALUES (?)
                """, (user_id,))
                
                # Update user activity
                cursor.execute("""
                    UPDATE users SET last_activity = CURRENT_TIMESTAMP 
                    WHERE user_id = ?
                """, (user_id,))
                
                # Save brief
                brief_data = brief.model_dump_json()
                cursor.execute("""
                    INSERT INTO briefs (user_id, topic, depth, is_follow_up, brief_data)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    user_id,
                    request.topic,
                    request.depth.value,
                    request.follow_up,
                    brief_data
                ))
                
                conn.commit()
                logger.info(f"Brief saved for user {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error saving brief: {e}")
            return False
    
    def get_user_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get user's research history.
        
        Args:
            user_id: User identifier
            limit: Maximum number of briefs to return
            
        Returns:
            List of previous briefs with database IDs
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, brief_data, created_at FROM briefs 
                    WHERE user_id = ? 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (user_id, limit))
                
                results = cursor.fetchall()
                briefs = []
                
                for row in results:
                    try:
                        brief_id, brief_data, created_at = row
                        brief_obj = json.loads(brief_data)
                        brief = FinalBrief.model_validate(brief_obj)
                        
                        # Create a dict with the brief data and additional fields
                        brief_dict = brief.model_dump()
                        brief_dict['id'] = brief_id
                        brief_dict['generated_at'] = created_at
                        
                        briefs.append(brief_dict)
                    except Exception as e:
                        logger.error(f"Error parsing brief data: {e}")
                        continue
                
                logger.info(f"Retrieved {len(briefs)} briefs for user {user_id}")
                return briefs
                
        except Exception as e:
            logger.error(f"Error retrieving user history: {e}")
            return []
    
    def save_conversation(self, user_id: str, user_input: str, bot_response: str, interaction_type: str = "chat") -> bool:
        """
        Save a conversation interaction to storage.
        
        Args:
            user_id: User identifier
            user_input: User's message
            bot_response: Bot's response
            interaction_type: Type of interaction (chat, brief, etc.)
            
        Returns:
            True if saved successfully
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Ensure user exists
                cursor.execute("""
                    INSERT OR IGNORE INTO users (user_id) VALUES (?)
                """, (user_id,))
                
                # Save conversation
                cursor.execute("""
                    INSERT INTO conversations (user_id, user_input, bot_response, interaction_type)
                    VALUES (?, ?, ?, ?)
                """, (user_id, user_input, bot_response, interaction_type))
                
                conn.commit()
                logger.info(f"Conversation saved for user {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error saving conversation: {e}")
            return False
    
    def get_conversation_history(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get user's conversation history.
        
        Args:
            user_id: User identifier
            limit: Maximum number of conversations to return
            
        Returns:
            List of conversation interactions
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT user_input, bot_response, interaction_type, created_at 
                    FROM conversations 
                    WHERE user_id = ? 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (user_id, limit))
                
                results = cursor.fetchall()
                conversations = []
                
                for row in results:
                    conversations.append({
                        "user_input": row[0],
                        "bot_response": row[1],
                        "interaction_type": row[2],
                        "created_at": row[3]
                    })
                
                logger.info(f"Retrieved {len(conversations)} conversations for user {user_id}")
                return conversations
                
        except Exception as e:
            logger.error(f"Error retrieving conversation history: {e}")
            return []
    
    def get_brief_by_id(self, brief_id: int) -> Optional[FinalBrief]:
        """
        Get a specific brief by ID.
        
        Args:
            brief_id: Brief identifier
            
        Returns:
            Brief if found, None otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT brief_data FROM briefs WHERE id = ?
                """, (brief_id,))
                
                result = cursor.fetchone()
                if result:
                    brief_data = json.loads(result[0])
                    return FinalBrief.model_validate(brief_data)
                
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving brief {brief_id}: {e}")
            return None
    
    def delete_user_briefs(self, user_id: str) -> bool:
        """
        Delete all briefs for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            True if deleted successfully
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    DELETE FROM briefs WHERE user_id = ?
                """, (user_id,))
                
                cursor.execute("""
                    DELETE FROM users WHERE user_id = ?
                """, (user_id,))
                
                conn.commit()
                logger.info(f"Deleted all briefs for user {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting user briefs: {e}")
            return False
    
    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get statistics for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary with user statistics
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get total briefs
                cursor.execute("""
                    SELECT COUNT(*) FROM briefs WHERE user_id = ?
                """, (user_id,))
                total_briefs = cursor.fetchone()[0]
                
                # Get recent activity
                cursor.execute("""
                    SELECT COUNT(*) FROM briefs 
                    WHERE user_id = ? AND created_at > datetime('now', '-7 days')
                """, (user_id,))
                recent_briefs = cursor.fetchone()[0]
                
                # Get user creation date
                cursor.execute("""
                    SELECT created_at FROM users WHERE user_id = ?
                """, (user_id,))
                result = cursor.fetchone()
                user_created = result[0] if result else None
                
                return {
                    "total_briefs": total_briefs,
                    "recent_briefs": recent_briefs,
                    "user_created": user_created
                }
                
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return {
                "total_briefs": 0,
                "recent_briefs": 0,
                "user_created": None
            }


# Global storage instance
brief_storage = BriefStorage()


# InMemoryStorage class removed - always using SQLite for persistence


# Always use SQLite storage for persistence
storage = brief_storage 