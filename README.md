# cadasta-platform

[![Build Status](https://travis-ci.org/Cadasta/cadasta-platform.svg)](https://travis-ci.org/Cadasta/cadasta-platform)

## Install for development

Install:

- [VirtualBox](https://www.virtualbox.org/)
- [Vagrant](https://www.vagrantup.com/)
- [Ansible](http://www.ansible.com/) (version 2: install with PIP for a recent version)

Clone the [repository](https://github.com/cadasta/cadasta-platform).

Provision the VM:

```
vagrant up --provision
```

SSH into to the VM, activate the virtualenv and run the server:

```
vagrant ssh
cd /vagrant/
source /opt/cadasta/env/bin/activate
python cadasta/manage.py runserver
```

Open `http://localhost:5000/` in your browser, you should see a default Django page.

See the wiki ([here](https://github.com/Cadasta/cadasta-platform/wiki/Installation) and [here](https://github.com/Cadasta/cadasta-platform/wiki/Run-for-development)) for detailed instructions on installation and running the platform for development.

## Run tests

Within the development VM, from the `/vagrant` directory run:

```
py.test cadasta
```

To get coverage reports run:

```
py.test cadasta --cov=cadasta  --cov-report=html
```

This creates a HTML report under `htmlcov`. See [pytest-cov docs](http://pytest-cov.readthedocs.org/en/latest/readme.html#reporting) for other report formats.
