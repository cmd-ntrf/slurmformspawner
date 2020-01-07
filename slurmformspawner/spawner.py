import os
import sys

from batchspawner import SlurmSpawner
from traitlets import Integer, Bool, Unicode

from . form import SlurmSpawnerForm

class FakeMultiDict(dict):
    getlist = dict.__getitem__

class SlurmFormSpawner(SlurmSpawner):

    mem_min = Integer(1024,
        help="Minimum amount of memory that can be requested"
        ).tag(config=True)

    mem_step = Integer(256,
        help="Define the step of size of memory request range"
        ).tag(config=True)

    mem_def = Integer(1024,
        help="Define the default amount of memory in the form"
        ).tag(config=True)

    mem_lock = Bool(False,
        help="Disable user input for memory request"
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
        prev_opts = self.orm_spawner.user_options
        if prev_opts is None:
            prev_opts = {}

        form_params = {}
        form_params['mem_min'] = self.mem_min
        form_params['mem_step'] = self.mem_step
        form_params['mem_def'] = self.mem_def
        form_params['mem_lock'] = self.mem_lock
        self.form = SlurmSpawnerForm(self.user.name,
                                     self.form_template_path,
                                     form_params,
                                     prev_opts)

    @property
    def cmd(self):
        gui = self.user_options.get('gui', '')
        if gui == 'lab':
            return ['jupyter-labhub']
        else:
            return ['jupyterhub-singleuser']

    @property
    def options_form(self):
        return self.form.render()

    def options_from_form(self, options):
        self.form.process(formdata=FakeMultiDict(options))
        return self.form.data

    @property
    def batch_script(self):
        with open(self.submit_template_path, 'r') as script_template:
            script = script_template.read()
        return script
