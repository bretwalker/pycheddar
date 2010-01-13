import httplib2
from lxml import etree


class Connection:
    """Class to interact with the CheddarGetter API"""
    
    def __init__(self, *args):
        """Create a new object and set the connection attributes"""
        
        # save connection attributes to the new object
        self._username = args[0]
        self._password = args[1]
        self.product_code = args[2]
        
        # create httplib2 object for http interactions
        self._http = httplib2.Http()
        
        # unfortunately, this authentication isn't working right now - not sure why
        self._http.add_credentials(self._username, self._password)
    
    def _process(self, **kwargs):
        
        # set default values for kwargs
        if 'require_id' not in kwargs:
            kwargs['require_id'] = True
        if 'pass_values' not in kwargs:
            kwargs['pass_values'] = True
        if 'pass_product_code' not in kwargs:
            kwargs['pass_product_code'] = True
        
        # if we require an id
        if kwargs['require_id']:
            
            # check to see if we have an id, and use it instead of code
            if 'id' in kwargs['values']:
                
                # remove code from kwargs so we don't send id AND code
                if kwargs['pass_values']:
                    params = kwargs['values']
                    if 'code' in kwargs['values']:
                        del kwargs['values']['code']
                
                # if we don't need all values, set params to just the id
                else:
                    params = {'id': kwargs['id']}
            
            # since we didn't have an id, see if we can use code instead
            elif 'code' in kwargs['values']:
                
                # if we have code and we're passing values, we can just pass everything
                if kwargs['pass_values']:
                    params = kwargs['values']
                
                # if we don't need all values, set params to just the code
                else:
                    params = {'code': kwargs['code']}
            
            # if kwargs did not include id or code, raise Exception
            else:
                raise Exception('Either a code or id is required')
        
        # if we don't require an id, we're either passing all params or nothing
        else:
            if kwargs['pass_values']:
                params = kwargs
            else:
                params = {}
        
        # build the base request URL
        url = "https://cheddargetter.com/xml/" + kwargs['key'] + "/" + kwargs['val']
        
        # add in the params
        for key, val in params.iteritems():
            url += '/' + key + '/' + val
        
        # add in the product code
        if include_product_code:
            url += '/productCode/' + self.product_code
        
        # make the request and retrieve the data
        request, content = self._http.request(url, "POST")
        if int(request['status']) == 200:
            content = etree.fromstring(content)
        
        # return the processed content from CheddarGetter
        return content
        
    def get_plans(self, **kwargs):
        """Get all pricing plans in the product"""
        return self._process(key="plans", val="get", require_id=False)
    
    def get_plan(self, **kwargs):
        """Get a single pricing plan"""
        return self._process(key="plans", val="get", pass_values=False)
    
    def delete_plan(self, **kwargs):
        """Delete a plan"""
        return self._process(key="plans", val="delete", pass_values=False)
    
    def get_customers(self, **kwargs):
        """Get all customers in the product"""
        return self._process(key="customers", val="get", require_id=False)
    
    def get_customer(self, **kwargs):
        """Get all plans in the product"""
        return self._process(key="customers", val="get", pass_values=False)
    
    def get_all_customers(self, **kwargs):
        """Get all plans in the product"""
        return self._process(key="customers", val="get-all", require_id=False, pass_product_code=False)
    
    def new_customer(self, **kwargs):
        """Create new customer"""
        return self._process(key="customers", val="new", require_id=False)
    
    def edit_customer(self, **kwargs):
        """Change customer information"""
        return self._process(key="customers", val="edit")
    
    def delete_customer(self, **kwargs):
        """Delete a customer"""
        return self._process(key="customers", val="delete", pass_values=False)
    
    def edit_subscription(self, **kwargs):
        """Change subscription information"""
        return self._process(key="customers", val="edit-subscription")
    
    def cancel_subscription(self, **kwargs):
        """Cancel subscription"""
        return self._process(key="customers", val="cancel", pass_values=False)
    
    def add_item_quantity(self, **kwargs):
        """Increment a usage item quantity"""
        return self._process(key="customers", val="add-item-quantity")
    
    def remove_item_quantity(self, **kwargs):
        """Decrement a usage item quantity"""
        return self._process(key="customers", val="remove-item-quantity")
    
    def set_item_quantity(self, **kwargs):
        """Set a usage item quantity"""
        return self._process(key="customers", val="set-item-quantity")
    
    def add_charge(self, **kwargs):
        """Add a custom charge (debit) or credit to the current invoice
        A positive 'eachAmount' will result in a debit. If negative, a credit."""
        return self._process(key="customers", val="add-charge")