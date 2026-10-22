#!/usr/bin/env python3
# Particle-array benchmark: uniform air flow in a 3D box with BENCH_NP particles spread over the whole domain, moving with the
# flow so they cross rank boundaries. Fixed dt and BENCH_STEPS steps. BENCH_GRID scales the 200x100x100 grid.
import argparse
import json
import os
import random

parser = argparse.ArgumentParser()
parser.add_argument("--mfc", type=json.loads, default="{}")
args = parser.parse_args()

n_particles = int(float(os.environ.get("BENCH_NP", "100000")))
steps = int(os.environ.get("BENCH_STEPS", "100"))
scale = float(os.environ.get("BENCH_GRID", "1"))

Lx, Ly, Lz = 2.0, 1.0, 1.0
Nx, Ny, Nz = int(200 * scale), int(100 * scale), int(100 * scale)
U = 50.0  # flow and initial particle velocity
p0, rho0, gamma = 101325.0, 1.2, 1.4
rp = 1.0e-4
dt = 0.4 * (Lx / Nx) / (U + (gamma * p0 / rho0) ** 0.5)

if args.mfc.get("command") == "run" and "pre_process" in args.mfc.get("targets", []):
    random.seed(1)
    indir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "input")
    os.makedirs(indir, exist_ok=True)
    with open(os.path.join(indir, "particles.dat"), "w") as f:
        for _ in range(n_particles):
            x = random.uniform(0.1 * Lx, 0.9 * Lx)
            y = random.uniform(rp, Ly - rp)
            z = random.uniform(rp, Lz - rp)
            f.write(f"{x:.10e} {y:.10e} {z:.10e} {U} 0.0 0.0 {rp}\n")

print(
    json.dumps(
        {
            "run_time_info": "F",
            "x_domain%beg": 0.0,
            "x_domain%end": Lx,
            "y_domain%beg": 0.0,
            "y_domain%end": Ly,
            "z_domain%beg": 0.0,
            "z_domain%end": Lz,
            "m": Nx - 1,
            "n": Ny - 1,
            "p": Nz - 1,
            "dt": dt,
            "t_step_start": 0,
            "t_step_stop": steps,
            "t_step_save": steps,
            "model_eqns": 2,
            "num_fluids": 1,
            "num_patches": 1,
            "time_stepper": 3,
            "weno_order": 5,
            "weno_eps": 1.0e-16,
            "mapped_weno": "T",
            "riemann_solver": 2,
            "wave_speeds": 1,
            "avg_state": 2,
            "bc_x%beg": -3,
            "bc_x%end": -3,
            "bc_y%beg": -15,
            "bc_y%end": -15,
            "bc_z%beg": -15,
            "bc_z%end": -15,
            "format": 1,
            "precision": 2,
            "prim_vars_wrt": "T",
            "parallel_io": "T",
            "patch_icpp(1)%geometry": 9,
            "patch_icpp(1)%x_centroid": Lx / 2,
            "patch_icpp(1)%y_centroid": Ly / 2,
            "patch_icpp(1)%z_centroid": Lz / 2,
            "patch_icpp(1)%length_x": Lx,
            "patch_icpp(1)%length_y": Ly,
            "patch_icpp(1)%length_z": Lz,
            "patch_icpp(1)%vel(1)": U,
            "patch_icpp(1)%vel(2)": 0.0,
            "patch_icpp(1)%vel(3)": 0.0,
            "patch_icpp(1)%pres": p0,
            "patch_icpp(1)%alpha_rho(1)": rho0,
            "patch_icpp(1)%alpha(1)": 1.0,
            "fluid_pp(1)%eos": "ideal_gas",
            "fluid_pp(1)%gamma": 1.0 / (gamma - 1.0),
            "fluid_pp(1)%cv": 717.5,
            "particles_lagrange": "T",
            "fd_order": 2,
            "particle_pp%rho0ref_particle": 2520.0,
            "particle_params%input_path": "input/particles.dat",
            "particle_params%nparticles_glb": n_particles,
            "particle_params%coupling": "two_way",
            "particle_params%vel_model": 2,
            "particle_params%qs_force": 3,
            "particle_params%pressure_gradient_force": "T",
            "particle_params%added_mass_force": 1,
            "particle_params%mu_ref(1)": 1.716e-5,
            "particle_params%interpolation_order": 2,
            "particle_params%epsilonb": 1.0,
            "particle_params%valmaxvoid": 0.9,
        }
    )
)
