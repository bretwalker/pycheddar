import copy
import httplib2
import re
import sys
from exceptions import *
from utils import *
from lxml import etree
from urllib import urlencode

VERSION = '1.0alpha'

httplib2.debuglevel = 4

class CheddarGetter:
    """Class designed to handle all interaction with the CheddarGetter API."""
    
    _server = 'https://cheddargetter.com'
    _http = httplib2.Http()
    _product_code = None
    
        
    @classmethod
    def settings(cls, username, password, product_code):
        """Define the settings used to connect to CheddarGetter."""
        
        # add the credentials to the HTTP connection
        cls._http.add_credentials(username, password)
        
        # define the product code in the class
        cls._product_code = product_code
        
        
    @classmethod
    def request(cls, path, code = None, pass_product_code = True, **kwargs):
        """Process an arbitrary request to CheddarGetter.
        
        Ordinarily, you shouldn't have to call this method directly,
        but it's available to send arbitrary requests if needed.
        
        The product code will be appended to the end of the request automatically,
        and does not need to be included"""

        # build the base request URL
        url = '%s/xml/%s' % (cls._server, path.strip('/'))

        # if a code was requested, I may be sent an ID instead; detect this
        # and change the key accordingly
        if code is not None:
            add_to_url = True
            if path.strip('/')[-3:] == 'new':
                add_to_url = False
                
            # make sure code is a string
            code = str(code)
            
            # it may be an ID instead; detect this
            if re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', code):
                if add_to_url is True:
                    url += '/id/' + code
                else:
                    raise ValueError, 'Cannot send an ID for an object creation request.'
            else:
                if add_to_url is True:
                    url += '/code/' + code
                else:
                    kwargs['code'] = code
                
        # mangle the kwargs to make them match what
        # CheddarGetter expects
        for key in copy.copy(kwargs):
            # move from Python naming conventions to Zend Framework conventions
            # (read: underscores become camel-case)
            if '_' in key:
                kwargs[to_camel_case(key)] = kwargs[key]
                del kwargs[key]
                                    
        # add in the product code
        if pass_product_code is True:
            # sanity check: is the product code set?
            if not cls._product_code:
                raise AttributeError, 'You must set a CheddarGetter product code. Use CheddarGetter.settings(username, password, product_code).'
            
            url += '/productCode/' + cls._product_code + '/'

        # create the curl command
        request, content = cls._http.request(url, method = 'POST', body = urlencode(kwargs))
        
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
        
            
    def edit_subscription(cls, **kwargs):
        """Change subscription information"""
        return self._process(key="customers", val="edit-subscription", values=kwargs)
    
    def cancel_subscription(cls, **kwargs):
        """Cancel subscription"""
        return self._process(key="customers", val="cancel", values=kwargs, pass_values=False)
    
    def add_item_quantity(cls, **kwargs):
        """Increment a usage item quantity"""
        return self._process(key="customers", val="add-item-quantity", values=kwargs)
    
    def remove_item_quantity(cls, **kwargs):
        """Decrement a usage item quantity"""
        return self._process(key="customers", val="remove-item-quantity", values=kwargs)
    
    def set_item_quantity(cls, **kwargs):
        """Set a usage item quantity"""
        return self._process(key="customers", val="set-item-quantity", values=kwargs)
    
    def add_charge(cls, **kwargs):
        """Add a custom charge (debit) or credit to the current invoice
        A positive 'eachAmount' will result in a debit. If negative, a credit."""
        return self._process(key="customers", val="add-charge", values=kwargs)
            

class CheddarObject(object):
    """A object that can represent most objects that come down
    from CheddarGetter."""
    
    
    def __init__(self, **kwargs):
        """Instantiate the plan object."""
        
        self._data = {}
        self._clean_data = {}
        self._id = None
        self._code = None
        self._cursor = 0
        
        # iterate over the keyword arguments provided
        # and set them to the object
        for i in kwargs:
            setattr(self, i, kwargs[i])
                        
                
    def __setattr__(self, key, value):
        """Set an arbitrary attribute on this object."""
        
        # if this item is private, set the instance's
        # attribute dictionary directly
        if key[0] == '_':
            self.__dict__[key] = value
        elif key == 'code':
            # code can only be modified if the id is not set
            if self._id is None:
                self._code = value
            else:
                raise AttributeError, 'Once an item has been saved to CheddarGetter, the code is immutable.'
        elif key == 'id':
            raise AttributeError, 'The CheddarGetter ID is immutable.'
        else:
            # in normal situations, write this item to the
            # self._data dictionary (using underscores, always)
            self._data[to_underscores(key)] = value
        
        
    def __getattr__(self, key):
        """Return an arbitrary attribute on this object."""

        # is this a dict method? if so, use the self._data
        # method
        if hasattr(self._data, key):
            return getattr(self._data, key)

        # handle the id and code in a special way
        if key == 'id' or key == 'code':
            return self.__dict__['_' + key]

        # if this is a special private key, return directly
        # from the object
        if key[0] == '_':
            return self.__dict__[key]
            
        # retrieve from the self._data dictionary
        if key in self._data:
            return self._data[to_underscores(key)]
            
        raise AttributeError, 'Key "%s" does not exist.' % key
        
        
    def __eq__(self, other):
        """Return True if these objects have equal _id properties, False otherwise."""
        
        if self._id == other._id and self._id is not None:
            return True
        return False
        
        
    def __ne__(self, other):
        """Return the negation of self.__eq__."""
        
        return not self.__eq__(other)
        
        
    def __contains__(self, key):
        """Return whether or not the key exists in self."""
        # special case: id
        if key == 'id' or key == '_id':
            return self._id is not None
            
        # special case: code
        if key == 'code' or key == '_code':
            return self._code is not None
            
        # for anything else, if it exists in
        # self._data, consider it to exist
        return key in self._data
        
    
    def __iter__(self):
        """Iterate over the items in this object.
        Fundamentally identical to self.iteritems()."""
        return self.iteritems()
        
        
    def is_new(self):
        """Return True if this represents an item not yet initially
        saved in CheddarGetter, False otherwise."""
        return not 'id' in self
        
        
    @classmethod
    def from_xml(cls, xml, clean = True):
        """Create a new object and load information for it from
        XML sent from CheddarGetter.
        
        Data loaded through this method is assumed to be clean.
        If it is dirty data (in other words, data that does not
        match what is currently saved in CheddarGetter), set
        clean = False."""
        
        new = cls()
        new._load_data_from_xml(xml, clean)
        
        # done -- return the new object
        return new
        
        
    def _load_data_from_xml(self, xml, clean = True, _exempt_keys = []):
        """Load information for this object based on XML retrieved
        from CheddarGetter.
        
        Data loaded through this method is assumed to be clean.
        If it is dirty data (in other words, data that does not
        match what is currently saved in CheddarGetter), set
        clean = False.
        
        This method should be considered opaque."""
        
        self._id = xml.get('id')
        self._code = xml.get('code')
        
        for child in xml.iterchildren():
            # is this a key I'm not supposed to handle?
            if child.tag in _exempt_keys:
                continue
            
            # get the element value -- if it's numeric, convert it
            value = child.text
            if value is not None:
                if re.match(r'^[\d]+$', value):
                    value = int(value)
                elif re.match(r'^[\d.]+$', value):
                    value = float(value)
                
            # set the data dictionaries in my object to
            # these values
            key = to_underscores(child.tag)
            self._data[key] = value
            if clean is True:
                self._clean_data[key] = value
        
        
    def _build_kwargs(self):
        """Build the list of keyword arguments based on all items
        modified in the current self._data dictionary."""
        
        kwargs = {}
        for item in self.iteritems():
            # if this item is a CheddarObject, then it'll be handled elsewhere
            if isinstance(item[1], CheddarObject):
                continue
            
            # if this item is dirty, include it in the list of material to send
            if item[0] not in self._clean_data or item[1] != self._clean_data[item[0]]:
                kwargs[item[0]] = item[1]
                
        return kwargs
                

class Plan(CheddarObject):
    """An object representing a CheddarGetter pricing plan."""
    
    
    @classmethod
    def all(cls):
        """Get all pricing plans in the product"""
        
        # retrieve the plans from CheddarGetter
        try: 
            plans = []
            xml = CheddarGetter.request('/plans/get/')
        
            # make a list of Plan objects and return it
            for plan_xml in xml.iterchildren(tag = 'plan'):
                plans.append(Plan.from_xml(plan_xml))
                
            return plans
            
        except NotFound:
            return []
                
    
    @classmethod
    def get(cls, code):
        """Get a single pricing plan"""
        
        # retrieve the plan from CheddarGetter
        xml = CheddarGetter.request('/plans/get/', code = code)
        
        # return a plan object
        for plan_xml in xml.iterchildren(tag = 'plan'):
            return Plan.from_xml(plan_xml)
            
            
    def save(self):
        """Saving of plans through the API is not yet implemented
        in CheddarGetter."""
        
        return NotImplemented

    
    def delete(self):
        """Delete the pricing plan in CheddarGetter."""
        
        # send the deletion request to CheddarGetter
        # note: CheddarGetter returns no response -- this is expected here
        try:
            CheddarGetter.request('/plans/delete/', code = self._code)
        except UnexpectedResponse:
            pass
            
            
    def is_free(self):
        """Return True if CheddarGetter considers this plan to be free,
        False otherwise."""
        
        # allow a small tolerance due to the unreliability of floating
        # point math in most languages (including Python)
        total = self.setup_charge_amount + self.recurring_charge_amount
        return total < 0.000001 and total > -0.000001
            
            
class Customer(CheddarObject):
    """An object representing a CheddarGetter customer."""
    
    
    def __init__(self, **kwargs):
        super(Customer, self).__init__(**kwargs)
        self.subscription = Subscription()
        
        
    def _load_data_from_xml(self, xml, clean = True):
        """Load information for this object from XML sent
        from CheddarGetter.
        
        Data loaded through this method is assumed to be clean.
        If it is dirty data (in other words, data that does not
        match what is currently saved in CheddarGetter), set
        clean = False."""
        
        # get the new customer object
        super(Customer, self)._load_data_from_xml(xml, clean, _exempt_keys = ['subscriptions'])
        
        # process the subscriptions for this customer
        subscription_xml = xml.find('subscriptions').find('subscription')
        self.subscription = Subscription.from_xml(subscription_xml)
        if clean is True:
            self._clean_data['subscription'] = self.subscription
        
        return self
        
        
    @classmethod
    def all(cls):
        """Retrieve all customers in CheddarGetter.
        Functionally identical to Customer.search() called with
        no arguments."""
        
        return Customer.search()
    
    
    @classmethod
    def search(cls, **kwargs):
        """Get customers in the CheddarGetter product plan,
        filters by the provided keyword arguments.
        
        To retrieve all customers, use Customer.all().
        To retrieve a single customer by ID or code, use Customer.get()."""
        
        # retreive the set of customers
        try:
            customers = []
            xml = CheddarGetter.request('/customers/get/', **kwargs)
            for customer_xml in xml.iterchildren('customer'):
                customers.append(Customer.from_xml(customer_xml))
                
            return customers

        except NotFound:
            return []


    @classmethod
    def get(cls, code):
        """Get a specific customer by the given customer code.

        Raises NotFound if the customer code does not exist
        in CheddarGetter."""

        xml = CheddarGetter.request('/customers/get/', code = code)
        for customer_xml in xml.iterchildren('customer'):
            return Customer.from_xml(customer_xml)
    
    
    def validate(self):
        """Verify that this is a well-formed Customer object.
        
        Return True to continue the save, or ValidationError
        otherwise."""
        
        # make sure this object has a code
        if not self._code:
            raise ValidationError, 'No code has been set.'
                                
        # the subscription object must also validate
        self.subscription.validate()
            
        # the customer object must have all required keys
        required_keys = ['first_name', 'last_name', 'email']
        for i in required_keys:
            if i not in self:
                raise ValidationError, 'Missing required key: "%s"' % i

        return True
    
        
    def save(self):
        """Save this customer to CheddarGetter"""
        
        # is this valid?
        self.validate()
        
        # build the list of arguments
        kwargs = self._build_kwargs()
        
        # if this is a new item, then CheddarGetter requires me
        # to send subscription data as well
        if self.is_new():
            # first, get the plan code
            kwargs['subscription[plan_code]'] = self.subscription.plan.code
            
            # if credit card information is available in the subscription,
            # send it as well
            cc_info = ['cc_first_name', 'cc_last_name', 'cc_number', 'cc_expiration', 'cc_card_code', 'cc_zip']
            for key in cc_info:
                if key in self.subscription:
                    kwargs['subscription[%s]' % key] = getattr(self.subscription, key)
            
            xml = CheddarGetter.request('/customers/new/', code = self._code, **kwargs)
        else:
            # okay, this isn't new -- send the update request
            xml = CheddarGetter.request('/customers/edit/', code = self._code, **kwargs)

        # either way, I should get a well-formed customer XML response
        # that can now be loaded into this object
        for customer_xml in xml.iterchildren('customer'):
            self._load_data_from_xml(customer_xml)
            break
            
        return self
    

    def delete(self):
        """Delete this customer from CheddarGetter."""
        
        # CheddarGetter does not return a response to deletion
        # requests in the success case
        try:
            xml = CheddarGetter.request('/customers/delete/', code = self._code)
        except UnexpectedResponse:
            pass
    
    
    
class Subscription(CheddarObject):
    """An object representing a CheddarGetter subscription."""
    
    def __init__(self):
        super(Subscription, self).__init__()
        self.plan = Plan()
        
        
    def _load_data_from_xml(self, xml, clean = True):
        """Load information for this object from XML sent
        from CheddarGetter.
        
        Data loaded through this method is assumed to be clean.
        If it is dirty data (in other words, data that does not
        match what is currently saved in CheddarGetter), set
        clean = False."""
        
        # get the new subscription object
        super(Subscription, self)._load_data_from_xml(xml, clean, _exempt_keys = ['plans', 'invoices'])
        
        # process the pricing plans within the subscription
        plan_xml = xml.find('plans').find('plan')
        self._data['plan'] = Plan.from_xml(plan_xml)
        if clean is True:
            self._clean_data['plan'] = self.plan
        
        # process the invoices within the subscription
        invoices = xml.find('invoices')
        self._data['invoices'] = self._clean_data['invoices'] = []
        for invoice_xml in invoices.iterchildren('invoice'):
            self.invoices.append(Invoice.from_xml(invoice_xml))
        if clean is True:
            self._clean_data['invoices'] = self._clean_data['invoices']
        
        return self
        
        
    def __getattr__(self, key):
        # plan_code is special; pull it from the Plan object
        if to_underscores(key) == 'plan_code':
            return self.plan.code
            
        return super(Subscription, self).__getattr__(key)
        
        
    def __setattr__(self, key, value):
        # sanity check: invoices are read-only
        if key == 'invoices':
            raise AttributeError, 'Invoices on subscription objects are read-only.'
        
        # plan and plan_code are special; I want to accept a plan code
        # string for both, or a Plan object for self.plan -- in all three
        # cases, I want to write a Plan object to self.plan
        if to_underscores(key) == 'plan_code' or (key == 'plan' and not isinstance(value, Plan)):
            self.plan = Plan.get(value)
        else:
            super(Subscription, self).__setattr__(key, value)
        
        
    def validate(self):
        return True
    

class Invoice(CheddarObject):
    """An object representing a CheddarGetter invoice."""
    
    
    
    
# if we are using Django, and if the appropriate settings
# are already set in Django, just import them automatically
try:
    from django.conf import settings
    
    if settings.CHEDDARGETTER_USERNAME and settings.CHEDDARGETTER_PASSWORD and settings.CHEDDARGETTER_PRODUCT_CODE:
        CheddarGetter.settings(settings.CHEDDARGETTER_USERNAME, settings.CHEDDARGETTER_PASSWORD, settings.CHEDDARGETTER_PRODUCT_CODE)
except ImportError:
    pass