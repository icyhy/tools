import os
import json

class PluginMeta:
    def __init__(self, p_id, name, meta):
        self.id = p_id
        self.name = name
        self.meta = meta

def get_available_plugins():
    plugins = {}
    plugins_dir = "app/plugins"
    if not os.path.exists(plugins_dir):
        return plugins
        
    for item in os.listdir(plugins_dir):
        item_path = os.path.join(plugins_dir, item)
        if os.path.isdir(item_path) and not item.startswith("__"):
            manifest_path = os.path.join(item_path, "manifest.json")
            if os.path.exists(manifest_path):
                try:
                    with open(manifest_path, 'r', encoding='utf-8') as f:
                        meta = json.load(f)
                        p_id = meta.get("id", item)
                        name = meta.get("name", p_id)
                        plugins[p_id] = PluginMeta(p_id, name, meta)
                except Exception as e:
                    print(f"Error loading manifest for {item}: {e}")
    return plugins
