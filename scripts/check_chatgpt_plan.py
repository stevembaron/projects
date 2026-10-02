#!/usr/bin/env python3
"""Read-only model-access check for a SIWC ChatGPT-plan credential record.

No inference, paid API fallback, or credential discovery. Supply the protected
credential record created by the supported Sign in with ChatGPT flow.
"""
import argparse
import json
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--credentials',required=True,type=Path)
    parser.add_argument('--model',default='gpt-6-astra')
    args=parser.parse_args()
    record=json.loads(args.credentials.read_text())
    scopes=record.get('scope', record.get('scopes', []))
    scopes=scopes.split() if isinstance(scopes,str) else scopes
    if 'chatgpt.tokens.use.direct' not in scopes:
        raise SystemExit('Credential record does not confirm ChatGPT plan consent. Complete the supported SIWC flow first.')
    token=record.get('access_token')
    if not isinstance(token,str) or not token.strip():
        raise SystemExit('Missing access token in the supplied SIWC record.')
    request=Request('https://api.openai.com/v1/models',headers={'Authorization':'Bearer '+token.strip()})
    try:
        with urlopen(request,timeout=20) as response:
            catalog=json.load(response)
    except HTTPError as error:
        raise SystemExit(f'Account model check failed (HTTP {error.code}). No inference was attempted.')
    models={m['slug'] for m in catalog.get('models',[]) if m.get('visibility')=='list'}
    if args.model not in models:
        raise SystemExit(f'{args.model} is not listed for this account. No inference was attempted.')
    print(f'{args.model} is listed for this ChatGPT account. This does not verify unattended runner eligibility or token renewal.')

if __name__=='__main__':main()
