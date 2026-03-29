#########################################################################################
##
##     Heat pump cycle (R290) with Isentropic Efficiency — Parametric COP surface
##     Source: fwitte.github.io/intro-to-thermal-engineering/model/exercise-sm.html
##
##     PathView renders COP vs evaporation temperature for seven condensation
##     temperatures (40-70 deg C), capturing the same parametric data as the
##     3D COP surface plot.
##
##     Time axis: t=0..30 maps to T_evap = -15..+15 deg C
##
#########################################################################################

# IMPORTS ===============================================================================

import numpy as np
from CoolProp.CoolProp import PropsSI

from pathsim import Simulation, Connection
from pathsim.blocks import Source, Function, Scope
from pathsim.solvers import SSPRK22


# HEAT PUMP PARAMETERS ==================================================================

fluid = "R290"
eta_s = 0.8        # compressor isentropic efficiency
heat = -1e6        # condenser heat production [W] (1 MW)

# Condensation temperatures for parametric study [K]
t_cond_40 = 313.15
t_cond_45 = 318.15
t_cond_50 = 323.15
t_cond_55 = 328.15
t_cond_60 = 333.15
t_cond_65 = 338.15
t_cond_70 = 343.15


# THERMODYNAMIC FUNCTIONS ===============================================================

def run_forward(fluid, t_2, t_4, eta_s, heat):
    """Full cycle: returns (mass_flow, power, COP, heat_evap)."""
    p_2 = PropsSI("P", "T", t_2, "Q", 1, fluid)
    p_4 = PropsSI("P", "T", t_4, "Q", 0, fluid)
    h_2 = PropsSI("H", "T", t_2, "Q", 1, fluid)
    s_2 = PropsSI("S", "T", t_2, "Q", 1, fluid)
    p_3 = p_4
    h_3s = PropsSI("H", "S", s_2, "P", p_3, fluid)
    h_3 = h_2 + (h_3s - h_2) / eta_s
    h_4 = PropsSI("H", "T", t_4, "Q", 0, fluid)
    m = heat / (h_4 - h_3)
    power = m * (h_3 - h_2)
    cop = abs(heat) / power
    heat_evap = abs(heat) - power
    return m, power, cop, heat_evap


def cop_at(t_evap, t_cond):
    """COP for given evaporation and condensation temperatures [K]."""
    return run_forward(fluid, t_evap, t_cond, eta_s, heat)[2]


def power_at(t_evap, t_cond):
    """Compressor power [kW] for given temperatures [K]."""
    return run_forward(fluid, t_evap, t_cond, eta_s, heat)[1] / 1e3


# PATHSIM MODEL =========================================================================

dt = 1.0

# Source sweeps evaporation temp: t=0 -> -15 deg C (258.15 K), t=30 -> +15 deg C (288.15 K)
Tevap = Source(func=lambda t: 258.15 + t)

# COP at each condensation temperature
COP_40 = Function(func=lambda x: cop_at(x, t_cond_40))
COP_45 = Function(func=lambda x: cop_at(x, t_cond_45))
COP_50 = Function(func=lambda x: cop_at(x, t_cond_50))
COP_55 = Function(func=lambda x: cop_at(x, t_cond_55))
COP_60 = Function(func=lambda x: cop_at(x, t_cond_60))
COP_65 = Function(func=lambda x: cop_at(x, t_cond_65))
COP_70 = Function(func=lambda x: cop_at(x, t_cond_70))

# Power at 60 deg C condensation (reference case)
Pwr_60 = Function(func=lambda x: power_at(x, t_cond_60))

# Scopes
Sco_COP = Scope(labels=[
    "COP @ Tcond=40C",
    "COP @ Tcond=45C",
    "COP @ Tcond=50C",
    "COP @ Tcond=55C",
    "COP @ Tcond=60C",
    "COP @ Tcond=65C",
    "COP @ Tcond=70C",
])
Sco_Pwr = Scope(labels=["Power (kW) @ Tcond=60C"])

blocks = [
    Tevap,
    COP_40, COP_45, COP_50, COP_55, COP_60, COP_65, COP_70,
    Pwr_60,
    Sco_COP, Sco_Pwr,
]

connections = [
    Connection(Tevap, COP_40, COP_45, COP_50, COP_55, COP_60, COP_65, COP_70, Pwr_60),
    Connection(COP_40, Sco_COP[0]),
    Connection(COP_45, Sco_COP[1]),
    Connection(COP_50, Sco_COP[2]),
    Connection(COP_55, Sco_COP[3]),
    Connection(COP_60, Sco_COP[4]),
    Connection(COP_65, Sco_COP[5]),
    Connection(COP_70, Sco_COP[6]),
    Connection(Pwr_60, Sco_Pwr),
]

Sim = Simulation(blocks, connections, dt=dt, Solver=SSPRK22, log=True)


# RUN ====================================================================================

if __name__ == "__main__":
    import matplotlib.pyplot as plt
    import pandas as pd
    from matplotlib import cm
    from fluprodia import FluidPropertyDiagram

    Sim.run(30.0)
    Sco_COP.plot()
    Sco_Pwr.plot()

    # --- 3D surface plot (standalone only) ---
    t_2_range = np.linspace(-15, 15, 31)
    t_4_range = np.linspace(40, 70, 31)

    cop_parametric = pd.DataFrame(index=t_2_range, columns=t_4_range)
    for t2_val in t_2_range:
        _, _, cop_val, _ = run_forward(fluid, t2_val + 273.15, t_4_range + 273.15, eta_s, heat)
        cop_parametric.loc[t2_val] = cop_val

    fig4, ax4 = plt.subplots(1, figsize=(12, 7.5), subplot_kw={"projection": "3d"})
    X, Y = np.meshgrid(t_4_range, t_2_range)
    surf = ax4.plot_surface(X, Y, cop_parametric.values, cmap=cm.coolwarm, linewidth=0, antialiased=False)
    ax4.set_xlabel("Condensation temperature in °C")
    ax4.set_ylabel("Evaporation temperature in °C")
    ax4.set_zlabel("COP")
    ax4.view_init(elev=30, azim=225)
    ax4.set_box_aspect(aspect=None, zoom=0.9)
    fig4.colorbar(surf, shrink=0.5, aspect=15)
    plt.tight_layout()

    # --- T-s diagram (standalone only) ---
    t_2 = 283.15
    t_4 = 333.15

    p_2 = PropsSI("P", "T", t_2, "Q", 1, fluid)
    p_4 = PropsSI("P", "T", t_4, "Q", 0, fluid)
    p_1 = p_2
    p_3 = p_4

    h_2 = PropsSI("H", "T", t_2, "Q", 1, fluid)
    s_2 = PropsSI("S", "T", t_2, "Q", 1, fluid)
    h_3s = PropsSI("H", "S", s_2, "P", p_3, fluid)
    h_3 = h_2 + (h_3s - h_2) / eta_s
    h_4 = PropsSI("H", "T", t_4, "Q", 0, fluid)
    h_1 = h_4

    diagram = FluidPropertyDiagram(fluid)
    diagram.set_unit_system(T="°C", h="kJ/kg")
    diagram.set_isolines(
        T=np.arange(-25, 101, 25),
        s=np.arange(1250, 3001, 250),
        h=np.arange(100, 801, 100)
    )
    diagram.calc_isolines()

    fig, ax = plt.subplots(1, figsize=(12, 6))
    diagram.draw_isolines(fig, ax, "Ts", 1000, 2500, -25, 125)

    t = []
    s = []
    for p, h in zip([p_1, p_2, p_3, p_4], [h_1, h_2, h_3, h_4]):
        t += [PropsSI("T", "P", p, "H", h, fluid) - 273.15]
        s += [PropsSI("S", "P", p, "H", h, fluid)]

    ax.scatter(s, t)

    lines = {
        "12": {
            "isoline_property": "p",
            "isoline_value": p_1,
            "starting_point_property": "h",
            "starting_point_value": h_1 / 1e3,
            "ending_point_property": "h",
            "ending_point_value": h_2 / 1e3
        },
        "23": {
            "isoline_property": "s",
            "isoline_value": s[1],
            "isoline_value_end": s[2],
            "starting_point_property": "p",
            "starting_point_value": p_2,
            "ending_point_property": "p",
            "ending_point_value": p_3
        },
        "34": {
            "isoline_property": "p",
            "isoline_value": p_3,
            "starting_point_property": "h",
            "starting_point_value": h_3 / 1e3,
            "ending_point_property": "h",
            "ending_point_value": h_4 / 1e3
        },
        "41": {
            "isoline_property": "h",
            "isoline_value": h_4 / 1e3,
            "starting_point_property": "p",
            "starting_point_value": p_4,
            "ending_point_property": "p",
            "ending_point_value": p_1
        },
    }

    for line in lines.values():
        line_data = diagram.calc_individual_isoline(**line)
        ax.plot(line_data["s"], line_data["T"], color="#FF0000")

    ax.set_ylabel("temperature in °C")
    ax.set_xlabel("entropy in J/kgK")
    plt.tight_layout()

    plt.show()
