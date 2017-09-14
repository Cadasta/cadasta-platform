# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure(2) do |config|
  if Vagrant.has_plugin?("vagrant-proxyconf")
      if ENV["http_proxy"]
          puts "http_proxy: " + ENV["http_proxy"]
          config.proxy.http     = ENV["http_proxy"]
      end
      if ENV["https_proxy"]
          puts "https_proxy: " + ENV["https_proxy"]
          config.proxy.https    = ENV["https_proxy"]
      end
      if ENV["no_proxy"]
          config.proxy.no_proxy = ENV["no_proxy"]
      end
  end

  config.vm.box = "ubuntu/trusty64"
  config.vm.network "forwarded_port", guest: 8000, host: 8000
  config.vm.network "forwarded_port", guest: 5432, host: 5433

  config.vm.provider "virtualbox" do |vb|
    vb.memory = "2048"
    # vb.cpus = 2
  end

  config.vm.provision "ansible" do |ansible|
    # ansible.verbose = "vvv"
    ansible.playbook = "provision/vagrant.yml"
  end

  config.vm.provider :aws do |aws, override|

    aws.tags = {
    'Name' => 'cadasta-platform-dev'
    }
    aws.ami = 'ami-fce3c696' # Ubuntu Server 14.04 LTS (HVM)
    aws.access_key_id = ENV["CADASTA_AWS_ACCESS_KEY_ID"]
    aws.secret_access_key = ENV["CADASTA_AWS_SECRET_ACCESS_KEY"]
    aws.region = "us-east-1"
    aws.instance_type = "t2.micro"
    aws.keypair_name = ENV['CADASTA_PEM_KEY_NAME']
    aws.security_groups = ENV['CADASTA_SECURITY_GROUP']
    # aws.subnet_id = ENV["SUBNET_ID"]
    aws.associate_public_ip = false
    override.ssh.username = 'ubuntu'
    override.ssh.private_key_path = ENV['CADASTA_PEM_KEY_LOCATION']
    override.vm.box = "dummy"
    override.vm.box_url = "https://github.com/mitchellh/vagrant-aws/raw/master/dummy.box"
  end
end
