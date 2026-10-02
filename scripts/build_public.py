"""Stage only public website assets, preserving the repository's other sites."""
from pathlib import Path
import shutil
ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {'.html','.css','.js','.mjs','.json','.png','.jpg','.jpeg','.gif','.svg','.webp','.ico','.woff','.woff2','.ttf','.pdf','.mp4','.mp3','.webmanifest','.txt','.ics'}


def build(root=ROOT):
    target = root/'_site'
    if target.exists():
        shutil.rmtree(target)
    target.mkdir()
    sites = [p for p in root.iterdir() if p.is_dir() and not p.name.startswith(('.', '_')) and (p/'index.html').is_file()]
    for site in sites + ([root/'assets'] if (root/'assets').exists() else []):
        for p in site.rglob('*'):
            if p.is_symlink() or not p.is_file() or any(part.startswith('.') for part in p.relative_to(root).parts) or p.suffix.lower() not in ALLOWED:
                continue
            out=target/p.relative_to(root);out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,out)
    for name in ['index.html','CNAME','robots.txt','favicon.ico']:
        p=root/name
        if p.is_file() and not p.is_symlink():shutil.copy2(p,target/name)
    (target/'.nojekyll').touch()
    return target

if __name__=='__main__':
    print(build())
