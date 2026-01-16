using Microsoft.AspNetCore.SignalR;
using System.Collections.Concurrent;

namespace InteractiveTraining.Api.Hubs;

public class InteractionHub : Hub
{
    private static int _connectedUsers = 0;
    private static ConcurrentDictionary<string, string> _userNames = new ConcurrentDictionary<string, string>();

    public override async Task OnConnectedAsync()
    {
        await base.OnConnectedAsync();
    }

    public override async Task OnDisconnectedAsync(Exception? exception)
    {
        if (_userNames.TryRemove(Context.ConnectionId, out _))
        {
            Interlocked.Decrement(ref _connectedUsers);
            await Clients.All.SendAsync("UserCountUpdate", _connectedUsers);
        }
        await base.OnDisconnectedAsync(exception);
    }

    public async Task JoinSession(string userName)
    {
        if (_userNames.TryAdd(Context.ConnectionId, userName))
        {
            Interlocked.Increment(ref _connectedUsers);
            await Clients.All.SendAsync("UserJoined", new { Id = Context.ConnectionId, Name = userName });
            await Clients.All.SendAsync("UserCountUpdate", _connectedUsers);
        }
    }

    public async Task JoinHost(string password)
    {
        if (password == "admin123") // Simple hardcoded password for now
        {
            await Groups.AddToGroupAsync(Context.ConnectionId, "Host");
            await Clients.Caller.SendAsync("HostAuthSuccess");
        }
        else
        {
            await Clients.Caller.SendAsync("HostAuthFailed");
        }
    }

    public async Task StartInteraction(string pluginId)
    {
        await Clients.All.SendAsync("SwitchPlugin", pluginId);
    }

    public async Task SubmitAction(string pluginId, object data)
    {
        // Broadcast to Host/Admin
        await Clients.Group("Host").SendAsync("ActionReceived", new { PluginId = pluginId, Data = data, UserId = Context.ConnectionId });
    }
}
