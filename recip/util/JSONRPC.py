METHOD_OBJECT_KEYS = ['jsonrpc', 'method', 'params', 'id']
RESULT_OBJECT_KEYS = ['jsonrpc', 'result', 'id']
ERROR_OBJECT_KEYS = ['jsonrpc', 'error', 'id']
VERSION = '2.0'

def validate(payload):
    pass
    
def createMethodObject(method, params, _id):
    return {
        'jsonrpc': VERSION, 
        'method': method, 
        'params': params, 
        'id': _id
    }

def createResultObject(result, _id):
    return {
        'jsonrpc': VERSION, 
        'result': result, 
        'id': _id
    }

def createErrorObject(code, message, data, _id):
    return {
        'jsonrpc': VERSION, 
        'error': {
            'code': code, 
            'message': message,
            'data': data
        }, 
        'id': _id
    }
