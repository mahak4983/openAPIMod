

import yaml

def get_payload_name(operation_id, type_prefix):
    """Generate a payload name based on the operation ID and type prefix (Request/Response)."""
    if not operation_id:
        return None
    entity = operation_id.capitalize()  # Capitalize the operation ID to use in payload names
    return f"{entity}{type_prefix}Payload"

def migrate_openapi_spec(old_spec_path, new_spec_path):
    # Load the old OpenAPI YAML file
    with open(old_spec_path, 'r') as file:
        old_spec = yaml.safe_load(file)

    # Ensure components and schemas sections exist
    old_spec.setdefault('components', {}).setdefault('schemas', {})

    # Modify the paths to adjust request and response schemas
    for path, methods in old_spec['paths'].items():
        for method, details in methods.items():
            operation_id = details.get('operationId', '')

            # Generate new payload names for request and response
            request_payload_name = get_payload_name(operation_id, 'Request')
            response_payload_name = get_payload_name(operation_id, 'Response')

            # Modify the request body schema
            if 'requestBody' in details:
                request_body = details['requestBody']
                if 'content' in request_body and 'application/json' in request_body['content']:
                    old_request_schema = request_body['content']['application/json']['schema']
                    
                    # Create new request schema structure with nested 'attribute'
                    new_request_schema = {
                        'type': 'object',
                        'required': ['data'],
                        'properties': {
                            'data': {
                                'type': 'object',
                                'properties': {
                                    'attribute': old_request_schema  # Insert old schema under 'attribute'
                                }
                            }
                        }
                    }

                    # Add the new request payload schema to components
                    old_spec['components']['schemas'][request_payload_name] = new_request_schema
                    
                    # Update the request body to reference the new request payload
                    request_body['content']['application/json']['schema'] = {
                        '$ref': f'#/components/schemas/{request_payload_name}'
                    }

            # Modify the response schema for the '200' success case
            if response_payload_name and 'responses' in details and '200' in details['responses']:
                response_details = details['responses']['200']
                if 'content' in response_details and 'application/json' in response_details['content']:
                    old_response_schema = response_details['content']['application/json']['schema']
                    
                    # Create new response schema structure with nested 'attribute'
                    new_response_schema = {
                        'type': 'object',
                        'required': ['data'],
                        'properties': {
                            'links': {
                                '$ref': '../../common/shared/v1/shared_defs-yam#/components/schemas/Links'
                            },
                            'data': {
                                'type': 'object',
                                'properties': {
                                    'attribute': old_response_schema  # Insert old schema under 'attribute'
                                }
                            }
                        }
                    }

                    # Add the new response payload schema to components
                    old_spec['components']['schemas'][response_payload_name] = new_response_schema
                    
                    # Update the response to reference the new response payload
                    response_details['content']['application/json']['schema'] = {
                        '$ref': f'#/components/schemas/{response_payload_name}'
                    }

    # Save the modified OpenAPI YAML file
    with open(new_spec_path, 'w') as file:
        yaml.dump(old_spec, file)

    print(f"New OpenAPI spec saved to {new_spec_path}")

# Usage
if __name__ == "__main__":
    migrate_openapi_spec('C:\\Users\\user\\Desktop\\proj\\zisionx\\backend\\old.yaml', 'new_openapi.yaml')

