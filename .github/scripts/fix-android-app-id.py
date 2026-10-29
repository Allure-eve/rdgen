"""Keep generated R in the Kotlin namespace; customize installation ID only."""
import os,pathlib,re

def patch(text,appid):
    namespace=r'(?m)^(\s*namespace\s*(?:=\s*)?)["\'][^"\']+["\']'
    result,count=re.subn(namespace,lambda m:m[1]+'"com.carriez.flutter_hbb"',text)
    if count!=1:raise ValueError('Expected exactly one namespace declaration')
    application=r'(?m)^(\s*applicationId\s*(?:=\s*)?)["\'][^"\']+["\']'
    result,count=re.subn(application,lambda m:m[1]+'"'+appid+'"',result)
    if count!=1:raise ValueError('Expected exactly one applicationId declaration')
    return result

if __name__=='__main__':
    appid=os.environ['androidappid']
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*){2,}',appid):raise ValueError('Invalid Android application ID')
    path=pathlib.Path('flutter/android/app/build.gradle')
    path.write_text(patch(path.read_text(),appid))
    print('Application ID updated; Kotlin resource namespace retained.')
