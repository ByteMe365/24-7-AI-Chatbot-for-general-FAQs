# 24-7-AI-Chatbot-for-general-FAQs
Retail businesses often struggle to meet customer expectations for round-the-clock support. traditional customer service channels require significant manpower, making it difficult to respond to common inquiries outside business hours. Our Software solution tries to bridge this gap.

# 1. How-the-DynamoDB-Based-FAQ-Chatbot-System-Works
Architecture Overview:
User Question → Lambda Function → DynamoDB → Search FAQs → Return Answer

Core Components:
DynamoDB Table (ChatbotFAQ):
-Stores FAQ items as JSON documents
-Each item has: id, question, answer, category
-Acts as your knowledge base
-Supports fast scanning and filtering

Lambda Function (ChatbotFAQSearch):
-Receives user input (question text)
-Connects to DynamoDB using boto3
-Performs keyword matching against stored FAQ questions
-Returns the best matching answer
-Handles errors gracefully with fallback messages

Search Logic:
-Takes user input and converts to lowercase
-Scans all FAQ items in DynamoDB
-Checks if any words from user input appear in stored questions
-Returns the first match found
-Falls back to "contact customer service" if no match

Integration Options:
-Function URL: Direct HTTP endpoint to Lambda (simple)
-API Gateway: RESTful API wrapper around Lambda (moderate complexity)

Data Flow:
-User asks "store hours"
-Lambda receives {"inputTranscript": "store hours"}
-Lambda scans DynamoDB for questions containing "store" or "hours"
-Finds match: "What are your store hours?"
-Returns corresponding answer: "Monday-Saturday 9AM-9PM..."

Benefits:
-Serverless (scales automatically)
-Fast response times
-Easy to update FAQ content
-Cost-effective for moderate usage
-No complex NLP training required

The system works through simple keyword matching rather than sophisticated AI, making it reliable and predictable for common FAQ scenarios.

# 2. Lambda-Function-ChatbotFAQSearch
Overview
The ChatbotFAQSearch Lambda function serves as the core intelligence of the FAQ chatbot system. It processes user questions, searches the DynamoDB knowledge base, and returns appropriate answers.

Function Details:
-Runtime: Python 3.13 (or any latest one)
-Handler: lambda_function.lambda_handler
-Memory: 128 MB (adjustable based on needs)
-Timeout: 30 seconds
-Architecture: x86_64

How It Works?
Input Processing:
The function accepts multiple input formats:
-HTTP API format: {"body": "{\"message\": \"user question\"}"}
-Function URL format: {"inputTranscript": "user question"}
-Direct invocation: {"inputTranscript": "user question"}

Search Algorithm
1. Normalize Input: Converts user input to lowercase for case-insensitive matching
2. DynamoDB Scan: Retrieves all FAQ items from the ChatbotFAQ table
3. Keyword Matching:
    -Splits user input into individual words
    -Checks if any word appears in stored FAQ questions
    -Returns the first matching FAQ item
4. Response Generation: Formats the answer for the calling service

Search logic example:
```
User Input: "store hours"
    Split Words: ["store", "hours"]
    Search Process:
    -Check FAQ 1: "What are your store hours?" → Contains "store" 
    -Match found! Return corresponding answer
```


Response Handling

Successful match:
``` json
{
  "statusCode": 200,
  "headers": {"Content-Type": "application/json"},
  "body": "{\"reply\": \"Our stores are open Monday-Saturday 9AM-9PM, Sunday 10AM-7PM\"}"
}
```

No match found:
```json
{
  "statusCode": 200,
  "headers": {"Content-Type": "application/json"},
  "body": "{\"reply\": \"I'm sorry, I couldn't find an answer to your question. Please contact customer service for assistance.\"}"
}
```

Error handling:
```json
{
  "statusCode": 500,
  "headers": {"Content-Type": "application/json"},
  "body": "{\"reply\": \"Sorry, I'm having technical difficulties. Please try again later.\"}"
}
```

Required Permissions

The Lambda execution role needs the following IAM permissions:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:Scan",
        "dynamodb:GetItem"
      ],
      "Resource": "arn:aws:dynamodb:REGION:ACCOUNT:table/ChatbotFAQ"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

Environment Variables

No environment variables required. The function uses hardcoded table name ChatbotFAQ.

Integration Options

1. Lambda Function URL
   
    -Direct HTTP endpoint for web applications
   
    -Input: JSON body with inputTranscript field
   
    -Output: Simple JSON response with reply field

2. API Gateway HTTP API
   
    -RESTful API wrapper around Lambda function
   
    -Input: JSON body with message field
   
    -Output: Structured HTTP response

3. Direct Invocation
   
    -For testing and development
   
    -Input: Custom event object
   
    -Output: Structured response

Performance Characteristics

- Cold Start: ~300-500ms (first invocation)

- Warm Execution: ~50-100ms (subsequent calls)

- DynamoDB Scan: ~100-200ms (depends on table size)

- Memory Usage: ~60-80MB typical


Monitoring and Logging


The function includes comprehensive logging:

  - User input received

  - DynamoDB scan result
  
  - Match found/not found
  
  - Error conditions woth stack traces

CloudWatch Metrics to Monitor:

  - Invocation count
  
  - Duration
  
  - Error rate
  
  - Throttles


Testing

Test event format:
```json
{
  "inputTranscript": "store hours"
}
```


Expected Response

  The function should return a properly formatted answer from the DynamoDB FAQ database


Limitations:
  - Simple Keyword Matching: Does not use NLP or sematic
  - Sequential Search: Checks FAQs in order, returns first match
  - Case Sensitivity: Input converted to lowercase for matching
  - Exact Word Matching: Requires exact word matches, no fuzzy logic

Future Enhancements:
  - Implement fuzzy string matching for better question recognition
  - Add caching layer to reduce DynamoDB calls
  - Support for synonyms and alternative phrasings
  - Analytics tracking for popular questions
  - Multi-language support


Troubleshooting

Common Issues:
  - Permission Denied: Check IAM role has DynamoDB read access
  - Table Not Found: Verify DynamoDB table exists and is named correctly
  - No Matches: Check if FAQ questions contain keywords from user input
  - Timeout: Increase Lambda timeout if DynamoDB is slow


# 3. API-Gateway

This project uses Amazon API Gateway as the HTTPS entry point for the Telegram chatbot.

Purpose:

API Gateway provides a secure, public HTTPS endpoint that Telegram can call (via a webhook).
When a user sends a message to the bot, Telegram immediately sends an HTTP POST request to this endpoint.

Flow:
1. Telegram User → Telegram Server: A user sends a message to the bot.
2. Telegram Server → API Gateway: Telegram forwards the message as a JSON payload to the API Gateway route (for example, POST /telegram).
3. API Gateway → AWS Lambda: API Gateway passes the request to the associated Lambda function using a Lambda-proxy integration.
4. Lambda → DynamoDB → Telegram: The Lambda function processes the text, looks up or generates the answer (using DynamoDB and any extra logic like time-aware store hours), and replies to the user through the Telegram sendMessage API.

Why API Gateway is important
  - Provides a public HTTPS URL with SSL/TLS so Telegram can reach the bot without extra certificates.
  - Handles routing and authorization (you can attach IAM authorizers, secret tokens, or throttling if needed).
  - Supports logging and monitoring of requests through Amazon CloudWatch.

In short, API Gateway acts as the front door of the chatbot, safely exposing the Lambda function to Telegram and other clients (like Postman or curl) without exposing internal AWS resources directly.

Key Functions:
  - Single Endpoint: Provides a URL (e.g. https://<api-id>.execute-api.us-east-1.amazonaws.com/faq) that external clients (Telegram bot, Postman tests, web or mobile apps) can call.
  - Routing: Forwards all POST /faq requests to our Lambda function chatbotFAQsearch.
  - Request/Response Handling: Accepts JSON requests and passes them to Lambda as an event; sends Lambda’s JSON reply back to the client.
  - Security & Scaling: Supports IAM roles, API keys, throttling, and monitoring (CloudWatch) to secure and scale the endpoint.
  - Integration: Can connect to multiple consumers (Telegram webhook, future front-end apps) without changing backend code.

```
User (Telegram / Web)  →  API Gateway  →  Lambda (chatbotFAQsearch)  →  DynamoDB (ChatbotFAQ table)
```

Example Route:

  - Method: POST
  - Resource Post: /faq
  - Integration Target: chatbotFAQsearch (Lambda)


Sample Request:
```
curl -X POST "https://<api-id>.execute-api.us-east-1.amazonaws.com/faq" \
     -H "Content-Type: application/json" \
     -d '{"message":"What are your store hours?"}'
```













