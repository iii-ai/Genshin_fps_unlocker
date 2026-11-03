# -*- coding: utf-8 -*-
"""
core.py — 原神帧率解锁核心模块

原理（与开源项目 unlock_fps / genshin-fps-unlock 一致）：
  游戏把帧率上限写死在 Unity 引擎的 Application.targetFrameRate 里。
  UnityPlayer.dll 中读取该变量的指令序列是固定形状的：
        8B 0D ?? ?? ?? ??      mov  ecx, [rip + disp32]   ; 读 targetFrameRate
        66 0F 6E C9            movd xmm1, ecx
        0F 5B C9               cvtdq2ps xmm1, xmm1
  我们在 .text 段里按特征码定位它，由 RIP 相对寻址反推出变量绝对地址，
  然后用 WriteProcessMemory 把值改成目标帧率，并定期刷新防止被游戏重置。

全程只写入游戏进程内存，不读写、不替换、不生成游戏目录下的任何文件。
"""

import ctypes
import ctypes.wintypes as wt
import os
import struct
import subprocess
import threading
import time

k32 = ctypes.WinDLL("kernel32", use_last_error=True)
k32.GetModuleFileNameW.restype = wt.DWORD

# ---------------------------------------------------------------- 常量
PROCESS_VM_OPERATION = 0x0008
PROCESS_VM_READ = 0x0010
PROCESS_VM_WRITE = 0x0020
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

TH32CS_SNAPPROCESS = 0x00000002
TH32CS_SNAPMODULE = 0x00000008
TH32CS_SNAPMODULE32 = 0x00000010

MAX_PATH = 260
UNITY_MODULE = "unityplayer.dll"
GAME_EXE_NAMES = ("yuanshen.exe", "genshinimpact.exe")

# 特征码：None 表示通配
# 主特征码（开源项目 unlock_fps 同款）：mov ecx,[rip+disp32] / movd xmm1,ecx / cvtdq2ps xmm1,xmm1
FPS_PATTERN = (0x8B, 0x0D, None, None, None, None,
               0x66, 0x0F, 0x6E, 0xC9, 0x0F, 0x5B, 0xC9)
FPS_PATTERN_TEXT = "8B 0D ?? ?? ?? ?? 66 0F 6E C9 0F 5B C9"
# 回退特征码：不同 Unity 版本后续指令可能变化，前 10 字节通常稳定
FPS_PATTERN_ALT = (0x8B, 0x0D, None, None, None, None, 0x66, 0x0F, 0x6E, 0xC9)
FPS_PATTERN_ALT_TEXT = "8B 0D ?? ?? ?? ?? 66 0F 6E C9"
SCAN_PATTERNS = ((FPS_PATTERN, FPS_PATTERN_TEXT), (FPS_PATTERN_ALT, FPS_PATTERN_ALT_TEXT))

# setter 特征码：mov [rip+disp32], ecx / ret
# 游戏就是靠这一个函数把 60 写回去的；找到它之后可以把它改成“写死目标帧率”，
# 这样即使反作弊收回写权限，游戏自己再调 set(60) 也只会写进我们的值。
SETTER_PATTERN = (0x89, 0x0D, None, None, None, None, 0xC3)
SETTER_PATTERN_TEXT = "89 0D ?? ?? ?? ?? C3"
PAGE_EXECUTE_READ = 0x20
PAGE_EXECUTE_READWRITE = 0x40


# ---------------------------------------------------------------- 结构体
class MODULEENTRY32W(ctypes.Structure):
    _fields_ = [
        ("dwSize", wt.DWORD),
        ("th32ModuleID", wt.DWORD),
        ("th32ProcessID", wt.DWORD),
        ("GlblcntUsage", wt.DWORD),
        ("ProccntUsage", wt.DWORD),
        ("modBaseAddr", ctypes.POINTER(ctypes.c_byte)),
        ("modBaseSize", wt.DWORD),
        ("hModule", wt.HANDLE),
        ("szModule", wt.WCHAR * 256),
        ("szExePath", wt.WCHAR * MAX_PATH),
    ]


class PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [
        ("dwSize", wt.DWORD),
        ("cntUsage", wt.DWORD),
        ("th32ProcessID", wt.DWORD),
        ("th32DefaultHeapID", ctypes.c_size_t),
        ("th32ModuleID", wt.DWORD),
        ("cntThreads", wt.DWORD),
        ("th32ParentProcessID", wt.DWORD),
        ("pcPriClassBase", ctypes.c_long),
        ("dwFlags", wt.DWORD),
        ("szExeFile", wt.WCHAR * MAX_PATH),
    ]


k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
k32.OpenProcess.restype = wt.HANDLE
k32.CloseHandle.argtypes = [wt.HANDLE]
k32.CloseHandle.restype = wt.BOOL
k32.ReadProcessMemory.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                  ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
k32.ReadProcessMemory.restype = wt.BOOL
k32.WriteProcessMemory.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                   ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
k32.WriteProcessMemory.restype = wt.BOOL
k32.CreateToolhelp32Snapshot.argtypes = [wt.DWORD, wt.DWORD]
k32.CreateToolhelp32Snapshot.restype = wt.HANDLE
k32.Module32FirstW.argtypes = [wt.HANDLE, ctypes.POINTER(MODULEENTRY32W)]
k32.Module32FirstW.restype = wt.BOOL
k32.Module32NextW.argtypes = [wt.HANDLE, ctypes.POINTER(MODULEENTRY32W)]
k32.Module32NextW.restype = wt.BOOL
k32.Process32FirstW.argtypes = [wt.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
k32.Process32FirstW.restype = wt.BOOL
k32.Process32NextW.argtypes = [wt.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
k32.Process32NextW.restype = wt.BOOL
k32.GetExitCodeProcess.argtypes = [wt.HANDLE, ctypes.POINTER(wt.DWORD)]
k32.GetExitCodeProcess.restype = wt.BOOL
k32.VirtualProtectEx.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_size_t,
                                 wt.DWORD, ctypes.POINTER(wt.DWORD)]
k32.VirtualProtectEx.restype = wt.BOOL


def _bad_handle(h):
    v = h if isinstance(h, int) else (h or 0)
    return (not v) or (v & 0xFFFFFFFF) == 0xFFFFFFFF


def _snapshot(flags, pid):
    h = k32.CreateToolhelp32Snapshot(flags, pid)
    if _bad_handle(h):
        raise ctypes.WinError(ctypes.get_last_error())
    return h


# ---------------------------------------------------------------- 进程 / 模块
def is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def list_modules(pid):
    """返回 [(模块名, 基址, 大小, 路径)]"""
    snap = _snapshot(TH32CS_SNAPMODULE | TH32CS_SNAPMODULE32, pid)
    out = []
    try:
        me = MODULEENTRY32W()
        me.dwSize = ctypes.sizeof(MODULEENTRY32W)
        ok = k32.Module32FirstW(snap, ctypes.byref(me))
        while ok:
            out.append((me.szModule, ctypes.cast(me.modBaseAddr, ctypes.c_void_p).value,
                        me.modBaseSize, me.szExePath))
            ok = k32.Module32NextW(snap, ctypes.byref(me))
    finally:
        k32.CloseHandle(snap)
    return out


def find_game_pids():
    """查找正在运行的原神进程，返回 [(pid, exe 路径)]"""
    snap = _snapshot(TH32CS_SNAPPROCESS, 0)
    pids = []
    try:
        pe = PROCESSENTRY32W()
        pe.dwSize = ctypes.sizeof(PROCESSENTRY32W)
        ok = k32.Process32FirstW(snap, ctypes.byref(pe))
        while ok:
            if pe.szExeFile.lower() in GAME_EXE_NAMES:
                pids.append((pe.th32ProcessID, ""))
            ok = k32.Process32NextW(snap, ctypes.byref(pe))
    finally:
        k32.CloseHandle(snap)
    return pids


def wait_game_pid(timeout=180, prefer_pid=None, log=None):
    """等待真正的游戏进程出现（兼容从启动器拉起的情况）"""
    log = log or (lambda msg: None)
    deadline = time.time() + timeout
    told = False
    while time.time() < deadline:
        procs = find_game_pids()
        if procs:
            return procs[0][0]
        if prefer_pid and is_alive(prefer_pid):
            try:
                names = [m[0].lower() for m in list_modules(prefer_pid)]
                if UNITY_MODULE in names or any(n in GAME_EXE_NAMES for n in names):
                    return prefer_pid
            except OSError:
                pass
        if not told:
            log("等待游戏进程出现…（若走启动器，请在启动器里点“开始游戏”）")
            told = True
        time.sleep(1)
    return None


def is_alive(pid):
    # 先用权限要求最低的 LIMITED 权限，跨完整性级别也能判断存活
    for access in (PROCESS_QUERY_LIMITED_INFORMATION, PROCESS_QUERY_INFORMATION):
        h = k32.OpenProcess(access, False, pid)
        if _bad_handle(h):
            continue
        try:
            code = wt.DWORD()
            if not k32.GetExitCodeProcess(h, ctypes.byref(code)):
                return False
            return code.value == 259  # STILL_ACTIVE
        finally:
            k32.CloseHandle(h)
    return False


# ---------------------------------------------------------------- 读写
class ProcessMemory:
    def __init__(self, pid):
        self.pid = pid
        self.handle = k32.OpenProcess(
            PROCESS_VM_READ | PROCESS_VM_WRITE | PROCESS_VM_OPERATION | PROCESS_QUERY_INFORMATION,
            False, pid)
        if _bad_handle(self.handle):
            err = ctypes.get_last_error()
            raise OSError(err, "无法打开游戏进程（错误码 %d）%s" % (
                err, "，请以管理员身份运行" if not is_admin() else ""))

    def close(self):
        if self.handle and not _bad_handle(self.handle):
            k32.CloseHandle(self.handle)
            self.handle = None

    def read(self, addr, size):
        buf = ctypes.create_string_buffer(size)
        got = ctypes.c_size_t(0)
        if not k32.ReadProcessMemory(self.handle, ctypes.c_void_p(addr), buf, size,
                                     ctypes.byref(got)):
            raise OSError(ctypes.get_last_error(), "内存读取失败")
        return buf.raw[:got.value]

    def write(self, addr, data):
        buf = ctypes.create_string_buffer(data, len(data))
        put = ctypes.c_size_t(0)
        if not k32.WriteProcessMemory(self.handle, ctypes.c_void_p(addr), buf, len(data),
                                      ctypes.byref(put)):
            raise OSError(ctypes.get_last_error(), "内存写入失败")
        return put.value

    def read_i32(self, addr):
        return int.from_bytes(self.read(addr, 4), "little", signed=True)

    def write_i32(self, addr, value):
        return self.write(addr, int(value).to_bytes(4, "little", signed=True))

    # ---- 代码段改写（改 .text 必须先把页改成可写，否则写入必失败）
    def protect(self, addr, size, new_prot):
        old = wt.DWORD(0)
        if not k32.VirtualProtectEx(self.handle, ctypes.c_void_p(addr), size,
                                    new_prot, ctypes.byref(old)):
            raise OSError(ctypes.get_last_error(), "内存页保护修改失败")
        return old.value

    def write_code(self, addr, data):
        old = self.protect(addr, len(data), PAGE_EXECUTE_READWRITE)
        try:
            self.write(addr, data)
        finally:
            try:
                self.protect(addr, len(data), old)
            except OSError:
                pass
        return len(data)


# ---------------------------------------------------------------- PE 解析 / 扫描
def text_section(pm, base):
    """.text 段的 (起始地址, 长度)"""
    hdr = pm.read(base, 0x1000)
    if hdr[:2] != b"MZ":
        raise ValueError("UnityPlayer.dll 头部异常")
    e_lfanew = int.from_bytes(hdr[0x3C:0x40], "little")
    if hdr[e_lfanew:e_lfanew + 4] != b"PE\0\0":
        raise ValueError("无效的 PE 头")
    nsec = int.from_bytes(hdr[e_lfanew + 6:e_lfanew + 8], "little")
    size_opt = int.from_bytes(hdr[e_lfanew + 20:e_lfanew + 22], "little")
    sec_off = e_lfanew + 24 + size_opt
    need = sec_off + 40 * nsec
    if need > len(hdr):
        hdr = pm.read(base, need)
    for i in range(nsec):
        off = sec_off + 40 * i
        name = hdr[off:off + 8].rstrip(b"\0").decode("ascii", "ignore")
        vsize = int.from_bytes(hdr[off + 8:off + 12], "little")
        vaddr = int.from_bytes(hdr[off + 12:off + 16], "little")
        raw = int.from_bytes(hdr[off + 16:off + 20], "little")
        if name == ".text":
            # 映射后的段大小取两者较大值，避免个别版本 VirtualSize 偏小导致扫不全
            return base + vaddr, max(vsize, raw)
    raise ValueError("未找到 .text 段")


def scan_pattern(pm, start, size, pattern=FPS_PATTERN, chunk=1 << 21):
    """在 [start, start+size) 内按特征码扫描，返回匹配地址列表"""
    plen = len(pattern)
    first = bytes([pattern[0]])
    hits = []
    off = 0
    while off < size:
        n = min(chunk + plen - 1, size - off)
        try:
            data = pm.read(start + off, n)
        except OSError:
            off += chunk
            continue
        i = 0
        while True:
            i = data.find(first, i)
            if i < 0 or i + plen > len(data):
                break
            matched = True
            for k in range(1, plen):
                want = pattern[k]
                if want is not None and data[i + k] != want:
                    matched = False
                    break
            if matched:
                hits.append(start + off + i)
                if len(hits) > 64:
                    return hits
            i += 1
        off += chunk
    return hits


def resolve_target(pm, match_addr):
    """由 mov ecx,[rip+disp32] 反推目标变量绝对地址"""
    disp = int.from_bytes(pm.read(match_addr + 2, 4), "little", signed=True)
    return (match_addr + 6 + disp) & 0xFFFFFFFFFFFFFFFF


# ---------------------------------------------------------------- 解锁器
class FpsUnlocker:
    def __init__(self, log=None):
        self.log = log or (lambda msg: None)
        self.pid = None
        self.pm = None
        self.fps_addr = None
        self.setter_addr = None
        self.patched = False
        self.target_fps = 120
        self._stop = threading.Event()
        self._thread = None
        self.degraded = False
        self._read_blocked = False
        self._lock = threading.Lock()

    # ---- 挑选承载帧率变量的模块
    @staticmethod
    def _choose_module(mods):
        """
        新版客户端（如国服 7.x）把 Unity 播放器静态编译进了主程序，
        目录下没有 UnityPlayer.dll；老版本则走 UnityPlayer.dll。
        优先 UnityPlayer.dll，其次主程序模块。
        """
        unity, main = None, None
        for name, mbase, msize, _path in mods:
            low = name.lower()
            if low == UNITY_MODULE and unity is None:
                unity = (name, mbase, msize)
            elif low in GAME_EXE_NAMES and main is None:
                main = (name, mbase, msize)
        return unity or main

    def attach(self, pid, wait_module=0.0):
        self.pid = pid
        deadline = time.time() + max(wait_module, 0)
        mod = None
        last_err = None
        while True:
            try:
                mod = self._choose_module(list_modules(pid))
            except OSError as e:
                last_err = e
                mod = None
                # 权限被拒说明反作弊已经接管，再等也不会变好，直接失败
                if getattr(e, "winerror", None) == 5:
                    break
            if mod or time.time() >= deadline:
                break
            time.sleep(0.1)
        if not mod:
            if last_err is not None and getattr(last_err, "winerror", None) == 5:
                raise RuntimeError(
                    "反作弊已接管进程，无法中途注入 · 请退出游戏后由本工具启动")
            extra = ""
            if last_err is not None:
                extra = "（枚举模块失败：%s）" % last_err
            raise RuntimeError("游戏进程还没就绪，找不到 UnityPlayer.dll 或游戏主模块%s" % extra)

        name, base, size = mod
        self.log("命中模块：%s 基址 0x%X（%.0f MB）" % (name, base, size / 1048576.0))

        self.pm = ProcessMemory(pid)
        try:
            tstart, tsize = text_section(self.pm, base)
            self.log(".text 段地址 0x%X，大小 %.1f MB" % (tstart, tsize / 1048576.0))
        except (OSError, ValueError) as e:
            # PE 头解析失败时退化为整模块扫描
            tstart, tsize = base, size
            self.log("PE 解析失败（%s），改为扫描整个模块 %.1f MB" % (e, tsize / 1048576.0))

        hits, used = [], ""
        for _attempt in range(5):
            for pattern, text in SCAN_PATTERNS:
                hits = scan_pattern(self.pm, tstart, tsize, pattern)
                if hits:
                    used = text
                    break
            if hits:
                break
            time.sleep(2)
        if not hits:
            raise RuntimeError("没有找到帧率特征码（游戏更新可能改动了特征码）")

        best = None
        for h in hits:
            try:
                addr = resolve_target(self.pm, h)
                value = self.pm.read_i32(addr)
            except OSError:
                continue
            # 命中唯一时直接采信；多命中时按取值合理度排序
            # （Unity 的 targetFrameRate 默认 -1，游戏初始化后为 60）
            if value == 60:
                score = 0
            elif 30 <= value <= 1000:
                score = 1
            elif value in (-1, 0):
                score = 2
            else:
                score = 3
            if best is None or score < best[0]:
                best = (score, addr, value)
            if score == 0:
                break
        if best is None:
            raise RuntimeError("特征码命中但目标变量不可读，可能是游戏版本不匹配")

        self.fps_addr = best[1]
        self.log("特征码命中 %d 处（%s）" % (len(hits), used))
        self.log("帧率变量地址 0x%X（当前值 %d）" % (self.fps_addr, best[2]))

        # ---- 顺手把 setter 找出来（找不到不妨碍解锁，只是没法加固）
        try:
            self.setter_addr = self.find_setter(tstart, tsize)
        except OSError as e:
            self.log("查找 setter 失败：%s" % e)
        if self.setter_addr:
            self.log("帧率 setter 地址 0x%X" % self.setter_addr)
        else:
            self.log("没找到帧率 setter，只能靠保活补写（反作弊收权后会失效）")
        return self.fps_addr

    def find_setter(self, tstart, tsize):
        """定位 mov [rip+disp32], ecx ; ret —— 游戏唯一的帧率写入口"""
        if not self.fps_addr:
            return None
        for h in scan_pattern(self.pm, tstart, tsize, SETTER_PATTERN):
            try:
                if resolve_target(self.pm, h) == self.fps_addr:
                    return h
            except OSError:
                continue
        return None

    def install_patch(self, fps=None):
        """
        把 setter 改成“无论游戏传什么，都写死成目标帧率”。
        这一步必须在反作弊收回写权限之前完成，之后游戏再调 set(60) 也只会写进我们的值。
        返回 True 表示补丁已生效。
        """
        if fps is not None:
            self.target_fps = max(60, min(1000, int(fps)))
        if not self.pm or not self.fps_addr or not self.setter_addr:
            return False
        addr = self.setter_addr
        # C7 05 disp32 imm32 / ret  —— 共 11 字节，需要吃掉原 ret 后面的填充
        tail = self.pm.read(addr + 7, 4)
        if tail != b"\xCC\xCC\xCC\xCC":
            self.log("setter 后面不是填充（%s），为安全放弃改写代码段"
                     % " ".join("%02X" % b for b in tail))
            return False
        disp = (self.fps_addr - (addr + 10)) & 0xFFFFFFFF
        code = b"\xC7\x05" + struct.pack("<I", disp) + \
               struct.pack("<I", self.target_fps & 0xFFFFFFFF) + b"\xC3"
        try:
            self.pm.write_code(addr, code)
            back = self.pm.read(addr, len(code))
        except OSError as e:
            self.log("改写 setter 失败：%s" % e)
            return False
        if back != code:
            self.log("setter 改写校验不一致：%s" % " ".join("%02X" % b for b in back))
            return False
        self.patched = True
        self.log("已加固：游戏再调 set(x) 也只会写 %d FPS" % self.target_fps)
        return True

    # ---- 写入目标帧率
    def apply(self, fps=None):
        if fps is not None:
            self.target_fps = max(60, min(1000, int(fps)))
        if not self.pm or not self.fps_addr:
            return False
        with self._lock:
            try:
                self.pm.write_i32(self.fps_addr, self.target_fps)
                return True
            except OSError:
                return False

    def read_current(self):
        if not self.pm or not self.fps_addr:
            return None
        try:
            return self.pm.read_i32(self.fps_addr)
        except OSError:
            return None

    # ---- 保活线程：游戏会在读档 / 改画质时把 60 写回去
    def start_keepalive(self, interval=2.0, max_fail=3):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self.degraded = False
        self._thread = threading.Thread(target=self._loop, args=(interval, max_fail), daemon=True)
        self._thread.start()

    def _loop(self, interval, max_fail):
        fails = 0
        last = None
        while not self._stop.is_set():
            if self.pid and not is_alive(self.pid):
                self.log("游戏已退出，停止补写")
                break
            if not self.degraded:
                if self.apply():
                    fails = 0
                else:
                    fails += 1
                    if fails >= max_fail:
                        # 反作弊完成接管后外部句柄写不动了，继续重试没有意义，
                        # 但读通常还能读——转成只读监视，用来确认值有没有被游戏改回去
                        self.degraded = True
                        if self.patched:
                            self.log("游戏已接管进程内存，补写停止（代码段已加固，值应保持）")
                        else:
                            self.log("游戏已接管进程内存，无法继续补写（已写入的值可能被覆盖）")
            if self.degraded:
                v = self.read_current()
                if v is None:
                    if not self._read_blocked:
                        self._read_blocked = True
                        self.log("读取也被反作弊拒绝，停止监视")
                elif v != last:
                    last = v
                    if self.patched and v == self.target_fps:
                        self.log("监视：帧率变量 = %d（补丁生效）" % v)
                    else:
                        self.log("监视：帧率变量 = %d" % v)
            self._stop.wait(interval)

    def stop(self):
        self._stop.set()

    def release(self):
        self.stop()
        if self.pm:
            self.pm.close()
            self.pm = None


# ---------------------------------------------------------------- 启动 / 路径探测
def launch_game(exe_path):
    """以游戏自身目录为工作目录启动，避免启动参数/资源路径错乱"""
    return subprocess.Popen([exe_path], cwd=os.path.dirname(exe_path),
                            creationflags=0x00000008)  # DETACHED_PROCESS


def _reg_paths():
    out = []
    try:
        import winreg
    except Exception:
        return out

    def probe(root, path):
        try:
            with winreg.OpenKey(root, path) as k:
                for i in range(16):
                    try:
                        name, val, _ = winreg.EnumValue(k, i)
                    except OSError:
                        break
                    if isinstance(val, str) and val.lower().endswith(".exe"):
                        out.append(val)
                    elif isinstance(val, str) and os.path.isdir(val):
                        for exe in ("YuanShen.exe", "GenshinImpact.exe"):
                            out.append(os.path.join(val, exe))
        except OSError:
            pass

    # 米哈游启动器（HYP）记录的安装目录，最可靠
    for biz in ("hk4e_cn", "hk4e_global", "hk4e", "Genshin Impact"):
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                r"Software\miHoYo\HYP\1_1\%s" % biz) as k:
                folder, _ = winreg.QueryValueEx(k, "GameInstallPath")
                if isinstance(folder, str) and os.path.isdir(folder):
                    for exe in ("YuanShen.exe", "GenshinImpact.exe"):
                        out.append(os.path.join(folder, exe))
        except OSError:
            pass

    for root, path in (
        (winreg.HKEY_CURRENT_USER, r"Software\miHoYo\原神"),
        (winreg.HKEY_CURRENT_USER, r"Software\miHoYo\Genshin Impact"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\原神"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Genshin Impact"),
    ):
        probe(root, path)
    return out


def guess_game_paths():
    """返回可能存在的游戏可执行文件路径列表"""
    candidates = []

    for pid, _ in find_game_pids():
        try:
            for name, _b, _s, path in list_modules(pid):
                if name.lower() in GAME_EXE_NAMES:
                    candidates.append(path)
        except OSError:
            pass

    candidates.extend(_reg_paths())

    for drive in "CDEFGH":
        for sub in (
            r":\Program Files\Genshin Impact\Genshin Impact Game",
            r":\Program Files\Genshin Impact\Game",
            r":\Genshin Impact\Genshin Impact Game",
            r":\Program Files\YuanShen\Genshin Impact Game",
            r":\Games\Genshin Impact\Genshin Impact Game",
            r":\mihoyo\Genshin Impact Game",
        ):
            folder = drive + sub
            for exe in ("YuanShen.exe", "GenshinImpact.exe"):
                candidates.append(os.path.join(folder, exe))

    seen, result = set(), []
    for c in candidates:
        if not c:
            continue
        c = os.path.normpath(c)
        key = c.lower()
        if key in seen:
            continue
        seen.add(key)
        if os.path.isfile(c):
            result.append(c)
    return result
