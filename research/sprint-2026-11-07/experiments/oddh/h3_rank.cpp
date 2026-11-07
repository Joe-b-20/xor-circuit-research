// h=3 exploration: exact rank r of the four-term relations among O = B + {u,v,t}
// over structured sub-domains of helper triples.  Relations: helper + boundary triple
// (w_u+w_v+w_t rows), two helpers + boundary pair (<=3 rows), three helpers + one boundary
// value (<=1 row).  r <= w_u+w_v+w_t + d_uv+d_ut+d_vt + eps.
// Output: rank histogram per sub-domain, maximum, and the profile of the maxima.
// Compile: g++ -O2 -std=c++17 h3_rank.cpp -o h3_rank ; run: ./h3_rank [D1] [D2] [D3]
#include <algorithm>
#include <array>
#include <cassert>
#include <chrono>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <map>
#include <set>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>
using namespace std;
using U=uint64_t; using W=unsigned __int128;
unsigned mul(unsigned a,unsigned b){unsigned r=0;for(;b;b>>=1){if(b&1)r^=a;a<<=1;if(a&256)a^=0x11b;}return r;}
// Gaussian elimination over GF(2) on <=16 rows of 128 bits (fully reduced pivots).
static inline int rank_full(W* rows,int n){W piv[16];int pp[16];int r=0;
 for(int i=0;i<n;i++){W x=rows[i];
  for(int k=0;k<r;k++) if((x>>pp[k])&1) x^=piv[k];
  if(x){U hi=U(x>>64);int p=hi?64+63-__builtin_clzll(hi):63-__builtin_clzll(U(x));
   // eliminate this pivot from existing basis vectors so that later reductions stay valid
   for(int k=0;k<r;k++) if((piv[k]>>p)&1) piv[k]^=x;
   piv[r]=x;pp[r]=p;r++;}
 }
 return r;}
int main(int argc,char**argv){
 set<string> want;for(int i=1;i<argc;i++)want.insert(argv[i]);if(want.empty())want={"D1","D2","D3"};
 const int C[4][4]={{2,3,1,1},{1,2,3,1},{1,1,2,3},{3,1,1,2}};
 array<uint32_t,64>B{};for(int i=0;i<32;i++)B[i]=1u<<i;
 for(int o=0;o<32;o++)for(int i=0;i<32;i++)if((mul(C[o/8][i/8],1u<<(i%8))>>(o%8))&1)B[32+o]|=1u<<i;
 unordered_map<uint32_t,int> Bidx;for(int i=0;i<64;i++)Bidx[B[i]]=i;
 unordered_map<uint32_t,U> P;unordered_map<uint32_t,vector<U>> T;
 for(int i=0;i<64;i++)for(int j=i+1;j<64;j++){uint32_t v=B[i]^B[j];assert(!P.count(v));P[v]=(U(1)<<i)|(U(1)<<j);
  for(int k=j+1;k<64;k++)T[v^B[k]].push_back((U(1)<<i)|(U(1)<<j)|(U(1)<<k));}
 vector<uint32_t> rep,full,tv;for(auto&[v,L]:T){tv.push_back(v);if(L.size()>=2)rep.push_back(v);if(L.size()==3)full.push_back(v);}
 sort(rep.begin(),rep.end());sort(full.begin(),full.end());sort(tv.begin(),tv.end());
 assert(rep.size()==440&&full.size()==80&&tv.size()==41144);
 const W HU=W(1)<<64,HV=W(1)<<65,HT=W(1)<<66;
 auto rk=[&](uint32_t u,uint32_t v,uint32_t t,int* prof)->int{W rows[16];int n=0;
  auto add=[&](const vector<U>& L,W hb){for(U f:L)rows[n++]=W(f)|hb;};
  auto it=T.find(u);int wu=0,wv=0,wt=0;if(it!=T.end()){wu=it->second.size();add(it->second,HU);}
  it=T.find(v);if(it!=T.end()){wv=it->second.size();add(it->second,HV);}
  it=T.find(t);if(it!=T.end()){wt=it->second.size();add(it->second,HT);}
  int duv=0,dut=0,dvt=0,eps=0;auto p=P.find(u^v);if(p!=P.end()){duv=1;rows[n++]=W(p->second)|HU|HV;}
  p=P.find(u^t);if(p!=P.end()){dut=1;rows[n++]=W(p->second)|HU|HT;}
  p=P.find(v^t);if(p!=P.end()){dvt=1;rows[n++]=W(p->second)|HV|HT;}
  auto b=Bidx.find(u^v^t);if(b!=Bidx.end()){eps=1;rows[n++]=(W(1)<<b->second)|HU|HV|HT;}
  if(prof){prof[0]=wu;prof[1]=wv;prof[2]=wt;prof[3]=duv+dut+dvt;prof[4]=eps;}
  return rank_full(rows,n);};
 auto run=[&](const string& name,auto&& gen){
  auto t0=chrono::steady_clock::now();map<int,long long>hist;long long cnt=0;int mx=0;map<array<int,5>,long long>maxprof;
  gen([&](uint32_t u,uint32_t v,uint32_t t){int prof[5];int r=rk(u,v,t,prof);hist[r]++;cnt++;
   if(r>mx){mx=r;maxprof.clear();}if(r==mx)maxprof[{prof[0],prof[1],prof[2],prof[3],prof[4]}]++;});
  double s=chrono::duration<double>(chrono::steady_clock::now()-t0).count();
  cout<<"{\"domain\":\""<<name<<"\",\"triples\":"<<cnt<<",\"seconds\":"<<s<<",\"rank_hist\":{";bool c=false;
  for(auto[r,m]:hist){if(c)cout<<',';c=true;cout<<'"'<<r<<"\":"<<m;}cout<<"},\"max_rank\":"<<mx<<",\"max_profiles_(wu,wv,wt,sum_delta,eps):count\":[";c=false;
  for(auto&[pf,m]:maxprof){if(c)cout<<',';c=true;cout<<"[["<<pf[0]<<','<<pf[1]<<','<<pf[2]<<','<<pf[3]<<','<<pf[4]<<"],"<<m<<']';}cout<<"]}"<<endl;};
 unordered_set<uint32_t> Bset(B.begin(),B.end());
 if(want.count("D1")) run("D1: all 3-subsets of the 440 repeated values (w>=2)",[&](auto&& f){
  for(size_t i=0;i<rep.size();i++)for(size_t j=i+1;j<rep.size();j++)for(size_t k=j+1;k<rep.size();k++)f(rep[i],rep[j],rep[k]);});
 if(want.count("D2")) run("D2: (u,v) both full x t any boundary-triple value (w_t>=1)",[&](auto&& f){
  for(size_t i=0;i<full.size();i++)for(size_t j=i+1;j<full.size();j++)for(uint32_t t:tv){if(t==full[i]||t==full[j])continue;f(full[i],full[j],t);}});
 if(want.count("D3")) run("D3: (u,v) both repeated x t adjacent to u (t=u+boundary pair)",[&](auto&& f){
  for(size_t i=0;i<rep.size();i++)for(size_t j=0;j<rep.size();j++){if(i==j)continue;for(auto&[p,pf]:P){uint32_t t=rep[i]^p;if(t==rep[j]||Bset.count(t))continue;f(rep[i],rep[j],t);}}});
 if(want.count("D4")) run("D4: (u,v) both full x t adjacent to both (t=u+p, v+t also a pair value)",[&](auto&& f){
  for(size_t i=0;i<full.size();i++)for(size_t j=0;j<full.size();j++){if(i==j)continue;for(auto&[p,pf]:P){uint32_t t=full[i]^p;if(t==full[j]||Bset.count(t))continue;if(P.count(t^full[j]))f(full[i],full[j],t);}}});
 return 0;
}
