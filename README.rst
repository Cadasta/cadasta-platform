cadasta-platform
================

|build-status-image|


Install for development
-----------------------

Install:

- `VirtualBox <https://www.virtualbox.org/>`_
- `Vagrant <https://www.vagrantup.com/>`_
- `Ansible <http://www.ansible.com/>`_ (version 2: install with PIP for a recent version)

Clone the `repository <https://github.com/cadasta/cadasta-platform>`_.

Provision the VM::

  vagrant up --provision

SSH into to the VM (this automatically activate the Python virtual
environment) and run the server::

  vagrant ssh
  cd cadasta
  ./runserver

Open ``http://localhost:8000/`` in your browser, you should see the
front page of the platform site.

See the wiki `here <https://devwiki.corp.cadasta.org/Installation>`_ and `here <https://devwiki.corp.cadasta.org/Run%20for%20development>`_) for detailed instructions on installation and running the platform for development.

Run tests
---------

Within the development VM, from the ``/vagrant`` directory run::

  py.test cadasta

To get coverage reports run::

  py.test cadasta --cov=cadasta  --cov-report=html

This creates a HTML report under ``htmlcov``. See `pytest-cov docs <http://pytest-cov.readthedocs.org/en/latest/readme.html#reporting>`_ for other report formats.

AWS Deployment
--------------

Do this::

  vagrant box add dummy https://github.com/mitchellh/vagrant-aws/raw/master/dummy.box
  vagrant plugin install vagrant-aws
  ...

  vagrant up --provider=aws ...


.. |build-status-image| image:: https://secure.travis-ci.org/Cadasta/cadasta-platform.svg?branch=master
   :target: http://travis-ci.org/Cadasta/cadasta-platform?branch=master
