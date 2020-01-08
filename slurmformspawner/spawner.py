import os
import sys

from collections import defaultdict

from batchspawner import SlurmSpawner
from traitlets import Integer, Bool, Unicode, Float

from . form import SlurmSpawnerForm
from . import slurm

class FakeMultiDict(dict):
    getlist = dict.__getitem__


GUI_CHOICES = {
    'notebook' : {
        'name' : 'Jupyter Notebook',
        'cmd' : 'jupyterhub-singleuser'
    },
    'lab' : {
        'name' : 'JupyterLab',
        'cmd' : 'jupyter-labhub'
    }
}

class SlurmFormSpawner(SlurmSpawner):

    runtime_min = Float(0.25,
                        help="Minimum runtime that can be requested in hours"
                        ).tag(config=True)

    runtime_def = Float(1.0,
                        help="Define the default runtime in the form in hours"
                        ).tag(config=True)

    runtime_max = Float(12.0,
                        help="Maximum runtime that can be requested in hours (0 means unlimited)"
                        ).tag(config=True)

    runtime_step = Float(0.25,
                        help="Runtime increment that can be requested in hours"
                        ).tag(config=True)

    runtime_lock = Bool(False,
                        help="Disable user input for runtime"
                        ).tag(config=True)

    mem_min = Integer(1024,
        min=1,
        help="Minimum amount of memory that can be requested in MB"
        ).tag(config=True)

    mem_max = Integer(
        min=0,
        help="Maximum amount of memory that can be requested in MB (0: limits is infered from Slurm config)"
        ).tag(config=True)

    mem_step = Integer(1,
        min=1,
        help="Define the step of size of memory request range in MB"
        ).tag(config=True)

    mem_def = Integer(1024,
        min=0,
        help="Define the default amount of memory in the form in MB (0: maximum amounts of memory when skip_form = True)"
        ).tag(config=True)

    mem_lock = Bool(False,
        help="Disable user input for memory request"
        ).tag(config=True)

    core_min = Integer(1,
        min=1,
        help="Minimum amount of cores that can be requested"
        ).tag(config=True)

    core_max = Integer(
        min=0,
        help="Maximum amount of cores that can be requested (0: limits is infered from Slurm config)"
        ).tag(config=True)

    core_step = Integer(1,
        min=1,
        help="Define the step of cores request range"
        ).tag(config=True)

    core_def = Integer(1,
        min=0,
        help="Define the default amount of cores in the form (0: maximum amounts of cores when skip_form = True)"
        ).tag(config=True)

    core_lock = Bool(False,
        help="Disable user input for core request"
        ).tag(config=True)

    oversubscribe_def = Bool(False,
        help="Define the default value for oversubscription"
        ).tag(config=True)

    oversubscribe_lock = Bool(False,
        help="Disable user input for oversubscription"
        ).tag(config=True)

    gpus_def = Unicode('',
        help="Define the default value for gpu configuration"
        ).tag(config=True)

    gpus_lock = Bool(False,
        help="Disable user input for gpu request"
        ).tag(config=True)

    gui_def = Unicode(list(GUI_CHOICES.keys())[0],
        help="Define the default gui. Possible value: [{}]".format(list(GUI_CHOICES.keys()))
        ).tag(config=True)

    gui_lock = Bool(False,
        help="Disable user input for gui request"
        ).tag(config=True)

    skip_form = Bool(False,
        help="Disable the spawner input form"
        ).tag(config=True)

    form_template_path = Unicode(
        os.path.join(sys.prefix, 'share/slurmformspawner/templates/form.html'),
        help="Path to the Jinja2 template of the form"
        ).tag(config=True)

    submit_template_path = Unicode(
        os.path.join(sys.prefix, 'share/slurmformspawner/templates/submit.sh'),
        help="Path to the Jinja2 template of the submit file"
        ).tag(config=True)

    exec_prefix = ""
    env_keep = []
    batch_submit_cmd = "sudo --preserve-env={keepvars} -u {username} sbatch --parsable"
    batch_cancel_cmd = "sudo -u {username} scancel {job_id}"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.skip_form:
            prev_opts = self.orm_spawner.user_options
            if prev_opts is None:
                prev_opts = {}
            self.config_form(prev_opts)

    @property
    def user_options(self):
        if self.skip_form:
            return {
                'runtime' : int(self.runtime_def * 60),
                'nprocs'  : self.core_def if self.core_def > 0 else max(slurm.get_cpus()),
                'memory'  : self.mem_def if self.mem_def > 0 else max(slurm.get_mems()),
                'gpus'    : self.gpus_def,
                'oversubscribe' : self.oversubscribe_def,
            }
        else:
            return self._user_options

    @user_options.setter
    def user_options(self, value):
        if not self.skip_form:
            self._user_options = value

    @property
    def cmd(self):
        gui = self.user_options.get('gui', self.gui_def)
        return [GUI_CHOICES[gui]['cmd']]

    @property
    def options_form(self):
        if self.skip_form:
            return None

        accounts = slurm.get_accounts(self.user.name)
        reservations = slurm.get_active_reservations(self.user.name, accounts)
        return self.form.render(accounts, reservations)

    def options_from_form(self, options):
        if self.runtime_lock:
            options.pop('runtime', None)
        if self.mem_lock:
            options.pop('memory', None)
        if self.core_lock:
            options.pop('nprocs', None)
        if self.oversubscribe_lock:
            options.pop('oversubscribe', None)
        if self.gpus_lock:
            options.pop('gpus', None)
        self.form.process(formdata=FakeMultiDict(options),
                          runtime=self.runtime_def,
                          memory=self.mem_def,
                          nprocs=self.core_def,
                          oversubscribe=self.oversubscribe_def,
                          gpus=self.gpus_def)
        return self.form.data

    def config_form(self, prev_opts):
        form_params = defaultdict(dict)

        form_params['runtime']['def_'] = self.runtime_def
        form_params['runtime']['min_'] = self.runtime_min
        form_params['runtime']['max_'] = self.runtime_max if self.runtime_max > 0 else None
        form_params['runtime']['step'] = self.runtime_step
        form_params['runtime']['lock'] = self.runtime_lock

        form_params['core']['def_'] = self.core_def
        form_params['core']['min_'] = self.core_min
        form_params['core']['max_'] = max(slurm.get_cpus())
        if self.core_max > 0:
            form_params['core']['max_'] = min(self.core_max, form_params['core']['max_'])
        form_params['core']['step'] = self.core_step
        form_params['core']['lock'] = self.core_lock

        form_params['mem']['def_'] = self.mem_def
        form_params['mem']['min_'] = self.mem_min
        form_params['mem']['max_'] = max(slurm.get_mems())
        if self.mem_max > 0:
            form_params['mem']['max_'] = min(self.mem_max, form_params['mem']['max_'])
        form_params['mem']['step'] = self.mem_step
        form_params['mem']['lock'] = self.mem_lock

        form_params['oversubscribe']['def_'] = self.oversubscribe_def
        form_params['oversubscribe']['lock'] = self.oversubscribe_lock

        form_params['gpus']['def_'] = self.gpus_def
        form_params['gpus']['lock'] = self.gpus_lock
        form_params['gpus']['choices'] = slurm.get_gres()

        form_params['gui']['def_'] = self.gui_def
        form_params['gui']['lock'] = self.gui_lock
        form_params['gui']['choices'] = list(zip(GUI_CHOICES.keys(), (gui['name'] for gui in GUI_CHOICES.values())))

        self.form = SlurmSpawnerForm(self.form_template_path,
                                     form_params,
                                     prev_opts)

    @property
    def batch_script(self):
        with open(self.submit_template_path, 'r') as script_template:
            script = script_template.read()
        return script
