# Module taken and modified from Salt's built-in yaml_mako.py renderer.
#
"""
This module provides a custom renderer that process yaml with the Mako
templating engine, extract arguments for any 'state.config' and provide the
extracted arguments(including salt specific args, such as 'require', etc)
as template context. The goal is to make writing reusable/configurable/
parameterized salt files easier.


This module depends on a custom state function, 'state.config', which is
available in salt-contrib. If you don't want to get the whole custome 'state'
module, it's easy to define 'state.config' by yourself too. It's basically
just a no-op state function::

    def config(name, **kws):
        return dict(name=name, changes={}, result=True, comment='')

Save that in state.py in your /srv/salt/_states/ directory; put this module
in /srv/salt/_renderers/ then you should be good to go.

Here's a contrived example using this renderer::

    apache.sls:
    ------------
    #!yaml_mako_stateconf

    apache:
      state.config:
        - port: 80
        - source_conf: /path/to/httpd.conf

        - require_in:
          - cmd: apache_configured

    # --- end of state config ---

    apache_configured:
      cmd.run:
        - name: echo apached configured with port ${apache.port} using conf from ${apache.source_conf}
        - cwd: /


    webapp.sls:
    ------------
    #!yaml_mako_stateconf

    include:
      - apache

    extend:
      apache:
        state.config:
          - port: 8080
          - source_conf: /another/path/to/httpd.conf

    webapp:
      state.config:
        - app_port: 1234 

        - require:
          - state: apache

        - require_in:
          - cmd: webapp_deployed

    # --- end of state config ---

    webapp_deployed:
      cmd.run:
        - name: echo webapp deployed into apache!
        - cwd: /


Notice that the end of configuration marker(# --- end of state config --) is
needed to separate the use of 'state.config' form the rest of your salt file,
and don't forget to put the "#!yaml_mako_stateconf" shangbang at the beginning
of your salt files. Lastly, you need to have Mako already installed, of course.

"""

# TODO:
#   - support synthetic argument? Eg, 
#
#     apache:
#       state.config:
#         - host: localhost
#         - port: 1234
#         - url: 'http://${host}:${port}/'
#
#     Currently, this won't work, but can be worked around like so:
#
#     apache:
#       state.config:
#         - host: localhost
#         - port: 1234
#     ##  - url: 'http://${host}:${port}/'
#
#     # --- end of state config ---
#     <% 
#     apache.setdefault('url', "http://%(host)s:%(port)s/" % apache)
#     %>
#

import logging
import warnings
import re
from mako.template import Template
from mako import exceptions
from salt.utils.yaml import CustomLoader, load
from salt.exceptions import SaltRenderError

log = logging.getLogger(__name__)

__opts__ = {
  'stateconf_end_marker': r'#\s*-+\s*end of state config\s*-+'
  # eg, something like "# --- end of state config --" works by default.
}

def render(template_file, env='', sls=''):

    def do_it(data, context=None):
        if not context:
            match = re.search(__opts__['stateconf_end_marker'], data)
            if match:
                data = data[:match.start()]
        
        ctx = dict(salt=__salt__,
                   grains=__grains__,
                   opts=__opts__,
                   pillar=__pillar__,
                   env=env,
                   sls=sls)
        if context:
            ctx.update(context)
        try:
            yaml_data = Template(data).render(**ctx)
        except:
            raise SaltRenderError(exceptions.text_error_template().render())

        with warnings.catch_warnings(record=True) as warn_list:
            data = load(yaml_data, Loader=CustomLoader)
            if len(warn_list) > 0:
                for item in warn_list:
                    log.warn("{warn} found in {file_}".format(
                            warn=item.message, file_=template_file))
        if not context:
            extract_state_confs(data)
        return data


    with open(template_file, 'r') as f:
        sls_templ = f.read()

    # first pass to extract the state configuration
    data = do_it(sls_templ)

    # if some config has been extracted then
    # do a second pass that provides the extracted conf as template context
    if STATE_CONF:  
        data = do_it(sls_templ, STATE_CONF)

    return data



# Quick and dirty way to get attribute access for dictionary keys.
# So, we can do: ${apache.port} instead of ${apache['port']} when possible.
class Bunch(dict):
    def __getattr__(self, name):
        return self[name]


# With sls:
#
#   state_id:
#     state.config:
#       - name1: value1
#
# STATE_CONF is:
#    { state_id => {name1: value1} }
#
STATE_CONF = {}       # state.config
STATE_CONF_EXT = {}   # state.config under extend: ...

def extract_state_confs(data, is_extend=False):
    for state_id, state_dict in data.iteritems():
        if state_id == 'extend' and not is_extend:
            extract_state_confs(state_dict, True)
            continue

        if 'state' in state_dict:
            key = 'state'
        elif 'state.config' in state_dict:
            key = 'state.config'
        else:
            continue

        to_dict = STATE_CONF_EXT if is_extend else STATE_CONF
        conf = to_dict.setdefault(state_id, Bunch())
        for d in state_dict[key]:
            k, v = d.iteritems().next()
            conf[k] = v

        if not is_extend and state_id in STATE_CONF_EXT:
            extend = STATE_CONF_EXT[state_id]
            for requisite in 'require', 'watch':
                if requisite in extend:
                    extend[requisite] += to_dict[state_id].get(requisite, [])
            to_dict[state_id].update(STATE_CONF_EXT[state_id])


