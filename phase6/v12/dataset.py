"""Predeclared source-family split; no recorded human histories are claimed.

Each family contributes distinct malformed programs, never name-only variants.
Histories are reconstructed editing inputs, not a hidden repair oracle.
"""
import hashlib
from pathlib import Path
import re
from phase6.v11.history import reconstruct

ROOT=Path(__file__).resolve().parents[2]
DEVELOPMENT=[
 ('absolute','int absolute(int x){if(x<0){x=0-x;}return x;}'),
 ('countdown','int countdown(int n){int steps=0;while(n>0){n=n-1;steps=steps+1;}return steps;}'),
 ('minimum3','int minimum3(int a,int b,int c){int m=a;if(b<m){m=b;}if(c<m){m=c;}return m;}'),
 ('triangle','int triangle(int n){int sum=0;for(int i=1;i<=n;i++){sum=sum+i;}return sum;}'),
 ('compare','int compare(int a,int b){if(a<b){return -1;}else{if(a>b){return 1;}}return 0;}'),
 ('polynomial','int polynomial(int x){int y=(x+2)*(x-3);return (y+x)*2;}'),
 ('gcd','int gcd(int a,int b){while(b!=0){int r=a%b;a=b;b=r;}return a;}'),
 ('digitcount','int digitcount(int n){int digits=1;while(n>=10){n=n/10;digits=digits+1;}return digits;}'),
]
HELDOUT=[
 ('factorial','int factorial(int n){if(n<0){return 0;}int product=1;for(int k=2;k<=n;k++){product=product*k;}return product;}'),
 ('power','int power(int base,int exponent){int result=1;while(exponent>0){result=result*base;exponent=exponent-1;}return result;}'),
 ('fibonacci','int fibonacci(int n){int a=0;int b=1;for(int i=0;i<n;i++){int next=a+b;a=b;b=next;}return a;}'),
 ('clamp','int clamp(int x,int low,int high){if(low>high){return low;}if(x<low){x=low;}else{if(x>high){x=high;}}return x;}'),
 ('collatz','int collatz(int n){if(n%2==0){n=n/2;}else{n=(3*n)+1;}return n;}'),
 ('lcm','int divisor(int a,int b){while(b){int t=b;b=a%b;a=t;}return a;}int lcm(int x,int y){if(x==0){return 0;}return (x/divisor(x,y))*y;}'),
 ('primality','int primality(int n){if(n<2){return 0;}for(int d=2;d*d<=n;d++){if(n%d==0){return 0;}}return 1;}'),
 ('largestdivisor','int largestdivisor(int n){int best=1;for(int d=2;d<n;d++){if(n%d==0){best=d;}}return best;}'),
 ('alternatingsum','int alternatingsum(int n){int sum=0;int sign=1;for(int i=1;i<=n;i++){sum=sum+sign*i;sign=0-sign;}return sum;}'),
 ('reverse_digits','int reverse_digits(int n){int result=0;while(n>0){result=result*10+n%10;n=n/10;}if(result<0){return 0;}return result;}'),
 ('floor_sqrt','int floor_sqrt(int n){if(n<0){return -1;}int root=0;while((root+1)*(root+1)<=n){root=root+1;}return root;}'),
 ('sum_squares','int sum_squares(int n){int sum=0;for(int i=0;i<n;i++){int square=i*i;if(square>100){break;}sum=sum+square;}return sum;}'),
]


def canonical(source):
    keywords={'int','void','float','if','else','while','for','return','break','continue','char','struct','typedef','const','unsigned','long','sizeof'}
    return re.sub(r'\b[A-Za-z_]\w*\b|\b\d+\b',lambda m:m.group() if m.group() in keywords else 'NUM' if m.group().isdigit() else 'ID',source)


def cases(split):
    families=DEVELOPMENT if split=='development' else HELDOUT if split=='heldout' else []
    if not families:raise ValueError('Use development or heldout')
    rows=[];seen=set()
    for i,(family,good) in enumerate(families):
        positions=[m.start() for m in re.finditer(';',good)]
        # Signature or expression closer, whichever has an explicitly grouped expression.
        close=good.rfind(')') if 'return (' in good else good.index(')')
        inner=good.index('}')
        mutants=[('semicolon',good[:positions[0]]+good[positions[0]+1:],'missing'),
                 ('parenthesis',good[:close]+good[close+1:],'local'),
                 ('block',good[:inner]+good[inner+1:],'misleading' if i%3==0 else 'local'),
                 ('multiple', ''.join(c for j,c in enumerate(good) if j not in set(positions[:2])), 'incomplete' if i%4==0 else 'local')]
        for category,bad,condition in mutants:
            fingerprint=canonical(bad)
            if fingerprint in seen:continue
            seen.add(fingerprint)
            h=None if condition=='missing' else reconstruct(good,bad)
            if condition=='misleading':
                # A different valid candidate may own the last return; compiler validation
                # records whether this reconstructed alternative actually is valid.
                h=reconstruct(bad+'}',bad)
            if condition=='incomplete':h['events'][0]['version']+=1
            rows.append(dict(id=family+'-'+category,family=family,split=split,category=category,history_condition=condition,
                provenance='authored scalar C routine; synthetic token deletion; reconstructed event history',
                source=bad,ground_truth=good,history=h,source_fingerprint=hashlib.sha256(fingerprint.encode()).hexdigest()))
    if split=='heldout':
        for filename in ('C01_null.c','C02_leak.c','C03_double.c','C04_uaf.c'):
            path=ROOT/'phase6/v8/fixtures/c'/filename;good=path.read_bytes().decode('utf-8');bad=good.replace(';','',1)
            rows.append(dict(id='repository-'+filename,family='repository-memory',split=split,category='unsupported-realistic-C',history_condition='local',
                provenance=path.relative_to(ROOT).as_posix()+'; synthetic semicolon deletion, reconstructed history',
                source=bad,ground_truth=good,history=reconstruct(good,bad),source_fingerprint=hashlib.sha256(canonical(bad).encode()).hexdigest()))
    return rows


def manifest():
    dev=cases('development');held=cases('heldout')
    if {r['family'] for r in dev}&{r['family'] for r in held}:raise AssertionError('Family leakage')
    if {r['source_fingerprint'] for r in dev}&{r['source_fingerprint'] for r in held}:raise AssertionError('Normalized source leakage')
    return dict(development=dev,heldout=held)
