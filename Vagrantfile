# -*- mode: ruby -*-
# vi: set ft=ruby :

# All Vagrant configuration is done below. The "2" in Vagrant.configure
# configures the configuration version (we support older styles for
# backwards compatibility). Please don't change it unless you know what
# you're doing.
Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/xenial64"
  config.vm.network "private_network", ip: "192.168.33.10"
  config.vm.network "forwarded_port", guest: 8888, host: 8899, auto_correct: true
  config.vm.synced_folder "shared", "/home/vagrant/shared"

  # Provider-specific configuration so you can fine-tune various
  # backing providers for Vagrant. These expose provider-specific options.
  # Example for VirtualBox:
  #
  config.vm.provider "virtualbox" do |vb|
    vb.name = "Hackaton-RTT-ML"
    vb.gui = false
    #
    #   # Customize the amount of memory on the VM:
    vb.memory = 1024
    vb.cpus = 2
    vb.customize ["modifyvm", :id, "--cpuexecutioncap", "50"]

  end
  #
  # View the documentation for the provider you are using for more
  # information on available options.

  # Enable provisioning with a shell script. Additional provisioners such as
  # Puppet, Chef, Ansible, Salt, and Docker are also available. Please see the
  # documentation for more information about their specific syntax and use.
  config.vm.provision "shell", inline: <<-SHELL
     apt-get update
#     apt-get install -y -f tshark
     apt-get install gdb
     apt-get install -y gnuplot
     apt-get install -y iperf3 nginx aria2
     apt-get install -y libpython2.7

     apt-get install -y python-nfqueue
     apt-get install -y scapy

     apt-get install -y python-pip
     git clone git://github.com/mininet/mininet
     mininet/util/install.sh -nfv

  SHELL

  config.vm.provision "shell", path: "shared/anaconda.sh"

end
