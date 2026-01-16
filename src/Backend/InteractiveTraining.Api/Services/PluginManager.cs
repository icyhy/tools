using InteractiveTraining.Api.Models;

namespace InteractiveTraining.Api.Services;

public interface IPluginManager
{
    IEnumerable<PluginInfo> GetPlugins();
    PluginInfo? GetPlugin(string id);
}

public class PluginManager : IPluginManager
{
    private readonly string _pluginsPath;
    private readonly ILogger<PluginManager> _logger;
    private List<PluginInfo> _cachedPlugins = new();

    public PluginManager(IWebHostEnvironment env, ILogger<PluginManager> logger)
    {
        _pluginsPath = Path.Combine(env.ContentRootPath, "Plugins");
        _logger = logger;
        if (!Directory.Exists(_pluginsPath))
        {
            Directory.CreateDirectory(_pluginsPath);
        }
    }

    public IEnumerable<PluginInfo> GetPlugins()
    {
        RefreshPlugins();
        return _cachedPlugins;
    }

    public PluginInfo? GetPlugin(string id)
    {
        return _cachedPlugins.FirstOrDefault(p => p.Id.Equals(id, StringComparison.OrdinalIgnoreCase));
    }

    private void RefreshPlugins()
    {
        var plugins = new List<PluginInfo>();
        var directories = Directory.GetDirectories(_pluginsPath);

        foreach (var dir in directories)
        {
            var dirName = Path.GetFileName(dir);
            var configPath = Path.Combine(dir, "config.md");
            var readmePath = Path.Combine(dir, "README.md");
            
            // Prefer config.md, then README.md
            var metaFile = File.Exists(configPath) ? configPath : (File.Exists(readmePath) ? readmePath : null);

            var plugin = new PluginInfo
            {
                Id = dirName,
                Path = $"/plugins/{dirName}",
                Name = dirName // Default name
            };

            if (metaFile != null)
            {
                try
                {
                    ParseMetadata(metaFile, plugin);
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "Failed to parse metadata for plugin {PluginId}", dirName);
                }
            }

            plugins.Add(plugin);
        }

        _cachedPlugins = plugins;
    }

    private void ParseMetadata(string filePath, PluginInfo plugin)
    {
        var lines = File.ReadAllLines(filePath);
        bool inFrontMatter = false;

        foreach (var line in lines)
        {
            if (line.Trim() == "---")
            {
                if (inFrontMatter) break; // End of front matter
                inFrontMatter = true;
                continue;
            }

            if (inFrontMatter)
            {
                var parts = line.Split(':', 2);
                if (parts.Length == 2)
                {
                    var key = parts[0].Trim().ToLowerInvariant();
                    var value = parts[1].Trim();

                    switch (key)
                    {
                        case "name": plugin.Name = value; break;
                        case "description": plugin.Description = value; break;
                        case "icon": plugin.Icon = value; break;
                        case "entrypoint": plugin.EntryPoint = value; break;
                        default: plugin.Metadata[key] = value; break;
                    }
                }
            }
        }
    }
}
