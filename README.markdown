Woah there - this bad boy is not quite ready for prime time yet
---------------------------------------------------------------
This is mostly a port from the PHP and Ruby wrappers that already existed -
but it is not finished yet. We're building it to handle payment processing
for FeedMagnet.com, but we figure everyone else should be able to benefit
from it as well. We hope to be finished in the next few weeks.


A Python wrapper for CheddarGetter
----------------------------------
PyCheddar is a Python wrapper for CheddarGetter - which is a great service
for handling recurring subscription payments without having to reinvent a
mini-app to handle payments with each new project.


Installation
------------
Just clone this repository anywhere in your PythonPath like this:

    $ git clone http://github.com/jasford/pycheddar.git

Eventually - but definitely not yet - you will be able to use easy_install
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
This is how we hope everything will work once it is all finished. Note that most
of this does not work at all right now.

Connect to CheddarGetter

    >>> import pycheddar
    >>> cheddar = pyhcheddar.Connection(yourusername, yourpassword, yourproductcode)

Get a customer data

    >>> customer_list = cheddar.get_customers();
    >>> one_specific_customer = chedddar.get_customer(code='EXAMPLE_CUSTOMER')

Create a new customer

    >>> customer = cheddar.new_customer(
            code='EXAMPLE_CUSTOMER',
            firstName='Example',
            lastName='Customer',
            email='example_customer@example.com'
            subscription={
                'planCode': 'THE_PLAN_CODE',
                'ccFirstName': 'Example',
                'ccLastName': 'Customer',
                'ccNumber': '4111111111111111',
                'ccExpiration': '04/2011',
                'ccZip': '90210',
            },
        )


How does it work?
-----------------
pycheddar.Connection is the object used to interact with the CheddarGetter API.
pycheddar.Connection methods typically return a list or dictionary with the data
retrieved from the CheddarGetter API.