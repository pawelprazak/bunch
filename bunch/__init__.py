#!/usr/bin/env python
# encoding: utf-8
""" Bunch is a subclass of dict with attribute-style access.
    
    >>> b = Bunch()
    >>> b.hello = 'world'
    >>> b.hello
    'world'
    >>> b['hello'] += "!"
    >>> b.hello
    'world!'
    >>> b.foo = Bunch(lol=True)
    >>> b.foo.lol
    True
    >>> b.foo is b['foo']
    True
    
    It is safe to import * from this module:
    
        __all__ = ('Bunch', 'bunchify','unbunchify')
    
    (un)bunchify provide deep recursive dictionary conversion;
"""

__all__ = ('Bunch', 'bunchify','unbunchify')


class Bunch(dict):
    """ A dictionary that provides attribute-style access.
        See (un)bunchify for notes about conversions.
        
        >>> b = Bunch()
        >>> b.hello = 'world'
        >>> b.hello
        'world'
        >>> b['hello'] += "!"
        >>> b.hello
        'world!'
        >>> b.foo = Bunch(lol=True)
        >>> b.foo.lol
        True
        >>> b.foo is b['foo']
        True
        
        A Bunch is a subclass of dict; it supports all the methods a dict does...
        
        >>> b.keys()
        ['foo', 'hello']
        
        Including update()...
        
        >>> b.update({ 'ponies': 'are pretty!' }, hello=42)
        >>> print repr(b)
        Bunch({'ponies': 'are pretty!', 'foo': Bunch({'lol': True}), 'hello': 42})
        
        As well as iteration...
        
        >>> [ (k,b[k]) for k in b ]
        [('ponies', 'are pretty!'), ('foo', Bunch({'lol': True})), ('hello', 42)]
        
        And "splats".
        
        >>> "The {knights} who say {ni}!".format(**Bunch(knights='lolcats', ni='can haz'))
        'The lolcats who say can haz!'

		Test __contains__:

        >>> b = Bunch(ponies='are pretty!')
        >>> 'ponies' in b
        True
        >>> 'foo' in b
        False
        >>> b['foo'] = 42
        >>> 'foo' in b
        True
        >>> b.hello = 'hai'
        >>> 'hello' in b
        True
        
        Let's test JSON
        
        Encode:
        >>> import simplejson as json
        >>> s = json.dumps(Bunch({'4': 5, '6': 7}), sort_keys=True, indent=' '*4)
        >>> print '\\n'.join(l.rstrip() for l in s.splitlines())
        {
            "4": 5,
            "6": 7
        }
        
        Decode:
        >>> import simplejson as json
        >>> obj = {'4': 5, '6':7}
        >>> data = json.loads('{"4": 5, "6":7}')
        >>> data == obj
        True
        >>> Bunch(data)
        Bunch({'4': 5, '6': 7})
    """
    

    def __getattr__(self, name):
        """ Gets key if it exists, otherwise throws AttributeError.
            
            nb. __getattr__ is only called if key is not found in normal places.
            
            >>> b = Bunch(bar='baz', lol={})
            >>> b.foo
            Traceback (most recent call last):
                ...
            AttributeError: foo
            
            >>> b.bar
            'baz'
            >>> getattr(b, 'bar')
            'baz'
            >>> b['bar']
            'baz'
            
            >>> b.lol is b['lol']
            True
            >>> b.lol is getattr(b, 'lol')
            True
        """
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        """ Sets attribute k if it exists, otherwise sets key k. A KeyError
            raised by set-item (only likely if you subclass Bunch) will 
            propagate as an AttributeError instead.
            
            >>> b = Bunch(foo='bar', this_is='useful when subclassing')
            >>> b.values                            #doctest: +ELLIPSIS
            <built-in method values of Bunch object at 0x...>
            >>> b.values = 'uh oh'
            >>> b.values
            'uh oh'
            >>> b['values']
            Traceback (most recent call last):
                ...
            KeyError: 'values'
        """
        if hasattr(self, name):
            object.__setattr__(self, name, value)
        else:
            self.setdefault(name, value)

    def __delattr__(self, name):
        """ Deletes attribute k if it exists, otherwise deletes key k. 
            A KeyError raised by deleting the key--such as when the key is missing--
            will propagate as an AttributeError instead.
            
            >>> b = Bunch(lol=42)
            >>> del b.values
            Traceback (most recent call last):
                ...
            AttributeError: 'Bunch' object attribute 'values' is read-only
            >>> del b.lol
            >>> b.lol
            Traceback (most recent call last):
                ...
            AttributeError: lol
        """
        try:
            del self[name]
        except KeyError:
            object.__delattr__(self, name)
        
    def __repr__(self):
        """ String-form of a Bunch.
            
            >>> b = Bunch(foo=Bunch(lol=True), hello=42, ponies='are pretty!')
            >>> print repr(b)
            Bunch({'ponies': 'are pretty!', 'foo': Bunch({'lol': True}), 'hello': 42})
            >>> eval(repr(b))
            Bunch({'ponies': 'are pretty!', 'foo': Bunch({'lol': True}), 'hello': 42})
        """
        return '%s(%s)' % (self.__class__.__name__, str(dict.__repr__(self)))




# While we could convert abstract types like Mapping or Iterable, I think
# bunchify is more likely to "do what you mean" if it is conservative about
# casting (ex: isinstance(str,Iterable) == True ).
#
# Should you disagree, it is not difficult to duplicate this function with
# more aggressive coercion to suit your own purposes.

def bunchify(obj):
    """ Recursively transforms a dictionary into a Bunch via copy.
        
        >>> b = bunchify({'urmom': {'sez': {'what': 'what'}}})
        >>> b.urmom.sez.what
        'what'
        
        bunchify can handle intermediary dicts, lists and tuples (as well as 
        their subclasses), but ymmv on custom datatypes.
        
        >>> b = bunchify({ 'lol': ('cats', {'hah':'i win again'}), 'hello': [{'french':'salut', 'german':'hallo'}] })
        >>> b.hello[0].french
        'salut'
        >>> b.lol[1].hah
        'i win again'
        
        nb. As dicts are not hashable, they cannot be nested in sets/frozensets.
    """
    if isinstance(obj, dict):
        return Bunch((key, bunchify(val)) for key, val in obj.iteritems())
    elif isinstance(obj, (list, tuple)):
        return type(obj)(bunchify(item) for item in obj)
    else:
        return obj

def unbunchify(obj):
    """ Recursively transforms a Bunch into a dictionary.
        
        >>> b = Bunch(foo=Bunch(lol=True), hello=42, ponies='are pretty!')
        >>> unbunchify(b)
        {'ponies': 'are pretty!', 'foo': {'lol': True}, 'hello': 42}
        
        unbunchify will handle intermediary dicts, lists and tuples (as well as
        their subclasses), but ymmv on custom datatypes.
        
        >>> b = Bunch(foo=['bar', Bunch(lol=True)], hello=42, ponies=('are pretty!', Bunch(lies='are trouble!')))
        >>> unbunchify(b)
        {'ponies': ('are pretty!', {'lies': 'are trouble!'}), 'foo': ['bar', {'lol': True}], 'hello': 42}
        
        nb. As dicts are not hashable, they cannot be nested in sets/frozensets.
    """
    if isinstance(obj, dict):
        return dict((key, unbunchify(val)) for key, val in obj.iteritems())
    elif isinstance(obj, (list, tuple)):
        return type(obj)(unbunchify(o) for o in obj)
    else:
        return obj


if __name__ == "__main__":
    import doctest
    doctest.testmod()
