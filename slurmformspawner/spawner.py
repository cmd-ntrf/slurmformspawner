import os
import sys

from collections import defaultdict

from batchspawner import SlurmSpawner
from traitlets import Integer, CBool, Unicode, Float, Set, Dict

from . form import SbatchForm
from . slurm import SlurmAPI

class SlurmFormSpawner(SlurmSpawner):
    disable_form = CBool(
        False,
        help="Disable the spawner input form"
    ).tag(config=True)

    ui_args = Dict(
        {
            'notebook' : {
                'name' : 'Jupyter Notebook',
            },
            'lab' : {
                'name' : 'JupyterLab',
                'args' : ['--SingleUserNotebookApp.default_url=/lab']
            },
            'terminal' : {
                'name' : 'Terminal',
                'args' : ['--SingleUserNotebookApp.default_url=/terminals/1']
            },
        },
        help="Dictionary of dictionaries describing the names and args of UI options"
    ).tag(config=True)

    slurm_bin_path = Unicode(
        '/opt/slurm/bin',
        help="Absolute path to Slurm executables"
    ).tag(config=True)

    submit_template_path = Unicode(
        os.path.join(sys.prefix, 'share', 'slurmformspawner', 'templates', 'submit.sh'),
        help="Path to the Jinja2 template of the submit file"
    ).tag(config=True)

    error_template_path = Unicode(
        os.path.join(sys.prefix, 'share', 'slurmformspawner', 'templates', 'error.html'),
        help="Path to the Jinja2 template of the form when there is a problem with Slurm"
    ).tag(config=True)

    exec_prefix = ""
    env_keep = []
    batch_submit_cmd = "sudo --preserve-env={keepvars} -u {username} {slurm_bin_path}/sbatch --parsable"
    batch_cancel_cmd = "sudo -u {username} {slurm_bin_path}/scancel {job_id}"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.slurm_api = SlurmAPI.instance(self.config)
        self.form = SbatchForm(username=self.user.name,
                               slurm_api=self.slurm_api,
                               ui_args=self.ui_args,
                               user_options=self.orm_spawner.user_options or {},
                               config=self.config)

        self.batch_submit_cmd = self.batch_submit_cmd.format(
            username='{username}',
            keepvars='{keepvars}',
            slurm_bin_path=self.slurm_bin_path
        )
        self.batch_cancel_cmd = self.batch_cancel_cmd.format(
            username='{username}',
            job_id='{job_id}',
            slurm_bin_path=self.slurm_bin_path
        )

        with open(self.error_template_path, 'r') as file_:
            self.error_form = file_.read()

        with open(self.submit_template_path, 'r') as script_template:
            self.batch_script = script_template.read()

    @property
    def user_options(self):
        options = self.form.data.copy()
        options['runtime'] = int(options['runtime'] * 60)
        return options

    @user_options.setter
    def user_options(self, value):
        pass

    def get_args(self):
        args = super().get_args()
        ui = self.form.data.get('ui')
        return args + self.ui_args[ui].get('args', [])

    @property
    def options_form(self):
        if self.slurm_api.is_online():
            if self.disable_form:
                return None
            if self.form is not None:
                return self.form.render()
        return self.error_form

    def options_from_form(self, options):
        self.form.process(options)
        if not self.form.validate():
            raise Exception(', '.join((f"{key}: {error_list[0]}" for key, error_list in self.form.errors.items())))
        return self.form.data
