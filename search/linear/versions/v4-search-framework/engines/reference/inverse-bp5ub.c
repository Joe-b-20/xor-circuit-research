/* Randomized Boyar-Peralta-style SLP search for the 32 AES InvMixColumns targets.
 * TGT[32] = spec/invmc_target_masks.json (rows_sha256 b9c0cd9a...); ported 2026-09-08 from
 * slp-plateau-search/fleet10/cleanroom/work/ (forward MixColumns). No other edits.
 *
 * State: base S of 32-bit masks (starts as the 32 unit vectors).
 * d[t] = exact minimum number of S-elements whose XOR is target t.
 * Step: consider every pair sum u = S_i ^ S_j not already in S; score by the
 * total of new distances sum_t min(d[t], dist_S(t^u)+1); pick the best
 * (random among ties, optional norm tie-break). In symmetric mode the pick
 * also adds rot8/16/24 of u (parents are the rotations of the parents, which
 * are present by induction), and scoring uses min over the 4 rotations.
 * Distance queries are bounded: to improve d[t] we only need to know whether
 * dist_S(t^u) <= d[t]-2, which keeps queries cheap (hash of S, hash of pair
 * sums, then 3-sums / 4-sums / 5-sums by iteration only when the bound asks).
 *
 * Usage: ./bp seed mode(0=asym,1=sym) norm_mode(0=none,1=max,2=min) time_s out.json
 * Runs restarts until the monotonic deadline; writes best circuit (index pairs,
 * dead gates pruned) to out.json whenever improved. Prints progress lines.
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#define NT 32
#define MAXS 4096

static uint32_t TGT[NT] = {
560046560u,1654842145u,3292907075u,2850762087u,1924594222u,3832345692u,3369658552u,2427506800u,
1637998625u,2732794210u,1170621380u,3945621417u,3069849202u,1827953892u,3639130312u,2966450320u,
2715820385u,3810615970u,3326329925u,761768427u,4197348022u,4099728492u,3904424152u,3497038000u,
3760284065u,560112355u,1136936390u,1739189037u,779269882u,1558473972u,3100170472u,1888530640u};

static inline uint32_t rotl(uint32_t x, int r){ return (x<<r)|(x>>(32-r)); }

/* xorshift rng */
static uint64_t rng_s;
static inline uint64_t rnd(void){ uint64_t x=rng_s; x^=x<<13; x^=x>>7; x^=x<<17; return rng_s=x; }
static inline uint32_t rndn(uint32_t n){ return (uint32_t)(rnd()%n); }

/* ---- hash sets (open addressing, power-of-2) ---- */
#define HB 17
#define HSZ (1u<<HB)
#define HMASK (HSZ-1)
typedef struct { uint32_t key[HSZ]; uint8_t used[HSZ]; } HSet;
static inline uint32_t hsh(uint32_t x){ x*=0x9E3779B1u; x^=x>>16; x*=0x85EBCA6Bu; x^=x>>13; return x&HMASK; }
static inline void hs_clear(HSet*h){ memset(h->used,0,HSZ); }
static inline void hs_add(HSet*h, uint32_t k){ uint32_t i=hsh(k); while(h->used[i]){ if(h->key[i]==k) return; i=(i+1)&HMASK; } h->used[i]=1; h->key[i]=k; }
static inline int hs_has(const HSet*h, uint32_t k){ uint32_t i=hsh(k); while(h->used[i]){ if(h->key[i]==k) return 1; i=(i+1)&HMASK; } return 0; }

/* map mask -> index in S (for symmetric parent lookup) */
typedef struct { uint32_t key[HSZ]; int32_t val[HSZ]; uint8_t used[HSZ]; } HMap;
static inline void hm_clear(HMap*h){ memset(h->used,0,HSZ); }
static inline void hm_put(HMap*h, uint32_t k, int v){ uint32_t i=hsh(k); while(h->used[i]){ if(h->key[i]==k){return;} i=(i+1)&HMASK; } h->used[i]=1; h->key[i]=k; h->val[i]=v; }
static inline int hm_get(const HMap*h, uint32_t k){ uint32_t i=hsh(k); while(h->used[i]){ if(h->key[i]==k) return h->val[i]; i=(i+1)&HMASK; } return -1; }

/* ---- search state ---- */
static uint32_t S[MAXS]; static int par[MAXS][2]; static int ns;
static HSet HS;        /* set of S masks */
static HMap HM;        /* mask -> index */
static uint32_t PSUM[MAXS*64]; static int np;  /* all distinct pair sums (list may repeat; used for iteration) */
static HSet HP;        /* set of pair sums */
static int d[NT];

static void rebuild_pairs(void){
    np=0; hs_clear(&HP);
    for(int i=0;i<ns;i++) for(int j=i+1;j<ns;j++){
        uint32_t u=S[i]^S[j];
        if(!hs_has(&HP,u)){ hs_add(&HP,u); if(np<MAXS*64) PSUM[np++]=u; }
    }
}

/* Distance of v from S, bounded.  PORT NOTE (2026-09-08, InvMixColumns):
 * the original returned bound+1 ("undecided") beyond the 6-sum tier, which
 * on rows of weight 11-19 means no candidate ever scores as an improvement
 * (see bp/runs/w_seed12345.log: 92 restarts, 0 circuits).  This variant keeps
 * the exact tiers 1..4 always (O(1)/O(ns)/O(np)), runs the expensive exact
 * tiers 5..6 only when bound <= 6 (the regime the forward code lived in), and
 * otherwise falls back to an UPPER BOUND on the distance:
 *   FALLBACK=1  popcnt(v)                        (all 32 unit vectors are in S)
 *   FALLBACK=2  min(popcnt(v), 1 + min_a popcnt(v ^ S[a]))   (one-hop)
 * d[t] therefore becomes an upper bound on the true distance, not the exact
 * value; termination (d[t]==1 iff t in S) and circuit validity are unaffected.
 * Returns min(UB, bound+1); a return <= bound is not a proof of exactness. */
#ifndef FALLBACK
#define FALLBACK 2
#endif
/* Exact-tier cap, set once per greedy step from the number of unfinished
 * targets: tiers 1..3 are O(1)/O(1)/O(ns) and always run; tier 4 is O(np) and
 * tiers 5..6 are O(ns*np)/O(np^2) -- affordable only near the end. */
static int exact_cap = 3;
static void set_exact_cap(void){
    int unf=0; for(int t=0;t<NT;t++) if(d[t]>1) unf++;
    exact_cap = (unf<=6)? 6 : (unf<=10)? 4 : 3;
}
static inline int popc(uint32_t x){ return __builtin_popcount(x); }
static int dist_bounded(uint32_t v, int bound){
    if(bound<0) return 1; /* caller only cares about <=bound */
    if(v==0) return 0;
    if(hs_has(&HS,v)) return 1;
    if(bound<2) return bound+1;
    if(hs_has(&HP,v)) return 2;
    if(bound<3) return bound+1;
    for(int a=0;a<ns;a++) if(hs_has(&HP,v^S[a])) return 3;
    if(bound<4) return bound+1;
    int lo = 4; /* true distance is >= lo after the exact tiers that ran */
    if(exact_cap>=4){
        for(int p=0;p<np;p++) if(hs_has(&HP,v^PSUM[p])) return 4;
        if(bound<5) return bound+1;
        lo = 5;
        if(exact_cap>=6 && bound<=6){
            for(int a=0;a<ns;a++){ uint32_t va=v^S[a];
                for(int p=0;p<np;p++) if(hs_has(&HP,va^PSUM[p])) return 5; }
            if(bound<6) return bound+1;
            for(int p=0;p<np;p++){ uint32_t vp=v^PSUM[p];
                for(int q=0;q<np;q++) if(hs_has(&HP,vp^PSUM[q])) return 6; }
            return bound+1;
        }
    }
    /* fall back to an upper bound on the distance */
    int ub = popc(v);
#if FALLBACK>=2
    for(int a=0;a<ns;a++){ int c=1+popc(v^S[a]); if(c<ub) ub=c; }
#endif
    if(ub<lo) ub=lo;
    return ub<=bound ? ub : bound+1;
}

static void add_elem(uint32_t u, int pa, int pb){
    S[ns]=u; par[ns][0]=pa; par[ns][1]=pb; hs_add(&HS,u); hm_put(&HM,u,ns); ns++;
    /* exact incremental distance update: d[t]=min(d[t], dist_{S\u}(t^u)+1).
       We call this right after inserting u into HS; dist may then also use u,
       which is still correct (distance over S including u). */
    for(int t=0;t<NT;t++){
        if(d[t]<=1) continue;
        int q=dist_bounded(TGT[t]^u, d[t]-2);
        if(q+1<d[t]) d[t]=q+1;
    }
}

static int popcnt(uint32_t x){ return popc(x); }

/* ---------- exact-ish endgame: iterative deepening DFS ---------- */
static long dfs_nodes, dfs_cap;
static void rebuild_hs(void){
    hs_clear(&HS); hm_clear(&HM);
    for(int i=0;i<ns;i++){ hs_add(&HS,S[i]); hm_put(&HM,S[i],i); }
}
static int eg_lb(void){
    int unf=0, mx=0;
    for(int t=0;t<NT;t++) if(d[t]>1){ unf++; if(d[t]-1>mx) mx=d[t]-1; }
    if(mx>unf) unf=mx;
    return unf;
}
/* returns 1 on success; on success S/d stay extended (gates recorded in par) */
static int eg_dfs(int budget){
    int lb=eg_lb();
    if(lb==0) return 1;
    if(lb>budget) return 0;
    if(++dfs_nodes>dfs_cap) return 0;
    rebuild_pairs();
    /* generate improving candidates */
    typedef struct{ int i,j; long sum,norm; } C;
    C cs[512]; int nc=0;
    long cursum=0; for(int t=0;t<NT;t++) cursum+=d[t];
    for(int i=0;i<ns;i++) for(int j=i+1;j<ns;j++){
        uint32_t u=S[i]^S[j];
        if(hs_has(&HS,u)) continue;
        long sum=0,norm=0; int improved=0;
        for(int t=0;t<NT;t++){
            int nd=d[t];
            if(nd>1){
                int q=dist_bounded(TGT[t]^u, nd-2);
                if(q+1<nd){ nd=q+1; improved=1; }
            }
            sum+=nd; norm+=(long)nd*nd;
        }
        if(!improved) continue;
        if(nc<512){ cs[nc].i=i; cs[nc].j=j; cs[nc].sum=sum; cs[nc].norm=norm; nc++; }
    }
    /* sort by (sum asc, norm desc), take top K */
    for(int a=1;a<nc;a++){ C x=cs[a]; int b=a-1;
        while(b>=0 && (cs[b].sum>x.sum || (cs[b].sum==x.sum && cs[b].norm<x.norm))){ cs[b+1]=cs[b]; b--; }
        cs[b+1]=x; }
    int K = nc<14? nc:14;
    int ns_save=ns; int d_save[NT]; memcpy(d_save,d,sizeof(d_save));
    for(int k=0;k<K;k++){
        uint32_t u=S[cs[k].i]^S[cs[k].j];
        add_elem(u,cs[k].i,cs[k].j);
        if(eg_dfs(budget-1)) return 1;
        /* pop */
        ns=ns_save; memcpy(d,d_save,sizeof(d_save)); rebuild_hs();
        if(dfs_nodes>dfs_cap) return 0;
    }
    return 0;
}
/* try to finish endgame exactly within maxbudget; 1 if finished */
static int endgame(int maxbudget){
    int lb=eg_lb();
    if(lb==0) return 1;
    for(int b=lb;b<=maxbudget;b++){
        dfs_nodes=0; dfs_cap=150000;
        if(eg_dfs(b)) return 1;
        if(dfs_nodes>dfs_cap) return 0; /* capped out: fall back to greedy */
    }
    return 0;
}

/* load index-pair circuit from json (scan integers pairwise); returns ngates */
static int load_circ(const char*path, int (*g)[2], int maxg){
    FILE*f=fopen(path,"r"); if(!f) return -1;
    static char buf[1<<20]; size_t n=fread(buf,1,sizeof(buf)-1,f); buf[n]=0; fclose(f);
    int vals[2], nv=0, ng=0; char*p=buf;
    /* skip past "gates" key */
    char*q=strstr(buf,"["); if(!q) return -1; p=q;
    while(*p && ng<maxg){
        if(*p=='-'||(*p>='0'&&*p<='9')){
            long v=strtol(p,&p,10);
            vals[nv++]=(int)v;
            if(nv==2){ g[ng][0]=vals[0]; g[ng][1]=vals[1]; ng++; nv=0; }
        } else p++;
    }
    return ng;
}

/* atomically publish circuit to shared best file if better */
static void publish(const char*path, int cnt, int (*g)[2]){
    static int tmpg[MAXS][2];
    int cur=load_circ(path,tmpg,MAXS);
    if(cur>=0 && cur<=cnt) return;
    char tmp[512]; snprintf(tmp,sizeof(tmp),"%s.tmp.%d",path,(int)getpid());
    FILE*f=fopen(tmp,"w"); if(!f) return;
    fprintf(f,"{\"gates\":[");
    for(int i=0;i<cnt;i++) fprintf(f,"%s[%d,%d]", i?",":"", g[i][0], g[i][1]);
    fprintf(f,"]}\n"); fclose(f);
    rename(tmp,path);
}

int main(int argc, char**argv){
    if(argc<6){ fprintf(stderr,"usage: bp2 seed mode norm time_s out.json [sharedbest.json]\n"); return 2; }
    rng_s = strtoull(argv[1],0,0)*0x9E3779B97F4A7C15ull + 0xD1B54A32D192ED03ull; if(!rng_s) rng_s=1;
    int sym = atoi(argv[2]);
    int normmode = atoi(argv[3]);
    double time_s = atof(argv[4]);
    const char*outpath = argv[5];
    const char*shared = (argc>6)? argv[6] : 0;

    struct timespec t0; clock_gettime(CLOCK_MONOTONIC,&t0);
    int best = 1<<30;
    long restarts=0;

    static int cand_i[MAXS*64], cand_j[MAXS*64];
    static int seedg[MAXS][2];
    static int incg[MAXS][2]; int ninc=-1;

    for(;;){
        struct timespec tn; clock_gettime(CLOCK_MONOTONIC,&tn);
        double el = (tn.tv_sec-t0.tv_sec)+(tn.tv_nsec-t0.tv_nsec)*1e-9;
        if(el>time_s) break;
        restarts++;
        /* init */
        ns=0; hs_clear(&HS); hm_clear(&HM);
        for(int i=0;i<32;i++){ S[ns]=1u<<i; par[ns][0]=par[ns][1]=-1; hs_add(&HS,S[ns]); hm_put(&HM,S[ns],ns); ns++; }
        for(int t=0;t<NT;t++) d[t]=popcnt(TGT[t]);
        /* seeded restart: load shared best, keep a randomly thinned
           dependency-closed subset, and let the greedy repair the rest.
           Occasionally (1 in 6) do a fresh unseeded restart for diversity. */
        if(shared && (ninc<=0 || rndn(8)==0)){
            int nsg=load_circ(shared,seedg,MAXS);
            if(nsg>0 && (ninc<=0 || nsg<ninc)){ memcpy(incg,seedg,sizeof(int)*2*nsg); ninc=nsg; }
        }
        if(ninc>0){
            int nsg=ninc; memcpy(seedg,incg,sizeof(int)*2*nsg);
            {
                if(nsg<best) best=nsg;
                /* drop probability varies per restart: 0.03 .. 0.30 */
                uint32_t dp = 30 + rndn(270); /* per-mille */
                static uint8_t kept[MAXS]; memset(kept,1,32);
                static int map[MAXS];
                for(int i=0;i<32;i++) map[i]=i;
                for(int k=0;k<nsg;k++){
                    int a=seedg[k][0], b=seedg[k][1], oi=32+k;
                    if(a<0||a>=oi||b<0||b>=oi||!kept[a]||!kept[b]){ kept[oi]=0; continue; }
                    if(rnd()%1000 < dp){ kept[oi]=0; continue; }
                    uint32_t m=S[map[a]]^S[map[b]];
                    if(hs_has(&HS,m)){ kept[oi]=1; map[oi]=hm_get(&HM,m); continue; }
                    kept[oi]=1; map[oi]=ns;
                    S[ns]=m; par[ns][0]=map[a]; par[ns][1]=map[b];
                    hs_add(&HS,m); hm_put(&HM,m,ns); ns++;
                }
                /* recompute exact target distances from this base */
                rebuild_pairs();
                for(int t=0;t<NT;t++){
                    int b2; for(b2=1;b2<=8;b2++){ int q=dist_bounded(TGT[t],b2); if(q<=b2){ d[t]=q; break; } }
                }
            }
        }
        int steps=0; int eg_last_fail=1<<20;
        while(1){
            int done=1; for(int t=0;t<NT;t++) if(d[t]>1){done=0;break;}
            if(done) break;
            { int cap = (ninc>0? ninc+1 : best); if(ns-32>cap) break; } /* allow +1 uphill */
            if(++steps>400) break;
            {   /* endgame: few gates left -> exact-ish DFS */
                int rem=0, unf=0;
                for(int t=0;t<NT;t++) if(d[t]>1){ rem+=d[t]-1; unf++; }
                int cap = (ninc>0? ninc+1 : 1<<20) - (ns-32);
                if(rem<=8 && unf<=6 && rem<eg_last_fail){
                    int mb = rem<cap? rem:cap;
                    if(endgame(mb)) break;  /* all targets finished */
                    eg_last_fail=rem;
                }
            }
            set_exact_cap();
            rebuild_pairs();
            /* score all candidate pairs */
            long bestsum=1L<<40; long bestnorm = (normmode==2)? (1L<<40) : -1;
            int ncand=0;
            for(int i=0;i<ns;i++) for(int j=i+1;j<ns;j++){
                uint32_t u=S[i]^S[j];
                if(hs_has(&HS,u)) continue;
                long sum=0, norm=0; int improved=0;
                for(int t=0;t<NT;t++){
                    int nd=d[t];
                    if(nd>1){
                        int bnd=nd-2;
                        if(sym){
                            for(int r=0;r<4;r++){
                                int q=dist_bounded(TGT[t]^rotl(u,8*r), bnd);
                                if(q+1<nd){ nd=q+1; bnd=nd-2; }
                            }
                        } else {
                            int q=dist_bounded(TGT[t]^u, bnd);
                            if(q+1<nd) nd=q+1;
                        }
                        if(nd<d[t]) improved=1;
                    }
                    sum+=nd; norm+=(long)nd*nd;
                }
                if(!improved) continue;
                int better=0, equal=0;
                if(sum<bestsum) better=1;
                else if(sum==bestsum){
                    if(normmode==1){ if(norm>bestnorm) better=1; else if(norm==bestnorm) equal=1; }
                    else if(normmode==2){ if(norm<bestnorm) better=1; else if(norm==bestnorm) equal=1; }
                    else equal=1;
                }
                if(better){ bestsum=sum; bestnorm=norm; ncand=0; cand_i[ncand]=i; cand_j[ncand]=j; ncand=1; }
                else if(equal && ncand<MAXS*64){ cand_i[ncand]=i; cand_j[ncand]=j; ncand++; }
            }
            if(!ncand) break; /* stuck (shouldn't happen) */
            if(!sym && rndn(4)==0){
                /* re-collect with sum <= bestsum+1, uniform choice */
                long lim=bestsum+1; ncand=0;
                for(int i=0;i<ns && ncand<MAXS*64;i++) for(int j=i+1;j<ns;j++){
                    uint32_t u=S[i]^S[j];
                    if(hs_has(&HS,u)) continue;
                    long sum=0; int improved=0;
                    for(int t=0;t<NT;t++){
                        int nd=d[t];
                        if(nd>1){ int q=dist_bounded(TGT[t]^u, nd-2); if(q+1<nd){ nd=q+1; improved=1; } }
                        sum+=nd;
                    }
                    if(improved && sum<=lim && ncand<MAXS*64){ cand_i[ncand]=i; cand_j[ncand]=j; ncand++; }
                }
            }
            if(!ncand) break;
            int k=rndn(ncand);
            int i=cand_i[k], j=cand_j[k];
            uint32_t u=S[i]^S[j];
            add_elem(u,i,j);
            if(sym){
                for(int r=1;r<4;r++){
                    uint32_t ur=rotl(u,8*r);
                    if(hs_has(&HS,ur)) continue;
                    int pa=hm_get(&HM, rotl(S[i],8*r));
                    int pb=hm_get(&HM, rotl(S[j],8*r));
                    if(pa<0||pb<0) continue; /* parent missing: skip rotation */
                    add_elem(ur,pa,pb);
                }
            }
        }
        int done=1; for(int t=0;t<NT;t++) if(d[t]>1){done=0;break;}
        { struct timespec tr; clock_gettime(CLOCK_MONOTONIC,&tr);
          double elr=(tr.tv_sec-t0.tv_sec)+(tr.tv_nsec-t0.tv_nsec)*1e-9;
          printf("restart %ld: steps=%d ns=%d done=%d t=%.1fs\n", restarts, steps, ns, done, elr); fflush(stdout); }
        if(!done) continue;
        /* prune dead gates: keep only ancestors of targets */
        static uint8_t need[MAXS]; memset(need,0,ns);
        for(int t=0;t<NT;t++){ int ix=hm_get(&HM,TGT[t]); if(ix>=0) need[ix]=1; }
        for(int ix=ns-1;ix>=32;ix--) if(need[ix]){ need[par[ix][0]]=1; need[par[ix][1]]=1; }
        int cnt=0; for(int ix=32;ix<ns;ix++) if(need[ix]) cnt++;
        /* annealing acceptance into in-memory incumbent */
        if(ninc<=0 || cnt<=ninc || (cnt==ninc+1 && rndn(100)<15)){
            /* store pruned circuit as incumbent */
            static int remap2[MAXS]; int w2=32, ng2=0;
            for(int i=0;i<32;i++) remap2[i]=i;
            for(int ix=32;ix<ns;ix++) if(need[ix]){
                remap2[ix]=w2++;
                incg[ng2][0]=remap2[par[ix][0]]; incg[ng2][1]=remap2[par[ix][1]]; ng2++;
            }
            ninc=ng2;
        }
        if(cnt<=best){
            int strictly=cnt<best; best=cnt;
            static int remap[MAXS]; static int outg[MAXS][2];
            for(int i=0;i<32;i++) remap[i]=i;
            int w=32, ng=0;
            for(int ix=32;ix<ns;ix++) if(need[ix]){
                remap[ix]=w++;
                outg[ng][0]=remap[par[ix][0]]; outg[ng][1]=remap[par[ix][1]]; ng++;
            }
            FILE*f=fopen(outpath,"w");
            fprintf(f,"{\"gates\":[");
            for(int i2=0;i2<ng;i2++) fprintf(f,"%s[%d,%d]", i2?",":"", outg[i2][0], outg[i2][1]);
            fprintf(f,"]}\n"); fclose(f);
            if(shared) publish(shared,ng,outg);
            if(strictly){ printf("BEST %d gates (restart %ld, %.0fs)\n", best, restarts, el); fflush(stdout); }
        }
    }
    printf("done: best=%d restarts=%ld\n", best, restarts);
    return 0;
}
