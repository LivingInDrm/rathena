"""Silent wrapper for npc_cn_translate - redirects all output to log file."""
import sys
import os

log_path = r'D:\Projects\rathena\tmp\translate_run2.log'
os.makedirs(os.path.dirname(log_path), exist_ok=True)

with open(log_path, 'w', encoding='utf-8') as log:
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = log
    sys.stderr = log
    try:
        sys.argv = ['npc_cn_translate.py', '--no-backup']
        sys.path.insert(0, os.path.dirname(__file__))
        import npc_cn_translate
        npc_cn_translate.main()
    except Exception as e:
        log.write(f'\nFATAL ERROR: {e}\n')
        import traceback
        traceback.print_exc(file=log)
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr

print('Translation complete. See log:', log_path)
