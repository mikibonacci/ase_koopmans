"""Logging for molecular dynamics."""

import weakref
import sys
import ase_koopmans.units as units
# ase_koopmans.parallel imported in __init__


class MDLogger:
    """Class for logging molecular dynamics simulations.

    Parameters:
    dyn:           The dynamics.  Only a weak reference is kept.

    atoms:         The atoms.

    logfile:       File name or open file, "-" meaning standard output.

    stress=False:  Include stress in log.

    peratom=False: Write energies per atom.

    mode="a":      How the file is opened if logfile is a filename.
    """
    def __init__(self, dyn, atoms, logfile, header=True, stress=False,
                 peratom=False, mode="a"):
        import ase_koopmans.parallel
        if ase_koopmans.parallel.world.rank > 0:
            logfile="/dev/null"  # Only log on master
        if hasattr(dyn, "get_time"):
            self.dyn = weakref.proxy(dyn)
        else:
            self.dyn = None
        self.atoms = atoms
        global_natoms = atoms.get_global_number_of_atoms()
        if logfile == "-":
            self.logfile = sys.stdout
            self.ownlogfile = False
        elif hasattr(logfile, "write"):
            self.logfile = logfile
            self.ownlogfile = False
        else:
            self.logfile = open(logfile, mode, 1)
            self.ownlogfile = True
        self.stress = stress
        self.peratom = peratom
        if self.dyn is not None:
            self.hdr = "%-9s " % ("Time[ps]",)
            self.fmt = "%-10.4f "
        else:
            self.hdr = ""
            self.fmt = ""
        if self.peratom:
            self.hdr += "%12s %12s %12s  %6s" % ("Etot/N[eV]", "Epot/N[eV]",
                                                 "Ekin/N[eV]", "T[K]")
            self.fmt += "%12.4f %12.4f %12.4f  %6.1f"
        else:
            self.hdr += "%12s %12s %12s  %6s" % ("Etot[eV]", "Epot[eV]",
                                                 "Ekin[eV]", "T[K]")
            # Choose a sensible number of decimals
            if global_natoms <= 100:
                digits = 4
            elif global_natoms <= 1000:
                digits = 3
            elif global_natoms <= 10000:
                digits = 2
            else:
                digits = 1
            self.fmt += 3*("%%12.%df " % (digits,)) + " %6.1f"
        if self.stress:
            self.hdr += "      ---------------------- stress [GPa] -----------------------"
            self.fmt += 6*" %10.3f"
        self.fmt += "\n"
        if header:
            self.logfile.write(self.hdr+"\n")

    def __del__(self):
        self.close()

    def close(self):
        if self.ownlogfile:
            self.logfile.close()

    def __call__(self):
        epot = self.atoms.get_potential_energy()
        ekin = self.atoms.get_kinetic_energy()
        global_natoms = self.atoms.get_global_number_of_atoms()
        temp = ekin / (1.5 * units.kB * global_natoms)
        if self.peratom:
            epot /= global_natoms
            ekin /= global_natoms
        if self.dyn is not None:
            t = self.dyn.get_time() / (1000*units.fs)
            dat = (t,)
        else:
            dat = ()
        dat += (epot+ekin, epot, ekin, temp)
        if self.stress:
            dat += tuple(self.atoms.get_stress(include_ideal_gas=True) / units.GPa)
        self.logfile.write(self.fmt % dat)
        self.logfile.flush()
