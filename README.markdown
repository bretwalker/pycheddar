A Python wrapper for CheddarGetter
----------------------------------
PyCheddar is a Python wrapper for CheddarGetter - which is a great service
for handling recurring subscription payments without having to reinvent a
mini-app to handle payments with each new project.


Installation
------------
Just clone this repository anywhere in your PythonPath like this:

    $ git clone http://github.com/jasford/pycheddar.git

Eventually - but not just yet - you will be able to use easy_install
like this:

    $ easy_install pycheddar

Once you've done one of the above, you can test to see if it is installed from
the Python interactive terminal:

    >>> import pycheddar

If you don't get an error, you should be good to go.


A Note From FeedMagnet
----------------------
PyCheddar was created as part of the code base for FeedMagnet - an online app
that helps businesses harness with social media. We use CheddarGetter to handle
all of our payment processing for premium accounts.

We really believe in open source software - and we've benefited a lot from it.
We use Ubuntu, Python, Django, MySQL, CouchDB - and a ton of other open source
tools to make FeedMagnet run. Open source only works if we all give back. This
is hopefully just our first minor contribution to the open source community.


Example Usage
-------------

Set up your CheddarGetter login info:

    >>> from pycheddar import *
    >>> CheddarGetter.settings('e-mail address', 'password', 'product code')

Get all customers (returns a list of Customer objects):

    >>> customers = Customer.all()
    >>> for customer in Customer.all():
    ...     print customer.last_name

Get a customer that already exists, either by the ID or the code in CheddarGetter:

    >>> customer = Customer.get('4072cc12-5375-102d-86dc-40402145ee8b')
    >>> customer = Customer.get('MY_CODE')
    
Get customers based on arbitrary criteria:

    >>> customers = Customer.search(last_name = 'Smith')
    
Edit information about a customer:

    >>> customer = Customer.get('4072cc12-5375-102d-86dc-40402145ee8b')
    >>> customer.last_name = 'Jones'
    >>> customer.save()
    
Add a new customer:

    >>> # this works...
    >>> customer = Customer(code = 'JOHN_SMITH', first_name = 'John', last_name = 'Smith', email = 'john.smith@gmail.com', plan_code = 'FREE')
    >>> customer.save()
    >>>
    >>> # and this does too...
    >>> customer = Customer()
    >>> customer.code = 'JOHN_SMITH'
    >>> customer.first_name = 'John'
    >>> customer.last_name = 'Smith'
    >>> customer.email = 'john.smith@gmail.com'
    >>> customer.plan_code = 'FREE'
    >>> customer.save()
    
Get a customer's subscription information:

    >>> subscription = Customer.get('JOHN_SMITH').subscription
    
Edit a customer's subscription information:

    >>> subscription = Customer.get('JOHN_SMITH').subscription
    >>> subscription.cc_number = '4111111111111111'
    >>> subscription.cc_first_name = 'John'
    >>> subscription.cc_last_name = 'Smith'
    >>> subscription.cc_expiration = '01/2013'
    >>> subscription.cc_zip = '77777'
    >>> subscription.cc_card_code = '000'
    >>> subscription.save()
    
Switch a customer to a new plan:

    >>> # lots of ways to do this...here's one:
    >>> subscription.plan = Plan.get('COMPREHENSIVE')
    >>> subscription.save()
    >>>
    >>> # or...
    >>> subscription.plan = 'COMPREHENSIVE'
    >>> subscription.save()
    >>>
    >>> # or...
    >>> customer.plan_code = 'COMPREHENSIVE'
    >>> customer.save()
    
View the items included in a plan...

    >>> for item in plan.items:
    ...     print (item.code, item.quantity)
    
Set an item's quantity (if the item is attached to a customer):

    >>> item = customer.items[0]
    >>> item.quantity = 5
    >>> item.save()
    >>>
    >>> # note, CheddarGetter doesn't let you edit item quantity on
    >>> # plans through the API, so that will fail...
    >>> item = plan.items[0]
    >>> item.quantity = 5
    >>> item.save()
    pycheddar.exceptions.ValidationError: Items may only have their quantity altered if they are directly attached to a customer.
    