// X3 sa.c: fixed-K "infeasible" search. K ANDs, operands = XOR of inputs and earlier ANDs (constants are
// irrelevant for spans). Score = deficit = dim(span(1,x,ANDs,T)) - dim(span(1,x,ANDs)); 0 = circuit found.
// Target: x^E in GF(2^n) (E = 2^n-2: inversion), optional output mask OM (which output bits to compute),
// optional AND-depth cap.  usage: sa n K seconds seed [E] [OM] [capAD]
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <math.h>
#include <time.h>
typedef uint64_t u64;
#define W 4
#define MAXK 40
static int n,K,NP,m; static int POLY[]={0,0,7,11,19,37,67,131,0x11B};
static int gmul(int a,int b){int r=0;while(b){if(b&1)r^=a;a<<=1;if(a>>n)a^=POLY[n];b>>=1;}return r;}
typedef struct{u64 w[W];} TT;
static TT X[8], Tg[8], ONE;
static u64 opL[MAXK], opR[MAXK];  // masks over gens: bit j<n input j, bit n+i AND i
static u64 rs=0x1234567; static u64 rnd(void){rs^=rs<<13;rs^=rs>>7;rs^=rs<<17;return rs;}
static int capAD=99;
static int lead(const TT*a){for(int i=0;i<W;i++)if(a->w[i])return i*64+__builtin_ctzll(a->w[i]);return -1;}
static int eval(int *adout){
  TT g[MAXK]; TT bas[64]; int piv[64]; int r=0; int dep[MAXK]; int ad=0;
  #define ADDV(v,cnt) { TT t=v; for(int q=0;q<r;q++) if((t.w[piv[q]>>6]>>(piv[q]&63))&1) for(int z=0;z<W;z++)t.w[z]^=bas[q].w[z]; int l=lead(&t); if(l>=0){bas[r]=t;piv[r]=l;r++;cnt++;} }
  int dummy=0;
  ADDV(ONE,dummy); for(int j=0;j<n;j++)ADDV(X[j],dummy);
  for(int i=0;i<K;i++){ TT a={{0}},b={{0}}; int d=0;
    for(int s=0;s<2;s++){ u64 mk=s?opR[i]:opL[i]; TT*t=s?&b:&a;
      while(mk){int j=__builtin_ctzll(mk); mk&=mk-1; const TT*src=j<n?&X[j]:&g[j-n]; if(j>=n&&dep[j-n]>d)d=dep[j-n]; for(int z=0;z<W;z++)t->w[z]^=src->w[z];}}
    for(int z=0;z<W;z++)g[i].w[z]=a.w[z]&b.w[z]; dep[i]=d+1; if(dep[i]>ad)ad=dep[i];
    ADDV(g[i],dummy); }
  int def=0; for(int o=0;o<m;o++)ADDV(Tg[o],def);
  if(adout)*adout=ad; return def + (ad>capAD? (ad-capAD)*3:0);
}
int main(int argc,char**argv){
  n=atoi(argv[1]);K=atoi(argv[2]);double secs=atof(argv[3]);rs^=strtoull(argv[4],0,10)*0x9E3779B97F4A7C15ULL; for(int i=0;i<10;i++)rnd();
  int E=(1<<n)-2; if(argc>5&&atoi(argv[5])>0)E=atoi(argv[5]); int OM=(1<<n)-1; if(argc>6&&atoi(argv[6])>0)OM=atoi(argv[6]); if(argc>7)capAD=atoi(argv[7]);
  NP=1<<n; memset(X,0,sizeof X);memset(Tg,0,sizeof Tg);memset(&ONE,0,sizeof ONE); m=0; int omap[8];
  for(int o=0;o<n;o++)if((OM>>o)&1)omap[m++]=o;
  for(int x=0;x<NP;x++){int r=1,b=x,ex=E;while(ex){if(ex&1)r=gmul(r,b);b=gmul(b,b);ex>>=1;} int y=x?r:0;
    ONE.w[x>>6]|=1ULL<<(x&63);
    for(int o=0;o<m;o++)if((y>>omap[o])&1)Tg[o].w[x>>6]|=1ULL<<(x&63);
    for(int j=0;j<n;j++)if((x>>j)&1)X[j].w[x>>6]|=1ULL<<(x&63);}
  time_t t0=time(0); int best=99; u64 it=0; int restarts=0;
  while(difftime(time(0),t0)<secs){
    for(int i=0;i<K;i++){u64 mk=(1ULL<<(n+i))-1; opL[i]=rnd()&mk; opR[i]=rnd()&mk; if(i>2){ // sparse-ish init
        opL[i]&=rnd()|rnd(); opR[i]&=rnd()|rnd(); } }
    int ad; int cur=eval(&ad); double Tm=0.35; u64 stall=0;
    while(stall<400000){ it++; if((it&4095)==0&&difftime(time(0),t0)>=secs)break;
      int i=rnd()%K; int s=rnd()&1; u64*p=s?&opR[i]:&opL[i]; u64 old=*p; u64 mk=(1ULL<<(n+i))-1;
      int r=rnd()%10; if(r<7)*p^=1ULL<<(rnd()%(n+i)); else if(r<9){*p^=1ULL<<(rnd()%(n+i));*p^=1ULL<<(rnd()%(n+i));} else *p=rnd()&mk;
      if(*p==0||opL[i]==opR[i]){*p=old;continue;}
      int nw=eval(&ad);
      if(nw<=cur || (double)(rnd()>>11)*(1.0/9007199254740992.0) < exp((cur-nw)/Tm)){ if(nw<cur)stall=0; else stall++; cur=nw; } else {*p=old; stall++;}
      if(cur<best){best=cur; fprintf(stderr,"best deficit %d it %llu restart %d\n",best,(unsigned long long)it,restarts);}
      if(cur==0){ eval(&ad); printf("FOUND n %d K %d E %d OM %d AD %d it %llu:",n,K,E,OM,ad,(unsigned long long)it); for(int q=0;q<K;q++)printf(" (%llx,%llx)",(unsigned long long)opL[q],(unsigned long long)opR[q]); printf("\n"); fflush(stdout); return 0; }
    }
    restarts++;
  }
  printf("NOTFOUND n %d K %d best deficit %d iters %llu restarts %d\n",n,K,best,(unsigned long long)it,restarts);
  return 1;
}
