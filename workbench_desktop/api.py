import json
import requests
import semver


def send_snapshot(domain, snapshot):
    URL_upload = "https://" + domain + "/usodybeta/lives/"
    post_headers = {'Content-type': 'application/json'}
    snapshot_json = json.dumps(snapshot, indent=2)
    try:
        response = requests.post(URL_upload, data=snapshot_json, headers=post_headers)
        if response.status_code == 201:
            return 0
        else:
            return -1
    except:
        return -1


def get_license(domain, version, language):
    URL_license = "https://" + domain + "/usodybeta/licences/"
    try:
        response = requests.get(URL_license)
        if response.status_code == 200:
            licenses = json.loads(response.json())
            for license in licenses:
                if semver.compare(license["WorkbenchDesktopVersion"], version) == 0 and license["Language"] == language:
                    last_license = license
            return last_license
        else:
            return "Can't retrieve valid license"
    except:
        return "Can't communicate with the license server"
