// X3 bilc.c: rank<=2 tensors (4x8) per coset of T_b. args: 8 x "pivot:hex" echelon rows of T_b, then mode.
// Output: histogram of coset sizes; cosets with >= MINC tensors are written to stdout as "C class n t1 t2 ...".
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
typedef uint64_t u64; typedef uint32_t u32;
static int piv[8]; static u32 tb[8];
static u32 cls(u32 t){for(int i=0;i<8;i++)if((t>>piv[i])&1)t^=tb[i];return t;}
static int cmp(const void*a,const void*b){u64 x=*(u64*)a,y=*(u64*)b;return x<y?-1:x>y;}
int main(int argc,char**argv){
  for(int i=0;i<8;i++){sscanf(argv[1+i],"%d:%x",&piv[i],&tb[i]);}
  int minc=argc>9?atoi(argv[9]):4;
  size_t cap=35u*65536u; u64*v=malloc(8*cap); size_t nv=0;
  for(int a=1;a<16;a++)for(int b=a+1;b<16;b++){ if((a^b)<b)continue;
    for(u32 l1=0;l1<256;l1++){u32 ta=0;for(int j=0;j<4;j++)if((a>>j)&1)ta|=l1<<(8*j);
      for(u32 l2=0;l2<256;l2++){u32 t=ta;for(int j=0;j<4;j++)if((b>>j)&1)t^=l2<<(8*j); if(!t)continue; v[nv++]=((u64)cls(t)<<32)|t;}}}
  qsort(v,nv,8,cmp); size_t m=0; for(size_t i=0;i<nv;i++)if(i==0||v[i]!=v[i-1])v[m++]=v[i]; nv=m;
  fprintf(stderr,"rank<=2 tensors %zu\n",nv);
  long hist[64]={0}; long ncl=0;
  for(size_t i=0;i<nv;){size_t j=i;while(j<nv&&(v[j]>>32)==(v[i]>>32))j++; int c=j-i; hist[c<63?c:63]++; ncl++;
    if(c>=minc){printf("C %x %d",(u32)(v[i]>>32),c);for(size_t k=i;k<j;k++)printf(" %x",(u32)v[k]);printf("\n");}
    i=j;}
  fprintf(stderr,"cosets %ld; size histogram:",ncl);for(int c=0;c<64;c++)if(hist[c])fprintf(stderr," %d:%ld",c,hist[c]);fprintf(stderr,"\n");
  return 0;}
