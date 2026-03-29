#########################################################################################
##
##     Heat pump cycle (R290) — COP and power vs. evaporation temperature
##     Source: fwitte.github.io/intro-to-thermal-engineering/model/exercise-sm.html
##
#########################################################################################

# IMPORTS ===============================================================================

import numpy as np
import matplotlib.pyplot as plt

from CoolProp.CoolProp import PropsSI

from pathsim import Simulation, Connection

from pathsim.blocks import (
    Source,
    Function,
    Scope
    )

from pathsim.solvers import SSPRK22


# HEAT PUMP PARAMETERS ==================================================================

fluid = "R290"
t_cond = 333.15   # condenser outlet temperature [K] (60 °C)
eta_s = 0.8        # compressor isentropic efficiency
q_cond = -1e6      # condenser heat production [W] (1 MW)


# THERMODYNAMIC FUNCTIONS ===============================================================

def compute_cop(t_evap):
    """Compute real COP for given evaporation temperature [K]."""
    p_cond = PropsSI("P", "T", t_cond, "Q", 0, fluid)
    h_2 = PropsSI("H", "T", t_evap, "Q", 1, fluid)
    s_2 = PropsSI("S", "T", t_evap, "Q", 1, fluid)
    h_3s = PropsSI("H", "S", s_2, "P", p_cond, fluid)
    h_3 = h_2 + (h_3s - h_2) / eta_s
    h_4 = PropsSI("H", "T", t_cond, "Q", 0, fluid)
    m = q_cond / (h_4 - h_3)
    power = m * (h_3 - h_2)
    return abs(q_cond) / power


def compute_power_kw(t_evap):
    """Compute compressor power [kW] for given evaporation temperature [K]."""
    p_cond = PropsSI("P", "T", t_cond, "Q", 0, fluid)
    h_2 = PropsSI("H", "T", t_evap, "Q", 1, fluid)
    s_2 = PropsSI("S", "T", t_evap, "Q", 1, fluid)
    h_3s = PropsSI("H", "S", s_2, "P", p_cond, fluid)
    h_3 = h_2 + (h_3s - h_2) / eta_s
    h_4 = PropsSI("H", "T", t_cond, "Q", 0, fluid)
    m = q_cond / (h_4 - h_3)
    return m * (h_3 - h_2) / 1e3


# PATHSIM MODEL =========================================================================

# simulation timestep
dt = 1.0

# Source sweeps evaporation temp from -15 °C to +15 °C over 30 s
Tevap = Source(func=lambda t: 258.15 + t)

# Function blocks compute thermodynamic quantities
COP_fn = Function(func=lambda x: compute_cop(x))
Carnot_fn = Function(func=lambda x: t_cond / (t_cond - x))
Pwr_fn = Function(func=lambda x: compute_power_kw(x))

# Scopes to record results
Sco_COP = Scope(labels=["COP (R290)", "COP (Carnot)"])
Sco_Pwr = Scope(labels=["Power (kW)"])

blocks = [Tevap, COP_fn, Carnot_fn, Pwr_fn, Sco_COP, Sco_Pwr]

connections = [
    Connection(Tevap, COP_fn, Carnot_fn, Pwr_fn),
    Connection(COP_fn, Sco_COP[0]),
    Connection(Carnot_fn, Sco_COP[1]),
    Connection(Pwr_fn, Sco_Pwr)
    ]

Sim = Simulation(blocks, connections, dt=dt, Solver=SSPRK22, log=True)


# RUN ====================================================================================

if __name__ == "__main__":

    Sim.run(30.0)

    Sco_COP.plot()
    Sco_Pwr.plot()

    plt.show()
