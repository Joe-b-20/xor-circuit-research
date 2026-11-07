import sys, qh_lp
for key in [(14,1,1,6,0,"M"), (15,0,0,6,0,"M"), (16,3,3,4,0,"M"), (16,2,2,4,1,"M"), (11,5,0,5,1,"Mt"), (12,3,1,4,2,"Mt"), (9,5,4,8,0,"Mt"), (18,1,1,1,4,"Mt")]:
    h,y,F,q,z,ori = key
    qh_lp.vertices(h,y,F,q,z,ori,"GstarN1HUB2DARKMFMPK", n=3); sys.stdout.flush()
