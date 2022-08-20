import numpy as np
import pandas as pd
from io import StringIO
from tkinter import *
from tkinter.ttk import *
from tkinter import filedialog

from cctbx import crystal, miller
from cctbx.array_family import flex
import iotbx.cif as cif
from iotbx.reflection_file_reader import any_reflection_file
from .widgets import Spinbox, Hoverbox

class GroupReflectionsGUI(LabelFrame):
    """A GUI frame for reflections grouping"""
    def __init__(self, parent):
        LabelFrame.__init__(self, parent, text='Reflection Tool')
        self.parent = parent

        self.init_vars()

        frame = Frame(self)

        self.FileButton = Button(frame, text='Select File', width=15, command=self.open_file, state=NORMAL)
        self.FileButton.grid(row=0, column=0, sticky='EW', padx=5)
        self.lb_file = Label(frame, text='')
        self.lb_file.grid(row=0, column=1, sticky='W', padx=5)

        frame.pack(side='top', fill='x', expand=False, padx=5)

        frame = Frame(self)

        Separator(frame, orient=HORIZONTAL).grid(row=0, columnspan=18, sticky='ew', pady=5)
        Label(frame, text='Size').grid(row=1, column=0, sticky='EW')
        Spinbox(frame, textvariable=self.var_img_size, width=6, from_=0.0, to=4096, increment=1).grid(row=1, column=1, sticky='EW', padx=5)
        Label(frame, text='Cent X').grid(row=1, column=2, sticky='EW')
        Spinbox(frame, textvariable=self.var_center_x, width=6, from_=0.0, to=4096, increment=0.01).grid(row=1, column=3, sticky='EW', padx=5)
        Label(frame, text='Cent Y').grid(row=1, column=4, sticky='EW')
        Spinbox(frame, textvariable=self.var_center_y, width=6, from_=0.0, to=4096, increment=0.01).grid(row=1, column=5, sticky='EW', padx=5)
        Label(frame, text='Slope').grid(row=1, column=6, sticky='EW')
        Spinbox(frame, textvariable=self.var_slope, width=6, from_=0.0, to=100.0, increment=0.01).grid(row=1, column=7, sticky='EW', padx=5)
        Checkbutton(frame, text='Lorentz Corr', variable=self.var_lorentz_corr).grid(row=1, column=8, sticky='W')
        Checkbutton(frame, text='EXTI Corr', variable=self.var_exti_corr).grid(row=2, column=0, columnspan=2, sticky='EW')
        Label(frame, text='EXTI').grid(row=2, column=2, sticky='EW')
        Spinbox(frame, textvariable=self.var_exti_param, width=6, from_=0.0, to=100.0, increment=0.01).grid(row=2, column=3, sticky='EW', padx=5)
        Label(frame, text='Prec').grid(row=2, column=4, sticky='EW')
        Spinbox(frame, textvariable=self.var_prec_angle, width=6, from_=0.0, to=100.0, increment=0.01).grid(row=2, column=5, sticky='EW', padx=5)
        Label(frame, text='Lambda').grid(row=2, column=6, sticky='EW')
        Spinbox(frame, textvariable=self.var_lambda, width=6, from_=0.0, to=100.0, increment=0.01).grid(row=2, column=7, sticky='EW', padx=5)

        frame.pack(side='top', fill='x', expand=False, padx=5, pady=5)

        frame = Frame(self)
        Separator(frame, orient=HORIZONTAL).grid(row=0, columnspan=18, sticky='ew', pady=5)
        self.lb_cell = Label(frame, text='Unit Cell')
        self.lb_cell.grid(row=1, column=0, sticky='EW')
        vcmd = (self.parent.register(self.validate), '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')

        self.lb_a = Label(frame, text='a')
        self.lb_a.grid(row=1, column=1, sticky='EW', padx=5)
        self.e_a = Entry(frame, textvariable=self.var_a, width=5, validate='key', validatecommand=vcmd, state=NORMAL)
        self.e_a.focus()
        self.e_a.grid(row=1, column=2, sticky='EW')
        Label(frame, text='Å').grid(row=1, column=3, sticky='EW')

        self.lb_b = Label(frame, text='b')
        self.lb_b.grid(row=1, column=4, sticky='EW', padx=5)
        self.e_b = Entry(frame, textvariable=self.var_b, width=5, validate='key', validatecommand=vcmd, state=NORMAL)
        self.e_b.grid(row=1, column=5, sticky='EW')
        Label(frame, text='Å').grid(row=1, column=6, sticky='EW')

        self.lb_c = Label(frame, text='c')
        self.lb_c.grid(row=1, column=7, sticky='EW', padx=5)
        self.e_c = Entry(frame, textvariable=self.var_c, width=5, validate='key', validatecommand=vcmd, state=NORMAL)
        self.e_c.grid(row=1, column=8, sticky='EW')
        Label(frame, text='Å').grid(row=1, column=9, sticky='EW')

        self.lb_alpha = Label(frame, text='alpha')
        self.lb_alpha.grid(row=1, column=10, sticky='EW', padx=5)
        self.e_alpha = Entry(frame, textvariable=self.var_alpha, width=5, validate='key', validatecommand=vcmd, state=NORMAL)
        self.e_alpha.grid(row=1, column=11, sticky='EW')
        Label(frame, text='°').grid(row=1, column=12, sticky='EW')

        self.lb_beta = Label(frame, text='beta')
        self.lb_beta.grid(row=1, column=13, sticky='EW', padx=5)
        self.e_beta = Entry(frame, textvariable=self.var_beta, width=5, validate='key', validatecommand=vcmd, state=NORMAL)
        self.e_beta.grid(row=1, column=14, sticky='EW')
        Label(frame, text='°').grid(row=1, column=15, sticky='EW')

        self.lb_gamma = Label(frame, text='gamma')
        self.lb_gamma.grid(row=1, column=16, sticky='EW', padx=5)
        self.e_gamma = Entry(frame, textvariable=self.var_gamma, width=5, validate='key', validatecommand=vcmd, state=NORMAL)
        self.e_gamma.grid(row=1, column=17, sticky='EW')
        Label(frame, text='°').grid(row=1, column=18, sticky='EW')

        frame.pack(side='top', fill='x', expand=False, padx=5, pady=5)

        frame = Frame(self)

        self.lb_space_group = Label(frame, text='Space Group')
        self.lb_space_group.grid(row=0, column=0, sticky='EW')
        self.e_space_group = Entry(frame, textvariable=self.var_space_group, width=8, state=NORMAL)
        self.e_space_group.grid(row=0, column=1, sticky='EW', padx=5)

        self.lb_save_name = Label(frame, text='Save File')
        self.lb_save_name.grid(row=0, column=2, sticky='EW', padx=5)
        self.e_save_name = Entry(frame, textvariable=self.var_save_name, width=8, state=NORMAL)
        self.e_save_name.grid(row=0, column=3, sticky='EW')
        appendix_options = [".hkl", ".csv"]
        self.e_rotspeed = OptionMenu(frame, self.var_appendix, ".hkl", *appendix_options)
        self.e_rotspeed.grid(row=0, column=4, sticky='W')

        self.lb_ratio = Label(frame, text="Ratio")
        self.lb_ratio.grid(row=0, column=5, sticky='EW', padx=5)
        vcmd_range = (self.parent.register(self.validate_range), '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')
        self.e_ratio = Entry(frame, textvariable=self.var_ratio, width=8, validate='key', validatecommand=vcmd_range, state=NORMAL)
        self.e_ratio.grid(row=0, column=6, sticky='EW')

        Label(frame, text="Resolution").grid(row=0, column=7, sticky='EW', padx=5)
        self.e_ratio = Entry(frame, textvariable=self.var_resolution, width=8, state=NORMAL)
        self.e_ratio.grid(row=0, column=8, sticky='EW')

        frame.pack(side='top', fill='x', expand=False, padx=5, pady=5)

        frame = Frame(self)

        Checkbutton(frame, text='Scale Iobs', variable=self.var_scale_iobs, width=8).grid(row=1, column=0, sticky='EW')
        Label(frame, text="Power").grid(row=1, column=1, sticky='EW', padx=5)
        self.e_power = Entry(frame, textvariable=self.var_power, width=10, state=NORMAL)
        self.e_power.grid(row=1, column=2, sticky='EW')
        Checkbutton(frame, text='Save smaller', variable=self.var_save_smaller, width=12).grid(row=1, column=3, sticky='EW', padx=5)

        frame.pack(side='top', fill='x', expand=False, padx=5, pady=5)

        frame = Frame(self)
        Separator(frame, orient=HORIZONTAL).grid(row=0, columnspan=18, sticky='ew', pady=5)
        self.IntegratedButton = Button(frame, text='XDS integrated', width=15, command=self.transform_integrated, state=NORMAL)
        self.IntegratedButton.grid(row=1, column=0, sticky='EW')
        self.SaveButton = Button(frame, text='Save Grouped', width=15, command=self.save_grouped, state=NORMAL)
        self.SaveButton.grid(row=1, column=1, sticky='EW', padx=5)
        self.SplitButton = Button(frame, text='Split Grouped', width=15, command=self.split_grouped, state=NORMAL)
        self.SplitButton.grid(row=1, column=2, sticky='EW')
        self.GenFcalcButton = Button(frame, text='Gen Fcalc', width=15, command=self.gen_fcalc, state=NORMAL)
        self.GenFcalcButton.grid(row=1, column=3, sticky='EW', padx=5)
        self.RemoveRefButton = Button(frame, text='Remove Refl', width=15, command=self.remove_reflection, state=NORMAL)
        self.RemoveRefButton.grid(row=1, column=4, sticky='EW')
        self.CorrPrecButton = Button(frame, text='Corr Prec', width=15, command=self.corr_prec, state=NORMAL)
        self.CorrPrecButton.grid(row=2, column=0, sticky='EW')
        self.CorrPrecButton = Button(frame, text='Check I seq', width=15, command=self.check_I_frame_seq, state=NORMAL)
        self.CorrPrecButton.grid(row=2, column=1, sticky='EW', padx=5)

        frame.pack(side='top', fill='x', expand=False, padx=5, pady=5)

        

    def init_vars(self):
        self.file_name = ""
        self.var_img_size = IntVar(value=512)
        self.var_center_x = DoubleVar(value=256.0)
        self.var_center_y = DoubleVar(value=256.0)
        self.var_slope = DoubleVar(value=0.0)
        self.var_lorentz_corr = BooleanVar(value=True)
        self.var_exti_corr = BooleanVar(value=False)
        self.var_exti_param = DoubleVar(value=0.0)
        self.var_prec_angle = DoubleVar(value=1.2)
        self.var_lambda = DoubleVar(value=0.01968)
        self.var_a = DoubleVar(value=10.0)
        self.var_b = DoubleVar(value=10.0)
        self.var_c = DoubleVar(value=10.0)
        self.var_alpha = DoubleVar(value=90.0)
        self.var_beta = DoubleVar(value=90.0)
        self.var_gamma = DoubleVar(value=90.0)
        self.var_space_group = StringVar(value="")
        self.var_save_name = StringVar(value="")
        self.var_appendix = StringVar(value=".hkl")
        self.var_ratio = DoubleVar(value=0.5)
        self.var_resolution = DoubleVar(value=0.8)
        self.var_scale_iobs = BooleanVar(value=False)
        self.var_power = DoubleVar(value=1.5)
        self.var_save_smaller = BooleanVar(value=False)


    def validate(self, action, index, value_if_allowed, prior_value, text, validation_type, trigger_type, widget_name):
        if value_if_allowed:
            try:
                value = float(value_if_allowed)
                return True
            except ValueError:
                return False
        else:
            return False

    def validate_range(self, action, index, value_if_allowed, prior_value, text, validation_type, trigger_type, widget_name):
        if value_if_allowed:
            try:
                value = float(value_if_allowed)
                if value > 0 and value < 1:
                    return True
                else:
                    return False
            except ValueError:
                return False
        else:
            return False

    def remove_reflection(self):
        self.unit_cell = (self.var_a.get(), self.var_b.get(), self.var_c.get(), self.var_alpha.get(), self.var_beta.get(), self.var_gamma.get())
        self.space_group = self.var_space_group.get()
        hkl = any_reflection_file(f"{self.file_name}=hklf4").as_miller_arrays(crystal.symmetry(unit_cell=self.unit_cell, space_group_symbol=self.space_group))[0]
        hkl_df = pd.DataFrame(hkl,columns=('indice','I','sigma'))
        filtered_df = hkl_df[hkl_df['indice'].apply(lambda x: x[0] != 0 and x[1] != 0 and x[2] != 0)]
        self.save_file(filtered_df)

    def corr_prec(self):
        # Correct precession intensities, see Daliang Zhang's paper for formula
        self.unit_cell = (self.var_a.get(), self.var_b.get(), self.var_c.get(), self.var_alpha.get(), self.var_beta.get(), self.var_gamma.get())
        self.space_group = self.var_space_group.get()
        hkl = any_reflection_file(f"{self.file_name}=hklf4").as_miller_arrays(crystal.symmetry(unit_cell=self.unit_cell, space_group_symbol=self.space_group))[0]
        hkl_df = pd.DataFrame(hkl,columns=('indice','I','sigma'))
        d_spacings = hkl.d_spacings().data()
        hkl_df['d_spacings'] = d_spacings
        self.lorentz_corr(hkl_df)
        self.save_file(hkl_df)

    def lorentz_corr(self, df):
        angle = self.var_prec_angle.get() * np.pi / 180
        wavelength = self.var_lambda.get()
        factor = (1/df['d_spacings']) * np.sqrt(((1/wavelength)*np.sin(angle))**2 - (1/df['d_spacings']/2)**2) * wavelength / 2 
        print(df)
        print(factor)
        df['I'] = df['I'] * factor
        df['sigma'] = df['sigma'] * factor
        print(df)

    def read_cif(self,f):
        #read a cif file  One cif file can contain multiple structures
        try:
            if isinstance(f,str):
                structures=cif.reader(file_path=f,raise_if_errors=True).build_crystal_structures()
            else:
                raise TypeError('read_cif: Cannot deal is type {}'.format(type(f)))
        except libtbx.utils.Sorry as e:
            print(e)
            print("Error parsing cif file, check if the data tag does not contain any spaces.")
            exit()
        return structures

    def f_calc_structure_factors(self,structure,**kwargs):
        """Takes cctbx structure and returns f_calc miller array
        Takes an optional options dictionary with keys:
        input:
            **kwargs:
                'd_min': minimum d-spacing for structure factor calculation
                'algorithm': which algorithm to use ('direct', 'fft', 'automatic')
            structure: <cctbx.xray.structure.structure object>
        output:
            f_calc: <cctbx.miller.array object> with calculated structure factors
                in the f_calc.data() function
        
        """
     
        dmin        = kwargs.get('dmin',1.0)
        algorithm   = kwargs.get('algorithm',"automatic")
        anomalous   = kwargs.get('anomalous',False)
        table       = kwargs.get('scatfact_table','wk1995')
        return_as   = kwargs.get('return_as',"series")
        verbose     = kwargs.get('verbose', False)

        if dmin <= 0.0:
            raise ValueError("d-spacing must be greater than zero.")

        if algorithm == "automatic":
            if structure.scatterers().size() <= 100:
                algorithm = "direct"
            else:
                algorithm = None

        structure.scattering_type_registry(table=table)

        f_calc_manager = structure.structure_factors(
                anomalous_flag = anomalous,
                d_min = dmin,
                algorithm = algorithm)
        f_calc = f_calc_manager.f_calc()
        
        if verbose:
            print("\nScattering table:", structure.scattering_type_registry_params.table)
            structure.scattering_type_registry().show()
        print("Minimum d-spacing: %g" % f_calc.d_min())

        if return_as == "miller":
            return f_calc
        elif return_as == "series":
            fcalc = pd.Series(index=f_calc.indices(),data=np.abs(f_calc.data()))
            phase = pd.Series(index=f_calc.indices(),data=np.angle(f_calc.data()))
            return fcalc,phase
        elif return_as == "df":
            dffcal = pd.DataFrame(index=f_calc.index)
            dffcal['fcalc'] = np.abs(f_calc.data())
            dffcal['phase'] = np.angle(f_calc.data())
            return dffcal
        else:
            raise ValueError("Unknown argument for 'return_as':{}".format(return_as))
            
    def calc_structure_factors(self,structures,dmin=1.0,table='electron',prefix='',verbose=True,**kwargs):
        """Wrapper around f_calc_structure_factors()
        Takes a structure object in which there is only one strcture

        dmin can be a dataframe and it will take the minimum dspacing (as specified by col 'd') or a float
        if combine is specified, function will return a dataframe combined with the given one, otherwise a
        dictionary of dataframes

        prefix is a prefix for the default names fcalc/phases to identify different structures
        """    
        fcalc = self.f_calc_structure_factors(structures,dmin=dmin,scatfact_table=table,\
                                        return_as="miller",verbose=verbose,**kwargs)

        return fcalc

    def gen_fcalc(self):
        cif_structures = self.read_cif(self.file_name)
        for name, cif_structure in list(cif_structures.items()):
            Fcalc = self.calc_structure_factors(cif_structure,dmin=self.var_resolution.get())
            break 
        Fcalc_P1 = Fcalc.expand_to_p1()
        Fcalc_data = Fcalc_P1.data()
        Fcalc_indices = list(Fcalc_P1.indices())
        Fcalc_ds = Fcalc_P1.d_spacings().data()
        Fcalc_DF = pd.DataFrame(index=pd.MultiIndex.from_tuples(Fcalc_indices),\
                                data=np.array([np.abs(Fcalc_data),Fcalc_ds]).transpose())
        Fcalc_DF.to_csv(self.var_save_name.get() + '.csv')

    def point_to_rotation_axis(self, x, y, center, slope):
        return np.abs(-slope[0] * (x - center[0]) + slope[1] * (y - center[1])) / np.sqrt(slope[0]**2 + slope[1]**2)

    def exti_corr(self, value, power, param):
        if value > 0:
            return (1 + param * value)**power
        else:
            return - (1 - param * value)**power

    def exti_corr_der(self, value, power, param):
        if value > 0:
            return power * param * self.exti_corr(value, power-1, param)
        else:
            return -power * param * self.exti_corr(value, power-1, param)

    def transform_integrated(self):
        with open(self.file_name, 'r') as f:
            contents = f.readlines()
        header = contents[:32]
        df = pd.read_csv(StringIO(''.join(contents[32:-1])), sep='\s+', names=['H','K','L','IOBS','SIGMA','XCAL','YCAL','ZCAL',
                                        'RLP','PEAK','CORR','MAXC','XOBS','YOBS','ZOBS','ALF0','BET0','ALF1','BET1','PSI','ISEG'])

        for line in header:
            if 'NX' in line:
                self.var_img_size.set(int(line.split()[1]))
            if 'ORGX' in line:
                split = line.split()
                self.var_center_x.set(float(split[1]))
                self.var_center_y.set(float(split[3]))
            if 'ROTATION_AXIS' in line:
                split = line.split()
                self.var_slope.set(np.tan(np.arccos(-float(split[1]))))

        df.loc[:, 'IOBS'] = df['IOBS'] / df['RLP'] / 10
        df.loc[:, 'SIGMA'] = df['SIGMA'] / df['RLP'] / 10
        if self.var_lorentz_corr.get():
            factor = self.point_to_rotation_axis(df['XOBS'], df['YOBS'], [self.var_center_x.get(), self.var_center_y.get()], [self.var_slope.get(),1]) / self.var_img_size.get()
            df.loc[:, 'IOBS'] = df['IOBS'] * factor
            df.loc[:, 'SIGMA'] = df['SIGMA'] * factor

        if self.var_exti_corr.get():
            power = self.var_power.get()
            exti = self.var_exti_param.get()
            #df.loc[:, 'SIGMA'] = df.loc[:, 'SIGMA'] * (df.loc[:, 'IOBS'] * df.loc[:, 'IOBS'].apply(lambda x: self.exti_corr_der(x, power, exti))
            #                                        + df.loc[:, 'IOBS'].apply(lambda x: self.exti_corr(x, power, exti)))
            #df.loc[:, 'IOBS'] = df.loc[:, 'IOBS'].apply(lambda x: self.exti_corr(x, power, exti)) * df.loc[:, 'IOBS']


        with open(self.var_save_name.get() + '.hkl', 'w') as f:
            for i in range(len(df)):
                f.write(f"{df.loc[i, 'H']:4}{df.loc[i, 'K']:4}{df.loc[i, 'L']:4}{df.loc[i, 'IOBS']:8.1f}{df.loc[i, 'SIGMA']:8.1f}\n")

    def open_file(self):
        self.file_name = filedialog.askopenfilename(title='Select file', 
                            filetypes=(('hkl files', '*.hkl'), ('cif files', '*.cif'), ('all files', '*.*')))
        self.lb_file.config(text=self.file_name)

    def save_file(self, df):
        filetype = self.var_appendix.get()
        if filetype == ".csv":
            df.to_csv(self.var_save_name.get()+self.var_appendix.get())
        elif filetype == ".hkl":
            ms = miller.set(crystal_symmetry=crystal.symmetry(space_group_symbol=self.space_group, unit_cell=self.unit_cell), anomalous_flag=False,
               indices=flex.miller_index(list(df['indice'])))
            ma = miller.array(ms, data=flex.double(list(df['I'].map(lambda x: round(x,2)))), 
                  sigmas=flex.double(list(df['sigma'].map(lambda x: round(x,2)))))
            with open(self.var_save_name.get()+filetype, 'w') as f:
                ma.export_as_shelx_hklf(f)

    def group_df(self):
        self.unit_cell = (self.var_a.get(), self.var_b.get(), self.var_c.get(), self.var_alpha.get(), self.var_beta.get(), self.var_gamma.get())
        self.space_group = self.var_space_group.get()
        hkl = any_reflection_file(f"{self.file_name}=hklf4").as_miller_arrays(crystal.symmetry(unit_cell=self.unit_cell, space_group_symbol=self.space_group))[0]
        merge_eq_hkl = hkl.merge_equivalents().array()
        merge_eq_hkl_indice = pd.DataFrame(merge_eq_hkl,columns=('indice2', 'I', 'sigma'))

        df = pd.DataFrame(merge_eq_hkl.expand_to_p1(),columns=('indice1','I','sigma')).merge(merge_eq_hkl_indice,left_on='indice1',right_on='indice2',how='left')[['indice1','indice2']]
        df = df.fillna(method='ffill')
        df_fpair = pd.DataFrame(df['indice1'].apply(lambda x:(-x[0],-x[1],-x[2])))
        df_fpair['indice2'] = df['indice2']
        df = df.append(df_fpair)

        hkl_df = pd.DataFrame(hkl,columns=('indice','I','sigma'))
        hkl_df_no_dup = hkl_df.groupby('indice').mean().reset_index()

        merged = hkl_df_no_dup.merge(df,left_on='indice',right_on='indice1',how='left')
        merged = merged.sort_values('indice2').drop(['indice1'], axis=1)

        return merged

    def check_I_frame_seq(self):
        self.unit_cell = (self.var_a.get(), self.var_b.get(), self.var_c.get(), self.var_alpha.get(), self.var_beta.get(), self.var_gamma.get())
        with open(self.file_name, 'r') as f:
            contents = f.readlines()
            header = contents[:32]
            df = pd.read_csv(StringIO(''.join(contents[32:-1])), sep='\s+', names=['H','K','L','IOBS','SIGMA','XCAL','YCAL','ZCAL',
                                'RLP','PEAK','CORR','MAXC','XOBS','YOBS','ZOBS','ALF0','BET0','ALF1','BET1','PSI','ISEG'])

        for line in header:
            if 'STARTING_ANGLE' in line:
                start_angle = float(line[17:].strip())
            elif 'OSCILLATION_RANGE' in line:
                oscillation_angle = float(line[20:].strip())
        df['index'] = list(zip(df.H, df.K, df.L))
        df_sorted = df.sort_values('ZOBS')
        df_sorted = df_sorted.drop(columns=['H', 'K', 'L'])
        df_sorted  =df_sorted[df_sorted['ZOBS'] != 0.0]
        start_frame = df_sorted['ZOBS'].min()
        end_frame = df_sorted['ZOBS'].max()
        num_frame =  end_frame - start_frame + 1
        start_angle = start_angle + start_frame * oscillation_angle

        file = any_reflection_file(self.file_name).file_content()
        intensity = flex.double(file.iobs)
        sigma = flex.double(file.sigma)
        miller_set = miller.set(crystal.symmetry(unit_cell=self.unit_cell, space_group_symbol=self.var_space_group.get()), 
                                indices=flex.miller_index(file.hkl))
        hkl = miller.array(miller_set, data=intensity, sigmas=sigma)
        hkl = hkl.remove_systematic_absences()
        df_hkl = pd.DataFrame(list(hkl), columns=['index', 'intensity', 'sigma'])
        merged = df_sorted.merge(df_hkl)
        merged.to_csv('1.csv')
        Iobs_diff_acc = 0

        for i in range(len(merged) - 1):
            Iobs_first = merged['IOBS'][i]
            target = merged['index'][i]
            target = list(target)
            target[0] = -target[0]
            target[1] = -target[1]
            target[2] = -target[2]
            target = tuple(target)
            search = merged[i+1:]
            result = search[search['index']==target]
            result = result.reset_index(drop=True)
            if len(result['IOBS']) == 1:
                Iobs_second = result['IOBS'][0]
                Iobs_diff_acc = Iobs_diff_acc + (Iobs_first - Iobs_second) 
            elif len(result['IOBS']) > 1:
                print('Two reflections at the same time?')

        print(f'{target}: {Iobs_first}, {Iobs_second}')
        print(f'start: {start_angle: .2f}, end: {start_angle + oscillation_angle*num_frame: .2f}, frame number: {num_frame}, oscillation: {oscillation_angle}')
        print(f'The difference is {Iobs_diff_acc}.\n')

    def scaling_factor(self, value, power):
        if value > 0:
            result =  value ** power
        else:
            result = (-value) ** power
            result = - result
        return result

    def scaling_func(self, value, power):
        if value > 0:
            result = (1 + value) ** power
        else:
            result  = -(1 - value) ** power
        return result

    def save_grouped(self):
        merged = self.group_df()
        self.save_file(merged)

    def split_grouped(self):
        merged = self.group_df()

        merged_g = merged.groupby(['indice2'], group_keys=False)
        merged_g_sorted = merged_g.apply(pd.DataFrame.sort_values, ['I'])

        selected_g_larger = merged_g_sorted.groupby('indice2', group_keys=False).apply(lambda x: x.iloc[int(x.I.size*self.var_ratio.get()):])
        selected_g_smaller = merged_g_sorted.groupby('indice2', group_keys=False).apply(lambda x: x.iloc[:int(x.I.size*self.var_ratio.get())])

        if self.var_scale_iobs.get():
            power = self.var_power.get()
            #selected_g_larger['I'] = selected_g_larger['I'] / 400
            #selected_g_larger['sigma'] = selected_g_larger['sigma'] / 400

            selected_g_larger['sigma'] = selected_g_larger['sigma'] * selected_g_larger['I'].apply(lambda x: power*self.scaling_func(x, power-1))
            selected_g_larger['I'] = selected_g_larger['I'].apply(lambda x: self.scaling_func(x, power)) * selected_g_larger['I']
            
        if self.var_save_smaller.get():
            self.save_file(selected_g_smaller)
        else:
            self.save_file(selected_g_larger)

def main():
    root = Tk()
    GroupReflectionsGUI(root).pack(side='top', fill='both', expand=True)
    root.mainloop()

if __name__ == '__main__':
    main()
