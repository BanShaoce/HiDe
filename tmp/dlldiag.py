import ctypes, os, glob
d = r'C:\Users\19457\anaconda3\envs\HiDe\Lib\site-packages\torch\lib'
os.add_dll_directory(d)
for f in sorted(os.listdir(d)):
    if not f.lower().endswith('.dll'):
        continue
    p = os.path.join(d, f)
    try:
        ctypes.WinDLL(p)
        print('OK   ', f)
    except Exception as e:
        print('FAIL ', f, '->', type(e).__name__, getattr(e, 'winerror', None))
