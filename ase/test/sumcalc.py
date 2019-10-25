"""This test checks the basic functionality of the SumCalculator.
The example system is based on the SinglePointCalculator test case.
"""
import numpy as np

from ase.build import fcc111
from ase.calculators.emt import EMT
from ase.calculators.sum import SumCalculator
from ase.constraints import FixAtoms

# Calculate reference values:
atoms = fcc111('Cu', (2, 2, 1), vacuum=10.)
atoms[0].x += 0.2

# First run the test with EMT similarly to the test of the single point calculator.
calc = EMT()
atoms.set_calculator(calc)
forces = atoms.get_forces()

# Alternative ways to associate a calaculator with an atoms object.
atoms1 = atoms.copy()
calc1 = SumCalculator(EMT(), EMT())
atoms1.set_calculator(calc1)

atoms2 = atoms.copy()
calc2 = SumCalculator(EMT(), EMT(), atoms=atoms2)

# Check the results.
assert np.isclose(2 * forces, atoms1.get_forces()).all()
assert np.isclose(2 * forces, atoms2.get_forces()).all()

# testing  step
atoms1[0].x += 0.2
assert not np.isclose(2 * forces, atoms1.get_forces()).all()

# Check constraints
atoms1.set_constraint(FixAtoms(indices=[atom.index for atom in atoms]))
assert np.isclose(0, atoms1.get_forces()).all()

