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






































