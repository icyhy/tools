using Microsoft.AspNetCore.SignalR;
using System.Collections.Concurrent;

namespace InteractiveTraining.Api.Hubs;

public class GameState
{
    public string? PluginId { get; set; }
    public string Phase { get; set; } = "idle";
    public int MissingNumber { get; set; }
    public DateTime StartTime { get; set; }
    public ConcurrentDictionary<string, AnswerSubmission> Submissions { get; set; } = new();
}

public class AnswerSubmission
{
    public string UserId { get; set; } = string.Empty;
    public string UserName { get; set; } = string.Empty;
    public int Answer { get; set; }
    public DateTime SubmitTime { get; set; }
    public bool IsCorrect { get; set; }
}

public class InteractionHub : Hub
{
    private static int _connectedUsers = 0;
    private static ConcurrentDictionary<string, string> _userNames = new ConcurrentDictionary<string, string>();
    private static GameState _currentGame = new GameState();
    private readonly ILogger<InteractionHub> _logger;

    public InteractionHub(ILogger<InteractionHub> logger)
    {
        _logger = logger;
    }

    public override async Task OnConnectedAsync()
    {
        _logger.LogInformation("User connected: {ConnectionId}", Context.ConnectionId);
        await base.OnConnectedAsync();
    }

    public override async Task OnDisconnectedAsync(Exception? exception)
    {
        if (_userNames.TryRemove(Context.ConnectionId, out _))
        {
            Interlocked.Decrement(ref _connectedUsers);
            await Clients.All.SendAsync("UserCountUpdate", _connectedUsers);
            _logger.LogInformation("User disconnected: {ConnectionId}, Total: {Count}", Context.ConnectionId, _connectedUsers);
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
            _logger.LogInformation("User joined: {UserName} ({ConnectionId})", userName, Context.ConnectionId);
        }
    }

    public async Task JoinHost(string password)
    {
        if (password == "admin123") // Simple hardcoded password for now
        {
            await Groups.AddToGroupAsync(Context.ConnectionId, "Host");
            await Clients.Caller.SendAsync("HostAuthSuccess");
            _logger.LogInformation("Host authenticated: {ConnectionId}", Context.ConnectionId);
        }
        else
        {
            await Clients.Caller.SendAsync("HostAuthFailed");
            _logger.LogWarning("Host authentication failed: {ConnectionId}", Context.ConnectionId);
        }
    }

    public async Task StartInteraction(string pluginId, object? config = null)
    {
        _logger.LogInformation("Starting interaction: {PluginId}", pluginId);
        
        // Initialize game state
        _currentGame = new GameState
        {
            PluginId = pluginId,
            Phase = "running",
            StartTime = DateTime.UtcNow,
            MissingNumber = new Random().Next(1, 101) // Random missing number 1-100
        };

        // Broadcast to all clients
        await Clients.All.SendAsync("SwitchPlugin", pluginId, new { MissingNumber = _currentGame.MissingNumber });
        
        // Send game config to host
        await Clients.Group("Host").SendAsync("GameStarted", new 
        { 
            PluginId = pluginId, 
            MissingNumber = _currentGame.MissingNumber,
            StartTime = _currentGame.StartTime
        });
    }

    public async Task SubmitAnswer(string pluginId, int answer)
    {
        if (_currentGame.PluginId != pluginId || _currentGame.Phase != "running")
        {
            _logger.LogWarning("Invalid submission attempt for {PluginId} in phase {Phase}", pluginId, _currentGame.Phase);
            return;
        }

        var userName = _userNames.GetValueOrDefault(Context.ConnectionId, "Unknown");
        var isCorrect = answer == _currentGame.MissingNumber;

        var submission = new AnswerSubmission
        {
            UserId = Context.ConnectionId,
            UserName = userName,
            Answer = answer,
            SubmitTime = DateTime.UtcNow,
            IsCorrect = isCorrect
        };

        _currentGame.Submissions.AddOrUpdate(Context.ConnectionId, submission, (key, old) => submission);

        _logger.LogInformation("Answer submitted: {UserName} -> {Answer} (Correct: {IsCorrect})", userName, answer, isCorrect);

        // Notify host of new submission
        var stats = GetCurrentStats();
        await Clients.Group("Host").SendAsync("SubmissionReceived", new 
        { 
            UserId = Context.ConnectionId,
            UserName = userName,
            Answer = answer,
            Stats = stats
        });

        // Update all clients with current stats
        await Clients.All.SendAsync("StatsUpdate", stats);

        // Confirm to participant
        await Clients.Caller.SendAsync("SubmissionConfirmed", new { IsCorrect = isCorrect });
    }

    public Task<Dictionary<string, object>> GetGameStatus()
    {
        return Task.FromResult(GetCurrentStats());
    }

    public async Task EndGame()
    {
        if (_currentGame.Phase != "running")
        {
            return;
        }

        _logger.LogInformation("Ending game: {PluginId}", _currentGame.PluginId);
        _currentGame.Phase = "finished";

        var stats = GetCurrentStats();
        var results = new
        {
            MissingNumber = _currentGame.MissingNumber,
            Stats = stats,
            Submissions = _currentGame.Submissions.Values.OrderByDescending(s => s.IsCorrect).ThenBy(s => s.SubmitTime).Take(10)
        };

        // Broadcast results to all clients
        await Clients.All.SendAsync("GameEnded", results);
        _logger.LogInformation("Game ended with {TotalSubmissions} submissions, {CorrectCount} correct", 
            stats["totalSubmissions"], stats["correctCount"]);
    }

    public async Task NextPhase(string phase)
    {
        _logger.LogInformation("Moving to next phase: {Phase}", phase);
        
        // Generate new missing number for new phase
        _currentGame.MissingNumber = new Random().Next(1, 101);
        _currentGame.Submissions.Clear();
        _currentGame.StartTime = DateTime.UtcNow;

        await Clients.All.SendAsync("PhaseChanged", new 
        { 
            Phase = phase, 
            MissingNumber = _currentGame.MissingNumber 
        });
    }

    private Dictionary<string, object> GetCurrentStats()
    {
        var totalSubmissions = _currentGame.Submissions.Count;
        var correctCount = _currentGame.Submissions.Values.Count(s => s.IsCorrect);
        var accuracy = totalSubmissions > 0 ? (correctCount * 100.0 / totalSubmissions) : 0;

        return new Dictionary<string, object>
        {
            { "pluginId", _currentGame.PluginId ?? "" },
            { "phase", _currentGame.Phase },
            { "totalUsers", _connectedUsers },
            { "totalSubmissions", totalSubmissions },
            { "correctCount", correctCount },
            { "accuracy", Math.Round(accuracy, 1) },
            { "missingNumber", _currentGame.Phase == "finished" ? _currentGame.MissingNumber : (int?)null }
        };
    }
}
