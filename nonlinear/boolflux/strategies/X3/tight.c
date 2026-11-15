// X3 tight.c: exhaustive search for circuits of the "tight" shape for x -> x^-1 in GF(2^n), n <= 6:
//   L "low" ANDs (any products of affine forms of earlier values), then M "top" ANDs, each of which
//   must lie in V_L + T (V_L = span(1, x, low ANDs), T = span of the n outputs).  Operands of every AND:
//   any affine combination of inputs and ALL earlier ANDs (low and top).  With M = n (slack 0) the
//   restriction "top AND in V_L + T" is forced (if the low ANDs do not help span T), see NOTES.
// usage: tight n L M [maxprint] [first_lo first_hi]  (restrict the index of the first AND's pair for splitting)
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
typedef uint64_t u64;
static int n, L, M, K, NP; static u64 FULL;
static int POLY[] = {0,0,7,11,19,37,67};
static int gmul(int a,int b){int r=0;while(b){if(b&1)r^=a;a<<=1;if(a>>n)a^=POLY[n];b>>=1;}return r;}
static u64 T[8];           // output truth tables
static u64 gen[16];        // generators mod const: x_1..x_n, then ANDs
static int opa[16], opb[16]; // chosen operand masks (over gens so far)
static u64 lvl[20]; static u64 found=0, nodes=0; static int maxprint=5; static int dep[16]; static u64 hist[16]; static u64 firstcnt[1<<12];
// echelon basis helper
typedef struct { u64 v[40]; int r; } Ech;
static u64 red(const Ech*e,u64 x){for(int i=0;i<e->r;i++){u64 p=e->v[i]&-e->v[i]; if(x&p)x^=e->v[i];}return x;}
static int add(Ech*e,u64 x){x=red(e,x);if(!x)return 0;u64 p=x&-x;for(int i=0;i<e->r;i++)if(e->v[i]&p)e->v[i]^=x; e->v[e->r++]=x;return 1;}
static int FA=0,FB=0,RND=0; static long CLO=0,CHI=1L<<60; static u64 rs=88172645463325252ULL; static u64 rnd(void){rs^=rs<<13;rs^=rs>>7;rs^=rs<<17;return rs;}
static Ech VT; // V_L + T (fixed during the top phase)
static void printsol(void){
  printf("SOL");
  for(int i=0;i<K;i++)printf(" (%x,%x)",opa[i],opb[i]);
  printf("\n");
}
static void rec(int i){ // choose AND i (0-based); gens count = n+i
  int d=n+i; nodes++; lvl[i]++; if(getenv("COUNTONLY")&&i==L)return;
  Ech V; V.r=0; add(&V,FULL); for(int j=0;j<d;j++)add(&V,gen[j]);
  if(i==L){ VT=V; for(int o=0;o<n;o++)add(&VT,T[o]); }
  if(i==K){ int ok=1; for(int o=0;o<n;o++) if(red(&V,T[o])){ok=0;break;}
    if(ok){found++; int ad=0; for(int j=0;j<K;j++){int dd=0; for(int g=n;g<n+j;g++) if(((opa[j]|opb[j])>>g)&1){ if(dep[g-n]>dd)dd=dep[g-n]; } dep[j]=dd+1; if(dep[j]>ad)ad=dep[j];} hist[ad]++; firstcnt[opa[0]*64+opb[0]]++; if(found<=(u64)maxprint || (ad<=n-2 && hist[ad]<=3)){printf("AD%d ",ad);printsol();}} return; }
  // quick bound: remaining ANDs must cover deficit
  { Ech W=V; int def=0; for(int o=0;o<n;o++)def+=add(&W,T[o]); if(def>K-i)return; }
  int S=1<<d; u64 *tab=malloc(sizeof(u64)*S); tab[0]=0;
  for(int m=1;m<S;m++){int b=__builtin_ctz(m); tab[m]=tab[m&(m-1)]^gen[b];}
  if(i==0 && FA){ opa[0]=FA;opb[0]=FB;gen[d]=tab[FA]&tab[FB]; rec(1); free(tab); return; }
  if(RND && i<L){ for(int t=0;t<RND;t++){ int a=1+rnd()%(S-1), b=1+rnd()%(S-1); if(a==b)continue; u64 p=tab[a]&tab[b]; if(!red(&V,p))continue; opa[i]=a;opb[i]=b;gen[d]=p; rec(i+1);} free(tab); return; }
  for(int a=1;a<S;a++) for(int b=a+1;b<S;b++){
    if((a^b)<b) continue;            // canonical basis of the 2-subspace: a < b < a^b
    u64 p=tab[a]&tab[b];
    if(i==1){ static long idx=0; long me=idx++; if(me<CLO||me>=CHI) continue; }
    if(i>=L){ if(red(&VT,p)) continue; }
    if(!red(&V,p)) continue;         // adds nothing
    opa[i]=a;opb[i]=b;gen[d]=p; rec(i+1);
  }
  free(tab);
}
int main(int argc,char**argv){
  n=atoi(argv[1]);L=atoi(argv[2]);M=atoi(argv[3]);K=L+M; if(argc>4)maxprint=atoi(argv[4]); if(argc>6){FA=atoi(argv[5]);FB=atoi(argv[6]);} if(argc>7)RND=atoi(argv[7]); if(getenv("CLO"))CLO=atol(getenv("CLO")); if(getenv("CHI"))CHI=atol(getenv("CHI")); if(argc>8)rs^=strtoull(argv[8],0,10)*0x9E3779B97F4A7C15ULL;
  NP=1<<n; FULL=(NP==64)?~0ULL:((1ULL<<NP)-1);
  for(int o=0;o<n;o++)T[o]=0; for(int j=0;j<n;j++)gen[j]=0;
  for(int x=0;x<NP;x++){int y=x; for(int e=0;e<n-2;e++){ /* y = x^(2^n-2) */ } 
    int r=1,b=x; int ex=(1<<n)-2; while(ex){if(ex&1)r=gmul(r,b);b=gmul(b,b);ex>>=1;} y=x?r:0;
    for(int o=0;o<n;o++)if((y>>o)&1)T[o]|=1ULL<<x;
    for(int j=0;j<n;j++)if((x>>j)&1)gen[j]|=1ULL<<x;}
  rec(0);
  for(int a=0;a<16;a++)if(hist[a])printf("AD %d: %llu\n",a,(unsigned long long)hist[a]);
  {int c=0,z=0; for(int a=1;a<NP;a++)for(int b=a+1;b<NP;b++){ if((a^b)<b)continue; z++; if(firstcnt[a*64+b])c++;} printf("first ANDs (2-subspaces) with a completion: %d of %d\n",c,z);}
  for(int a=0;a<=K;a++)printf("level %d nodes %llu\n",a,(unsigned long long)lvl[a]);
  printf("n %d L %d M %d found %llu nodes %llu\n",n,L,M,(unsigned long long)found,(unsigned long long)nodes);
  return 0;
}
