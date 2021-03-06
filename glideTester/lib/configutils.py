

class KeyValueConfig():

    def __init__(self, content = None):
        self.settings = {}
        if content != None:
            self.load_string(content)
    
    def load_string(self, content, key_prefix = None, key_mapper = None, value_mapper = None):
        lines = content.splitlines()
        for ln in lines:
            no_comment = ln.split('#', 1)[0].strip()
            if len(no_comment) == 0 or no_comment.isspace():
                continue 
            pair = [itm.strip() for itm in no_comment.split('=', 1)]
            assert(len(pair) == 2)
            key = pair[0]
            if key_mapper is not None:
                key = key_mapper(key)
            if key_prefix is not None: 
                if not key.startswith(key_prefix):
                    continue 
                else:
                    key = key[len(key_prefix):]
            value = pair[1]
            if value_mapper is not None:
                value = value_mapper(value)
            self.settings[key] = value

def get_config_file_list(file_name = None, arg_path = None):
    import os 

    retval = []

    if arg_path is not None: 
        if not os.path.exists(arg_path):
            raise RuntimeError, "Error creating config file list: %s is not a valid path."%(str(arg_path))
        elif os.path.isfile(arg_path) and file_name is None:
            file_name = os.path.basename(arg_path)
        print('CFG ARG PATH: %s'%(str(arg_path)))
        retval.append(arg_path)
    if file_name is None:
        file_name = ''
    cur_path = os.path.dirname(os.path.abspath(__file__))
    default_directories = ['~/.config/glideTester', '/etc/glideTester', os.path.join(cur_path, '../etc')]
    possible_defaults = [os.path.join(dir_name, file_name) for dir_name in default_directories]
    defaults = [default_path for default_path in possible_defaults if os.path.exists(default_path)]

    retval.extend(defaults)

    return retval


def parse_kv_file(file_name, key_prefix = None, key_mapper = None, value_mapper = None):
    fl = open(file_name, 'r')
    fl_content = fl.read()
    conf = KeyValueConfig()
    conf.load_string(fl_content, key_prefix=key_prefix, key_mapper=key_mapper)
    fl.close()
    return conf


def parse_argv(args, valid_flags = None, valid_kv_settings = None, key_markers = ['--', '-']):
    if args is None or len(args) <= 0:
        return {}
    retval = {}
    idx = 0
    print('Parsing args: %s'%(str(args)))
    while idx + 1 < len(args):
        key = args[idx]
        if not _starts_with_any(key, key_markers):
            raise RuntimeError, "Could not parse key arg %s"%(str(key))
        next_item = args[idx + 1]
        if _starts_with_any(next_item, key_markers):
            if valid_flags is not None and key not in valid_flags:
                raise RuntimeError, "Invalid flag :%s. Flags must be one of %s."%(str(key), str(valid_flags))
            retval[key] = True 
        else:
            if valid_kv_settings is not None and key not in valid_kv_settings:
                raise RuntimeError, "Invalid parameter %s with value %s. The parameters must be one of %s."%(str(key), str(next_item), str(valid_kv_settings))
            retval[key] = next_item
            idx += 1
        idx += 1
    return retval

def _starts_with_any(item, prefix_list):
    prefix_checker = lambda prefix: item.startswith(prefix)
    return any(map(prefix_checker, prefix_list))