from subprocess import check_output

from jinja2 import Template
from wtforms import BooleanField, DecimalField, SelectField, StringField, Form, RadioField
from wtforms.validators import InputRequired
from wtforms.fields.html5 import IntegerField
from wtforms.widgets.html5 import NumberInput

def get_slurm_cpus():
    cpus = check_output(['sinfo', '-h', '-e', '--format=%c'], encoding='utf-8').split()
    return list(map(int, cpus))

def get_slurm_accounts(username):
    output = check_output(['sacctmgr', 'show', 'user', username, 'withassoc',
                           'format=account', '-p', '--noheader'], encoding='utf-8').split()
    return [out.rstrip('|') for out in output]

def get_slurm_gres():
    return check_output(['sinfo', '-h', '--format=%G'], encoding='utf-8').split()

class SlurmSpawnerForm(Form):
    account = SelectField("Account")
    runtime = DecimalField('Time (hours)', validators=[InputRequired()],
                           widget=NumberInput(min=0.25, max=12, step=0.25))
    gui     = RadioField('GUI',
                         choices=[('notebook', 'Jupyter Notebook'), ('lab', 'JupyterLab')],
                         default='notebook')
    nprocs  = IntegerField('Number of cores', validators=[InputRequired()],
                           widget=NumberInput(min=1, step=1))
    memory  = IntegerField('Memory (MB)',  validators=[InputRequired()],
                           widget=NumberInput(min=256, step=256))
    gpus    = SelectField('GPU configuration')
    oversubscribe = BooleanField('Enable core oversubscription?')

    template = """
<div class="row">
    <div class="col">
        <div class="form-group col-md-6">
            {{ form.account.label }}
            {{ form.account(class_="form-control") }}
        </div>
    </div>
    <div class="col">
        <div class="form-group col-md-6">
            {{ form.runtime.label }}
            {{ form.runtime(class_="form-control") }}
        </div>
    </div>
</div>
<div class="form-group">
    {{ form.nprocs.label }}
    {{ form.nprocs(class_="form-control") }}
</div>
<div class="form-group">
    <div class="form-check">
        {{ form.oversubscribe(class_="form-check-input") }}
        {{ form.oversubscribe.label(class_="form-check-label") }}
        <small id="overs_help" class="form-text text-muted">Recommended for interactive usage</small>
    </div>
</div>
<div class="form-group">
    {{ form.memory.label }}
    {{ form.memory(class_="form-control") }}
</div>
<div class="form-group">
    {{ form.gpus.label }}
    {{ form.gpus(class_="form-control") }}
</div>
<div class="form-group">
    {{ form.gui.label }}
    {% for subfield in form.gui %}
        <div class="radio">
            <label>{{ subfield }}{{subfield.label.text}}</label>
        </div>
    {% endfor %}
</div>
"""
    def __init__(self, username, fields):
        super().__init__()
        self.set_account_choices(get_slurm_accounts(username))
        self.set_nproc_max(get_slurm_cpus())
        self.set_gpu_choices(get_slurm_gres())

        for field, value in fields:
            if value:
                self[field].data = value

        # Convert runtime to minutes
        if self['runtime'].data:
            self['runtime'].data //= 60
        self.runtime.filters = [lambda x: int(x * 60)]

    def render(self):
        return Template(self.template).render(form=self)

    def set_nproc_max(self, cpu_choices):
        self.nprocs.widget.max = max(cpu_choices)

    def set_account_choices(self, accounts):
        self.account.choices = list(zip(accounts, accounts))

    def set_gpu_choices(self, gres_list):
        gpu_choices = {'gpu:0': 'None'}
        for gres in gres_list:
            gres = gres.split(':')
            if gres[0] == 'gpu':
                number = int(gres[-1])
                if len(gres) == 2:
                    strings = ('gpu:{}', '{} x GPU')
                elif len(gres) > 2:
                    strings = ('gpu:{}:{{}}'.format(gres[1]), '{{}} x {}'.format(gres[1].upper()))
                for i in range(1, number + 1):
                    gpu_choices[strings[0].format(i)] = strings[1].format(i)
        self.gpus.choices = gpu_choices.items()
