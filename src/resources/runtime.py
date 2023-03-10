import io,os,sys,time,threading,ctypes,inspect,traceback,textwrap,pathlib
import logging

from os.path import dirname, join

### Logging
root = logging.getLogger()
root.setLevel(logging.DEBUG)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('RUNTIME::%(levelname)s::%(name)s (at %(asctime)s) - %(message)s')
handler.setFormatter(formatter)
root.addHandler(handler)

###

class System:
    CurrentPath = os.listdir(pathlib.Path(__file__).parent.resolve())

    def File(name, format):
        path = join(dirname(__file__), name)
        return open(path, format)

def indent(text, amount, ch='\t'):
    return textwrap.indent(text, amount * ch)

def _async_raise(tid, exctype):
    tid = ctypes.c_long(tid)
    if not inspect.isclass(exctype):
        exctype = type(exctype)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("invalid thread id")
    elif res != 1:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
        raise SystemError("Timeout Exception")

def stop_thread(thread):
    _async_raise(thread.ident, SystemExit)

import types

wrap = '''\
{code}
try:
    {name}()
except Exception as e:
    print(e)
'''

func_template = '''\
def {name}(args):
{body}
'''

def getConstants(function):
    f_code = function.__code__
    return f_code.co_consts

def build(name, code, local={}):
    builtins = {
        "returner":""
    }
    final_string = wrap.format(
            code = 
            func_template.format(
                name = name,
                body = indent(code, 1)
            ),
            name = name
        )
    code_obj = compile(
        final_string,
        '<string>',
        'exec'
    )
    func_typed = types.FunctionType(code_obj.co_consts[0], {**builtins, **globals(), **local})
    return func_typed

def text_thread_run(name, code, args, return_store):
    try:
        return_store.append(build(name, code)(args))
    except Exception as e:
        print(e)

#   This is the code to run Text functions...
def mainTextCode(name, code, args, output):
    global thread1
    return_store = []
    thread1 = threading.Thread(target=text_thread_run, args=(name, code, args, return_store),daemon=True)
    thread1.start()
    thread1.join()
    sys.stdout = output
    if len(return_store) >= 1:
        print(return_store[0])
        return return_store[0]
    else:
        return return_store
