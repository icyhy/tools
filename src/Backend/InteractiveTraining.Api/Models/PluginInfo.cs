namespace InteractiveTraining.Api.Models;

public class PluginInfo
{
    public string Id { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    public string Icon { get; set; } = string.Empty;
    public string EntryPoint { get; set; } = "index.vue"; // Default entry point
    public string Path { get; set; } = string.Empty;
    public Dictionary<string, object> Metadata { get; set; } = new();
}
