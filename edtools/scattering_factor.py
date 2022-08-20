# Periodic table referenced from https://gist.github.com/slabach/11197977 and
# https://stackoverflow.com/questions/60267444/interactive-periodic-table-with-tkinter-python
import lmfit
import yaml
import numpy as np
import pandas as pd
import tkinter as tk
from pathlib import Path
from tkinter import *
from tkinter.ttk import *

from edtools.widgets import Spinbox, Hoverbox

from collections import namedtuple
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

atomlib  = Path(__file__).parent / "atomlib.yaml"

FitResult_4p = namedtuple('FitResult_4p', 'a0 b0 a1 b1 a2 b2 a3 b3 c'.split())
FitResult_5p = namedtuple('FitResult_5p', 'a0 b0 a1 b1 a2 b2 a3 b3 a4 b4 c'.split())

def fit_4_param(s, target, is_xray=False, method: str = 'leastsq', verbose: bool = False, **param):
    params = lmfit.Parameters()
    params.add('a0', value=param.get('a0', 1), min=-1000, max=1000)
    params.add('b0', value=param.get('b0', 1), min=0, max=10000)
    params.add('a1', value=param.get('a1', 1), min=-1000, max=1000)
    params.add('b1', value=param.get('b1', 1), min=0, max=10000)
    params.add('a2', value=param.get('a2', 1), min=-1000, max=1000)
    params.add('b2', value=param.get('b2', 1), min=0, max=10000)
    params.add('a3', value=param.get('a3', 1), min=-1000, max=1000)
    params.add('b3', value=param.get('b3', 1), min=0, max=10000)
    params.add('c', value=param.get('c', 0), vary=is_xray)
    
    def objective_func(params, s, arr):
        a0 = params['a0'].value
        b0 = params['b0'].value
        a1 = params['a1'].value
        b1 = params['b1'].value
        a2 = params['a2'].value
        b2 = params['b2'].value
        a3 = params['a3'].value
        b3 = params['b3'].value
        c = params['c'].value
        
        fit = a0 * np.exp(-b0 * s**2) + a1 * np.exp(-b1 * s**2) + a2 * np.exp(-b2 * s**2) + a3 * np.exp(-b3 * s**2) + c
        
        return fit - arr
    
    args = (s, target)
    res = lmfit.minimize(objective_func, params, args=args, method=method, nan_policy='omit')

    if res.success and not verbose:
        print(f'Minimization converged after {res.nfev} cycles with chisqr of {res.chisqr}')
    else:
        lmfit.report_fit(res)
        
    a0 = res.params['a0'].value
    b0 = res.params['b0'].value
    a1 = res.params['a1'].value
    b1 = res.params['b1'].value
    a2 = res.params['a2'].value
    b2 = res.params['b2'].value
    a3 = res.params['a3'].value
    b3 = res.params['b3'].value
    c = res.params['c'].value
    
    return FitResult_4p(a0, b0, a1, b1, a2, b2, a3, b3, c)

def fit_5_param(s, target, is_xray=False, method: str = 'leastsq', verbose: bool = False, **param):
    params = lmfit.Parameters()
    params.add('a0', value=param.get('a0', 1), min=-1000, max=1000)
    params.add('b0', value=param.get('b0', 1), min=0, max=10000)
    params.add('a1', value=param.get('a1', 1), min=-1000, max=1000)
    params.add('b1', value=param.get('b1', 1), min=0, max=10000)
    params.add('a2', value=param.get('a2', 1), min=-1000, max=1000)
    params.add('b2', value=param.get('b2', 1), min=0, max=10000)
    params.add('a3', value=param.get('a3', 1), min=-1000, max=1000)
    params.add('b3', value=param.get('b3', 1), min=0, max=10000)
    params.add('a4', value=param.get('a4', 1), min=-1000, max=1000)
    params.add('b4', value=param.get('b4', 1), min=0, max=10000)
    params.add('c', value=param.get('c', 0), vary=is_xray)
    
    def objective_func(params, s, arr):
        a0 = params['a0'].value
        b0 = params['b0'].value
        a1 = params['a1'].value
        b1 = params['b1'].value
        a2 = params['a2'].value
        b2 = params['b2'].value
        a3 = params['a3'].value
        b3 = params['b3'].value
        a4 = params['a4'].value
        b4 = params['b4'].value
        c = params['c'].value
        
        fit = a0 * np.exp(-b0 * s**2) + a1 * np.exp(-b1 * s**2) + a2 * np.exp(-b2 * s**2) + a3 * np.exp(-b3 * s**2) + a4 * np.exp(-b4 * s**2) + c
        
        return fit - arr
    
    args = (s, target)
    res = lmfit.minimize(objective_func, params, args=args, method=method, nan_policy='omit')

    if res.success and not verbose:
        print(f'Minimization converged after {res.nfev} cycles with chisqr of {res.chisqr}')
    else:
        lmfit.report_fit(res)
        
    a0 = res.params['a0'].value
    b0 = res.params['b0'].value
    a1 = res.params['a1'].value
    b1 = res.params['b1'].value
    a2 = res.params['a2'].value
    b2 = res.params['b2'].value
    a3 = res.params['a3'].value
    b3 = res.params['b3'].value
    a4 = res.params['a4'].value
    b4 = res.params['b4'].value
    c = res.params['c'].value
    
    return FitResult_5p(a0, b0, a1, b1, a2, b2, a3, b3, a4, b4, c)

class ScatteringFactorGUI(LabelFrame):
    """A GUI frame for scattering factor"""
    def __init__(self, parent):
        LabelFrame.__init__(self, parent, text='Scattering factor')
        self.parent = parent
        self.buttons_container = []

        self.init_vars()

        frame = Frame(self)

        column1 = [
            ('H', 'Hydrogen', 'Atomic # = 1\nAtomic Weight =1.01\nState = Gas\nCategory = Alkali Metals'),
            ('Li', 'Lithium', 'Atomic # = 3\nAtomic Weight = 6.94\nState = Solid\nCategory = Alkali Metals'),
            ('Na', 'Sodium', 'Atomic # = 11\nAtomic Weight = 22.99\nState = Solid\nCategory = Alkali Metals'),
            ('K', 'Potassium', 'Atomic # = 19\nAtomic Weight = 39.10\nState = Solid\nCategory = Alkali Metals'),
            ('Rb', 'Rubidium', 'Atomic # = 37\nAtomic Weight = 85.47\nState = Solid\nCategory = Alkali Metals'),
            ('Cs', 'Cesium', 'Atomic # = 55\nAtomic Weight = 132.91\nState = Solid\nCategory = Alkali Metals'),
            ('Fr', 'Francium', 'Atomic # = 87\nAtomic Weight = 223.00\nState = Solid\nCategory = Alkali Metals')]
        # create all tk.Buttons with a loop
        r = 1
        c = 0
        for b in column1: 
            tmp = tk.Button(frame, text=b[0], width=2, height=1, bg="grey", command=lambda e=b[0]: self.select_element(e))
            tmp.grid(row=r, column=c)
            Hoverbox(tmp, b[2])
            r += 1
            if r > 7: 
                r = 1
                c += 1

        column2 = [
            ('Be', 'Beryllium', 'Atomic # = 4\nAtomic Weight = 9.01\nState = Solid\nCategory = Alkaline Earth Metals'),
            ('Mg', 'Magnesium', 'Atomic # = 12\nAtomic Weight = 24.31\nState = Solid\nCategory = Alkaline Earth Metal'),
            ('Ca', 'Calcium', 'Atomic # = 20\nAtomic Weight = 40.08\nState = Solid\nCategory = Alkaline Earth Metals'),
            ('Sr', 'Strontium', 'Atomic # = 38\nAtomic Weight = 87.62\nState = Solid\nCategory = Alkaline Earth Metal'),
            ('Ba', 'Barium', 'Atomic # = 56\nAtomic Weight = 137.33\nState = Solid\nCategory = Alkaline Earth Metals'),
            ('Ra', 'Radium', 'Atomic # = 88\nAtomic Weight = 226.03\nState = Solid\nCategory = Alkaline Earth Metals')]
        r = 2
        c = 1
        for b in column2: 
            tmp = tk.Button(frame, text=b[0], width=2, height=1, bg="light green", command=lambda e=b[0]: self.select_element(e))
            tmp.grid(row=r, column=c)
            Hoverbox(tmp, b[2])
            r += 1
            if r > 7: 
                r = 1
                c += 1

        column3 = [
            ('Sc', 'Scandium', 'Atomic # = 21\nAtomic Weight = 44.96\nState = Solid\nCategory = Trans Metals'),
            ('Y', 'Yttrium', 'Atomic # = 39\nAtomic Weight = 88.91\nState = Solid\nCategory = Trans Metals'),
            ('La', 'Lanthanum', 'Atomic # = 57\nAtomic Weight = 138.91\nState = Solid\nCategory = Trans Metals'),
            ('Ac', 'Actinium', 'Atomic # = 89\nAtomic Weight = 227.03\nState = Solid\nCategory = Trans Metals')]
        r = 4
        c = 2
        for b in column3: 
            tmp = tk.Button(frame, text=b[0], width=2, height=1, bg="light goldenrod", command=lambda e=b[0]: self.select_element(e))
            tmp.grid(row=r, column=c)
            Hoverbox(tmp, b[2])
            r += 1
            if r > 7: 
                r = 1
                c += 1

        column4 = [
            ('Ti', 'Titanium', 'Atomic # = 22\nAtomic Weight = 47.90\nState = Solid\nCategory = Trans Metals'),
            ('Zr', 'Zirconium', 'Atomic # = 40\nAtomic Weight = 91.22\nState = Solid\nCategory = Trans Metals'),
            ('Hf', 'Hanium', 'Atomic # = 72\nAtomic Weight = 178.49\nState = Solid\nCategory = Trans Metals'),
            ('Rf', 'Rutherfordium', 'Atomic # = 104\nAtomic Weight = 261.00\nState = Synthetic\nCategory = Tran Metal')]
        r = 4
        c = 3
        for b in column4: 
            tmp = tk.Button(frame, text=b[0], width=2, height=1, bg="light goldenrod", command=lambda e=b[0]: self.select_element(e))
            tmp.grid(row=r, column=c)
            Hoverbox(tmp, b[2])
            r += 1
            if r > 10: 
                r = 1
                c += 1

        column5 = [
            ('V', 'Vanadium', 'Atomic # = 23\nAtomic Weight = 50.94\nState = Solid\nCategory = Trans Metals'),
            ('Nb', 'Niobium', 'Atomic # = 41\nAtomic Weight = 92.91\nState = Solid\nCategory = Trans Metals'),
            ('Ta', 'Tantalum', 'Atomic # = 73\nAtomic Weight = 180.95\nState = Solid\nCategory = Trans Metals'),
            ('Ha', 'Hahnium', 'Atomic # = 105\nAtomic Weight = 262.00\nState = Synthetic\nCategory = Trans Metals')]
        r = 4
        c = 4
        for b in column5: 
            tmp = tk.Button(frame, text=b[0], width=2, height=1, bg="light goldenrod", command=lambda e=b[0]: self.select_element(e))
            tmp.grid(row=r, column=c)
            Hoverbox(tmp, b[2])
            r += 1
            if r > 10: 
                r = 1
                c += 1

        column6 = [
            ('Cr', 'Chromium', 'Atomic # = 24\nAtomic Weight = 51.99\nState = Solid\nCategory = Trans Metals'),
            ('Mo', 'Molybdenum', 'Atomic # = 42\nAtomic Weight = 95.94\nState = Solid\nCategory = Trans Metals'),
            ('W', 'Tungsten', 'Atomic # = 74\nAtomic Weight = 183.85\nState = Solid\nCategory = Trans Metals'),
            ('Sg', 'Seaborgium', 'Atomic # = 106\nAtomic Weight = 266.00\nState = Synthetic\nCategory = Trans Metals')]
        r = 4
        c = 5
        for b in column6: 
            tmp = tk.Button(frame, text=b[0], width=2, height=1, bg="light goldenrod", command=lambda e=b[0]: self.select_element(e))
            tmp.grid(row=r, column=c)
            Hoverbox(tmp, b[2])
            r += 1
            if r > 7: 
                r = 1
                c += 1

        column7 = [
            ('Mn', 'Manganese', 'Atomic # = 25\nAtomic Weight = 178.49\nState = Solid\nCategory = Trans Metals'),
            ('Tc', 'Technetium', 'Atomic # = 43\nAtomic Weight = 178.49\nState = Synthetic\nCategory = Trans Metals'),
            ('Re', 'Rhenium', 'Atomic # = 75\nAtomic Weight = 178.49\nState = Solid\nCategory = Trans Metals'),
            ('Bh', 'Bohrium', 'Atomic # = 107\nAtomic Weight = 262.00\nState = Synthetic\nCategory = Trans Metals')]
        r = 4
        c = 6
        for b in column7: 
            tmp = tk.Button(frame, text=b[0], width=2, height=1, bg="light goldenrod", command=lambda e=b[0]: self.select_element(e))
            tmp.grid(row=r, column=c)
            Hoverbox(tmp, b[2])
            r += 1
            if r > 7: 
                r = 1
                c += 1

        column8 = [
            ('Fe', 'Iron', 'Atomic # = 26\nAtomic Weight = 55.85\nState = Solid\nCategory = Trans Metals'),
            ('Ru', 'Ruthenium', 'Atomic # = 44\nAtomic Weight = 101.07\nState = Solid\nCategory = Trans Metals'),
            ('Os', 'Osmium', 'Atomic # = 76\nAtomic Weight = 190.20\nState = Solid\nCategory = Trans Metals'),
            ('Hs', 'Hassium', 'Atomic # = 108\nAtomic Weight = 265.00\nState = Synthetic\nCategory = Trans Metals')]
        r = 4
        c = 7
        for b in column8: 
            tmp = tk.Button(frame, text=b[0], width=2, height=1, bg="light goldenrod", command=lambda e=b[0]: self.select_element(e))
            tmp.grid(row=r, column=c)
            Hoverbox(tmp, b[2])
            r += 1
            if r > 7: 
                r = 1
                c += 1

        column9 = [
            ('Co', 'Cobalt', 'Atomic # = 27\nAtomic Weight = 58.93\nState = Solid\nCategory = Trans Metals'),
            ('Rh', 'Rhodium', 'Atomic # = 45\nAtomic Weight = 102.91\nState = Solid\nCategory = Trans Metals'),
            ('Ir', 'Iridium', 'Atomic # = 77\nAtomic Weight = 192.22\nState = Solid\nCategory = Trans Metals'),
            ('Mt', 'Meitnerium', 'Atomic # = 109\nAtomic Weight = 266.00\nState = Synthetic\nCategory = Trans Metals')]
        r = 4
        c = 8
        for b in column9: 
            tmp = tk.Button(frame, text=b[0], width=2, height=1, bg="light goldenrod", command=lambda e=b[0]: self.select_element(e))
            tmp.grid(row=r, column=c)
            Hoverbox(tmp, b[2])
            r += 1
            if r > 7: 
                r = 1
                c += 1

        column10 = [
            ('Ni', 'Nickle', 'Atomic # = 28\nAtomic Weight = 58.70\nState = Solid\nCategory = Trans Metals'),
            ('Pd', 'Palladium', 'Atomic # = 46\nAtomic Weight = 106.40\nState = Solid\nCategory = Trans Metals'),
            ('Pt', 'Platinum', 'Atomic # = 78\nAtomic Weight = 195.09\nState = Solid\nCategory = Trans Metals')]
        r = 4
        c = 9
        for b in column10: 
            tmp = tk.Button(frame, text=b[0], width=2, height=1, bg="light goldenrod", command=lambda e=b[0]: self.select_element(e))
            tmp.grid(row=r, column=c)
            Hoverbox(tmp, b[2])
            r += 1
            if r > 7: 
                r = 1
                c += 1

        column11 = [
            ('Cu', 'Copper', 'Atomic # = 29\nAtomic Weight = 63.55\nState = Solid\nCategory = Trans Metals'),
            ('Ag', 'Silver', 'Atomic # = 47\nAtomic Weight = 107.97\nState = Solid\nCategory = Trans Metals'),
            ('Au', 'Gold', 'Atomic # = 79\nAtomic Weight = 196.97\nState = Solid\nCategory = Trans Metals')]
        r = 4
        c = 10
        for b in column11: 
            tmp = tk.Button(frame, text=b[0], width=2, height=1, bg="light goldenrod", command=lambda e=b[0]: self.select_element(e))
            tmp.grid(row=r, column=c)
            Hoverbox(tmp, b[2])
            r += 1
            if r > 7: 
                r = 1
                c += 1

        column12 = [
            ('Zn', 'Zinc', 'Atomic # = 30\nAtomic Weight = 65.37\nState = Solid\nCategory = Trans Metals'),
            ('Cd', 'Cadmium', 'Atomic # = 48\nAtomic Weight = 112.41\nState = Solid\nCategory = Trans Metals'),
            ('Hg', 'Mercury', 'Atomic # = 80\nAtomic Weight = 200.59\nState = Liquid\nCategory = Trans Metals')]
        r = 4
        c = 11
        for b in column12: 
            tmp = tk.Button(frame, text=b[0], width=2, height=1, bg="light goldenrod", command=lambda e=b[0]: self.select_element(e))
            tmp.grid(row=r, column=c)
            Hoverbox(tmp, b[2])
            r += 1
            if r > 7: 
                r = 1
                c += 1

        column13_1 = [
            ('B', 'Boron', 'Atomic # = 5\nAtomic Weight = 10.81\nState = Solid\nCategory = Nonmetals')]
        r = 2
        c = 12
        for b in column13_1: 
            tmp = tk.Button(frame, text=b[0], width=2, height=1, bg="light blue", command=lambda e=b[0]: self.select_element(e))
            tmp.grid(row=r, column=c)
            Hoverbox(tmp, b[2])
            r += 1
            if r > 7: 
                r = 1
                c += 1

        column13_2 = [
            ('Al', 'Aluminum', 'Atomic # = 13\nAtomic Weight = 26.98\nState = Solid\nCategory = Other Metals'),
            ('Ga', 'Gallium', 'Atomic # = 31\nAtomic Weight = 69.72\nState = Solid\nCategory = Other Metals'),
            ('In', 'Indium', 'Atomic # = 49\nAtomic Weight = 69.72\nState = Solid\nCategory = Other Metals'),
            ('Ti', 'Thallium', 'Atomic # = 81\nAtomic Weight = 204.37\nState = Solid\nCategory = Other Metals')]
        r = 3
        c = 12
        for b in column13_2: 
            tmp = tk.Button(frame, text=b[0], width=2, height=1, bg="light pink", command=lambda e=b[0]: self.select_element(e))
            tmp.grid(row=r, column=c)
            Hoverbox(tmp, b[2])
            r += 1
            if r > 7: 
                r = 1
                c += 1

        column14_1 = [
            ('C', 'Carbon', 'Atomic # = 6\nAtomic Weight = 12.01\nState = Solid\nCategory = Nonmetals'),
            ('Si', 'Silicon', 'Atomic # = 14\nAtomic Weight = 28.09\nState = Solid\nCategory = Nonmetals')]
        r = 2
        c = 13
        for b in column14_1: 
            tmp = tk.Button(frame, text=b[0], width=2, height=1, bg="light blue", command=lambda e=b[0]: self.select_element(e))
            tmp.grid(row=r, column=c)
            Hoverbox(tmp, b[2])
            r += 1
            if r > 7: 
                r = 1
                c += 1

        column14_2 = [
            ('Ge', 'Germanium', 'Atomic # = 32\nAtomic Weight = 72.59\nState = Solid\nCategory = Other Metals'),
            ('Sn', 'Tin', 'Atomic # = 50\nAtomic Weight = 118.69\nState = Solid\nCategory = Other Metals'),
            ('Pb', 'Lead', 'Atomic # = 82\nAtomic Weight = 207.20\nState = Solid\nCategory = Other Metals')]
        r = 4
        c = 13
        for b in column14_2: 
            tmp = tk.Button(frame, text=b[0], width=2, height=1, bg="light pink", command=lambda e=b[0]: self.select_element(e))
            tmp.grid(row=r, column=c)
            Hoverbox(tmp, b[2])
            r += 1
            if r > 7: 
                r = 1
                c += 1

        column15_1 = [
            ('N', 'Nitrogen', 'Atomic # = 7\nAtomic Weight = 14.01\nState = Gas\nCategory = Nonmetals'),
            ('P', 'Phosphorus', 'Atomic # = 15\nAtomic Weight = 30.97\nState = Solid\nCategory = Nonmetals'),
            ('As', 'Arsenic', 'Atomic # = 33\nAtomic Weight = 74.92\nState = Solid\nCategory = Nonmetals')]
        r = 2
        c = 14
        for b in column15_1: 
            tmp = tk.Button(frame, text=b[0], width=2, height=1, bg="light blue", command=lambda e=b[0]: self.select_element(e))
            tmp.grid(row=r, column=c)
            Hoverbox(tmp, b[2])
            r += 1
            if r > 7: 
                r = 1
                c += 1

        column15_2 = [
            ('Sb', 'Antimony', 'Atomic # = 51\nAtomic Weight = 121.75\nState = Solid\nCategory = Other Metals'),
            ('Bi', 'Bismuth', 'Atomic # = 83\nAtomic Weight = 208.98\nState = Solid\nCategory = Other Metals')]
        r = 5
        c = 14
        for b in column15_2: 
            tmp = tk.Button(frame, text=b[0], width=2, height=1, bg="light pink", command=lambda e=b[0]: self.select_element(e))
            tmp.grid(row=r, column=c)
            Hoverbox(tmp, b[2])
            r += 1
            if r > 7: 
                r = 1
                c += 1

        column16_1 = [
            ('O', 'Oxygen', 'Atomic # = 8\nAtomic Weight = 15.99\nState = Gas\nCategory = Nonmetals'),
            ('S', 'Sulfur', 'Atomic # = 16\nAtomic Weight = 32.06\nState = Solid\nCategory = Nonmetals'),
            ('Se', 'Selenium', 'Atomic # = 34\nAtomic Weight = 78.96\nState = Solid\nCategory = Nonmetals'),
            ('Te', 'Tellurium', 'Atomic # = 52\nAtomic Weight = 127.60\nState = Solid\nCategory = Nonmetals')]
        r = 2
        c = 15
        for b in column16_1: 
            tmp = tk.Button(frame, text=b[0], width=2, height=1, bg="light blue", command=lambda e=b[0]: self.select_element(e))
            tmp.grid(row=r, column=c)
            Hoverbox(tmp, b[2])
            r += 1
            if r > 7: 
                r = 1
                c += 1

        column16_2 = [
            ('Po', 'Polonium', 'Atomic # = 84\nAtomic Weight = 209.00\nState = Solid\nCategory = Other Metals')]
        r = 6
        c = 15
        for b in column16_2: 
            tmp = tk.Button(frame, text=b[0], width=2, height=1, bg="light pink", command=lambda e=b[0]: self.select_element(e))
            tmp.grid(row=r, column=c)
            Hoverbox(tmp, b[2])
            r += 1
            if r > 7: 
                r = 1
                c += 1

        column17 = [
            ('F', 'Fluorine', 'Atomic # = 9\nAtomic Weight = 18.99\nState = Gas\nCategory = Nonmetals'),
            ('Cl', 'Chlorine', 'Atomic # = 17\nAtomic Weight = 35.45\nState = Gas\nCategory = Nonmetals'),
            ('Br', 'Bromine', 'Atomic # = 35\nAtomic Weight = 79.90\nState = Liquid\nCategory = Nonmetals'),
            ('I', 'Iodine', 'Atomic # = 53\nAtomic Weight = 126.90\nState = Solid\nCategory = Nonmetals'),
            ('At', 'Astatine', 'Atomic # = 85\nAtomic Weight = 210.00\nState = Solid\nCategory = Nonmetals')]
        r = 2
        c = 16
        for b in column17: 
            tmp = tk.Button(frame, text=b[0], width=2, height=1, bg="light blue", command=lambda e=b[0]: self.select_element(e))
            tmp.grid(row=r, column=c)
            Hoverbox(tmp, b[2])
            r += 1
            if r > 7: 
                r = 1
                c += 1

        column18 = [
            ('He', 'Helium', 'Atomic # = 2\nAtomic Weight = 4.00\nState = Gas\nCategory = Nobel Gases'),
            ('Ne', 'Neon', 'Atomic # = 10\nAtomic Weight = 20.18\nState = Gas\nCategory = Nobel Gases'),
            ('Ar', 'Argon', 'Atomic # = 18\nAtomic Weight = 39.95\nState = Gas\nCategory = Nobel Gases'),
            ('Kr', 'Krypton', 'Atomic # = 36\nAtomic Weight = 83.80\nState = Gas\nCategory = Nobel Gases'),
            ('Xe', 'Xenon', 'Atomic # = 54\nAtomic Weight = 131.30\nState = Gas\nCategory = Nobel Gases'),
            ('Rn', 'Radon', 'Atomic # = 86\nAtomic Weight = 222.00\nState = Gas\nCategory = Nobel Gases')]
        r = 1
        c = 17
        for b in column18: 
            tmp = tk.Button(frame, text=b[0], width=2, height=1, bg="light blue", command=lambda e=b[0]: self.select_element(e))
            tmp.grid(row=r, column=c)
            Hoverbox(tmp, b[2])
            r += 1
            if r > 7: 
                r = 1
                c += 1

        self.fillerLine = tk.Label(frame, text="")
        self.fillerLine.grid(row=8, column=0)

        lanthanide = [
            ('Ce', 'Cerium', 'Atomic # = 58\nAtomic Weight = 140.12\nState = Solid\nCategory = Trans Metals'),
            ('Pr', 'Praseodymium', 'Atomic # = 59\nAtomic Weight = 140.91\nState = Solid\nCategory = Trans Metals'),
            ('Nd', 'Neodymium', 'Atomic # = 60\nAtomic Weight = 144.24\nState = Solid\nCategory = Trans Metals'),
            ('Pm', 'Promethium', 'Atomic # = 61\nAtomic Weight = 145.00\nState = Synthetic\nCategory = Trans Metals'),
            ('Sm', 'Samarium', 'Atomic # = 62\nAtomic Weight = 150.40\nState = Solid\nCategory = Trans Metals'),
            ('Eu', 'Europium', 'Atomic # = 63\nAtomic Weight = 151.96\nState = Solid\nCategory = Trans Metals'),
            ('Gd', 'Gadolinium', 'Atomic # = 64\nAtomic Weight = 157.25\nState = Solid\nCategory = Trans Metals'),
            ('Tb', 'Terbium', 'Atomic # = 65\nAtomic Weight = 158.93\nState = Solid\nCategory = Trans Metals'),
            ('Dy', 'Dyprosium', 'Atomic # = 66\nAtomic Weight = 162.50\nState = Solid\nCategory = Trans Metals'),
            ('Ho', 'Holmium', 'Atomic # = 67\nAtomic Weight = 164.93\nState = Solid\nCategory = Trans Metals'),
            ('Er', 'Erbium', 'Atomic # = 68\nAtomic Weight = 167.26\nState = Solid\nCategory = Trans Metals'),
            ('Tm', 'Thulium', 'Atomic # = 69\nAtomic Weight = 168.93\nState = Solid\nCategory = Trans Metals'),
            ('Yb', 'Ytterbium', 'Atomic # = 70\nAtomic Weight = 173.04\nState = Solid\nCategory = Trans Metals'),
            ('Lu', 'Lutetium', 'Atomic # = 71\nAtomic Weight = 174.97\nState = Solid\nCategory = Trans Metals')]
        r = 9
        c = 2
        for b in lanthanide: 
            tmp = tk.Button(frame, text=b[0], width=2, height=1, bg="light goldenrod", command=lambda e=b[0]: self.select_element(e))
            tmp.grid(row=r, column=c)
            Hoverbox(tmp, b[2])
            c += 1
            if c > 18: 
                c = 1
                r += 1

        actinide = [
            ('Th', 'Thorium', 'Atomic # = 90\nAtomic Weight = 232.04\nState = Solid\nCategory = Trans Metals'),
            ('Pa', 'Protactinium', 'Atomic # = 91\nAtomic Weight = 231.04\nState = Solid\nCategory = Trans Metals'),
            ('U', 'Uranium', 'Atomic # = 92\nAtomic Weight = 238.03\nState = Solid\nCategory = Trans Metals'),
            ('Np', 'Neptunium', 'Atomic # = 93\nAtomic Weight = 237.05\nState = Synthetic\nCategory = Trans Metals'),
            ('Pu', 'Plutonium', 'Atomic # = 94\nAtomic Weight = 244.00\nState = Synthetic\nCategory = Trans Metals'),
            ('Am', 'Americium', 'Atomic # = 95\nAtomic Weight = 243.00\nState = Synthetic\nCategory = Trans Metals'),
            ('Cm', 'Curium', 'Atomic # = 96\nAtomic Weight = 247\nState = Synthetic\nCategory = Trans Metals'),
            ('Bk', 'Berkelium', 'Atomic # = 97\nAtomic Weight = 247\nState = Synthetic\nCategory = Trans Metals'),
            ('Cf', 'Californium', 'Atomic # = 98\nAtomic Weight = 247\nState = Synthetic\nCategory = Trans Metals'),
            ('Es', 'Einsteinium', 'Atomic # = 99\nAtomic Weight = 252.00\nState = Synthetic\nCategory = Trans Metals'),
            ('Fm', 'Fermium', 'Atomic # = 100\nAtomic Weight = 257.00\nState = Synthetic\nCategory = Trans Metals'),
            ('Md', 'Mendelevium', 'Atomic # = 101\nAtomic Weight = 260.00\nState = Synthetic\nCategory = Trans Metals'),
            ('No', 'Nobelium', 'Atomic # = 102\nAtomic Weight = 259\nState = Synthetic\nCategory = Trans Metals'),
            ('Lr', 'Lawrencium', 'Atomic # = 103\nAtomic Weight = 262\nState = Synthetic\nCategory = Trans Metals')]
        r = 10
        c = 2
        for b in actinide: 
            tmp = tk.Button(frame, text=b[0], width=2, height=1, bg="light goldenrod", command=lambda e=b[0]: self.select_element(e))
            tmp.grid(row=r, column=c)
            Hoverbox(tmp, b[2])
            c += 1
            if c > 18: 
                c = 1
                r += 1

        Label(frame, text="Element Chosen:").grid(row=2, column=4, columnspan=4)
        self.l_element = Label(frame, text="")
        self.l_element.grid(row=2, column=8)
        Button(frame, text="Load Library", width=14, command=self.load_lib).grid(row=1, column=4, columnspan=4, sticky='E')

        Label(frame, text="sin(θ)/λ").grid(row=1, column=18, padx=5)
        Entry(frame, textvariable=self.var_s_range, width=8).grid(row=1, column=19)
        Label(frame, text="Points").grid(row=2, column=18, padx=5)
        Entry(frame, textvariable=self.var_s_points, width=8).grid(row=2, column=19)

        tmp = Checkbutton(frame, text='Charge term', variable=self.var_add_charge_term)
        tmp.grid(row=3, column=18, columnspan=2, padx=5)
        Hoverbox(tmp, 'This button must be checked for charged ions.')
        tmp = Checkbutton(frame, text='Use neutral', variable=self.var_use_neutral)
        tmp.grid(row=4, column=18, columnspan=2, padx=5)
        Hoverbox(tmp, 'This is used for use different scattering factors (from neutral atom or ion atom).')
        self.o_param = OptionMenu(frame, self.var_param, '4p_electron', '4p_electron', '5p_electron_1', '5p_electron_2', '4p_xray_1992', '5p_xray_1995')
        self.o_param.grid(row=5, column=18, columnspan=2, sticky='EW', padx=5)
        Hoverbox(self.o_param, 'Scattering factor from different sources.')
        Button(frame, text="Plot", command=self.plot).grid(row=6, column=18, columnspan=2, sticky='EW', padx=5)
        Button(frame, text="Clear", command=self.clear_plot).grid(row=7, column=18, columnspan=2, sticky='EW', padx=5)
        Button(frame, text="Fit 4 Param", command=self.fit_4_param).grid(row=8, column=18, columnspan=2, sticky='EW', padx=5)
        Button(frame, text="Fit 5 Param", command=self.fit_5_param).grid(row=9, column=18, columnspan=2, sticky='EW', padx=5)
        Button(frame, text="Output", command=self.output).grid(row=10, column=18, columnspan=2, sticky='EW', padx=5)
        
        Label(frame, text="Charge").grid(row=7, column=9, columnspan=3, sticky='E', padx=5)
        tmp = OptionMenu(frame, self.var_charge, "", "7-", "6-", "5-", "4-", "3-", "2-", "1-", "", "1+", "2+", "3+", "4+", "5+", "6+", "7+")
        tmp.grid(row=7, column=12, columnspan=2, sticky='W')
        Hoverbox(tmp, 'Charge in integral: some elements have their own charged parameters and it is more accurate than using neutral scattering factor.')
        Spinbox(frame, width=5, textvariable=self.var_frac_charge, from_=-1.0, to=1.0, increment=0.01).grid(row=7, column=14, columnspan=3, sticky='W')

        tmp = Button(frame, text="Read", width=9, command=self.read)
        tmp.grid(row=8, column=10, columnspan=3, sticky='E')
        Hoverbox(tmp, 'Read a file with only atomic scattering factor.')
        Button(frame, text="Draw", width=9, command=self.draw).grid(row=8, column=13, columnspan=3, sticky='E')

        frame.pack(side='top', fill='x', expand=False, padx=5, pady=5)

        frame = Frame(self)

        self.fig = Figure(figsize=(5.3, 3), dpi=100)
        self.fig.subplots_adjust(left=0.1, bottom=0.07, right=0.95, top=0.95, wspace=0, hspace=0)
        self.ax = self.fig.add_subplot(1, 1, 1)
        self.canvas = FigureCanvasTkAgg(self.fig, frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row=0, column=0, padx=5)
        self.toolbar = NavigationToolbar2Tk(self.canvas, frame, pack_toolbar=False)
        self.toolbar.update()
        self.toolbar.grid(row=1, column=0, padx=5)

        frame.pack(side='top', fill='x', expand=False, padx=5, pady=5)

    def init_vars(self):
        with open(atomlib, 'r') as f:
            self.scat_factor_lib = yaml.load(f, Loader=yaml.Loader)
        
        self.element = ""
        self.var_charge = StringVar(value="")
        self.var_frac_charge = DoubleVar(value=0.0)
        self.var_add_charge_term = BooleanVar(value=True)
        self.var_use_neutral = BooleanVar(value=False)
        self.var_s_range = StringVar(value="0.04-1Å")
        self.var_s_points = IntVar(value=2000)
        self.var_param = StringVar(value='4p_electron')

    def load_lib(self):
        file_name = tk.filedialog.askopenfilename(initialdir='.', title='Select file', 
                            filetypes=(('scattering factor files', '*.yaml'), ('all files', '*.*')))
        if len(file_name) != 0:
            with open(file_name, 'r') as f:
                self.scat_factor_lib = yaml.load(f, Loader=yaml.Loader)

    def read(self):
        file_name = tk.filedialog.askopenfilename(title='Select file', 
                            filetypes=(('scattering factor files', '*.yaml'), ('all files', '*.*')))
        if len(file_name) != 0:
            with open(file_name, 'r') as f:
                self.scat_factor = yaml.load(f, Loader=yaml.Loader)
                print(self.scat_factor)

    def draw(self):
        charge = self.var_charge.get()
        frac_charge = self.var_frac_charge.get()
        s_range = self.var_s_range.get()[:-1].split('-')
        self.s = np.logspace(np.log10(float(s_range[0])), np.log10(float(s_range[1])), self.var_s_points.get())
        if len(self.scat_factor) == 9:
            if charge == "" and frac_charge == 0:
                self.f = self.func_4p(self.scat_factor, self.s)
            else:
                if charge == "":
                    c = frac_charge
                else:
                    c = float(charge[::-1]) + frac_charge
                self.f = self.func_4p_charge(self.scat_factor, self.s, c)

            self.ax.plot(self.s, self.f, label="Loaded 4p")

        elif len(self.scat_factor) == 11:
            if charge == "" and frac_charge == 0:
                self.f = self.func_5p(self.scat_factor, self.s)
            else:
                if charge == "":
                    c = frac_charge
                else:
                    c = float(charge[::-1]) + frac_charge
                self.f = self.func_5p_charge(self.scat_factor, self.s, c)

            self.ax.plot(self.s, self.f, label="Loaded 5p")

        self.ax.legend()
        self.canvas.draw()

    def get_parameters(self, scat_lib, source, atom, charge):
        if self.var_use_neutral.get():
            if source == "4p_electron":
                return scat_lib[atom]['sfac_electron']
            elif source == "5p_electron_1":
                return scat_lib[atom]['sfac_electron_5_1']
            elif source == "5p_electron_2":
                return scat_lib[atom]['sfac_electron_5_2']
        else:
            if source == "4p_electron":
                return scat_lib[atom+charge]['sfac_electron']
            elif source == "5p_electron_1":
                return scat_lib[atom+charge]['sfac_electron_5_1']
            elif source == "5p_electron_2":
                return scat_lib[atom+charge]['sfac_electron_5_2']
        if source == "4p_xray_1992":
            return scat_lib[atom+charge]['sfac_xray_1992']
        elif source == "5p_xray_1995":
            return scat_lib[atom+charge]['sfac_xray_1995']

    def func_4p(self, param, s):
        result = 0
        for i in range(4):
            result += param[2*i] * np.exp(-param[2*i+1] * s**2)
        result += param[8]
        return result

    def func_5p(self, param, s):
        result = 0
        for i in range(5):
            result += param[2*i] * np.exp(-param[2*i+1] * s**2)
        result += param[10]
        return result

    def func_4p_charge(self, param, s, charge=0):
        result = 0
        for i in range(4):
            result += param[2*i] * np.exp(-param[2*i+1] * s**2)
        if self.var_add_charge_term.get():
            result += param[8] + 0.02394 * charge / s**2
        return result

    def func_5p_charge(self, param, s, charge=0):
        result = 0
        for i in range(5):
            result += param[2*i] * np.exp(-param[2*i+1] * s**2)
        if self.var_add_charge_term.get():
            result += param[10] + 0.023934 * charge / s**2
        return result

    def select_element(self, element):
        self.element = element.lower()
        self.l_element.config(text=element)

    def plot(self):
        charge = self.var_charge.get()
        frac_charge = self.var_frac_charge.get()
        num_param = self.var_param.get()
        self.param = self.get_parameters(self.scat_factor_lib, num_param, self.element, charge)
        s_range = self.var_s_range.get()[:-1].split('-')
        self.s = np.logspace(np.log10(float(s_range[0])), np.log10(float(s_range[1])), self.var_s_points.get())
        if num_param[0] == "4":
            if charge == "" and frac_charge == 0:
                self.f = self.func_4p(self.param, self.s)
                self.ax.plot(self.s, self.f, label=self.element+' '+num_param)
            else:
                if charge == "":
                    c = frac_charge
                else:
                    c = float(charge[::-1]) + frac_charge
                self.f = self.func_4p_charge(self.param, self.s, c)
                self.ax.plot(self.s, self.f, label=self.element+f'{c}'+' '+num_param)
        elif num_param[0] == "5":
            if charge == "" and frac_charge == 0:
                self.f = self.func_5p(self.param, self.s)
                self.ax.plot(self.s, self.f, label=self.element+' '+num_param)
            else:
                if charge == "":
                    c = frac_charge
                else:
                    c = float(charge[::-1]) + frac_charge
                self.f = self.func_5p_charge(self.param, self.s, c)
                self.ax.plot(self.s, self.f, label=self.element+f'{c}'+' '+num_param)

        if self.var_add_charge_term.get():
            print(f'Charge: {charge}, frac_charge: {frac_charge}, added charged term in structure factor.')
        else:
            print(f'Charge: {charge}, frac_charge: {frac_charge}, no charged term in structure factor.')
        print(f'Base parameter: {self.param}')
        self.ax.legend()
        self.canvas.draw()

    def clear_plot(self):
        self.ax.cla()
        self.canvas.draw()

    def fit_4_param(self):
        init_param = self.get_parameters(self.scat_factor_lib, "4p_electron", self.element, "")
        self.fit_result = fit_4_param(self.s, self.f, is_xray=False, verbose=True, **dict(FitResult_4p(*init_param)._asdict()))

    def fit_5_param(self):
        init_param = self.get_parameters(self.scat_factor_lib, "5p_electron_2", self.element, "")
        self.fit_result = fit_5_param(self.s, self.f, is_xray=False, verbose=True, **dict(FitResult_5p(*init_param)._asdict()))

    def output(self):
        if len(self.fit_result) == 9:
            self.ax.plot(self.s, self.func_4p(self.fit_result, self.s), label=self.element+' fitted 4 param')
            a0 = self.fit_result.a0
            b0 = self.fit_result.b0
            a1 = self.fit_result.a1
            b1 = self.fit_result.b1
            a2 = self.fit_result.a2
            b2 = self.fit_result.b2
            a3 = self.fit_result.a3
            b3 = self.fit_result.b3
            c = self.fit_result.c
            tk.messagebox.showinfo(title='Scattering Factor', message=f'- {a0}\n- {b0}\n- {a1}\n- {b1}\n- {a2}\n- {b2}\n- {a3}\n- {b3}\n- {c}\n')
            self.parent.clipboard_clear()
            self.parent.clipboard_append(f'{a0:>10.4f}{b0:>10.4f}{a1:>10.4f}{b1:>10.4f}{a2:>10.4f}{b2:>10.4f}{a3:>10.4f}{b3:>10.4f}{c:>10.4f}')
        elif len(self.fit_result) == 11:
            a0 = self.fit_result.a0
            b0 = self.fit_result.b0
            a1 = self.fit_result.a1
            b1 = self.fit_result.b1
            a2 = self.fit_result.a2
            b2 = self.fit_result.b2
            a3 = self.fit_result.a3
            b3 = self.fit_result.b3
            a4 = self.fit_result.a4
            b4 = self.fit_result.b4
            c = self.fit_result.c
            self.ax.plot(self.s, self.func_5p(self.fit_result, self.s), label=self.element+' fitted 5 param')
            tk.messagebox.showinfo(title='Scattering Factor', message=f'- {a0}\n- {b0}\n- {a1}\n- {b1}\n- {a2}\n- {b2}\n- {a3}\n- {b3}\n- {a4}\n- {b4}\n- {c}\n')
            self.parent.clipboard_clear()
            self.parent.clipboard_append(f'{a0:>10.4f}{b0:>10.4f}{a1:>10.4f}{b1:>10.4f}{a2:>10.4f}{b2:>10.4f}{a3:>10.4f}{b3:>10.4f}{a4:>10.4f}{b4:>10.4f}{c:>10.4f}')

        self.parent.update()
        self.ax.legend()
        self.canvas.draw()



def main():
    root = Tk()
    ScatteringFactorGUI(root).pack(side='top', fill='both', expand=True)
    root.mainloop()

if __name__ == '__main__':
    main()
