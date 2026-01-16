using InteractiveTraining.Api.Hubs;
using InteractiveTraining.Api.Services;
using Microsoft.Extensions.FileProviders;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
builder.Services.AddControllers();
builder.Services.AddSignalR();
builder.Services.AddAuthorization();
builder.Services.AddSingleton<IPluginManager, PluginManager>();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

// Add CORS
builder.Services.AddCors(options =>
{
    options.AddDefaultPolicy(policy =>
    {
        policy.WithOrigins("http://localhost:5173", "http://127.0.0.1:5173") // Vite dev server
              .AllowAnyHeader()
              .AllowAnyMethod()
              .AllowCredentials();
    });
});

var app = builder.Build();

// Configure the HTTP request pipeline.
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseHttpsRedirection();
app.UseCors();

app.UseAuthorization();

// Serve static files from Plugins directory
var pluginsPath = Path.Combine(app.Environment.ContentRootPath, "Plugins");
if (!Directory.Exists(pluginsPath))
{
    Directory.CreateDirectory(pluginsPath);
}

app.UseStaticFiles(new StaticFileOptions
{
    FileProvider = new PhysicalFileProvider(pluginsPath),
    RequestPath = "/plugins",
    ServeUnknownFileTypes = true // Allow serving .vue files
});

app.MapControllers();
app.MapHub<InteractionHub>("/hub");

app.Run();
