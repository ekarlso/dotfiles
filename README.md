Development - Getting Started
---------------

- Create a virtual env:
virtualenv bookie

- Enter it:
cd bookie

- Activate VirtualEnv:
  bin/active 

- cd <directory containing this file>

- Install deps:
for req in tools/*-requires; do pip install -r $req; done

- Set it up for development:
python setup.py develop

- Initialize the db:
initialize_bookie_db development.ini#bookie

- Start the server
pserve development.ini


Howto develop:
1. Add ssh key to your account in Gerrit
2. git clone git@github.com:sefsoma/bookie-frontend.git
3. git config remote.origin.pushurl ssh://$USER@home.cloudistic.me:29418/bookie-frontend.git
4. git config remote.origin.push HEAD:refs/for/master

Do you changes, commit them and push to get changes up for review
* git push

You'll get a URL to where the review is and build status
