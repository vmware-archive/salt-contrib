# Module taken and modified from Salt's built-in yaml_mako.py renderer.
#
"""
This module provides a custom renderer that process yaml with the Mako
templating engine, extract arguments for any ``state.config`` and provide
the extracted arguments(including salt specific args, such as 'require', etc)
as template context. The goal is to make writing reusable/configurable/
parameterized salt files easier and cleaner.

This module depends on a custom state function, 'state.config', which is
available in salt-contrib. If you don't want to get the whole custome 'state'
module, it's easy to define 'state.config' by yourself too. It's basically
just a no-op state function::

    def config(name, **kws):
        return dict(name=name, changes={}, result=True, comment='')

Save that in `state.py` in your `/srv/salt/_states/` directory; put this module
in `/srv/salt/_renderers/` then you should be good to go.

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


``state.config`` let's you declare and set default values for the parameters
used by your salt file. These parameters will be available in your template 
context, so you can generate the rest of your salt file according to their
values. And your parameterized salt file can be included and then extended
just like any other salt files! So, with the above two salt files, running
``state.highstate`` will actually output::

  apache configured with port 8080 using conf from /another/path/to/httpd.conf

Notice that the end of configuration marker(``# --- end of state config --``)
is needed to separate the use of 'state.config' form the rest of your salt
file, and don't forget to put the ``#!yaml_mako_stateconf`` shangbang at the
beginning of your salt files. Lastly, you need to have Mako already installed,
of course.

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
from os import path as ospath
from mako.template import Template
from mako import exceptions
from salt.utils.yaml import CustomLoader, load
from salt.exceptions import SaltRenderError

log = logging.getLogger(__name__)

__opts__ = {
  'stateconf_end_marker': r'#\s*-+\s*end of state config\s*-+',
  # eg, something like "# --- end of state config --" works by default.
}

def render(template_file, env='', sls=''):

    def do_it(data, context=None):
        if not context:
            match = re.search(__opts__['stateconf_end_marker'], data)
            if match:
                data = data[:match.start()]
        
        uripath = sls.replace('.', '/')
        ctx = dict(salt=__salt__,
                   grains=__grains__,
                   opts=__opts__,
                   pillar=__pillar__,
                   env=env,
                   sls=sls,
                   sls_dir=ospath.dirname(uripath))
        if context:
            ctx.update(context)
        try:
            yaml_data = Template(data,
                             uri=uripath,
                             strict_undefined=True,
                             lookup=SaltMakoTemplateLookup(__opts__, env)
                        ).render(**ctx)
        except:
            raise SaltRenderError(exceptions.text_error_template().render())

        with warnings.catch_warnings(record=True) as warn_list:
            data = load(yaml_data, Loader=CustomLoader)
            if len(warn_list) > 0:
                for item in warn_list:
                    log.warn("{warn} found in {file_}".format(
                            warn=item.message, file_=template_file))
    
        rewrite_sls_includes_excludes(data, sls)
        rename_state_ids(data, sls)
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
        tmplctx = STATE_CONF.copy()
        prefix = sls + '::'
        for k in tmplctx.keys():
            if k.startswith(prefix):
                tmplctx[k[len(prefix):]] = tmplctx[k]
                del tmplctx[k]
        data = do_it(sls_templ, tmplctx)

    return data


def _parent_sls(sls):
    i = sls.rfind('.')
    return sls[:i]+'.' if i != -1 else ''

def rewrite_sls_includes_excludes(data, sls):
    # if the path of the included/excluded sls starts with a leading dot(.) then
    # it's taken to be relative to the including/excluding sls.
    sls = _parent_sls(sls)
    for sid in data: 
        if sid == 'include':
            includes = data[sid]
            for i, each in enumerate(includes):
                if each.startswith('.'):
                    includes[i] = sls + each[1:]
        elif sid == 'exclude':
            for d in data[sid]:
                if 'sls' in d and d['sls'].starstwith('.'):
                    d['sls'] = sls + d['sls'][1:]



RESERVED_SIDS = set(['include', 'exclude'])
RESERVED_ARGS = set(['require', 'require_in', 'watch', 'watch_in', 'use', 'use_in'])

def _local_to_abs_sid(id, sls): # id must starts with '.'
    return _parent_sls(sls)+id[1:] if '::' in id else sls+'::'+id[1:] 

def rename_state_ids(data, sls, is_extend=False):
    # if the .sls file is salt://my/salt/file.sls
    # then rename all state ids defined in it that start with a dot(.) with
    # "my.salt.file::" + the_state_id_without_the_first_dot.

    # update "local" references to the renamed states.
    for sid, states in data.items():
        if sid in RESERVED_SIDS:
            continue

        if sid == 'extend' and not is_extend:
            rename_state_ids(states, sls, True)
            continue

        for args in states.itervalues():
            for name, value in (nv.iteritems().next() for nv in args):
                if name not in RESERVED_ARGS:
                    continue
                for req in value:
                    id = req.itervalues().next()
                    if id in data and id.startswith('.'):
                        req[req.iterkeys().next()] = _local_to_abs_sid(id, sls)

    for sid in data.keys():
        if sid.startswith('.'):
            data[_local_to_abs_sid(sid, sls)] = data[sid]
            del data[sid]




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





import urlparse
from mako.lookup import TemplateCollection, TemplateLookup
import salt.fileclient

# With some code taken and modified from salt.utils.jinja.SaltCacheLoader
class SaltMakoTemplateLookup(TemplateCollection):
    """
    Look up Mako template files on Salt master via salt://... URLs.

    If URL is a relative path(without an URL scheme) then assume it's relative
    to the directory of the salt file that's doing the lookup(with <%include/>
    or <%namespace/>).

    If URL is an absolute path then it's treated as if it has been prefixed
    with salt://.

    """

    def __init__(self, opts, env='base'):
        self.opts = opts
        self.env = env
        if __opts__['file_client'] == 'local':
            searchpath = opts['file_roots'][env]
        else:
            searchpath = [ospath.join(opts['cachedir'], 'files', env)]
        self.lookup = TemplateLookup(directories=searchpath)

        self.file_client = salt.fileclient.get_file_client(self.opts)
        self.cache = {}
        
    def adjust_uri(self, uri, filename):
        scheme = urlparse.urlparse(uri).scheme
        if scheme == 'salt':
            return uri
        elif scheme:
            raise ValueError("Unsupported URL scheme(%s) in %s" % \
                             (scheme, uri))
        else:
            return self.lookup.adjust_uri(uri, filename)


    def get_template(self, uri):
        prefix = "salt://"
        salt_uri = uri if uri.startswith(prefix) else prefix+uri
        self.cache_file(salt_uri)
        return self.lookup.get_template(salt_uri[len(prefix):])


    def cache_file(self, fpath):
        if fpath not in self.cache:
            self.cache[fpath] = \
                    self.file_client.get_file(fpath, '', True, self.env)



