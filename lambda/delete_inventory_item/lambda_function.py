import json
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from decimal import Decimal

def lambda_handler(event, context):
    # Initialize DynamoDB client
    dynamo_client = boto3.client('dynamodb')
    table_name = 'Inventory'

    # DynamoDB setup
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table("Inventory")

    # Function to convert Decimal to int/float
    def convert_decimals(obj):
        if isinstance(obj, list):
            return [convert_decimals(i) for i in obj]
        elif isinstance(obj, dict):
            return {k: convert_decimals(v) for k, v in obj.items()}
        elif isinstance(obj, Decimal):  
            return int(obj) if obj % 1 == 0 else float(obj)  # Convert to int if whole number, else float
        return obj

    # Extract the '_id' from the path parameters
    if 'pathParameters' not in event or 'id' not in event['pathParameters']:
        return {
            'statusCode': 400,
            'body': json.dumps("Missing 'id' path parameter")
        }

    id_value = event['pathParameters']['id']

    # Get the item from the table
    try:
        response = table.query(
            KeyConditionExpression=Key("id").eq(id_value)
        )
        items = response.get('Items', [])

        items = convert_decimals(items)

        if not items:
            return {
                'statusCode': 404,
                'body': json.dumps('Item not found')
            }

        location_id = items[0]['location_id']
        
        dynamo_client.delete_item(TableName=table_name, Key= {'id': {'S': id_value}, 
        'location_id': {'N': str(location_id)}})
        return {
            'statusCode': 200,
            'body': json.dumps(f"Item with ID {id_value} deleted successfully.")
        }

    except ClientError as e:
        print(f"Failed to query items: {e.response['Error']['Message']}")
        return {
            'statusCode': 500,
            'body': json.dumps("Failed to query items")
        }

    except Exception as e:
        print(e)
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error deleting item: {str(e)}")
        }