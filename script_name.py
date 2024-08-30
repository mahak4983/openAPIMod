import yaml
from collections import OrderedDict
import re

def to_camel_case(snake_str):
    """Convert a snake_case string to CamelCase."""
    components = snake_str.split('_')
    return ''.join(x.capitalize() for x in components)

def to_kebab_case(camel_str):
    """Convert a CamelCase string to kebab-case."""
    return re.sub(r'(?<!^)(?=[A-Z])', '-', camel_str).lower()

def get_payload_name(operation_id, type_prefix, payload_suffix="Payload"):
    """
    Generate a camel-cased payload name based on the operation ID and type prefix (Request/Response).
    Returns both 'RequestPayload'/'ResponsePayload' and 'Request'/'Response'.
    """
    if not operation_id:
        return None, None
    # Capitalize each word for camel casing (e.g., activateEbill -> ActivateEbill)
    entity = ''.join(word.capitalize() for word in re.split(r'_|(?=[A-Z])', operation_id))
    
    # Create names for both 'RequestPayload'/'ResponsePayload' and 'Request'/'Response'
    payload_name = f"{entity}{type_prefix}{payload_suffix}"
    general_name = f"{entity}{type_prefix}"
    return general_name, payload_name

def migrate_openapi_spec(old_spec_path, new_spec_path):
    # Load the old OpenAPI YAML file
    with open(old_spec_path, 'r') as file:
        old_spec = yaml.safe_load(file)

    # Ensure components and schemas sections exist
    old_spec.setdefault('components', {}).setdefault('schemas', {})

    # Modify the paths to adjust request and response schemas and convert IDs to kebab-case
    new_paths = {}
    for path, methods in old_spec['paths'].items():
        # Convert path parameters (e.g., /v1/payees/{payeeId}) to kebab-case (e.g., /v1/payees/{payee-id})
        kebab_path = re.sub(r'{(\w+?)}', lambda m: f"{{{to_kebab_case(m.group(1))}}}", path)
        new_methods = {}

        for method, details in methods.items():
            operation_id = details.get('operationId', '')

            # Generate new payload names for request and response
            request_name, request_payload_name = get_payload_name(operation_id, 'Request')
            response_name, response_payload_name = get_payload_name(operation_id, 'Response')

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
                    # Remove the 'examples' property if it exists
                    response_content = response_details['content']['application/json']
                    if 'examples' in response_content:
                        del response_content['examples']

                    old_response_schema = response_content['schema']
                    
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

            new_methods[method] = details
        new_paths[kebab_path] = new_methods

    old_spec['paths'] = new_paths

    # Reorder the keys to move 'components' to the end
    reordered_spec = OrderedDict()
    for key in old_spec:
        if key != 'components':
            reordered_spec[key] = old_spec[key]
    reordered_spec['components'] = old_spec['components']

    # Save the modified OpenAPI YAML file
    with open(new_spec_path, 'w') as file:
        yaml.dump(reordered_spec, file)

    print(f"New OpenAPI spec saved to {new_spec_path}")

# Usage
if __name__ == "__main__":
    migrate_openapi_spec('C:\\Users\\user\\Desktop\\proj\\zisionx\\backend\\old.yaml', 'new_openapi.yaml')
