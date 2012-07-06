#!/usr/bin/env python
"""
Test that autopep8 runs without crashing on various Python files.
"""
import os
import sys
import subprocess
import tempfile


def run(filename, log_file, fast_check=False, passes=2000,
        ignore=''):
    """Run autopep8 on file at filename.
    Return True on success.
    """
    ignore_option = '--ignore=' + ignore

    autopep8_path = os.path.split(os.path.abspath(
            os.path.dirname(__file__)))[0]
    autoppe8_bin = os.path.join(autopep8_path, 'autopep8.py')
    command = [autoppe8_bin, '--pep8-passes={p}'.format(p=passes),
               ignore_option, filename]

    if fast_check:
        if 0 != subprocess.call(command + ['--diff'], stderr=log_file):
            log_file.write('autopep8 crashed on ' + filename + '\n')
            return False
    else:
        with tempfile.NamedTemporaryFile(suffix='.py') as tmp_file:
            if 0 != subprocess.call(command, stdout=tmp_file, stderr=log_file):
                log_file.write('autopep8 crashed on ' + filename + '\n')
                return False

            if 0 != subprocess.call(['pep8', ignore_option,
                                     '--show-source', tmp_file.name],
                                    stderr=tmp_file):
                log_file.write('autopep8 did not completely fix ' +
                               filename + '\n')

            try:
                if _check_syntax(filename):
                    try:
                        _check_syntax(tmp_file.name, raise_error=True)
                    except (SyntaxError, TypeError) as exception:
                        log_file.write('autopep8 broke ' + filename + '\n' +
                                       str(exception) + '\n')
                        return False
            except IOError as exception:
                log_file.write(str(exception) + '\n')

    return True


def _detect_encoding(filename):
    """Return file encoding."""
    try:
        # Python 3
        try:
            with open(filename, 'rb') as input_file:
                import tokenize
                encoding = tokenize.detect_encoding(input_file.readline)[0]

            # Check for correctness of encoding
            with open(filename, encoding=encoding) as input_file:
                input_file.read()

            return encoding
        except (SyntaxError, LookupError, UnicodeDecodeError):
            return 'latin-1'
    except AttributeError:
        return 'utf-8'


def _open_with_encoding(filename, encoding, mode='r'):
    """Open file with a specific encoding."""
    try:
        # Python 3
        return open(filename, mode=mode, encoding=encoding)
    except TypeError:
        return open(filename, mode=mode)


def _check_syntax(filename, raise_error=False):
    """Return True if syntax is okay."""
    with _open_with_encoding(filename, _detect_encoding(filename)) as f:
        try:
            compile(f.read(), '<string>', 'exec')
            return True
        except (SyntaxError, TypeError):
            if raise_error:
                raise
            else:
                return False


def main():
    import optparse
    parser = optparse.OptionParser()
    parser.add_option('--fast-check', action='store_true',
                      help='ignore incomplete PEP8 fixes and broken files')
    parser.add_option('--log-errors',
                      help='log autopep8 errors instead of exiting')
    parser.add_option('--ignore',
                      help='comma-separated errors to ignore',
                      default='')
    parser.add_option('-p', '--pep8-passes',
                      help='maximum number of additional pep8 passes'
                           ' (default: %default)',
                      default=2000)
    opts, args = parser.parse_args()

    if opts.log_errors:
        log_file = open(opts.log_errors, 'w')
    else:
        log_file = sys.stderr

    if args:
        dir_paths = args
    else:
        dir_paths = sys.path

    try:
        filenames = dir_paths
        while filenames:
            name = filenames.pop(0)
            if os.path.isdir(name):
                for root, _, children in os.walk(name):
                    filenames += [os.path.join(root, f) for f in children
                                  if f.endswith('.py')]
            else:
                sys.stderr.write('--->  Testing with ' + name + '\n')

                if not run(os.path.join(name),
                        log_file=log_file,
                        fast_check=opts.fast_check,
                        ignore=opts.ignore,
                        passes=opts.pep8_passes):
                    if not opts.log_errors:
                        sys.exit(1)
    finally:
        # Only close if it is an actual log file
        if opts.log_errors:
            log_file.close()


if __name__ == '__main__':
    main()
