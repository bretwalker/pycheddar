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
    
    def _get_data(self, **kwargs):
        """send a request and get back data from the API"""
        
        # build the request URL
        url = "https://cheddargetter.com/xml"
        for key, val in kwargs.iteritems():
            url += '/' + key + '/' + val
        url += '/productCode/' + self.product_code
        
        # make the request and retrieve the data
        request, content = self._http.request(url, "POST")
        if int(request['status']) == 200:
            content = etree.fromstring(content)
        return content