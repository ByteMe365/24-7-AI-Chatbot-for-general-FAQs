import json
import boto3
from datetime import datetime

# Set up DynamoDB
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Orders')

def get_slot_value(slots, slot_name):
    slot = slots.get(slot_name)
    if slot and isinstance(slot, dict):
        value = slot.get('value')
        if value and isinstance(value, dict):
            return value.get('interpretedValue')
    return None

def Validate(slots):
    order_id = get_slot_value(slots, 'OrderID')

    if not order_id:
        return {
            'isValid': False,
            'violatedSlot': 'OrderID',
        }

    return {'isValid': True}


def lambda_handler(event, context):
    print("Event:", json.dumps(event, indent=2))  # Log full event to CloudWatch

    invocation_source = event['invocationSource']
    intent = event['sessionState']['intent']['name']
    slots = event['sessionState']['intent']['slots']

    # ========== TrackOrder intent ==========
    if intent == "TrackOrder":
        validation_result = Validate(event['sessionState']['intent']['slots'])

        if invocation_source == 'DialogCodeHook':
            if not validation_result['isValid']:
                return {
                    "sessionState": {
                        "dialogAction": {
                            "slotToElicit": validation_result['violatedSlot'],
                            "type": "ElicitSlot"
                        },
                        "intent": {
                            "name": intent,
                            "slots": slots
                        }
                    }
                }
            else:
                return {
                    "sessionState": {
                        "dialogAction": {"type": "Delegate"},
                        "intent": {
                            "name": intent,
                            "slots": slots
                        }
                    }
                }

        elif invocation_source == 'FulfillmentCodeHook':
            # FIXED: Use get_slot_value function instead of manual extraction
            order_id = get_slot_value(slots, 'OrderID')
            
            if order_id:
                order_id = order_id.upper().strip()
            
            print(f"Looking up OrderID: '{order_id}' in DynamoDB table: {table.table_name}")
            
            try:
                response = table.get_item(Key={'OrderID': order_id})
                print(f"DynamoDB response: {response}")

                if 'Item' in response:
                    order = response['Item']
                    print(f"Found order: {order}")
                    message = (
                        f"Found your order! Your {order['Item']} is currently "
                        f"{order['OrderStatus']}. Estimated delivery: {order['EstimatedTime']}.\n"
                        f"Let me know if you need anything else 😁"
                    )
                else:
                    print(f"No order found with ID: '{order_id}'")
                    message = f"Sorry, I couldn't find an order with ID '{order_id}'. Please check the order ID and try again."

            except Exception as e:
                print(f"DynamoDB error: {str(e)}")
                message = f"Error checking order: {str(e)}"

            return {
                "sessionState": {
                    "dialogAction": {"type": "Close"},
                    "intent": {
                        "name": intent,
                        "slots": slots,
                        "state": "Fulfilled"
                    }
                },
                "messages": [
                    {
                        "contentType": "PlainText",
                        "content": message
                    }
                ]
            }

    # ========== Fallback intent ==========
    elif intent == "FallbackIntent":
        session_attributes = event.get("sessionState", {}).get("sessionAttributes", {})
        user_input = event.get("inputTranscript", "").lower()

        # Case 1: User said "yes" after fallback
        if session_attributes.get("pendingAction") == "TrackOrder" and user_input in ["yes", "yeah", "yep", "sure", "ok"]:
            session_attributes.pop("pendingAction", None)

            return {
                "sessionState": {
                    "dialogAction": {
                        "type": "ElicitSlot",
                        "slotToElicit": "OrderID"
                    },
                    "intent": {
                        "name": "TrackOrder",
                        "slots": {"OrderID": None},
                        "state": "InProgress"
                    },
                    "sessionAttributes": session_attributes
                },
                "messages": [
                    {
                        "contentType": "PlainText",
                        "content": "Okay, let's check your order. What's your Order ID?"
                    }
                ]
            }

        # Case 2: User said "no"
        elif session_attributes.get("pendingAction") == "TrackOrder" and user_input in ["no", "nah", "nope", "not now"]:
            session_attributes.pop("pendingAction", None)

            return {
                "sessionState": {
                    "dialogAction": {"type": "Close"},
                    "intent": {
                        "name": "TrackOrder",
                        "slots": {"OrderID": None},
                        "state": "Fulfilled"
                    },
                    "sessionAttributes": session_attributes
                },
                "messages": [
                    {
                        "contentType": "PlainText",
                        "content": "No problem! Let me know if you need help with anything else."
                    }
                ]
            }

        # Case 3: Normal fallback
        else:
            session_attributes["pendingAction"] = "TrackOrder"

            return {
                "sessionState": {
                    "dialogAction": {"type": "Close"},
                    "intent": {
                        "name": intent,
                        "slots": slots,
                        "state": "Fulfilled"
                    },
                    "sessionAttributes": session_attributes
                },
                "messages": [
                    {
                        "contentType": "PlainText",
                        "content": "Sorry, I didn't get that. Do you want to check your order?"
                    }
                ]
            }