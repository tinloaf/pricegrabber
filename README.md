PriceGrabber
============

This is a Python package to retrieve prices for specific products from all sorts of websites, such as Amazon, Aliexpress, or price comparison websites.

New websites can be supported by means of a simple configuration entry. Currently supported sites include:

* Geizhals.{de, at}
* Amazon.{de, com, co.uk, probably all)
* Idealo.de
* Aliexpress.com

Usage
-----

Usage is pretty simple. Mostly you should be able to put in an URL to the site of a product you're interested in, and you should get out a price (or a list of prices). Here is an Example for an AliExpress product:

```python
>>> from pricegrabber import Grabber
>>> cfg = {"url": "https://de.aliexpress.com/store/product/Cherry-cherry-shaft-shaft-mx-mechanical-keyboard-shaft-switch-black-shaft-tea-shaft-white-shaft-green/2230037_32682571027.html?spm=a2g0x.12010612.8148356.2.75987786TNUZUO"}
>>> g = Grabber(cfg)
>>> g.grab()
[(8.9, '$')]
```

So in this case we know that the pack of Cherry MX key switches from AliExpress costs $8,90. Note that a list is returned. Some sites may report multiple prices instead of just one.
