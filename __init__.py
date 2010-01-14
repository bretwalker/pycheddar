import copy
import httplib2
import re
from lxml import etree


class CheddarGetter:
    """Class to interact with the CheddarGetter API"""
    
    def __init__(self, username, password, product_code):
        """Create a new object and set the connection attributes"""
        
        # save an HTTP connection object
        self._http = httplib2.Http()
        self._http.add_credentials(username, password)
        
        self._product_code = product_code
    
    
    def get_plans(self):
        """Get all pricing plans in the product"""
        
        # retrieve the plans from CheddarGetter
        try: 
            plans = []
            xml = self.request('/plans/get/')
        
            # make a list of Plan objects and return it
            for plan in xml.iterchildren(tag = 'plan'):
                plans.append(Plan(self, plan))
                
            return plans
            
        except NotFound:
            return []
                
    
    def get_plan(self, code):
        """Get a single pricing plan"""
        
        # retrieve the plan from CheddarGetter
        xml = self.request('/plans/get/', code = code)
        
        # return a plan object
        for plan in xml.iterchildren(tag = 'plan'):
            return Plan(self, plan)
        
    
    def get_customers(self, **kwargs):
        """Get all customers in the CheddarGetter product plan,
        optionally filtered by the provided keyword arguments."""
        
        # retreive the set of customers
        try:
            xml = self.request('/customers/get/', **kwargs)
            for customer in xml.iterchildren('customer'):
                print customer
            
        except NotFound:
            return []
        
    
    def get_customer(self, code):
        """Get a specific customer by the given customer code."""
        return self.request('/customers/get/', code = code)
        

    def new_customer(self, **kwargs):
        """Create a new CheddarGetter customer, and return the Customer object."""
        
        xml = self.request('/customers/new/', **kwargs)
        return xml
    
    def edit_customer(self, **kwargs):
        """Change customer information"""
        return self._process(key="customers", val="edit", values=kwargs)
    
    def delete_customer(self, **kwargs):
        """Delete a customer"""
        return self._process(key="customers", val="delete", values=kwargs, pass_values=False)
    
    def edit_subscription(self, **kwargs):
        """Change subscription information"""
        return self._process(key="customers", val="edit-subscription", values=kwargs)
    
    def cancel_subscription(self, **kwargs):
        """Cancel subscription"""
        return self._process(key="customers", val="cancel", values=kwargs, pass_values=False)
    
    def add_item_quantity(self, **kwargs):
        """Increment a usage item quantity"""
        return self._process(key="customers", val="add-item-quantity", values=kwargs)
    
    def remove_item_quantity(self, **kwargs):
        """Decrement a usage item quantity"""
        return self._process(key="customers", val="remove-item-quantity", values=kwargs)
    
    def set_item_quantity(self, **kwargs):
        """Set a usage item quantity"""
        return self._process(key="customers", val="set-item-quantity", values=kwargs)
    
    def add_charge(self, **kwargs):
        """Add a custom charge (debit) or credit to the current invoice
        A positive 'eachAmount' will result in a debit. If negative, a credit."""
        return self._process(key="customers", val="add-charge", values=kwargs)
    
    
    def request(self, path, code = None, pass_product_code = True, **kwargs):
        """Process an arbitrary request to CheddarGetter.
        
        Ordinarily, you shouldn't have to call this method directly,
        but it's available to send arbitrary requests if needed.
        
        The product code will be appended to the end of the request automatically,
        and does not need to be included"""

        # build the base request URL
        url = 'https://cheddargetter.com/xml/' + path.strip('/')

        # if a code was requested, I may be sent an ID instead; detect this
        # and change the key accordingly
        if code is not None:
            # make sure code is a string
            code = str(code)
            
            # it may be an ID instead; detect this
            if re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', code):
                url += '/id/' + code
            else:
                url += '/code/' + code
                
        # mangle the kwargs to make them match what
        # CheddarGetter expects
        for key in copy.copy(kwargs):
            # move from Python naming conventions to Zend Framework conventions
            # (read: underscores become camel-case)
            if '_' in key:
                old_key = key
                while '_' in key:
                    ix = key.index('_')
                    next = key[ix + 1].upper()
                    key = key[0:ix] + next + key[ix + 2:]

                kwargs[key] = kwargs[old_key]
                del kwargs[old_key]
                
            # CheddarGetter expects some items expected in a "subscription" array-like structure in POST
            subscription_keys = ['planCode', 'ccFirstName', 'ccLastName', 'ccNumber', 'ccExpiration', 'ccCardCode', 'ccZip']
            for i in subscription_keys:
                if i in kwargs:
                    kwargs['subscription[%s]' % i] = kwargs[i]
                    del kwargs[i]
                    
        # add in the product code
        if pass_product_code is True:
            url += '/productCode/' + self._product_code + '/'

        # create the curl command
        request, content = self._http.request(url, method = 'POST', body = kwargs)
        
        # DEBUG: I need to see the XML response that is coming back for testing.
        print >> sys.stderr, content
        
        # parse the XML
        try:
            content = etree.fromstring(content)
        except:
            raise UnexpectedResponse, "The server sent back something that wasn't valid XML."
        
        # raise appropriate exceptions if there is an error
        # of any kind
        if content.tag == 'error':
            status = int(content.get('code'))
            if status == 404:
                raise NotFound, content.text
            elif status == 401:
                raise AuthorizationRequired, content.text
            elif status == 400:
                raise BadRequest, content.text
            elif status == 403:
                raise Forbidden, content.text
            else:
                raise UnexpectedResponse, content.text
            
        # return the processed content from CheddarGetter
        return content
        
        
class CheddarObject(object):
    """A object that can represent most objects that come down
    from CheddarGetter."""
    
    def __init__(self, cg, xml = None):
        """Instantiate the plan object."""
        
        # save a reference to the CheddarGetter connection
        self._cg = cg
        
        # am I instantiating a plan that already exists?
        if xml is not None:
            self._id = xml.get('id')
            self._code = xml.get('code')
            
            for child in xml.iterchildren():
                # get the element value -- if it's numeric, convert it
                value = child.text
                if re.match(r'^[\d]+$', value):
                    value = int(value)
                elif re.match(r'^[\d.]+$', value):
                    value = float(value)
                setattr(self, child.tag, value)
        

class Plan(CheddarObject):
    """An object representing a CheddarGetter pricing plan."""
    
    def delete(self):
        """Delete the pricing plan in CheddarGetter."""
        
        # send the deletion request to CheddarGetter
        # note: CheddarGetter returns no response -- this is expected here
        try:
            self._cg.request('/plans/delete/', code = self._code)
        except UnexpectedResponse:
            pass


class Customer(CheddarObject):
    """An object representing a CheddarGetter customer."""
    


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