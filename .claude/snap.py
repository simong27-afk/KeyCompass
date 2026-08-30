import re, subprocess, sys, os
SP="/private/tmp/claude-501/-Users-simongeils-Desktop-KeyCompass/7d9741cb-f051-4d7f-a680-3fde281c66f3/scratchpad"
CH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
src=open('index.html',encoding='utf-8').read()

def snap(name, offset, h, w=1440, extra=""):
    inject = """<style id="__snap">
.js .ln i,.ln i,.hero__lead,.hero__acts,.hero__facts,.plan,
[data-reveal] .rowhead,[data-reveal] .rule,[data-reveal] .wrap>*{opacity:1!important;transform:none!important}
.ch__edge,.ch__lbl,.plan__names text{opacity:1!important}
.plan__rings .ring,.ring--core{stroke-dashoffset:0!important}
html{scroll-behavior:auto}
.hdr{display:none!important}
body{margin-top:-%dpx}
%s
</style>
</head>""" % (offset, extra)
    open('__snap.html','w',encoding='utf-8').write(src.replace('</head>', inject, 1))
    out=os.path.join(SP, name+".png")
    subprocess.run([CH,"--headless=new","--disable-gpu","--hide-scrollbars",
        "--window-size=%d,%d"%(w,h),"--screenshot="+out,"--virtual-time-budget=6000",
        "http://127.0.0.1:4321/__snap.html"],capture_output=True)
    print(name, os.path.getsize(out))

for args in eval(sys.argv[1]):
    snap(*args)
