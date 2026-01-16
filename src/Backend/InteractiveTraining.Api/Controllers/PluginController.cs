using InteractiveTraining.Api.Models;
using InteractiveTraining.Api.Services;
using Microsoft.AspNetCore.Mvc;

namespace InteractiveTraining.Api.Controllers;

[ApiController]
[Route("api/[controller]")]
public class PluginController : ControllerBase
{
    private readonly IPluginManager _pluginManager;

    public PluginController(IPluginManager pluginManager)
    {
        _pluginManager = pluginManager;
    }

    [HttpGet]
    public IEnumerable<PluginInfo> Get()
    {
        return _pluginManager.GetPlugins();
    }

    [HttpGet("{id}")]
    public IActionResult Get(string id)
    {
        var plugin = _pluginManager.GetPlugin(id);
        if (plugin == null)
            return NotFound();
        return Ok(plugin);
    }
}
