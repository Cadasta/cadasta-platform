# cadasta-platform

[![Build Status](https://travis-ci.com/Cadasta/cadasta-platform.svg?token=3Gq6szrnpvs9ousfkQxj&](https://travis-ci.com/Cadasta/cadasta-platform)

## Install for development

Install:

- [VirtualBox](https://www.virtualbox.org/)
- [Vagrant](https://www.vagrantup.com/)
- [Ansible](http://www.ansible.com/)

Clone the [repository](https://github.com/cadasta/cadasta-platform).

Provision the VM:

```
run vagrant up --provision
```

SSH into to the VM, activate the virtualenv and run the server:

```
vagrant ssh
cd /vagrant/
source env/bin/activate
python app/manage.py runserver
```

Open `http://localhost:5000/` in your browser, you should see a default Django page.
