# install conda
anacaconda=Anaconda3-5.1.0-Linux-x86_64.sh
cd /vagrant
if [[ ! -f $anaconda ]]; then

    wget --quiet https://repo.continuum.io/archive/$anaconda
fi
chmod +x $anaconda
sudo bash ./$anaconda -b -p /opt/anaconda

cat >> /home/vagrant/.bashrc <<EOF
# add for anaconda install
PATH=/opt/anaconda/bin:\$PATH
EOF