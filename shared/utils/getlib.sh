
GIT=/workspace/git/ejogarv/MASTER
LIB_PATH=$GIT/cdpi-main/scons_build/linux_x86_64.test-oscryp_1.1.0c/NSDcanalyzer/lib/out/libcdpi.so
rm epg/libcdpi.so ; rsync -avz --append-verify --progress ejogarv@eselnts1523.mo.sw.ericsson.se:$LIB_PATH /vagrant_data/dpisim/epg
