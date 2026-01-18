from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, default="内部培训")
    started_at = Column(DateTime, default=datetime.utcnow)
    host_password_hash = Column(String) # Store hashed password
    admin_password_hash = Column(String, default="admin123") # Admin panel password
    logo_url = Column(String, nullable=True) # URL or Base64
    is_active = Column(Boolean, default=True)
    status = Column(String, default="pending") # pending, running, ended
    enabled_plugins = Column(JSON, default=[]) # List of plugin IDs enabled for this event
    plugins_config = Column(JSON, default={}) # Event-specific config for plugins
    current_plugin_id = Column(String, nullable=True) # Currently active plugin ID for display
    current_plugin_state = Column(String, default="idle") # idle, running, results

class Participant(Base):
    __tablename__ = "participants"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"))
    session_token = Column(String, unique=True, index=True) # Browser session token
    name = Column(String, nullable=True)
    department = Column(String, nullable=True)
    role = Column(String, default="user") # 'user', 'host', 'admin'
    code4 = Column(String, nullable=True) # Random 4-digit code
    created_at = Column(DateTime, default=datetime.utcnow)
    
    event = relationship("Event")

class Plugin(Base):
    __tablename__ = "plugins"

    id = Column(String, primary_key=True) # Plugin folder name as ID
    name = Column(String)
    description = Column(String, nullable=True)
    is_enabled = Column(Boolean, default=True)
    config = Column(JSON, nullable=True)

class PluginSubmission(Base):
    __tablename__ = "plugin_submissions"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"))
    plugin_id = Column(String, ForeignKey("plugins.id"))
    user_id = Column(Integer, ForeignKey("participants.id"))
    data = Column(JSON) # User submission data
    created_at = Column(DateTime, default=datetime.utcnow)
