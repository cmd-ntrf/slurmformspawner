import os
import re
import sys

from functools import partial
from datetime import datetime

from jinja2 import Template

from traitlets.config.configurable import Configurable
from traitlets import Integer, CBool, Unicode, Float, Set, Dict, Unicode

from jupyterhub.traitlets import Callable

from wtforms import BooleanField, DecimalField, SelectField, StringField, Form, RadioField
from wtforms.form import BaseForm
from wtforms.validators import InputRequired, NumberRange, AnyOf
from wtforms.fields.html5 import IntegerField
from wtforms.widgets.html5 import NumberInput

from . traitlets import NumericRangeWidget, SelectWidget

class FakeMultiDict(dict):
    getlist = dict.__getitem__

def resolve(value, *args, **kargs):
    if callable(value):
        return value(*args, **kargs)
    else:
        return value

class SbatchForm(Configurable):

    runtime = NumericRangeWidget(
        {
            'min' : 0.25,
            'def' : 1.0,
            'step': 0.25,
            'lock': False,
        },
        help="Define parameters of runtime numeric range widget"
    ).tag(config=True)

    memory = NumericRangeWidget(
        {
            'min' : 1024,
            'step': 1,
            'lock': False,
            'def': lambda api, user: int(max(api.get_mems()) / max(api.get_cpus())),
            'max': lambda api, user: max(api.get_mems())
        },
        help="Define parameters of memory numeric range widget in MB"
    ).tag(config=True)

    nprocs = NumericRangeWidget(
        {
            'min' : 1,
            'step': 1,
            'lock': False,
            'def': 1,
            'max' : lambda api, user: max(api.get_cpus())
        },
        help="Define parameters of core numeric range widget"
    ).tag(config=True)

    oversubscribe = Dict({'def' : False, 'lock' : True}).tag(config=True)

    gpus = SelectWidget(
        {
            'def' : 'gpu:0',
            'choices' : lambda api, user: api.get_gres(),
            'lock' : False
        },
        help="Define the list of available gpu configurations."
    ).tag(config=True)

    account = SelectWidget(
        {
            'choices' : lambda api, user: api.get_accounts(user),
            'lock' : False
        },
        help="Define the list of available accounts."
    ).tag(config=True)

    reservation = SelectWidget(
        {
            'def' : '',
            'choices' : lambda api, user: api.get_active_reservations(user, api.get_accounts(user)),
            'lock' : False
        },
        help="Define the list of available reservations."
    ).tag(config=True)

    ui = SelectWidget(
        {
            'lock' : False,
            'def' : 'lab',
            'choices' : ['notebook', 'lab', 'terminal']
        },
        help="Define the list of available user interface."
    ).tag(config=True)

    form_template_path = Unicode(
        os.path.join(sys.prefix, 'share', 'slurmformspawner', 'templates', 'form.html'),
        help="Path to the Jinja2 template of the form"
    ).tag(config=True)

    def __init__(self, username, slurm_api, ui_args, user_options = {}, config=None):
        super().__init__(config=config)
        fields = {
            'account' : SelectField("Account", validators=[AnyOf([])]),
            'runtime' : DecimalField('Time (hours)', validators=[InputRequired(), NumberRange()], widget=NumberInput()),
            'ui'      : SelectField('User interface', validators=[AnyOf([])]),
            'nprocs'  : IntegerField('Number of cores', validators=[InputRequired(), NumberRange()], widget=NumberInput()),
            'memory'  : IntegerField('Memory (MB)',  validators=[InputRequired(), NumberRange()], widget=NumberInput()),
            'gpus'    : SelectField('GPU configuration', validators=[AnyOf([])]),
            'oversubscribe' : BooleanField('Enable core oversubscription?'),
            'reservation' : SelectField("Reservation", validators=[AnyOf([])])
        }
        self.form = BaseForm(fields)
        self.form['runtime'].filters = [float]
        self.resolve = partial(resolve, api=slurm_api, user=username)
        self.ui_args = ui_args

        with open(self.form_template_path, 'r') as template_file:
            self.template = template_file.read()

        for key in fields:
            dict_ = getattr(self, key)
            if dict_.get('lock') is True:
                if dict_.get('def') is None:
                    raise Exception(f'You need to define a default value for {key} because it is locked.')
            if key in user_options:
                self.form[key].process(formdata=FakeMultiDict({key : [user_options[key]]}))
            else:
                self.form[key].process(formdata=FakeMultiDict({key : [self.resolve(getattr(self, key).get('def'))]}))

    @property
    def data(self):
        return self.form.data

    @property
    def errors(self):
        return self.form.errors

    def process(self, formdata):
        for key in self.form._fields.keys():
            lock = self.resolve(getattr(self, key).get('lock'))
            value = formdata.get(key)
            if not lock and value is not None:
                self.form[key].process(formdata=FakeMultiDict({key : value}))

    def validate(self):
        valid = True
        for key in self.form._fields.keys():
            lock = self.resolve(getattr(self, key).get('lock'))
            if not lock:
                valid = self.form[key].validate(self.form) and valid
        return valid

    def render(self):
        self.config_runtime()
        self.config_nprocs()
        self.config_memory()
        self.config_oversubscribe()
        self.config_ui()
        self.config_gpus()
        self.config_reservations()
        self.config_account()
        return Template(self.template).render(form=self.form)

    def config_runtime(self):
        lock = self.resolve(self.runtime.get('lock'))
        if lock:
            def_ = self.resolve(self.runtime.get('def'))
            self.form['runtime'].render_kw = {'disabled': 'disabled'}
            self.form['runtime'].widget.min = def_
            self.form['runtime'].widget.max = def_
            self.form['runtime'].validators[-1].min = def_
            self.form['runtime'].validators[-1].max = def_
            self.form['runtime'].validators[-1].message = f'Runtime can only be {def_}'
        else:
            min_ = self.resolve(self.runtime.get('min'))
            max_ = self.resolve(self.runtime.get('max'))
            step = self.resolve(self.runtime.get('step'))
            self.form['runtime'].widget.min = min_
            self.form['runtime'].widget.max = max_
            self.form['runtime'].widget.step = step
            if min_ is not None:
                self.form['runtime'].validators[-1].min = min_
            if max_ is not None:
                self.form['runtime'].validators[-1].max = max_
            self.form['runtime'].validators[-1].message = f'Runtime outside of allowed range [{min_}, {max_}]'

    def config_nprocs(self):
        lock = self.resolve(self.nprocs.get('lock'))
        if lock:
            def_ = self.resolve(self.nprocs.get('def'))
            self.form['nprocs'].render_kw = {'disabled': 'disabled'}
            self.form['nprocs'].widget.min = def_
            self.form['nprocs'].widget.max = def_
            self.form['nprocs'].validators[-1].min = def_
            self.form['nprocs'].validators[-1].max = def_
        else:
            min_ = self.resolve(self.nprocs.get('min'))
            max_ = self.resolve(self.nprocs.get('max'))
            step = self.resolve(self.nprocs.get('step'))
            self.form['nprocs'].widget.min = min_
            self.form['nprocs'].widget.max = max_
            self.form['nprocs'].widget.step = step
            self.form['nprocs'].validators[-1].min = min_
            self.form['nprocs'].validators[-1].max = max_

    def config_memory(self):
        lock = self.resolve(self.memory.get('lock'))
        if lock:
            def_ = self.resolve(self.memory.get('def'))
            self.form['memory'].render_kw = {'disabled': 'disabled'}
            self.form['memory'].widget.min = def_
            self.form['memory'].widget.max = def_
            self.form['memory'].validators[-1].min = def_
            self.form['memory'].validators[-1].max = def_
        else:
            min_ = self.resolve(self.memory.get('min'))
            max_ = self.resolve(self.memory.get('max'))
            step = self.resolve(self.memory.get('step'))
            self.form['memory'].widget.min = min_
            self.form['memory'].widget.max = max_
            self.form['memory'].widget.step = step
            self.form['memory'].validators[-1].min = min_
            self.form['memory'].validators[-1].max = max_

    def config_oversubscribe(self):
        if self.oversubscribe['lock']:
            self.form['oversubscribe'].render_kw = {'disabled': 'disabled'}

    def config_account(self):
        choices = self.resolve(self.account.get('choices'))
        lock = self.resolve(self.account.get('lock'))
        if choices:
            self.form['account'].choices = list(zip(choices, choices))
            self.form['account'].validators[-1].values = choices
            if not hasattr(self.form['account'], 'data'):
                self.form['account'].process_data(self.form['account'].choices[0])
            if lock:
                self.form['account'].render_kw = {'disabled': 'disabled'}
        else:
            self.account['lock'] = True
            self.form['account'].choices = [("", "None")]
            self.form['account'].validators[-1].values = [("", "None")]
            self.form['account'].render_kw = {'disabled': 'disabled'}

    def config_gpus(self):
        choices = self.resolve(self.gpus.get('choices'))
        lock = self.resolve(self.gpus.get('lock'))

        gpu_choice_map = {}
        for gres in choices:
            if gres == 'gpu:0':
                gpu_choice_map['gpu:0'] = 'None'
                continue
            match = re.match(r"(gpu:[\w:]+)", gres)
            if match:
                gres = match.group(1).split(':')
                number = int(gres[-1])
                if len(gres) == 2:
                    strings = ('gpu:{}', '{} x GPU')
                elif len(gres) > 2:
                    strings = ('gpu:{}:{{}}'.format(gres[1]), '{{}} x {}'.format(gres[1].upper()))
                for i in range(1, number + 1):
                    gpu_choice_map[strings[0].format(i)] = strings[1].format(i)
        self.form['gpus'].choices = list(gpu_choice_map.items())
        if lock:
            self.form['gpus'].render_kw = {'disabled': 'disabled'}
        self.form['gpus'].validators[-1].values = [key for key, value in self.form['gpus'].choices]

    def config_ui(self):
        choices = self.resolve(self.ui.get('choices'))
        lock = self.resolve(self.ui.get('lock'))
        self.form['ui'].validators[-1].values = [key for key in choices]
        self.form['ui'].choices = [(key, self.ui_args[key]['name']) for key in choices]

        if lock:
            self.form['ui'].render_kw = {'disabled': 'disabled'}

    def config_reservations(self):
        choices = self.resolve(self.reservation.get('choices'))
        lock = self.resolve(self.reservation.get('lock'))
        prev = self.form['reservation'].data
        if choices is None:
            choices = []

        now = datetime.now()
        prev_is_valid = False
        self.form['reservation'].choices = [("", "None")]
        for rsv in choices:
            name = rsv['ReservationName']
            duration = rsv['EndTime'] - now
            string = '{} - time left: {}'.format(name, duration)
            self.form['reservation'].choices.append((name, string))
            if prev == name:
                prev_is_valid = True
        if lock:
            self.form['reservation'].render_kw = {'disabled': 'disabled'}
        self.form['reservation'].validators[-1].values = [key for key, value in self.form['reservation'].choices]
