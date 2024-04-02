from os import environ, path
from glob import glob

import paramiko
import scp
import sys
import math
import re
import tempfile
import os


envs = environ
INPUT_HOST = envs.get("INPUT_HOST")
INPUT_PORT = int(envs.get("INPUT_PORT", "22"))
INPUT_USER = envs.get("INPUT_USER")
INPUT_PASS = envs.get("INPUT_PASS")
INPUT_KEY = envs.get("INPUT_KEY")
INPUT_CONNECT_TIMEOUT = envs.get("INPUT_CONNECT_TIMEOUT", "30s")
INPUT_SCP = envs.get("INPUT_SCP")
INPUT_LOCAL = envs.get("INPUT_LOCAL")
INPUT_REMOTE = envs.get("INPUT_REMOTE")
INPUT_SCRIPT = envs.get("INPUT_SCRIPT")

seconds_per_unit = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800, "M": 86400*30}
pattern_seconds_per_unit = re.compile(r'^(' + "|".join(['\\d+'+k for k in seconds_per_unit.keys()]) + ')$')


def convert_to_seconds(s):
    if s is None:
        return 30
    if isinstance(s, str):
        return int(s[:-1]) * seconds_per_unit[s[-1]] if pattern_seconds_per_unit.search(s) else 30
    if (isinstance(s, int) or isinstance(s, float)) and not math.isnan(s):
        return round(s)
    return 30


strips = [" ", "\"", " ", "'", " "]


def strip_and_parse_envs(p):
    if not p:
        return None
    for c in strips:
        p = p.strip(c)
    return path.expandvars(p) if p != "." else f"{path.realpath(p)}/*"


def connect():
    tmp = tempfile.NamedTemporaryFile(delete=False)
    try:
        ssh = paramiko.SSHClient()
        p_key = None
        if INPUT_KEY:
            tmp.write(INPUT_KEY.encode())
            tmp.close()
            p_key = paramiko.RSAKey.from_private_key_file(filename=tmp.name)
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(INPUT_HOST, port=INPUT_PORT, username=INPUT_USER,
                    pkey=p_key, password=INPUT_PASS,
                    timeout=convert_to_seconds(INPUT_CONNECT_TIMEOUT))
        return ssh
    finally:
        os.unlink(tmp.name)
        tmp.close()


# Define progress callback that prints the current percentage completed for the file
def progress(filename, size, sent):
    sys.stdout.write(f"{filename}... {float(sent)/float(size)*100:.2f}%\n")


def scp_process():
    if (INPUT_KEY is None and INPUT_PASS is None) or (not INPUT_SCP and not (INPUT_LOCAL and INPUT_REMOTE)):
        print("SCP invalid (Script/Key/Passwd)")
        return

    print("+++++++++++++++++++Pipeline: RUNNING SCP+++++++++++++++++++")

    copy_list = []
    if INPUT_LOCAL and INPUT_REMOTE:
        copy_list.append({
            "l": strip_and_parse_envs(INPUT_LOCAL),
            "r": strip_and_parse_envs(INPUT_REMOTE)
        })
    for c in INPUT_SCP.splitlines():
        if not c:
            continue
        l2r = c.split("=>")
        if len(l2r) == 2:
            local = strip_and_parse_envs(l2r[0])
            remote = strip_and_parse_envs(l2r[1])
            if local and remote:
                copy_list.append({"l": local, "r": remote})
                continue
        print(f"SCP ignored {c.strip()}")
    print(copy_list)

    if len(copy_list) <= 0:
        print("SCP no copy list found")
        return

    with connect() as ssh:
        with scp.SCPClient(ssh.get_transport(), progress=progress, sanitize=lambda x: x) as conn:
            for l2r in copy_list:
                remote = l2r.get('r')
                ssh.exec_command(f"mkdir -p {remote} || true")
                for f in [f for f in glob(l2r.get('l'))]:
                    conn.put(f, remote_path=remote, recursive=True)
                    print(f"{f} -> {remote}")
    execute_commands()
       
      
        
def execute_commands():
    with connect() as ssh:
        print("执行开始")
        # 将字符串按行分割成命令列表
        commands = INPUT_SCRIPT.split('\n')
        commands=" ;".join(list(filter(lambda x: x.strip() != "", commands)))
        try:
            print("命令",command)
            ssh.exec_command(command)
        except Exception as e:
            # 如果命令执行失败，则打印错误信息
            print(f"Command '{command}' failed with error: {e}")
if __name__ == '__main__':
    scp_process()





