# 24-7-AI-Chatbot-for-general-FAQs
Retail businesses often struggle to meet customer expectations for round-the-clock support. traditional customer service channels require significant manpower, making it difficult to respond to common inquiries outside business hours. Our Software solution tries to bridge this gap.

# 1. DynamoDB-Setup-for-FAQ-Chatbot

Prerequisites:
AWS Account with appropriate permissions
Access to AWS Console

Step 1: Create DynamoDB Table
1. Navigate to DynamoDB Console
    -Go to AWS Console
    -Search for "DynamoDB"
    -Click "Create table"

2. Table Configuration
    -Table name: ChatbotFAQ
    -Partition key: id (String)
    -Keep all other settings as default
    -Click "Create table"

Step 2: Populate FAQ Data-Using AWS Console 
1. Access Your Table
  -Go to DynamoDB Console
  -Click on your "ChatbotFAQ" table
  -Click "Explore table items"
   
2. Add FAQ Items
  -Click "Create item"
  -Switch to "JSON view" (toggle at top)
  -Copy and paste each JSON item from repository DynamoDB/ChatbotFAQ.json
  -Click "Create item"
  -Repeat for all 20 items
      
Sample FAQ Data:
For the complete FAQ data with all 12 items, see the file DynamoDB/ChatbotFAQ.json in this repository.
Each FAQ item follows those JSON format.

Notes:
-Table uses on-demand billing mode (pay per request)
-No secondary indexes required for basic FAQ functionality
-Items can be updated or added through the AWS Console or programmatically
-Consider adding more FAQ items based on common customer inquiries

Troubleshooting:
-Permission Issues: Ensure your AWS user/role has DynamoDB read/write permissions
-Table Not Found: Verify you're in the correct AWS region
-Data Loading Issues: Check JSON formatting when adding items manually






































