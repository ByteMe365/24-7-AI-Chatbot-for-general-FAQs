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
User Input: "store hours"
Split Words: ["store", "hours"]
Search Process:
-Check FAQ 1: "What are your store hours?" → Contains "store" 
-Match found! Return corresponding answer





Response Handling
Successful Match:
json{
  "statusCode": 200,
  "headers": {"Content-Type": "application/json"},
  "body": "{\"reply\": \"Our stores are open Monday-Saturday 9AM-9PM, Sunday 10AM-7PM\"}"
}
No Match Found:
json{
  "statusCode": 200,
  "headers": {"Content-Type": "application/json"},
  "body": "{\"reply\": \"I'm sorry, I couldn't find an answer to your question. Please contact customer service for assistance.\"}"
}
Error Handling:
json{
  "statusCode": 500,
  "headers": {"Content-Type": "application/json"},
  "body": "{\"reply\": \"Sorry, I'm having technical difficulties. Please try again later.\"}"
}
Required Permissions
The Lambda execution role needs the following IAM permissions:
json{
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
Environment Variables
No environment variables required. The function uses hardcoded table name ChatbotFAQ.
Integration Options
1. Lambda Function URL

Direct HTTP endpoint for web applications
Input: JSON body with inputTranscript field
Output: Simple JSON response with reply field

2. API Gateway HTTP API

RESTful API wrapper around Lambda function
Input: JSON body with message field
Output: Structured HTTP response

3. Direct Invocation

For testing and development
Input: Custom event object
Output: Structured response

Performance Characteristics

Cold Start: ~300-500ms (first invocation)
Warm Execution: ~50-100ms (subsequent calls)
DynamoDB Scan: ~100-200ms (depends on table size)
Memory Usage: ~60-80MB typical

Monitoring and Logging
The function includes comprehensive logging:

User input received
DynamoDB scan results
Match found/not found
Error conditions with stack traces

CloudWatch Metrics to Monitor:

Invocation count
Duration
Error rate
Throttles

Testing
Test Event Format
json{
  "inputTranscript": "store hours"
}
Expected Response
The function should return a properly formatted answer from the DynamoDB FAQ database.
Limitations

Simple Keyword Matching: Does not use NLP or semantic search
Sequential Search: Checks FAQs in order, returns first match
Case Sensitivity: Input converted to lowercase for matching
Exact Word Matching: Requires exact word matches, no fuzzy logic

Future Enhancements

Implement fuzzy string matching for better question recognition
Add caching layer to reduce DynamoDB calls
Support for synonyms and alternative phrasings
Analytics tracking for popular questions
Multi-language support

Troubleshooting
Common Issues:

Permission Denied: Check IAM role has DynamoDB read access
Table Not Found: Verify DynamoDB table exists and is named correctly
No Matches: Check if FAQ questions contain keywords from user input
Timeout: Increase Lambda timeout if DynamoDB is slow





































