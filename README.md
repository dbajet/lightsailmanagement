# lightsailmanagement

AWS LightSail management


# set up
The application is based on Python 3.10.6 (Docker to be added later).

Install the required libraries
```
sudo apt install python3-pip -y 
sudo apt install python3.10-venv -y 
```

Copy the code from GitHub
```
git clone git@github.com:dbajet/lightsailmanagement.git
cd lightsailmanagement
```

Create the necessary `.gitignore`
```
echo ".gitignore" > .gitignore
echo "*__pycache__*" >> .gitignore
echo "*pytest_cache*" >> .gitignore
echo ".coverage" >> .gitignore
echo "pytest.log" >> .gitignore
echo ".mypy_cache" >> .gitignore
echo "env_lightsailmanagement/*" >> .gitignore
echo "secrets/*.*" >> .gitignore

```

Create the environment (within `lightsailmanagement`)
```
python3.10 -m venv --copies ./env_lightsailmanagement
source ./env_lightsailmanagement/bin/activate
pip install -r requirements.txt
```
Add your AWS credentials to the envrionment variables `LIGHTSAIL_ACCOUNT` and `LIGHTSAIL_SECRET`.
For example add at the end of your `~/.bashrc`
```
export LIGHTSAIL_ACCOUNT="..."
export LIGHTSAIL_SECRET="..."
```
And reload it with: `source ~/.bashrc`

All important and secret files should be placed in the `secrets` directory.
For example, the AWS private key will be downloaded there.

### Few commands to consider

Activate the environment 
```
source ./env_lightsailmanagement/bin/activate
```

Run the test, type checks
```
./run_pytest.sh 
./run_mypy.sh 
```

Run the app
```
./run_app.sh servers
./run_app.sh servers --tag "server:web"
./run_app.sh command --tag "server:web" --command "uname -a"
./run_app.sh alerts --tag ""
```

## Set the alarms/alerts
In order to set alarms, create the `secrets/aws_firewall_rules.json` file like
```
[
  {
    "comment": "all servers can be SSHed from 1.2.3.4 only",
    "tagKey": "",
    "tagValue": "",
    "fromPort": 22,
    "toPort": 22,
    "protocol": "tcp",
    "cidrs": [
      "1.2.3.4/32"
    ]
  },
  {
    "comment": "web servers (defined with a key-only tag webServer)",
    "tagKey": "webServer",
    "tagValue": "",
    "fromPort": 80,
    "toPort": 80,
    "protocol": "tcp",
    "cidrs": [
      "0.0.0.0/0"
    ]
  }
]
```
