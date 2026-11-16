# campaign 2026-11-16-invsbox: inverse-S-box shim (see invshim.py); active only with XS_INVSBOX=1
import os
if os.environ.get("XS_INVSBOX") == "1":
    import invshim
    invshim.install()
    if os.environ.get("XS_INVSBOX_LINE") == "1":
        invshim.install_line_rule()
