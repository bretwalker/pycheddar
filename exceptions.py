class MouseTrap(Exception):
    pass

class NotFound(MouseTrap):
    pass
    
class AuthorizationRequired(MouseTrap):
    pass
    
class Forbidden(MouseTrap):
    pass
    
class UnexpectedResponse(MouseTrap):
    pass
    
class BadRequest(MouseTrap):
    pass
        
class GatewayFailure(MouseTrap):
    pass
    
class GatewayConnectionError(MouseTrap):
    pass
    
class ValidationError(MouseTrap):
    pass