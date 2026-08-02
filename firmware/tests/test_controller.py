import unittest
import shutil
import subprocess
import tempfile
from pathlib import Path

class StateMachineContract(unittest.TestCase):
    def test_required_states_and_safe_defaults(self):
        h=Path(__file__).parents[1]/'src/controller.h'; s=h.read_text()
        for name in ('OFF','ARMING','SOFT_START','RUN','OVERCURRENT','UNDERVOLTAGE','OVERTEMPERATURE','INPUT_FAULT','FAULT_LATCHED'):
            self.assertIn(name,s)
        self.assertIn('float duty = 0.0f',s)
        self.assertIn('State fault_reason = State::OFF',s)
    def test_configured_targets(self):
        s=(Path(__file__).parents[1]/'src/config.h').read_text()
        for value in ('15.0f','16.5f','40.0f','90.0f','20000.0f'):
            self.assertIn(value,s)

    def test_cpp_state_machine_when_compiler_available(self):
        compiler = shutil.which('g++') or shutil.which('clang++')
        if not compiler:
            self.skipTest('no host C++ compiler; run firmware/tests/controller_test.cpp in CI')
        firmware = Path(__file__).parents[1]
        with tempfile.TemporaryDirectory() as td:
            executable = Path(td) / ('controller_test.exe' if Path(compiler).name.lower().startswith('g++') and __import__('os').name == 'nt' else 'controller_test')
            subprocess.run([
                compiler, '-std=c++17', '-Wall', '-Wextra', '-Werror',
                '-I', str(firmware / 'src'),
                str(firmware / 'src/controller.cpp'),
                str(firmware / 'tests/controller_test.cpp'),
                '-o', str(executable),
            ], check=True)
            subprocess.run([str(executable)], check=True)
if __name__=='__main__': unittest.main()
