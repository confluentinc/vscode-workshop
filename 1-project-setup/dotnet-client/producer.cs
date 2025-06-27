using System;
using System.Threading.Tasks;
using Bogus;
using Confluent.Kafka;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using System.Text.Json;


namespace DotnetClient
{
    public class Producer
    {
        private readonly IConfiguration _configuration;
        private readonly string _bootstrapServer;
        private readonly bool _isLocal;
        private readonly string? _topic;
        private readonly ILogger<Producer> _logger;

        public Producer(IConfiguration configuration, ILogger<Producer> logger)
        {
            _configuration = configuration;
            _logger = logger;
            _topic = _configuration["Kafka:Topic"];
            _bootstrapServer = _configuration["Kafka:BootstrapServers"] ?? "localhost:9092";

            // Check for local environments
            _isLocal = _bootstrapServer.Contains("localhost") ||
                       _bootstrapServer.Contains("127.0.0.1") ||
                       _bootstrapServer.Contains("kafka:");

        }

        public async Task ProduceRandomMessages(int messageCount)
        {
            if (string.IsNullOrEmpty(_topic))
            {
                _logger.LogWarning("No topic specified");
                return;
            }

            // Configure Kafka producer
            var producerConfig = new ProducerConfig
            {
                BootstrapServers = _bootstrapServer,
                ClientId = Environment.GetEnvironmentVariable("CLIENT_ID") ?? "dotnet-client"
            };

            // Configure security based on environment
            if (_isLocal)
            {
                producerConfig.SecurityProtocol = SecurityProtocol.Plaintext;
                _logger.LogInformation("🐳 Using PLAINTEXT protocol for local broker");
                _logger.LogInformation("🔄 Using topic {Topic} - will be auto created if it doesn't exist", _topic);
            }
            else
            {
                producerConfig.SecurityProtocol = SecurityProtocol.SaslSsl;
                producerConfig.SaslMechanism = SaslMechanism.Plain;
                producerConfig.SaslUsername = Environment.GetEnvironmentVariable("CC_API_KEY");
                producerConfig.SaslPassword = Environment.GetEnvironmentVariable("CC_API_SECRET");
                _logger.LogInformation("☁️ Using SASL_SSL protocol for cloud broker");
            }

            // Verify Kafka setup
            try
            {
                bool exists = await VerifyKafkaSetup(producerConfig, _topic, _isLocal);
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


            // Create Faker to generate fake data
            var faker = new Faker();
            _logger.LogInformation("Producing to topic '{Topic}'...", _topic);

            _logger.LogInformation("Using plain JSON serialization (no Schema Registry)");

            // Create producer with JSON serialization
            using (var producer = new ProducerBuilder<string, string>(producerConfig).Build())
            {
                await ProduceMessagesJson(producer, faker, messageCount);
            }
            
            _logger.LogInformation("✅ Successfully produced {Count} messages to topic {Topic}", messageCount, _topic);
        }

        private async Task ProduceMessagesJson(IProducer<string, string> producer, Faker faker, int messageCount)
        {
            for (int i = 0; i < messageCount; i++)
            {
                // Generate fake transaction data
                string key = Guid.NewGuid().ToString();
                var transaction = CreateFakeTransaction(faker, key);

                try
                {
                    // Serialize transaction to JSON
                    string jsonData = JsonSerializer.Serialize(transaction);

                    var deliveryResult = await producer.ProduceAsync(_topic, new Message<string, string>
                    {
                        Key = key,
                        Value = jsonData
                    });

                    _logger.LogInformation("Produced message {Current}/{Total}: {JsonData}", i + 1, messageCount, jsonData);
                }
                catch (ProduceException<string, string> e)
                {
                    LogProduceError(e);
                }
            }
        }

        private TransactionRecord CreateFakeTransaction(Faker faker, string key)
        {
            return new TransactionRecord
            {
                TransactionId = key,
                AccountNumber = faker.Finance.Iban(),
                Amount = Math.Round(faker.Random.Double(1, 99999), 2),
                Currency = faker.Finance.Currency().Code,
                Timestamp = DateTime.UtcNow.ToString("o"),
                TransactionType = faker.PickRandom(new[] { "deposit", "withdrawal", "transfer", "payment" }),
                Status = faker.PickRandom(new[] { "pending", "completed", "failed" })
            };
        }

        private void LogProduceError(Exception e)
        {
            _logger.LogError(e, "Message failed delivery: {Reason}", (e as KafkaException)?.Error.Reason ?? e.Message);
            if (e.InnerException != null)
            {
                _logger.LogError("Inner Exception: {Message}", e.InnerException.Message);
            }
        }

        private Task<bool> VerifyKafkaSetup(ProducerConfig config, string topic, bool isLocal)
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
