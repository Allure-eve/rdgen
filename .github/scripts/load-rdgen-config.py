"""Load a small standalone build configuration without the RDGen web service."""
import base64,json,os,pathlib,re,shutil,uuid

def prepare(config, icon=False):
    required=['server','key']
    for name in required:
        if not config.get(name):raise ValueError('Missing configuration: '+name)
    server=str(config['server'])
    if not re.fullmatch(r'[A-Za-z0-9.-]+',server):raise ValueError('server must be an IPv4 address or hostname, without port or scheme')
    key=str(config['key'])
    if len(base64.b64decode(key,validate=True))!=32:raise ValueError('key must be the 32-byte RustDesk server public key in Base64')
    port=int(config.get('serverPort',21116))
    if not 1024<=port<=65532:raise ValueError('Invalid serverPort')
    appid=str(config.get('androidappid','fun.y1s1.rustdesk'))
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*){2,}',appid):raise ValueError('Invalid Android application ID')
    name=str(config.get('appname','HomeRemote'));filename=str(config.get('filename','home-remote'))
    if not re.fullmatch(r'[A-Za-z0-9_-]+',name):raise ValueError('Use ASCII letters, numbers, underscore or hyphen for appname')
    if not re.fullmatch(r'[A-Za-z0-9_-]+',filename):raise ValueError('Invalid filename')
    custom=config.get('custom',{})
    if not isinstance(custom,dict):raise ValueError('custom must be a JSON object')
    custom={'app-name':name,'default-settings':{},'override-settings':{},**custom}
    # Server fields are embedded separately in the RustDesk source. Keep all
    # passwords/advanced settings in the Base64 JSON instead of shell literals.
    encoded=base64.b64encode(json.dumps(custom,ensure_ascii=True).encode()).decode()
    return {'server':server,'serverPort':str(port),'key':key,'apiServer':'',
            'appname':name,'filename':filename,'androidappid':appid,'custom':encoded,
            'compname':'Home','urlLink':'https://rustdesk.com','downloadLink':'https://rustdesk.com/download',
            'iconlink_url':'local' if icon else 'false','delayFix':'false','xOffline':'false',
            'hidecm':'false','removeNewVersionNotif':'false','update_public_key':''}

def main():
    version=os.environ.get('BUILD_VERSION','')
    if not re.fullmatch(r'(?:master|\d+\.\d+\.\d+(?:[-.][A-Za-z0-9]+)*)',version):raise ValueError('Choose a RustDesk release tag or master')
    icon=pathlib.Path('.github/assets/rdgen-icon.png')
    if icon.exists():
        if icon.read_bytes()[:8]!=b'\x89PNG\r\n\x1a\n':raise ValueError('Custom icon must be a PNG')
        shutil.copyfile(icon,pathlib.Path(os.environ['RUNNER_TEMP'])/'rdgen-icon.png')
    config=prepare(json.loads(os.environ['BUILD_CONFIG_JSON']),icon.exists())
    with open(os.environ['GITHUB_ENV'],'a',encoding='utf-8') as f:
        for name,value in config.items():
            escaped=value.replace('%','%25').replace('\r','%0D').replace('\n','%0A')
            if value:print('::add-mask::'+escaped)
            marker='RDGEN_'+uuid.uuid4().hex
            f.write(name+'<<'+marker+'\n'+value+'\n'+marker+'\n')
    print('Standalone build configuration loaded; no generator callbacks configured.')

if __name__=='__main__':main()
