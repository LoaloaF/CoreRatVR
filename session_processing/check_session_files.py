import os
import h5py
from CustomLogger import CustomLogger as Logger

def get_fsize(full_fnamepath):
    fsize = os.path.getsize(full_fnamepath)
    return f"{fsize/1024:<{9}.2f} KB" if fsize < 1024**2 else f"{fsize/1024**2:<{9},.1f} MB"

def color_str(string, color):
    colors = {
        "red": "\033[1;31m",
        "yellow": "\033[1;33m",
        "green": "\033[1;32m",
        "blue": "\033[1;34m",
        "reset": "\033[0m"
    }
    return f"{colors[color]}{string}{colors['reset']}"

def format_data(data):
    # Find the longest key length for alignment
    max_subkey_len = 31

    # Create a formatted string
    result = ""
    for key, subdict in data.items():
        result += f"-----------\n{key}:\n"
        for subkey, value in subdict.items():
            result += f"  {subkey:<{max_subkey_len}} {value}\n"
    return result

def check_log_files(session_dir, fnames):
    # check if there are any critical warnings or errors in the log files
    # if so, print them out
    L = Logger()
    result = []
    
    for fn in sorted(fnames):
        L.logger.debug(f"Checking log file {fn}")    
        result.append("-----------")
        result.append(fn)
        if fn == 'unity.log':
            continue
        with open(os.path.join(session_dir, fn), 'r') as f:
            # check the size before reading
            if os.path.getsize(f.name) > 1e8: # 100 MB
                result.append("Exceptionally large logging file. Skipping.")
                continue
            
            try:
                lines = f.readlines()
            except UnicodeDecodeError as e:
                result.append(f"Error reading file: {e}")
                continue
            
            i = 0
            n_errors = sum(["ERROR" in line for line in lines])
            n_warnings = sum(["WARNING" in line for line in lines])
    
            err_msg = color_str(f"Errors: {n_errors}", "red" if n_errors else "green")
            result.append(err_msg)
            warning_msg = color_str(f"Warnings: {n_warnings}", "yellow" if n_warnings else "green")
            result.append(warning_msg)
            result.append("-----------")
            
            errors, warnings = [], []
            while i < len(lines):
                if "ERROR" in lines[i]:
                    # j indicates how many lines the message spans over
                    for j, line in enumerate(lines[i+1:]):
                        if "|" in line: break
                    errors.append("".join(lines[i:i+j+1]))
                    i += j
                    
                if "WARNING" in lines[i]:
                    # j indicates how many lines the message spans over
                    for j, line in enumerate(lines[i+1:]):
                        if "|" in line: break
                    warnings.append("".join(lines[i:i+j+1]))
                    i += j
                if len(warnings) > 20 or len(errors) > 20:
                    break
                else:
                    i += 1
            
            if len(errors) >20:
                errors = errors[:10] + [f"\t.. ({n_errors-20:,}) ..\n"] + errors[-10:]    
            if len(warnings) >20:
                warnings = warnings[:10] + [f"\t.. ({n_warnings-20:,}) ..\n"] + warnings[-10:]
            
            if L.logger.level <= 20:
                result.extend(errors)
                result.extend(warnings)
    return result        

def get_data_file_info(session_dir, fname):
    info = ''
    with h5py.File(os.path.join(session_dir, fname), 'r') as f:
        for key in list(f.keys()):
            key_str =  f"\n\t\'{key}\':"

            if 'table' in f[key]:
                info += f"{key_str:<29} {f[key]['table'].shape[0]:<5,} rows"
            else:
                info += f"{key_str:<29}"
    return info + '\n'

def check_file_existence(session_dir, fnames):
    expected_log_fnames = ( '__main__.log', 'portenta2shm2portenta.log', 'bodycam2shm.log', 'facecam2shm.log', 'log_bodycam.log', 'log_facecam.log', 'log_portenta.log', 'log_unity.log', 'log_unitycam.log')
    expected_data_fnames = ('portenta_output.hdf5', 'unitycam.hdf5', 'bodycam.hdf5', 'facecam.hdf5', 'unity_output.hdf5')
    expected_json_fnames = ('parameters.json', 'session_parameters.json')
    
    keys = "Log-Files", "Data-Files", "JSON-Files"
    result = dict(zip(keys, ({},{},{})))
    
    for key, which_fnamelist in zip(keys, [expected_log_fnames, expected_data_fnames,  expected_json_fnames]):
        for expec_fname in which_fnamelist:

            # check if file exists
            if expec_fname in fnames:
                info = get_fsize(os.path.join(session_dir, expec_fname))
                if key == "Data-Files":
                    info += get_data_file_info(session_dir, expec_fname)
                result[key][expec_fname] = info
                fnames.pop(fnames.index(expec_fname))
            else:
                result[key][expec_fname] = color_str("Missing!", "yellow")
              
    fsizes = [get_fsize(os.path.join(session_dir,fn)) for fn in fnames]
    result['Surplus-Files'] = dict(zip(fnames, fsizes))
    return result, format_data(result)