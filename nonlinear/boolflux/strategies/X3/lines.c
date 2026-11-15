// X3 lines.c: 3-term relations among top products over a fixed prefix.
// Input: prep file (zprep format; J = span(1, x, prefix)), tensor list (bil_cosets2.txt: members + semi-members).
// Each rank-2 tensor l1(x)lam1 + l2(x)lam2 is realised as the product (l1 + lam2)(l2 + lam1) (gamma = 0).
// g(p) = p mod (J + T).  Reports: rank of all g, number of pairs with g(p) = g(q), number of triples with
// g(p) + g(q) + g(r) = 0, and for each triple-line the number of further points in planes through it (richness).
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
typedef uint64_t u64; typedef struct{u64 w[4];} TT;
static TT J[64],T[8],X[8],Z[8],nb[4],Nb[4]; static int nJ,nT;
static TT E[80]; static int pe[80]; static int ne=0; static TT E1[80]; static int pe1[80]; static int ne1=0; static u64 H1[200000];
static int lead(const TT*a){for(int i=0;i<4;i++)if(a->w[i])return i*64+__builtin_ctzll(a->w[i]);return -1;}
static inline void xr(TT*a,const TT*b){for(int i=0;i<4;i++)a->w[i]^=b->w[i];}
static inline int bit(const TT*a,int p){return (a->w[p>>6]>>(p&63))&1;}
static void red(TT*a){for(int i=0;i<ne;i++)if(bit(a,pe[i]))xr(a,&E[i]);}
static void addE(TT v){red(&v);int l=lead(&v);if(l<0)return;for(int i=0;i<ne;i++)if(bit(&E[i],l))xr(&E[i],&v);E[ne]=v;pe[ne]=l;ne++;}
static void rd(FILE*f,TT*dst,int*cnt,const char*name){char nm[8];int k; if(fscanf(f,"%7s %d",nm,&k)!=2||strcmp(nm,name)){fprintf(stderr,"bad %s\n",name);exit(2);} for(int i=0;i<k;i++)for(int w=0;w<4;w++)if(fscanf(f,"%lx",&dst[i].w[w])!=1)exit(2); if(cnt)*cnt=k;}
static TT comb(const TT*g,int k,unsigned m){TT r={{0}};for(int i=0;i<k;i++)if((m>>i)&1)xr(&r,&g[i]);return r;}
static u64 rs=0x243F6A8885A308D3ULL; static u64 rnd(void){rs^=rs<<13;rs^=rs>>7;rs^=rs<<17;return rs;}
static TT HM[64];
static u64 lh(const TT*a){u64 h=0;for(int b=0;b<64;b++){u64 p=0;for(int i=0;i<4;i++)p^=a->w[i]&HM[b].w[i];h|=(u64)(__builtin_popcountll(p)&1)<<b;}return h;}
#define HS (1<<21)
static u64 hk[HS]; static int hv[HS];
static int hfind(u64 k){unsigned i=(unsigned)(k*0x9E3779B97F4A7C15ULL>>43);while(hk[i]){if(hk[i]==k)return hv[i];i=(i+1)&(HS-1);}return -1;}
static void hput(u64 k,int v){unsigned i=(unsigned)(k*0x9E3779B97F4A7C15ULL>>43);while(hk[i]){if(hk[i]==k)return;i=(i+1)&(HS-1);}hk[i]=k;hv[i]=v;}
int main(int argc,char**argv){
  FILE*f=fopen(argv[1],"r"); rd(f,J,&nJ,"J");rd(f,T,&nT,"T");rd(f,X,0,"X");rd(f,Z,0,"Z");rd(f,nb,0,"n");rd(f,Nb,0,"N"); fclose(f);
  for(int i=0;i<nJ;i++)addE(J[i]); memcpy(E1,E,sizeof E); memcpy(pe1,pe,sizeof pe); ne1=ne; for(int i=0;i<nT;i++)addE(T[i]);
  for(int b=0;b<64;b++)for(int i=0;i<4;i++)HM[b].w[i]=rnd();
  static uint32_t tens[200000]; static u64 H[200000]; int np=0;
  FILE*g=fopen(argv[2],"r"); char line[4096];
  while(fgets(line,sizeof line,g)){ char*p=strtok(line," \n"); int k=0; while(p){ if(k>=3){ tens[np++]=(uint32_t)strtoul(p,0,16);} k++; p=strtok(0," \n"); } }
  fclose(g);
  int lo=argc>3?atoi(argv[3]):0, hi=argc>4?atoi(argv[4]):np; long dup=0, zero=0;
  for(int i=0;i<np;i++){ uint32_t t=tens[i]; unsigned r[4]; for(int j=0;j<4;j++)r[j]=(t>>(8*j))&255;
    unsigned l1=0,l2=0; for(int j=0;j<4;j++){ if(!r[j])continue; if(!l1)l1=r[j]; else if(r[j]!=l1&&!l2)l2=r[j]; }
    unsigned m1=0,m2=0; for(int j=0;j<4;j++){ if(r[j]==l1)m1|=1<<j; else if(r[j]==l2)m2|=1<<j; else if(r[j]==(l1^l2)){m1|=1<<j;m2|=1<<j;} }
    TT A=comb(X,8,l1), B=comb(X,8,l2), la=comb(nb,4,m1), lb=comb(nb,4,m2); xr(&A,&lb); xr(&B,&la);
    TT p; for(int q=0;q<4;q++)p.w[q]=A.w[q]&B.w[q]; {TT p1=p; for(int q=0;q<ne1;q++)if(bit(&p1,pe1[q]))xr(&p1,&E1[q]); H1[i]=lh(&p1);} red(&p); H[i]=lh(&p); if(!H[i]){zero++;continue;} if(hfind(H[i])>=0)dup++; else hput(H[i],i); }
  fprintf(stderr,"points %d, zero classes %ld, duplicate classes %ld, dim(J+T) %d\n",np,zero,dup,ne);
  long tri=0, triT=0; 
  for(int i=lo;i<hi&&i<np;i++){ if(!H[i])continue; for(int j=i+1;j<np;j++){ if(!H[j])continue; int k=hfind(H[i]^H[j]); if(k>j){ tri++; if(H1[i]^H1[j]^H1[k]){ triT++; if(triT<=100000)printf("L %d %d %d  %x %x %x\n",i,j,k,tens[i],tens[j],tens[k]); } } } }
  fprintf(stderr,"range %d-%d: triples with g(p)+g(q)+g(r)=0: %ld\n",lo,hi,tri);
  return 0; }
