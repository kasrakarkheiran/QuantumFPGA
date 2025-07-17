
import sys

#Emulator
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
result = em.execute(tags=tags)

 # Graph the Q0.qdrv channel
result.graph_channel('Q0.qdrv')

 # Two rdrv simulation
# Define our circuit, for this DAC test, we will generate two pulses in seperate rdrv channels, and then visualize their added up DAC signal
prog = [{'name': 'X90', 'qubit': 'Q0'},
            {'name': 'barrier', 'qubit': 'Q0'},
            {'name': 'pulse', 'dest': 'Q0.rdrv', 'twidth': 100.e-9, 'amp': 0.5,
             'freq': 5.127e9, 'phase': 0, 'env': np.ones(50)},
            {'name': 'pulse', 'dest': 'Q2.rdrv', 'twidth': 100.e-9, 'amp': 0.5,
             'freq': 6.227e9, 'phase': 0, 'env': {'env_func': 'cos_edge_square', 
                                                  'paradict': {'ramp_fraction': 0.25}}}]

# Compile and assemble the circuit to get the binaries to feed our emulator
compiled_prog = tc.run_compile_stage(prog, fpga_config=hw.FPGAConfig(), qchip=qchip)
binary = tc.run_assemble_stage(compiled_prog, channel_config)

# Load and execute simulation
em.load_program(binary)
result = em.execute(tags=['DEBUG'])
result.graph_dac('DAC0') # rdrv channels belong to 0th dac
result.graph_channel('Q0.rdrv')
result.graph_channel('Q2.rdrv')
result.graph_multiple_channels(['DAC0', 'Q0.qdrv', 'Q2.rdrv'])

result.write_vcd('test.vcd', channels=['Q0.rdrv', 'Q2.rdrv', 'DAC0'])

prog = [{'name': 'pulse', 'phase': 0, 'freq': 6553826000.000857, 'amp': 1, 'twidth': 1e-6,
                'env': {'env_func': 'cos_edge_square', 'paradict': {'ramp_fraction': 0.15}},
                'dest': 'Q0.rdrv'},
        {'name': 'pulse', 'phase': 0, 'freq': 6553826000.000857, 'amp': 1, 'twidth': 1e-6,
                'env': {'env_func': 'cos_edge_square', 'paradict': {'ramp_fraction': 0.15}},
                'dest': 'Q0.rdlo'}]

# Compile and assemble the circuit to get the binaries to feed our emulator
compiled_prog = tc.run_compile_stage(prog, fpga_config=hw.FPGAConfig(), qchip=qchip)
binary = tc.run_assemble_stage(compiled_prog, channel_config)

# Load and execute simulation
em.load_program(binary)
result = em.execute(tags=['FPROC'], toggle_resonator=True, toggle_qubits=True)
result.graph_dac('DAC0') # rdrv channels belong to 0th dac
result.graph_adc('ADC0')
result.iq_values


#SWEEPING CIRCUIT
# Configuration and assembly
prog = [
    {'name': 'declare', 'var': 'loop_ind', 'scope': ['Q0']},
    {'name': 'set_var', 'value': 0, 'var': 'loop_ind'},
    {'name': 'declare', 'var': 'amp', 'scope': ['Q0'], 'dtype': 'amp'},
    {'name': 'set_var', 'value': 0.1, 'var': 'amp'}, # pulse amplitude is parameterized by processor register
    {'name': 'loop', 'cond_lhs': 10, 'alu_cond': 'ge', 'cond_rhs': 'loop_ind', 'scope': ['Q0'], 
    'body': [
            {'name': 'pulse', 'phase': 0, 'freq': 4460029188.07884, 'amp': 'amp', 'twidth': 2.4e-08,
            'env': {'env_func': 'cos_edge_square', 'paradict': {'ramp_fraction': 0.25}},
            'dest': 'Q0.qdrv'},
        {'name': 'alu', 'op': 'add', 'lhs': 1, 'rhs': 'loop_ind', 'out': 'loop_ind'},
        {'name': 'alu', 'op': 'add', 'lhs': 0.1, 'rhs': 'amp', 'out': 'amp'}
    ]}]
new_fpga_config = hw.FPGAConfig()
new_fpga_config.jump_cond_clks = 6
compiled_prog = tc.run_compile_stage(prog, fpga_config=new_fpga_config, qchip=qchip)
binary = tc.run_assemble_stage(compiled_prog, channel_config)

# Emulation
em.load_program(binary)
result = em.execute()
result.graph_channel('Q0.qdrv')

#BRANCHING CIRCUIT
rdlo_freq = 610000000
prog = [
    # initialize variables:
    {'name': 'declare', 'var': 'loop_ind', 'scope': ['Q0']},
    {'name': 'set_var', 'value': 0, 'var': 'loop_ind'},
    {'name': 'declare', 'var': 'amp', 'scope': ['Q0'], 'dtype': 'amp'},
    {'name': 'set_var', 'value': 0.1, 'var': 'amp'}, # pulse amplitude is parameterized by processor register
    
    {'name': 'loop', 'cond_lhs': 5, 'alu_cond': 'ge', 'cond_rhs': 'loop_ind', 'scope': ['Q0'], 
     'body': [
         
         # read (rdlo pulse):
        {'name': 'pulse', 'phase': 0, 'freq': rdlo_freq, 'amp': 0.9, 'twidth': 1.e-7,
         'env': {'env_func': 'cos_edge_square', 'paradict': {'ramp_fraction': 0.25}},
         'dest': 'Q0.rdrv'},
        {'name': 'pulse', 'phase': 0, 'freq': rdlo_freq, 'amp': 0.9, 'twidth': 1.e-7,
         'env': {'env_func': 'cos_edge_square', 'paradict': {'ramp_fraction': 0.25}},
         'dest': 'Q0.rdlo'},
         
        
         # Fill in branch_fproc + conditional amplitude increment here:
         {'name': 'branch_fproc', 'cond_lhs': 1, 'alu_cond': 'eq', 'func_id': 'Q0.meas',
          'true':[
              {'name': 'alu', 'op': 'add', 'lhs': 0.1, 'rhs': 'amp', 'out': 'amp'}
          ],
          'false': [], 'scope': ['Q0']},
         
         # pulse:
         {'name': 'pulse', 'phase': 0, 'freq': 4460029188.07884, 'amp': 'amp', 'twidth': 2.4e-08,
           'env': {'env_func': 'cos_edge_square', 'paradict': {'ramp_fraction': 0.25}},
           'dest': 'Q0.qdrv'},
         
         # increment loop counter
         {'name': 'alu', 'op': 'add', 'lhs': 1, 'rhs': 'loop_ind', 'out': 'loop_ind'}
     ] 
     }]
new_fpga_config = hw.FPGAConfig()
new_fpga_config.jump_cond_clks = 6
compiled_prog = tc.run_compile_stage(prog, fpga_config=new_fpga_config, qchip=qchip)
binary = tc.run_assemble_stage(compiled_prog, channel_config)

em.load_program(binary)
result = em.execute(tags=['FPROC'], toggle_resonator=True, toggle_qubits=True)
result.graph_channel('Q0.qdrv')

#CW PULSES
circuit = [
    # Play the CW pulse
    {'name': 'pulse', 'phase': 0, 'freq': 4658138379, 'amp': 0.5, 'twidth': 100e-9,
     'env': 'cw', 'dest': 'Q0.qdrv'},

    # Play the second pulse
    {'name': 'pulse', 'phase': 0, 'freq': 4658138379, 'amp': 1, 'twidth': 24e-9,
     'env': {'env_func': 'square', 'paradict': {'phase': 0.0, 'amplitude': 1.0}},
     'dest': 'Q0.qdrv'}
]

compiled_prog = tc.run_compile_stage(circuit, fpga_config=hw.FPGAConfig(), qchip=qchip)
binary = tc.run_assemble_stage(compiled_prog, channel_config)
em.load_program(binary)
result = em.execute()
result.graph_channel('Q0.qdrv')

#CW pulse with width set to 0
circuit = [
    # Play the CW pulse
    {'name': 'pulse', 'phase': 0, 'freq': 4658138379, 'amp': 0.5, 'twidth': 0,
     'env': 'cw', 'dest': 'Q0.qdrv'},

    # Allow CW pulse to run for 50 clock cycles
    {'name': 'delay', 't': 100.e-9}, 

    # Play the second pulse
    {'name': 'pulse', 'phase': 0, 'freq': 4658138379, 'amp': 1, 'twidth': 24e-9,
     'env': {'env_func': 'square', 'paradict': {'phase': 0.0, 'amplitude': 1.0}},
     'dest': 'Q0.qdrv'}
]

compiled_prog = tc.run_compile_stage(circuit, fpga_config=hw.FPGAConfig(), qchip=qchip)
binary = tc.run_assemble_stage(compiled_prog, channel_config)
em.load_program(binary)
result = em.execute()
result.graph_channel('Q0.qdrv')

#DC Pulses 
prog = [{'name': 'pulse', 'dest': 'C0.dc', 'twidth': 0, 'amp': 0.5,
             'freq': None, 'phase': 0, 'env': None},
             {'name': 'delay', 't': 20.e-9, 'scope': ['C0.dc']},
             {'name': 'pulse', 'dest': 'C0.dc', 'twidth': 0, 'amp': 0.0,
            'freq': None, 'phase': 0, 'env': None},
             {'name': 'delay', 't': 20.e-9, 'scope': ['C0.dc']},
             {'name': 'pulse', 'dest': 'C0.dc', 'twidth': 0, 'amp': 1.0,
             'freq': None, 'phase': 0, 'env': None},
             {'name': 'delay', 't': 20.e-9, 'scope': ['C0.dc']}]
compiled_prog = tc.run_compile_stage(prog, fpga_config=hw.FPGAConfig(), qchip=None, compiler_flags={'resolve_gates': False},
                                    proc_grouping=[('{qubit}.qdrv', '{qubit}.rdrv', '{qubit}.rdlo'),
                                                    ('{qubit}.qdrv2',),
                                                    ('{qubit}.cdrv', '{qubit}.dc')]) # Resolve gates = false, dont give it the qchip
binary = tc.run_assemble_stage(compiled_prog, channel_config)
em.load_program(binary)
result = em.execute()
result.graph_channel('C0.dc')