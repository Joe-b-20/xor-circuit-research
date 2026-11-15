// X3 zcos.c: coset statistics of top-layer products modulo free junk (Aff + Quad + V0) and the target T.
// Families (arg 1 = bitmask): 1: (l1 + lam_b)(l2 + lam_a), l1,l2 x-forms, {lam_a,lam_b} basis of a plane of n-forms
//   (every product of two forms in span(x, n), mod junk); 2: (l + z) * lam, z != 0 a class-9 quadratic (coordinate
//   form of x^33), lam an n-form;  4: (l + z + lam_b)(l2 + lam_a) restricted to l2 = 0 is family 2 -- not used.
// Output: number of distinct residues per family, histogram of coset sizes (cosets of T); cosets with >= MINC
// residues are printed with one witness product per residue: "C size | fam:opA:opB ...".
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
typedef uint64_t u64; typedef struct{u64 w[4];} TT;
static TT J[64],T[8],X[8],Z[8],nb[4],Nb[4]; static int nJ,nT;
static TT EJ[64]; static int pj[64]; static int ej=0; static TT ET[8]; static int pt[8]; static int et=0;
static int lead(const TT*a){for(int i=0;i<4;i++)if(a->w[i])return i*64+__builtin_ctzll(a->w[i]);return -1;}
static inline void xr(TT*a,const TT*b){for(int i=0;i<4;i++)a->w[i]^=b->w[i];}
static inline int bit(const TT*a,int p){return (a->w[p>>6]>>(p&63))&1;}
static void redJ(TT*a){for(int i=0;i<ej;i++)if(bit(a,pj[i]))xr(a,&EJ[i]);}
static void redT(TT*a){for(int i=0;i<et;i++)if(bit(a,pt[i]))xr(a,&ET[i]);}
static void addE(TT*E,int*p,int*cnt,TT v,int alsoJ){ if(alsoJ)redJ(&v); for(int i=0;i<*cnt;i++)if(bit(&v,p[i]))xr(&v,&E[i]); int l=lead(&v); if(l<0)return; for(int i=0;i<*cnt;i++)if(bit(&E[i],l))xr(&E[i],&v); E[*cnt]=v;p[*cnt]=l;(*cnt)++; }
static u64 h(const TT*a){u64 x=0x9E3779B97F4A7C15ULL; for(int i=0;i<4;i++){x^=a->w[i]; x*=0xBF58476D1CE4E5B9ULL; x^=x>>29; x*=0x94D049BB133111EBULL; x^=x>>32;} return x?x:1;}
typedef struct{u64 hc,hr; uint32_t a,b; int fam;} Rec;
static int cmp(const void*a,const void*b){const Rec*x=a,*y=b; if(x->hc!=y->hc)return x->hc<y->hc?-1:1; if(x->hr!=y->hr)return x->hr<y->hr?-1:1; return 0;}
static void rd(FILE*f,TT*dst,int*cnt,const char*name){char nm[8];int k; if(fscanf(f,"%7s %d",nm,&k)!=2||strcmp(nm,name)){fprintf(stderr,"bad %s\n",name);exit(2);} for(int i=0;i<k;i++)for(int w=0;w<4;w++)if(fscanf(f,"%lx",&dst[i].w[w])!=1)exit(2); if(cnt)*cnt=k;}
static TT comb(const TT*g,int k,unsigned m){TT r={{0}};for(int i=0;i<k;i++)if((m>>i)&1)xr(&r,&g[i]);return r;}
int main(int argc,char**argv){
  FILE*f=fopen(argv[1],"r"); int fam=atoi(argv[2]); int minc=argc>3?atoi(argv[3]):6;
  rd(f,J,&nJ,"J");rd(f,T,&nT,"T");rd(f,X,0,"X");rd(f,Z,0,"Z");rd(f,nb,0,"n");rd(f,Nb,0,"N");
  for(int i=0;i<nJ;i++)addE(EJ,pj,&ej,J[i],0);
  for(int i=0;i<nT;i++)addE(ET,pt,&et,T[i],1);
  fprintf(stderr,"dim J %d, dim T mod J %d\n",ej,et);
  static TT xl[256]; for(unsigned m=0;m<256;m++)xl[m]=comb(X,8,m);
  static TT zl[256]; for(unsigned m=0;m<256;m++)zl[m]=comb(Z,8,m);
  TT nl[16]; for(unsigned m=0;m<16;m++)nl[m]=comb(nb,4,m);
  size_t cap=6000000; Rec*R=malloc(cap*sizeof(Rec)); size_t nr=0;
  #define PUSH(P,F,A,B) { TT q_=P; redJ(&q_); if(lead(&q_)>=0){ Rec r; r.hr=h(&q_); redT(&q_); r.hc=h(&q_); r.a=A;r.b=B;r.fam=F; if(nr<cap)R[nr++]=r; } }
  if(fam&1) for(int a=1;a<16;a++)for(int b=a+1;b<16;b++){ if((a^b)<b)continue;
    for(unsigned l1=0;l1<256;l1++){ TT A=xl[l1]; xr(&A,&nl[b]);
      for(unsigned l2=0;l2<256;l2++){ TT B=xl[l2]; xr(&B,&nl[a]); TT p; for(int i=0;i<4;i++)p.w[i]=A.w[i]&B.w[i]; PUSH(p,1,(l1<<8)|b,(l2<<8)|a); }}}
  size_t n1=nr;
  if(fam&2) for(unsigned z=1;z<256;z++)for(unsigned l=0;l<256;l++){ TT A=zl[z]; xr(&A,&xl[l]); for(int a=1;a<16;a++){ TT p; for(int i=0;i<4;i++)p.w[i]=A.w[i]&nl[a].w[i]; PUSH(p,2,(z<<8)|l,a); }}
  fprintf(stderr,"products with nonzero residue: fam1 %zu fam2 %zu\n",n1,nr-n1);
  qsort(R,nr,sizeof(Rec),cmp);
  size_t m=0; for(size_t i=0;i<nr;i++) if(i==0||R[i].hc!=R[i-1].hc||R[i].hr!=R[i-1].hr) R[m++]=R[i]; nr=m;
  long d1=0,d2=0; for(size_t i=0;i<nr;i++){ if(R[i].fam==1)d1++; else d2++; }
  fprintf(stderr,"distinct residues %zu (first-witness family: fam1 %ld fam2 %ld)\n",nr,d1,d2);
  long hist[64]={0}; long inT=0;
  TT zero={{0}}; u64 hz=h(&zero);
  for(size_t i=0;i<nr;){ size_t j=i; while(j<nr&&R[j].hc==R[i].hc)j++; int c=j-i; if(R[i].hc==hz){inT+=c;} else { hist[c<63?c:63]++;
      if(c>=minc){ printf("C %d |",c); for(size_t k=i;k<j;k++)printf(" %d:%x:%x",R[k].fam,R[k].a,R[k].b); printf("\n"); } }
    i=j; }
  fprintf(stderr,"residues inside T itself: %ld\ncoset size histogram:",inT); for(int c=0;c<64;c++)if(hist[c])fprintf(stderr," %d:%ld",c,hist[c]); fprintf(stderr,"\n");
  return 0; }
