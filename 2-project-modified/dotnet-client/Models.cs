
namespace DotnetClient
{
    public class TransactionRecord
    {
        public required string TransactionId { get; set; }
        public required string AccountNumber { get; set; }
        public double Amount { get; set; }
        public required string Currency { get; set; }
        public required string Timestamp { get; set; }
        public required string TransactionType { get; set; }
        public required string Status { get; set; }
    }
}