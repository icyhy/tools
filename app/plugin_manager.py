import importlib
import os
import json
from abc import ABC, abstractmethod
from fastapi import APIRouter
from fastapi.templating import Jinja2Templates
from app.models import Plugin as PluginModel
from app.database import SessionLocal
import logging

logger = logging.getLogger(__name__)

class BasePlugin(ABC):
    def __init__(self, plugin_id: str, path: str):
        self.plugin_id = plugin_id
        self.path = path
        self.meta = {}
        self.load_metadata()

    def load_metadata(self):
        manifest_path = os.path.join(self.path, "manifest.json")
        if os.path.exists(manifest_path):
            with open(manifest_path, "r", encoding="utf-8") as f:
                self.meta = json.load(f)
        else:
            self.meta = {"name": self.plugin_id, "description": ""}

    @property
    def name(self):
        return self.meta.get("name", self.plugin_id)

    @abstractmethod
    async def start(self, event_id: int):
        pass

    @abstractmethod
    async def stop(self, event_id: int):
        pass
    
    @abstractmethod
    async def handle_input(self, event_id: int, user_id: int, data: dict):
        pass

    @abstractmethod
    async def get_results(self, event_id: int) -> dict:
        pass

class PluginManager:
    def __init__(self, plugin_dir: str = "plugins"):
        self.plugin_dir = plugin_dir
        self.plugins = {}
        self.templates = {} # plugin_id -> Jinja2Templates

    def load_plugins(self):
        logger.info(f"Scanning plugins in {self.plugin_dir}...")
        if not os.path.exists(self.plugin_dir):
            os.makedirs(self.plugin_dir)
            
        for name in os.listdir(self.plugin_dir):
            plugin_path = os.path.join(self.plugin_dir, name)
            if os.path.isdir(plugin_path) and os.path.exists(os.path.join(plugin_path, "plugin.py")):
                try:
                    # Import module
                    spec = importlib.util.spec_from_file_location(f"plugins.{name}", os.path.join(plugin_path, "plugin.py"))
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Find Plugin class
                    if hasattr(module, "Plugin"):
                        plugin_instance = module.Plugin(name, plugin_path)
                        self.plugins[name] = plugin_instance
                        
                        # Setup templates
                        template_dir = os.path.join(plugin_path, "templates")
                        if os.path.isdir(template_dir):
                            tmpl = Jinja2Templates(directory=template_dir)
                            tmpl.env.filters["tojson"] = json.dumps
                            self.templates[name] = tmpl
                            
                        logger.info(f"Loaded plugin: {name}")
                        
                        # Sync to DB
                        self.sync_to_db(plugin_instance)
                except Exception as e:
                    logger.error(f"Failed to load plugin {name}: {e}")

    def sync_to_db(self, plugin: BasePlugin):
        db = SessionLocal()
        try:
            db_plugin = db.query(PluginModel).filter(PluginModel.id == plugin.plugin_id).first()
            if not db_plugin:
                db_plugin = PluginModel(
                    id=plugin.plugin_id,
                    name=plugin.name,
                    description=plugin.meta.get("description"),
                    config=plugin.meta.get("config", {})
                )
                db.add(db_plugin)
            else:
                db_plugin.name = plugin.name
                db_plugin.description = plugin.meta.get("description")
                # db_plugin.config = plugin.meta.get("config", {}) # Don't overwrite config if modified
            db.commit()
        finally:
            db.close()

    def get_plugin(self, plugin_id: str):
        # 1. Check static plugins
        if plugin_id in self.plugins:
            return self.plugins[plugin_id]
            
        # 2. Check dynamic plugins (Custom)
        # Check simple heuristic or query DB if needed. 
        # Using a fresh session here for safety, though caching would be better.
        if plugin_id.startswith("custom_"):
            db = SessionLocal()
            try:
                event = db.query(Event).filter(Event.is_active == True).first()
                if event and event.custom_plugins:
                    custom_config = event.custom_plugins.get(plugin_id)
                    if custom_config:
                        return self.create_dynamic_plugin(plugin_id, custom_config)
            except Exception as e:
                logger.error(f"Error loading dynamic plugin {plugin_id}: {e}")
            finally:
                db.close()
                
        return None

    def create_dynamic_plugin(self, plugin_id: str, config: dict):
        p_type = config.get("type")
        instance = None
        
        try:
            if p_type == "survey":
                # Lazy import to avoid circular dependency
                from plugins.ai_survey.plugin import Plugin as SurveyPlugin
                # Use base plugin path for templates
                instance = SurveyPlugin(plugin_id, os.path.join(self.plugin_dir, "ai_survey"))
            elif p_type == "vote":
                from plugins.demo_vote.plugin import Plugin as VotePlugin
                instance = VotePlugin(plugin_id, os.path.join(self.plugin_dir, "demo_vote"))
        except ImportError as e:
            logger.error(f"Could not import base plugin for type {p_type}: {e}")
            return None
            
        if instance:
            # Override meta with custom config
            instance.meta = {
                "name": config.get("name", plugin_id),
                "description": "Custom Interaction",
                "config": config
            }
        return instance

    def get_templates(self, plugin_id: str):
        if plugin_id in self.templates:
            return self.templates[plugin_id]
            
        # Forward dynamic plugins to base templates
        if plugin_id.startswith("custom_survey"):
            return self.templates.get("ai_survey")
        elif plugin_id.startswith("custom_vote"):
            return self.templates.get("demo_vote")
            
        return None
        
    def get_all_plugins(self, db: SessionLocal):
        """Return combined list of static and dynamic plugins"""
        all_plugins = self.plugins.copy()
        
        # Merge dynamic plugins
        try:
            event = db.query(Event).filter(Event.is_active == True).first()
            if event and event.custom_plugins:
                for pid, config in event.custom_plugins.items():
                    plugin = self.create_dynamic_plugin(pid, config)
                    if plugin:
                        all_plugins[pid] = plugin
        except Exception as e:
            logger.error(f"Error fetching dynamic plugins: {e}")
            
        return all_plugins

plugin_manager = PluginManager()
