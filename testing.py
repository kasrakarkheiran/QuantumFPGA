# Emulator
from emulator.emulator import Emulator

# Compiler and assembler for pulse commands, alu instructions, and jumps
import distproc.assembler as asm 
import distproc.compiler as cm
from distproc.compiler import CompilerFlags

# HW configurations and qubic toolchain
import distproc.hwconfig as hw
from distproc.hwconfig import FPGAConfig, load_channel_configs
import qubic.toolchain as tc
import qubitconfig.qchip as qc

# Misc
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import animation
from qutip import Bloch

channel_config = hw.load_channel_configs('config/channel_config.json')
Emulator.generate_hwcfg("config/hw_config.json", channel_config, "config/dsp_config.yaml", hw.FPGAConfig())
Emulator.generate_qubitcfg("config/em_qubit_config.json", "config/qubitcfg.json")

# Qubit configurations for the compiler
qchip = qc.QChip('config/qubitcfg.json')

# Define our circuit, for this first test, we will just simulate a single X90 gate on Q0.qdrv
prog = [{'name': 'X90', 'qubit': 'Q0'}]

# Compile and assemble the circuit to get the binaries to feed our emulator
compiled_prog = tc.run_compile_stage(prog, fpga_config=hw.FPGAConfig(), qchip=qchip)
binary = tc.run_assemble_stage(compiled_prog, channel_config)

 # Create the Emulator object with the following parameters:
# Emulator(chanconfig file path, hwconfig file path, qubitconfig_path file path)
em = Emulator(chanconfig_path='config/channel_config.json', hwconfig_path='config/hw_config.json', qubitconfig_path='config/em_qubit_config.json')

# Load the assembled binaries into the emulator, which will parse the command, envelope, and frequency buffers
em.load_program(binary)

# To confirm that the commands, frequencies, and envelopes were parsed and placed correctly, we can print them out from
# the core and channel
print("Q0.qubit Commands:", em.dist_proc.cores['Q0.qubit'].commands)
print("Q0.qdrv Envelope Buffer:", em.dist_proc.cores['Q0.qubit'].channels['Q0.qdrv'].env_buffers)
print("Q0.qdrv Frequency Buffer:", em.dist_proc.cores['Q0.qubit'].channels['Q0.qdrv'].freq_buffers)

# Tags for this simulation (For larger circuits these flood the command line, but for a single gate it should not be bad)
# These will get passed in when we execute
tags = ["DEBUG", "REGISTER", "FPROC"]

# Load an fproc instruction
fproc_instr = [{'core': 'Q0.qubit', 'time': 4, 'value': 1}]
em.load_fproc(fproc_instr)

 # Execute the X90 gate
result = em.execute(tags=tags, toggle_resonator=True, toggle_qubits=True)
print(result.__dict__)
result.animate_bloch('Q0')
plt.savefig('bloch_Q0_final_frame.png')