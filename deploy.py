#!/usr/bin/env python

from twisted.web import server, resource
from twisted.internet import reactor, protocol
from twisted.python import log
import ConfigParser
import sys, os
import json

# read config file
config = ConfigParser.ConfigParser()
run_dir = os.path.dirname(os.path.realpath(__file__))
config_file = os.path.join(run_dir,"config.ini")
config.read(config_file)
cp = {}
KEY_lookup = {}
for section in config.sections():
    cp[section] = {}
    for key, value in config.items(section):
        cp[section][key] = value
    try:
        KEY_lookup[cp[section]["webhook_url"]] = cp[section]
    except:
        # need to log FIXIT
        pass
# run another process
# 1. git clone
# 2. run deploy

class DeployProcess(protocol.ProcessProtocol):
    def __init__(self,repoinfo,request,payload,step=1,logs=""):
        if logs == "":
            self.log = []
        else:
            self.log = [logs]
        self.repoinfo = repoinfo
        self.request = request
        self.payload = payload
        self.step = step
    def connectionMade(self):
        pass
    def outReceived(self, data):
        self.log.append(data)
        pass
    def errReceived(self, data):
        self.log.append(data)
        pass
    def inConnectionLost(self):
        pass
    def outConnectionLost(self):
        pass
    def errConnectionLost(self):
        pass
    def childConnectionLost(self,fd):
        pass
    def processExited(self, reason):
        pass
    def processEnded(self, reason):
        # fixit check reason
        if self.step is 1:
            # check deploy.sh
            target = self.repoinfo["dist_directory"]
            dp = DeployProcess(self.repoinfo, self.request,
                    self.payload, step=2, logs= "\n".join(self.log))
            print target
            reactor.spawnProcess(dp,
                    "/bin/bash",["/bin/bash","deploy.sh"],
                    path =  target )
            self.request.write("start to run deploy.sh\n")
        else:
            self.request.write("\n".join(self.log))
            self.request.finish()


# web service
class DeployWeb(resource.Resource):
    isLeaf = True
    def render_POST(self, request):
        uri = request.uri[1:]
        if uri not in KEY_lookup:
            request.setResponseCode(404)
            return "Not Found"
        payload = request.content.read()
        #payload = json.loads(request.form['payload'])
        #url = payload['repository']['url']
        repoinfo = KEY_lookup[uri]
        target = repoinfo["dist_directory"]
        print target
        if not os.path.exists(target):
            try:
                os.makedirs(target)
            except:
                # logging FIXIT
                request.setResponseCode(503)
                return "Not Found"
            # git clone
            dp = DeployProcess(repoinfo,request,payload)
            reactor.spawnProcess(dp,
                    "/usr/bin/git",["/usr/bin/git","clone",repoinfo["repo"]], path= target )
                    # uid, gid, usePTY, childFDs
        else:
            print "pull"
            # git pull
            dp = DeployProcess(repoinfo,request,payload)
            reactor.spawnProcess(dp,
                    "/usr/bin/git",["/usr/bin/git","pull"], path = target )
                    # uid, gid, usePTY, childFDs
        request.write("start to run git\n")
        return server.NOT_DONE_YET

site = server.Site(DeployWeb())
if __name__ == '__main__':
    reactor.listenTCP(19001, site)
    reactor.run()
