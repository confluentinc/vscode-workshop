using System;
using System.Threading;
using System.Threading.Tasks;
using Confluent.Kafka;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using System.Text.Json;


namespace DotnetClient
{
    public class Consumer
    {
        private readonly IConfiguration _configuration;
        private readonly string _bootstrapServer;
        private readonly bool _isLocal;
        private readonly string? _topic;
        private readonly ILogger<Consumer> _logger;
        private readonly CancellationTokenSource _cts;

        public Consumer(IConfiguration configuration, ILogger<Consumer> logger)
        {
            _configuration = configuration;
            _logger = logger;
            _topic = _configuration["Kafka:Topic"];
            _bootstrapServer = _configuration["Kafka:BootstrapServers"] ?? "localhost:9092";

            // Check for local environments
            _isLocal = _bootstrapServer.Contains("localhost") ||
                       _bootstrapServer.Contains("127.0.0.1") ||
                       _bootstrapServer.Contains("kafka:");

            _cts = new CancellationTokenSource();

            // Setup Ctrl+C handler
            Console.CancelKeyPress += (_, e) =>
            {
                e.Cancel = true;
                _cts.Cancel();
            };
        }

        public async Task Consume(int messageLimit = 10)
        {
            if (string.IsNullOrEmpty(_topic))
            {
                _logger.LogWarning("⚠️ No topic specified");
                return;
            }

            // Configure Kafka consumer
            var consumerConfig = new ConsumerConfig
            {
                BootstrapServers = _bootstrapServer,
                GroupId = Environment.GetEnvironmentVariable("GROUP_ID") ?? "dotnet-consumer-group-id",
                AutoOffsetReset = AutoOffsetReset.Earliest,
                ClientId = Environment.GetEnvironmentVariable("CLIENT_ID") ?? "dotnet-client"
            };

            // Configure security based on environment
            if (_isLocal)
            {
                consumerConfig.SecurityProtocol = SecurityProtocol.Plaintext;
                _logger.LogInformation("🐳 Using PLAINTEXT protocol for local broker");
                _logger.LogInformation("🔄 Using topic {Topic} - will be auto created if it doesn't exist", _topic);
            }
            else
            {
                consumerConfig.SecurityProtocol = SecurityProtocol.SaslSsl;
                consumerConfig.SaslMechanism = SaslMechanism.Plain;
                consumerConfig.SaslUsername = Environment.GetEnvironmentVariable("CC_API_KEY");
                consumerConfig.SaslPassword = Environment.GetEnvironmentVariable("CC_API_SECRET");
                _logger.LogInformation("☁️ Using SASL_SSL protocol for cloud broker");
            }

            // Verify Kafka setup before proceeding
            try
            {
                bool exists = await VerifyKafkaSetup(consumerConfig, _topic, _isLocal);
                if (!exists && !_isLocal)
                {
                    _logger.LogError("Topic '{Topic}' does not exist. Please create it first", _topic);
                    return;
                }
                _logger.LogInformation("✅ Connected to Kafka");
            }
            catch (Exception e)
            {
                _logger.LogError(e, "Kafka connection error: {Message}", e.Message);
                return;
            }

            _logger.LogInformation("Using plain JSON deserialization (no Schema Registry)");

            _logger.LogInformation("Listening on topic: '{Topic}'...", _topic);

            try
            {
                using (var consumer = new ConsumerBuilder<string, string>(consumerConfig)
                    .Build())
                {
                    consumer.Subscribe(_topic);
                    // Increased delay to allow for topic auto-creation in local environments
                    if (_isLocal)
                    {
                        await Task.Delay(5000);
                    }

                    int count = 0;

                    while (count < messageLimit && !_cts.Token.IsCancellationRequested)
                    {
                        try
                        {
                            var consumeResult = consumer.Consume(TimeSpan.FromSeconds(1));

                            if (consumeResult == null)
                                continue;

                            count++;
                            try
                            {
                                // Deserialize JSON message
                                var transaction = JsonSerializer.Deserialize<TransactionRecord>(consumeResult.Message.Value);
                                
                                // Format the output as requested
                                string jsonOutput = consumeResult.Message.Value;
                                _logger.LogInformation("Message {Current}/{Total}: {JsonData}", count, messageLimit, jsonOutput);
                            }
                            catch (JsonException ex)
                            {
                                _logger.LogError(ex, "Error deserializing message: {Message}", ex.Message);
                                _logger.LogDebug("Raw message: {RawMessage}", consumeResult.Message.Value);
                            }
                        }
                        catch (ConsumeException e)
                        {
                            _logger.LogError(e, "Error: {Reason}", e.Error.Reason);
                            if (e.InnerException != null)
                            {
                                _logger.LogError("Inner Exception: {Message}", e.InnerException.Message);
                            }
                        }
                        catch (Exception e)
                        {
                            _logger.LogError(e, "❌ Error processing message: {Message}", e.Message);
                            if (e.InnerException != null)
                            {
                                _logger.LogError("❌ Inner Exception: {Message}", e.InnerException.Message);
                            }
                        }
                    }

                    consumer.Close();
                    _logger.LogInformation("✅ Consumed {Count} messages from {Topic}", count, _topic);
                }
            }
            catch (OperationCanceledException)
            {
                _logger.LogInformation("Interrupted by user");
            }
        }

        private Task<bool> VerifyKafkaSetup(ConsumerConfig config, string? topic, bool isLocal)
        {
            if (isLocal || string.IsNullOrEmpty(topic))
            {
                return Task.FromResult(true);
            }

            try
            {
                var adminClientConfig = new AdminClientConfig
                {
                    BootstrapServers = config.BootstrapServers,
                    SecurityProtocol = config.SecurityProtocol,
                    SaslMechanism = config.SaslMechanism,
                    SaslUsername = config.SaslUsername,
                    SaslPassword = config.SaslPassword
                };

                using (var adminClient = new AdminClientBuilder(adminClientConfig).Build())
                {
                    var metadata = adminClient.GetMetadata(TimeSpan.FromSeconds(5));
                    return Task.FromResult(metadata.Topics.Exists(t => t.Topic == topic));
                }
            }
            catch
            {
                return Task.FromResult(false);
            }
        }

    }
}
