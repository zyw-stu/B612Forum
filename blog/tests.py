from django.test import TestCase

# Create your tests here.

dict1={'pageone': 'one', 'pagetwo': 'two', 'is_paginated': True, }
dict2={'pageone': 'one', 'title':'hello>'}
dict1.update(dict2)
print(dict1)


dict3={'pageone': 'one', 'pagetwo': 'two', 'is_paginated': True, }
dict4={'pageone': '1','pagetwo': '2', 'title':'hello>'}
dict3.update(dict4)
print(dict3)
