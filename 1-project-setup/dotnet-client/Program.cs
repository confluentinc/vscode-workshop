using System;
using System.IO;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using DotNetEnv;

namespace DotnetClient
{
    class Program
    {
        static async Task Main(string[] args)
        {
            if (args.Length == 0)
            {
                Console.WriteLine("❌ Please specify 'Producer' or 'Consumer'");
                return;
            }

            try
            {
                Env.Load();
                
                // Configure the application
                var host = Host.CreateDefaultBuilder(args)
                    .ConfigureServices((context, services) =>
                    {
                        // Create configuration from .env variables
                        var envVars = new Dictionary<string, string?>
                        {
                            { "Kafka:Topic", Environment.GetEnvironmentVariable("CC_TOPIC") ?? "transactions" },
                            { "Kafka:BootstrapServers", Environment.GetEnvironmentVariable("CC_BOOTSTRAP_SERVER") ?? "localhost:9092" },
                        };

                        var configuration = new ConfigurationBuilder()
                            .SetBasePath(Directory.GetCurrentDirectory())
                            .AddInMemoryCollection(envVars)
                            .AddEnvironmentVariables()
                            .Build();

                        services.AddSingleton<IConfiguration>(configuration);
                        services.AddSingleton<Producer>();
                        services.AddSingleton<Consumer>();
                    })
                    .ConfigureLogging(logging => 
                    {
                        logging.ClearProviders();
                        logging.AddConsole();
                    })
                    .Build();

                var serviceProvider = host.Services;
                string mode = args[0].ToLowerInvariant();
                var logger = serviceProvider.GetRequiredService<ILogger<Program>>();

                switch (mode)
                {
                    case "producer":
                        var producer = serviceProvider.GetRequiredService<Producer>();
                        await producer.ProduceRandomMessages(10);
                        break;
                    
                    case "consumer":
                        var consumer = serviceProvider.GetRequiredService<Consumer>();
                        await consumer.Consume();
                        break;
                    
                    default:
                        logger.LogError("Invalid argument. Use 'Producer' or 'Consumer'");
                        break;
                }
            }
            catch (Exception ex)
            {
                var loggerFactory = LoggerFactory.Create(builder => builder.AddConsole());
                var logger = loggerFactory.CreateLogger<Program>();
                logger.LogError(ex, "Application error: {Message}", ex.Message);
                if (ex.InnerException != null)
                {
                    logger.LogError("Inner exception: {Message}", ex.InnerException.Message);
                    logger.LogDebug("Stack trace: {StackTrace}", ex.StackTrace);
                }
            }
        }
    }
}
