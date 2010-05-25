import copy
import datetime
import httplib2
import re
import sys
from exceptions import *
from utils import *
from xml.etree import ElementTree
from urllib import urlencode

VERSION = '0.9.3'

class CheddarGetter:
    """Class designed to handle all interaction with the CheddarGetter API."""
    
    _server = 'https://cheddargetter.com'
    _http = httplib2.Http()
    _product_code = None
    
        
    @classmethod
    def auth(cls, username, password):
        """Define the settings used to connect to CheddarGetter."""
        
        # add the credentials to the HTTP connection
        cls._http.add_credentials(username, password)
        
    
    @classmethod
    def set_product_code(cls, product_code):
        # define the product code in the class
        cls._product_code = product_code
        
        
    @classmethod
    def request(cls, path, code = None, item_code = None, product_code = None, pass_product_code = True, **kwargs):
        """Process an arbitrary request to CheddarGetter.
        
        Ordinarily, you shouldn't have to call this method directly,
        but it's available to send arbitrary requests if needed.
        
        The product code will be appended to the end of the request automatically,
        and does not need to be included. Override this behavior by passing
        pass_product_code = False."""

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
            if re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', code):
                if add_to_url is True:
                    url += '/id/' + code
                else:
                    raise ValueError, 'Cannot send an ID for an object creation request.'
            else:
                if add_to_url is True:
                    url += '/code/' + code
                else:
                    kwargs['code'] = code
                    
        # item_code is also handled differently from other keyword arguments
        # (CheddarGetter expects it in the URL, not the POST body)
        if item_code is not None:
            url += '/itemCode/' + item_code
                
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
            # if the product code is None, use the one assigned to the class generically
            if product_code is None:
                product_code = cls._product_code
            
            # sanity check: is the product code set?
            if not product_code:
                raise AttributeError, 'You must set a CheddarGetter product code. Use CheddarGetter.set_product_code(product_code).'
            
            url += '/productCode/' + product_code + '/'
            
        # create the curl command
        request, content = cls._http.request(url, method = 'POST', body = urlencode(kwargs), headers = {
            'content-type': 'application/x-www-form-urlencoded'
        })
        
        # parse the XML
        try:
            content = ElementTree.fromstring(content)
        except:
            raise UnexpectedResponse, "The server sent back something that wasn't valid XML."
        
        # raise appropriate exceptions if there is an error
        # of any kind
        status = int(request['status'])
        if status >= 400 or content.tag == 'error':
            if status == 404:
                raise NotFound, content.text
            elif status == 401:
                raise AuthorizationRequired, content.text
            elif status == 400 or status == 412:  # CheddarGetter uses 400 and 412 roughly interchangably
                raise BadRequest, content.text
            elif status == 403:
                raise Forbidden, content.text
            elif status == 422:
                raise GatewayFailure, content.text
            elif status == 502:
                raise GatewayConnectionError, content.text
            else:
                raise UnexpectedResponse, content.text
            
        # return the processed content from CheddarGetter
        return content
                    

class CheddarObject(object):
    """A object that can represent most objects that come down
    from CheddarGetter."""
    
    
    def __init__(self, parent = None, **kwargs):
        """Instantiate the object."""
        
        self._product_code = CheddarGetter._product_code
        self._data = {}
        self._clean_data = {}
        self._id = None
        self._code = None
        self._cursor = 0
        
        # is this object a child of some other object?
        # note the relationship if it's sent
        if parent is not None:
            setattr(self, parent.__class__.__name__.lower(), parent)
        
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
            # id can only be modified if it is not set
            raise AttributeError, 'The CheddarGetter ID is immutable.'
        elif isinstance(value, CheddarObject) or isinstance(value, list):
            # if the value is a CheddarObject or a list, then it doesn't belong
            # as part of the data dictionary, but rather as a regular
            # instance attribute
            self.__dict__[key] = value
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

        # is this in the regular attribute dictionary?
        if key[0] == '_' or key in self.__dict__:
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
    def from_xml(cls, xml, **kwargs):
        """Create a new object and load information for it from
        XML sent from CheddarGetter.
        
        If there are additional positional arguments, they are
        passed on to the object's constructor.
        
        Data loaded through this method is assumed to be clean.
        If it is dirty data (in other words, data that does not
        match what is currently saved in CheddarGetter), set kwarg
        clean = False."""
        
        # default "clean" to True and "parent" to None
        clean = kwargs.pop('clean', True)
        parent = kwargs.pop('parent', None)
        
        # I don't recognize any other kwargs
        if len(kwargs) > 0:
            raise KeyError, 'Unrecognized keyword argument: %s' % kwargs.keys()[0]
        
        # create the new object and load in the data
        new = cls(parent = parent, **kwargs)
        new._load_data_from_xml(xml, clean)
        
        # done -- return the new object
        return new
        
        
    def _load_data_from_xml(self, xml, clean = True):
        """Load information for this object based on XML retrieved
        from CheddarGetter.
        
        Data loaded through this method is assumed to be clean.
        If it is dirty data (in other words, data that does not
        match what is currently saved in CheddarGetter), set
        clean = False.
        
        This method should be considered opaque."""
        
        self._id = xml.get('id')
        self._code = xml.get('code')
        
        # denote relationships where there will only
        # be one child object, rather than an arbitrary set
        singles = (
            ('customer', 'subscriptions'),
            ('subscription', 'plans'),
        )
        
        for child in xml.getchildren():
            # is this an element with children? if so, it's an object
            # relationship, not just an attribute
            if len(child.getchildren()) > 0:
                # is this a single-esque relationship, as opposed to one
                # where the object should contain a list?
                if (xml.tag, child.tag) in singles:
                    single_xml = child.getchildren()[0]
                    class_name = single_xml.tag.capitalize()
                    
                    if hasattr(sys.modules[__name__], class_name):
                        klass = getattr(sys.modules[__name__], single_xml.tag.capitalize())
                        setattr(self, single_xml.tag, klass.from_xml(single_xml, parent = self))
                        
                        # denote a clean version as well
                        setattr(self, '_clean_%s' % single_xml.tag, getattr(self, single_xml.tag))
                        
                    continue
                    
                # okay, it's not a single relationship -- follow my normal
                # process for a many to many
                setattr(self, child.tag, [])
                for indiv_xml in child.getchildren():
                    # get the class that this item is
                    try:
                        klass = getattr(sys.modules[__name__], indiv_xml.tag.capitalize())
                    
                        # the XML underneath here constitutes the necessary
                        # XML to generate that object; call its XML function
                        getattr(self, child.tag).append(klass.from_xml(indiv_xml, parent = self))
                    except AttributeError:
                        break
                        
                    # set the clean version
                    setattr(self, '_clean_' + child.tag, getattr(self, child.tag))
                        
                # done; move to the next child
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
        
        
    def _is_clean(self):
        """Return True if this object has not been modified, False otherwise."""
        
        if len(self._build_kwargs()) == 0:
            return True
            
        return False
                

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
            for plan_xml in xml.getiterator(tag = 'plan'):
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
        for plan_xml in xml.getiterator(tag = 'plan'):
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
            CheddarGetter.request('/plans/delete/', code = self._code, product_code = self._product_code)
        except UnexpectedResponse:
            pass
            
            
    def is_free(self):
        """Return True if CheddarGetter considers this plan to be free,
        False otherwise."""
        
        # allow a small tolerance due to the unreliability of floating
        # point math in most languages (including Python)
        total = self.setup_charge_amount + self.recurring_charge_amount
        return total < 0.000001 and total > -0.000001
        
        
    def get_item(item_code):
        """Retrieve an item by item code. If the item does not exist,
        raise ValueError."""
        
        for item in self.items:
            if item.code == item_code:
                return item
                
        raise ValueError, 'Item not found.'
            
            
class Customer(CheddarObject):
    """An object representing a CheddarGetter customer."""
    
    
    def __init__(self, **kwargs):
        self.subscription = Subscription(parent = self)
        super(Customer, self).__init__(**kwargs)
        
        
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
            for customer_xml in xml.getiterator(tag='customer'):
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
        for customer_xml in xml.getiterator(tag='customer'):
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
            
            xml = CheddarGetter.request('/customers/new/', product_code = self._product_code, code = self._code, **kwargs)
        else:
            # okay, this isn't new -- send the update request
            xml = CheddarGetter.request('/customers/edit/', product_code = self._product_code, code = self._code, **kwargs)
            
            # if the subscription has been altered, save it too
            # (this seems like expected behavior)
            if not self.subscription._is_clean():
                self.subscription.save()

        # either way, I should get a well-formed customer XML response
        # that can now be loaded into this object
        for customer_xml in xml.getiterator(tag='customer'):
            self._load_data_from_xml(customer_xml)
            break
            
        return self
    

    def delete(self):
        """Delete this customer from CheddarGetter."""
        
        # CheddarGetter does not return a response to deletion
        # requests in the success case
        xml = CheddarGetter.request('/customers/delete/', product_code = self._product_code, code = self._code)
        
    
    def get_item(item_code):
        """Retrieve an item by item code. If the item does not exist,
        raise ValueError."""

        for item in self.items:
            if item.code == item_code:
                return item

        raise ValueError, 'Item not found.'
        
        
    def add_charge(self, charge_code, item_code, amount = 0.0, quantity = 1, description = None):
        # set up the kwargs that CheddarGetter expects
        kwargs = {
            'item_code': item_code,
            'charge_code': charge_code,
            'each_amount': '%.2f' % float(amount),
            'quantity': quantity,
        }
        if description is not None:
            kwargs['description'] = description
        
        # send the request to CheddarGetter
        xml = CheddarGetter.request('/customers/add-charge/', product_code = self._product_code, code = self.code, **kwargs)
        
    
class Subscription(CheddarObject):
    """An object representing a CheddarGetter subscription."""
    
    def __init__(self, **kwargs):
        self._clean_plan = self.plan = Plan()
        super(Subscription, self).__init__(**kwargs)
        
    
    def __getattr__(self, key):
        # plan_code is special; pull it from the Plan object
        if to_underscores(key) == 'plan_code':
            return self.plan.code
            
        return super(Subscription, self).__getattr__(key)
        
        
    def __setattr__(self, key, value):
        # intercept the number and format it as digits only
        if to_underscores(key) == 'cc_number':
            return super(Subscription, self).__setattr__(key, re.sub(r'[\D]', '', value))
            
        # intercept the expiration date and format it how CheddarGetter expects
        if to_underscores(key) == 'cc_expiration':
            if value[2] != '/':
                value = value[0:2] + '/' + value[2:]
            
            # change "0312" (March 2012) to "032012", which is the format
            # that CheddarGetter expects
            if len(value) == 5:
                # try not to have something that will break in 2100
                # (even though nobody will use my stuff by then)
                year = datetime.datetime.now().year
                century = str(year)[0:2]
                if year % 100 > 90 and int(value[2:]) < 10:
                    century = str(year + 100)[0:2]
                    
                # add the century number into the value
                value = value[:3] + century + value[3:]
                
            # send it up
            return super(Subscription, self).__setattr__(key, value)
        
        # plan and plan_code are special; I want to accept a plan code
        # string for both, or a Plan object for self.plan -- in all three
        # cases, I want to write a Plan object to self.plan
        if to_underscores(key) == 'plan_code' or (key == 'plan' and not isinstance(value, Plan)):
            self.plan = Plan.get(value)
        else:
            super(Subscription, self).__setattr__(key, value)
        
        
    def validate(self):
        """If the plan connected to this subscription is not free, then
        I need to have credit card information."""
        
        # if the plan is free, then no other information is needed
        if self.plan.is_new() is False and self.plan.is_free():
            return True
            
        # check for required credit card information
        required = ['cc_first_name', 'cc_last_name', 'cc_number', 'cc_expiration', 'cc_card_code', 'cc_zip']
        try:
            for key in required:
                if not getattr(self, key):
                    return False
        except AttributeError:
            return False
            
        # no problems detected
        return True
        
        
    def _build_kwargs(self):
        """Build keyword arguments. Make sure plan code is included if appropriate."""
        
        # run the superclass method
        kwargs = super(Subscription, self)._build_kwargs()
        
        # make sure plan code is reflected accurately
        if self.plan != self._clean_plan:
            kwargs['plan_code'] = self.plan.code
            
        return kwargs
        
        
    def save(self):
        """Save this object's properties to CheddarGetter."""
        
        # CheddarGetter does not create subscriptions directly;
        # if this is a new object, it needs to be saved through the Customer
        if self.is_new() is True:
            self.customer.save()
            return self

        # sanity check: has anything changed?
        kwargs = self._build_kwargs()
        if len(kwargs) == 0:
            return self
            
        # this is an object being edited; update the subscription
        # by itself at CheddarGetter
        xml = CheddarGetter.request('/customers/edit-subscription/', product_code = self._product_code, code = self.customer.code, **kwargs)

        # either way, I should get a well-formed customer XML response
        # that can now be loaded into this object
        for subscription_xml in xml.getiterator(tag='subscription'):
            self._load_data_from_xml(subscription_xml)
            break
            
        return self
        
    
    def delete(self):
        """Remove this subscription from CheddarGetter."""
        
        # this is straightforward: just run the cancellation
        xml = CheddarGetter.request('/customers/cancel/', product_code = self._product_code, code = self.customer.code, **kwargs)
        
        
    def cancel(self):
        """Alias to Subscription.delete() -- provided because CheddarGetter
        uses the method name "cancel" for the URL.
        
        For consistency, Subscription.delete() is preferred."""
        return self.delete()
        
        

class Item(CheddarObject):
    """An object representing a distinct item."""
    
    def __setattr__(self, key, value):
        """Set an arbitrary attribute."""
        
        # CheddarGetter inconsistently uses "quantity included" and "quantity"
        # depending on whether this is attached to a customer or a plan -- always
        # allow "quantity" here
        if key == 'quantity' and hasattr(self, 'plan'):
            return setattr(self, 'quantity_included', value)
            
        # regular case
        super(Item, self).__setattr__(key, value)
        
        
    def __getattr__(self, key):
        """Get an arbitrary attribute."""
        
        # intercept "quantity" and allow it to stand in for "quantity_included"
        # if this item is a member of a plan
        if key == 'quantity' and hasattr(self, 'plan'):
            return getattr(self, 'quantity_included')
        
        # regular case
        return super(Item, self).__getattr__(key)
        
    
    def validate(self):
        """Validate that this item may be saved. Return True on success or
        raise ValidationError otherwise."""
        
        # sanity check: I can only modify this item if it's directly attached
        # to the cuastomer
        if not hasattr(self, 'customer'):
            raise ValidationError, 'Items may only have their quantity altered if they are directly attached to a customer.'
            
        # get what is being changed and run validation
        kwargs = self._build_kwargs()
        if len(kwargs) == 0:
            return self
        if 'quantity' not in kwargs or len(kwargs) > 1:
            raise ValidationError, 'Only the quantity of an item can be changed through the CheddarGetter API.'
        
        return True
    
    
    def save(self):
        """Save this item back to CheddarGetter."""
        
        # sanity check: validate first!
        self.validate()
    
        # okay, save to CheddarGetter
        xml = CheddarGetter.request('/customers/set-item-quantity/', product_code = self._product_code, item_code = self.code, code = self.customer.code)
        self._load_data_from_xml(xml)
        return self


class Invoice(CheddarObject):
    """An object representing a CheddarGetter invoice."""


class Charge(CheddarObject):
    """An object representing a CheddarGetter charge."""

# if we are using Django, and if the appropriate settings
# are already set in Django, just import them automatically
try:
    from django.conf import settings
    
    if hasattr(settings, 'CHEDDARGETTER_USERNAME') and hasattr(settings, 'CHEDDARGETTER_PASSWORD'):
        CheddarGetter.auth(settings.CHEDDARGETTER_USERNAME, settings.CHEDDARGETTER_PASSWORD)
    if hasattr(settings, 'CHEDDARGETTER_PRODUCT_CODE'):
        CheddarGetter.set_product_code(settings.CHEDDARGETTER_PRODUCT_CODE)
except ImportError:
    pass
