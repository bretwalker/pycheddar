class NotFound(Exception):
    pass
    
class AuthorizationRequired(Exception):
    pass
    
class Forbidden(Exception):
    pass
    
class UnexpectedResponse(Exception):
    pass
    
class BadRequest(Exception):
    pass
        
class GatewayFailure(Exception):
    pass
    
class GatewayConnectionError(Exception):
    pass
    
class ValidationError(Exception):
    pass