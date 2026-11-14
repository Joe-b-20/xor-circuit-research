s = open("fdrive.py").read()
def rep(old, new):
    global s
    assert old in s, old[:60]
    s = s.replace(old, new)
rep("""    if cap_ad is not None: cfg['cap.ad'] = cap_ad
    if extra""", """    if cap_ad is not None: cfg['cap.ad'] = cap_ad
    if CAP_A is not None: cfg['cap.a'] = CAP_A
    if extra""")
rep("""def metrics(c):""", """CAP_A = None


def metrics(c):""")
rep("""    ap.add_argument('--out', required=True)
    a = ap.parse_args()""", """    ap.add_argument('--cap-a', type=int, default=None)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    global CAP_A
    CAP_A = a.cap_a""")
rep("""    feas = lambda c: metrics(c)[2] <= D and metrics(c)[3] <= a.cap_ad""",
    """    feas = lambda c: metrics(c)[2] <= D and metrics(c)[3] <= a.cap_ad and (a.cap_a is None or metrics(c)[1] <= a.cap_a)""")
rep("""        base = best if feas(best) else cur
        if mode == 'gate':""", """        base = best if feas(best) else cur
        if mode == 'fresh':          # short independent restarts from the start (track D finding)
            base = start; mode = 'gate'
        if mode == 'gate':""")
open("fdrive.py", "w").write(s)
