#########################################################################################
##
##                    PathSim Example: Kalman Filter State Estimation
##
#########################################################################################

# IMPORTS ===============================================================================

import numpy as np
import matplotlib.pyplot as plt

from pathsim import Simulation, Connection
from pathsim.blocks import (
    Constant,
    Integrator,
    Adder,
    WhiteNoise,
    KalmanFilter,
    Scope
)


# KALMAN FILTER FOR POSITION/VELOCITY TRACKING =========================================

# Simulation parameters
dt = 0.05  # timestep

# True system: object moving with constant velocity
v_true = 2.0  # m/s
x0_true = 0.0  # initial position

# Measurement noise characteristics
measurement_std = 0.2  # standard deviation of position sensor noise

# Kalman filter parameters
F = np.array([[1, dt], [0, 1]])        # state transition (constant velocity model)
H = np.array([[1, 0]])                 # measurement matrix (measure position only)

# Process noise covariance - models uncertainty in constant velocity assumption
# Derived from continuous-time noise with intensity q = 0.1
q = 0.1  # process noise intensity (m/s^2)^2
Q = np.array([
    [dt**3/3, dt**2/2],
    [dt**2/2, dt]
]) * q

R = np.array([[measurement_std**2]])   # measurement noise covariance
x0_kf = np.array([0, 0])               # initial estimate [position, velocity]
P0_kf = np.diag([1.0, 1.0])            # initial covariance (more realistic uncertainty)

# Build the system -----------------------------------------------------------------------

# True system
vel = Constant(v_true)
pos = Integrator(x0_true)

# Noisy measurement (spectral_density must be scaled by dt for discrete-time white noise)
noise = WhiteNoise(spectral_density=measurement_std**2 * dt)
measured_pos = Adder()

# Kalman filter
kf = KalmanFilter(F, H, Q, R, x0=x0_kf, P0=P0_kf)

# Scopes for recording (organized by what we're comparing)
sc_pos = Scope(labels=["true position", "measured position", "estimated position"])
sc_vel = Scope(labels=["true velocity", "estimated velocity"])

blocks = [vel, pos, noise, measured_pos, kf, sc_pos, sc_vel]

# Connections
connections = [
    Connection(vel, pos, sc_vel[0]),
    Connection(pos, measured_pos[0], sc_pos[0]),
    Connection(noise, measured_pos[1]),
    Connection(measured_pos, kf, sc_pos[1]),
    Connection(kf[0], sc_pos[2]),
    Connection(kf[1], sc_vel[1])
]

# Initialize simulation
Sim = Simulation(
    blocks,
    connections,
    dt=dt,
)


# Run Example ===========================================================================

if __name__ == "__main__":

    # Run the simulation
    Sim.run(duration=20)

    # Plot position comparison using scope's plot method
    fig1, ax1 = sc_pos.plot()
    ax1.set_title('Kalman Filter: Position Estimation')
    ax1.set_ylabel('Position [m]')
    ax1.set_xlabel('Time [s]')

    # Plot velocity comparison using scope's plot method
    fig2, ax2 = sc_vel.plot()
    ax2.set_title('Kalman Filter: Velocity Estimation')
    ax2.set_ylabel('Velocity [m/s]')
    ax2.set_xlabel('Time [s]')

    # Calculate and plot estimation errors
    t_pos, [pos_true, pos_meas, pos_est] = sc_pos.read()
    t_vel, [vel_true, vel_est] = sc_vel.read()

    pos_error = np.abs(pos_est - pos_true)
    vel_error = np.abs(vel_est - vel_true)

    fig3, (ax3, ax4) = plt.subplots(2, 1, figsize=(8, 6), tight_layout=True, dpi=120)

    ax3.plot(t_pos, pos_error)
    ax3.set_ylabel('Position Error [m]')
    ax3.set_title('Kalman Filter Estimation Error')

    ax4.plot(t_vel, vel_error)
    ax4.set_ylabel('Velocity Error [m/s]')
    ax4.set_xlabel('Time [s]')

    plt.show()