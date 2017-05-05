cadasta-platform
================

|Build Status|

Install for development
~~~~~~~~~~~~~~~~~~~~~~~

-  `VirtualBox <https://www.virtualbox.org/>`__
-  `Vagrant <https://www.vagrantup.com/>`__
-  `Ansible <https://www.ansible.com/>`__

For Linux
~~~~~~~~~

::

      sudo apt-get update
      sudo apt-get install virtualbox
      sudo apt-get install dkms
      sudo apt-get install vagrant
      pip install ansible

dkms (optional): "Ubuntu/Debian users might want to install the dkms
package to ensure that the VirtualBox host kernel modules (vboxdrv,
vboxnetflt and vboxnetadp) are properly updated if the linux kernel
version changes during the next apt-get upgrade." In case , your are
behind proxy or facing connection timed out issue while installing you
should switch to pip3 8.2.1 + version for installing development
environment.

For Macs
~~~~~~~~

::

      brew cask install virtualbox
      brew cask install vagrant
      brew cask install vagrant-manager
      pip install --user --upgrade ansible

Vagrant-Manager helps you manage all your virtual machines in one place
directly from the menubar.

For Windows
~~~~~~~~~~~

You can download setup files for
`VirtualBox <https://www.virtualbox.org/wiki/Downloads>`__ and
`Vagrant <https://www.vagrantup.com/downloads.html>`__ respectively and
run it. Setup wizard is straightforward, just it will ask to accept
license agreement and the path to install, as you will need to use
command line. Windows isn’t supported for the control machine. Go
through ansible
`docs <http://docs.ansible.com/ansible/intro_windows.html>`__.
`Here <https://www.jeffgeerling.com/blog/running-ansible-within-windows>`__
is the steps for getting ansible running on Windows:

-  Download and install `Cygwin <http://cygwin.com/install.html>`__,
   with at least the following packages selected (you can select the
   packages during the install process):

   -  curl
   -  python (2.7.x)
   -  python-jinja
   -  python-crypto
   -  python-openssl
   -  python-setuptools
   -  git (1.7.x)
   -  vim
   -  openssh
   -  openssl
   -  openssl-devel

-  If you are working behind a proxy (as is the case in many corporate
   networks), edit the .bash\_profile used by Cygwin either using vim
   (open Cygwin and enter ``vim .bash_profile``), or with whatever
   editor you'd like, and add in lines like the following:

   ::

       export http_proxy=http://username:password@proxy-address-here:80/
       export https_proxy=https://username:password@proxy-address-here:80/

-  Download and install
   `PyYAML <https://pypi.python.org/pypi/PyYAML/3.10>`__ and
   `Jinja2 <https://pypi.python.org/pypi/Jinja2/2.6>`__ separately, as
   they're not available via Cygwin's installer:

   -  Open Cygwin
   -  Download PyYAML:

      ::

          curl -O https://pypi.python.org/packages/source/P/PyYAML/PyYAML-3.10.tar.gz

   -  Download Jinja2:


      ::

          curl -O https://pypi.python.org/packages/source/J/Jinja2/Jinja2-2.6.tar.gz

* `VirtualBox <https://www.virtualbox.org/>`_
    * Version 5.0.x
* `Vagrant <https://www.vagrantup.com/>`_
    * Version 1.8.1
    * If you are behind a proxy, you may need to install and configure the `vagrant-proxyconf <https://rubygems.org/gems/vagrant-proxyconf/versions/1.5.2>`_ plugin
* `Ansible <http://www.ansible.com/>`_
    * Version 2.1.3.0
    * For Linux and Mac, install Ansible 2 via pip
    * For Windows (unsupported), go through `Ansible Documentation <http://docs.ansible.com/ansible/intro_windows.html>`_ or this `blog <https://www.jeffgeerling.com/blog/running-ansible-within-windows>`_

Clone the `repository <https://github.com/cadasta/cadasta-platform>`_ to your local machine and enter the cadasta-platform directory.
Run the following commands to access the virtual machine.

Provision the VM::

   -  Untar both downloads:

      ::

          tar -xvf PyYAML-3.10.tar.gz && tar -xvf Jinja2-2.6.tar.gz

   -  Change directory into each of the expanded folders and run
      ``python setup.py install`` to install each package.
   -  Generate an SSH key for use later: ``ssh-keygen``, then hit enter
      to skip adding a password until you get back to the command
      prompt.
   -  Clone ansible from its repository on GitHub:

      ::

          git clone https://github.com/ansible/ansible /opt/ansible

-  If you'd like to work from a particular Ansible version (like 2.0.1,
   current as of this writing), change directory into ``/opt/ansible``
   and checkout the correct tag: ``git checkout v2.0.1`` (some users
   have also reported success with the tag ``v2_final``).

-  Add the following lines into your Cygwin ``.bash_profile`` (like you
   did the proxy settings—if you're behind one—in step 2):

   ::

           # Ansible settings
           ANSIBLE=/opt/ansible
           export PATH=$PATH:$ANSIBLE/bin
           export PYTHONPATH=$ANSIBLE/lib
           export ANSIBLE_LIBRARY=$ANSIBLE/library

-  At this point, you should be able to run ansible commands via Cygwin
   (once you restart, or enter ``source ~/.bash_profile`` to pick up the
   settings you just added). Try ``ansible --version`` to display
   Ansible's version.

If you using Windows 10's Subsystem for Linux refer to this
`blog <https://www.jeffgeerling.com/blog/2017/using-ansible-through-windows-10s-subsystem-linux>`__

Clone the `repository <https://github.com/Cadasta/cadasta-platform>`__
to your local machine and enter that directory. After cloning it go
inside to cadasta-platform directory and run below command to provision
the virtual machine. Provision the VM:

::

    vagrant up --provision


SSH into to the VM (this automatically activates the Python virtual
environment):

SSH into the VM (automatically activates the Python virtual environment)::


::


    vagrant ssh

Open ``http://localhost:8000/`` in your local machine's browser. This will forward you to the web server port on the VM and you should see the front page of the platform site.


Enter the cadasta directory and start the server:

::

    cd cadasta
    ./runserver

Open http://localhost:8000/ in your local machine's browser, this will
forward you to the port on the VM and you should see the front page of
the platform site.

See the wiki ( `here <https://devwiki.corp.cadasta.org/Installation>`__
and `here <https://devwiki.corp.cadasta.org/Run%20for%20development>`__)
for detailed instructions on installation and running the platform for
development.

Run tests
~~~~~~~~~

Within the development VM, from the ``/vagrant`` directory run:

::

    py.test cadasta

To get coverage reports run:

::

    py.test cadasta --cov=cadasta  --cov-report=html

This creates a HTML report under ``htmlcov``. See `pytest-cov
docs <http://pytest-cov.readthedocs.io/en/latest/readme.html#reporting>`__
for other report formats.

AWS Deployment
~~~~~~~~~~~~~~

Do this:

::

    vagrant box add dummy https://github.com/mitchellh/vagrant-aws/raw/master/dummy.box
    vagrant plugin install vagrant-aws
    ...

    vagrant up --provider=aws ...

Acknowledgements
~~~~~~~~~~~~~~~~

+----------------------------------------------------+------------------------------------+------------------------------------------+
| |Browserstack|                                     | |Opbeat|                           | |Travis CI|                              |
+====================================================+====================================+==========================================+
| `BrowserStack <https://www.browserstack.com/>`__   | `Opbeat <https://opbeat.com/>`__   | `Travis CI <https://travis-ci.com/>`__   |
+----------------------------------------------------+------------------------------------+------------------------------------------+

.. |Build Status| image:: https://travis-ci.org/Cadasta/cadasta-platform.svg?branch=master
   :target: https://travis-ci.org/Cadasta/cadasta-platform
.. |Browserstack| image:: https://avatars0.githubusercontent.com/u/1119453?v=3&s=144
   :target: https://www.browserstack.com/
.. |Opbeat| image:: https://avatars1.githubusercontent.com/u/1669860?v=3&s=144
   :target: https://opbeat.com/
.. |Travis CI| image:: https://avatars2.githubusercontent.com/u/639823?v=3&s=144
   :target: https://travis-ci.com/
