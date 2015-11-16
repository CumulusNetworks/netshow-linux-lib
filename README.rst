netshow-linux
=============

Netshow-linux is a Provider for
`Netshow <http://github.com/CumulusNetworks/netshow-core>`__, a Network
Abstraction Software. It is optimized to collect core networking data
from Linux devices that contain many interfaces.

Netshow-linux has 2 main modules.

netshowlib
----------

This module contains other modules that are responsible for retrieving
network information from the Linux kernel and associated components.
This information is abstracted in mainly into interface types, like
bonds, bridges, bond members and so on.

netshow
-------

Netshow modules are responsible for printing the network information
collected from the ``netshowlib`` modules. For example, the
``print_iface`` netshow module takes interface information retrieved by
``netshowlib`` modules and abstracted in python objects and prints the
information in a human readable form.

Installation
------------

Netshow is available on Pypi.python.org. Use the newish PIP version like 7.0+ and run

::

    pip install netshow-linux-lib


Documentation
-------------

Developer Documentation can be found on `readthedocs.org
<http://netshow.readthedocs.org>`_. This may move to a
github.io address in the near future.

Contributing
------------

1. Fork it.
2. Create your feature branch (``git checkout -b my-new-feature``).
3. Commit your changes (``git commit -am 'Add some feature'``).
4. Push to the branch (``git push origin my-new-feature``).
5. Create new Pull Request.

License and Authors
-------------------

Author:: Cumulus Networks Inc.

Copyright:: 2015 Cumulus Networks Inc.

.. figure:: http://cumulusnetworks.com/static/cumulus/img/logo_2014.png
   :alt: Cumulus icon

   Cumulus icon

Cumulus Linux
~~~~~~~~~~~~~

Cumulus Linux is a software distribution that runs on top of industry
standard networking hardware. It enables the latest Linux applications
and automation tools on networking gear while delivering new levels of
innovation and ﬂexibility to the data center.

For further details please see:
`cumulusnetworks.com <http://www.cumulusnetworks.com>`__

This project is licensed under the GNU General Public License, Version
2.0
