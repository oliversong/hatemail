import sys, logging

activate_this = '/home/ec2-user/hatemail/venv/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

sys.path.insert(0,'/home/ec2-user/hatemail')
sys.path.insert(1,'/home/ec2-user')

logging.basicConfig(stream=sys.stderr)

from badassery import app as application
