"""
Module to gather network configuration from Linux hosts
"""

import re
import subprocess

def __virtual__():
    """
    Only run on Linux systems
    """
    return 'netconfig' if __grains__['kernel'] == 'Linux' else False

# num name flags extra link addr brd
LINK_MATCHER = re.compile(r"""
    ^
            (?P<num>   [0-9]     +?) :
    \       (?P<name>  [^:]      +?) :
    \      <(?P<flags> [^>]      +?)>  # uppercase, comma-separated list of flags
    \       (?P<extra> .         *?)   # space-separated pairs of "key value"
    \ *\\\ *
    \ *link/(?P<link>  [^ ]      +?)
    \       (?P<addr>  [0-9a-f:] +?)
    \ brd\  (?P<brd>   [0-9a-f:] +?)
    $
    """, re.X | re.M)


# num name type addr brd? scope alias? extra?
ADDR_MATCHER = re.compile(r"""
    ^
             (?P<num>   [0-9]     +?) :
    \        (?P<name>  [^ ]       +)
    \ +
             (?P<type>  [^ ]       +)
    \        (?P<addr>  [^ ]       +)
    (?:
      \ brd\ (?P<brd>   [^ ]       +)
    )?
    \ scope\ (?P<scope> [^ ]       +)
    (?:
      \      (?P<alias> [^\\] [^ ] +)
    )?
    (?:
      \ \\\ +
             (?P<extra> .         *?)
    )?
    $
    """, re.X | re.M)

# addr dev lladdr? state?
NEIGH_MATCHER = re.compile(r"""
    ^
                (?P<addr> [^ ] +)
    \      dev\ (?P<dev>  [^ ] +)
    (?:
      \ lladdr\ (?P<lladdr> [^ ]+)
    )?
    \           (?P<state> [A-Z]+)?
    $
    """, re.X | re.M)



def _int_if_possible(string):
    """
    PRIVATE METHOD
    Tries to convert a string to an integer, falls back to the original value
    """
    try:
        return int(string)
    except ValueError:
        return string

def _dict_from_spaced_kv(string):
    """
    PRIVATE METHOD
    Turns a string "foo bar baz 0 trailing" into {'foo':'bar','baz':0}
    """
    list = string.split(' ')
    return dict([(list[n],_int_if_possible(list[n+1])) for n in range(0,len(list)/2*2,2)])

def _structured_link(match):
    """
    PRIVATE METHOD
    Turns a LINK_MATCHER match into structured data
    """

    res = (match.group('name'), {
        'num':   int(match.group('num')),
        'flags': match.group('flags').split(","),
        'link':  match.group('link'),
        'addr':  match.group('addr'),
        'brd':   match.group('brd') })

    extra = match.group('extra')
    if extra:
        res[1]['settings'] = _dict_from_spaced_kv(extra)

    return res

def _structured_addr(match):
    """
    PRIVATE METHOD
    Turns an ADDR_MATCHER match into structured data
    """

    res = (match.group('name'), {
        'addr':  match.group('addr'),
        'type':  match.group('type'),
        'scope': match.group('scope'),
    })

    brd   = match.group('brd')
    alias = match.group('alias')
    extra = match.group('extra')

    if brd:
        res[1]['brd'] = brd
    if alias:
        res[1]['alias'] = alias
    if extra:
        res[1]['settings'] = _dict_from_spaced_kv(extra)

    return res

def _structured_neigh(match):
    """
    PRIVATE METHOD
    Turns a NEIGH_MATCHER match into structured data
    """
    identifier = (match.group('addr'), match.group('dev'))
    infos = {}
    state  = match.group('state')
    lladdr = match.group('lladdr')
    if state:
        infos['state'] = state
    if lladdr:
        infos['lladdr'] = lladdr
    return identifier, infos

def _structured_links_output(output):
    """
    PRIVATE METHOD
    Return a dictionary mapping link names to link informations from the ip output
    """
    res = {}
    for line in iter(output.splitlines()):
        link_match = LINK_MATCHER.match(line)
        if link_match:
            name, infos = _structured_link(link_match)
            res[name] = infos

    return res

def _structured_addresses_output(output):
    """
    PRIVATE METHOD
    Return a dictionary mapping link names to addresses from the ip output
    """
    res = {}
    for line in iter(output.splitlines()):
        addr_match = ADDR_MATCHER.match(line)
        if addr_match:
            name, infos = _structured_addr(addr_match)
            res.setdefault(name, [])
            res[name].append(infos)

    return res

def _structured_neigh_output(output):
    """
    PRIVATE METHOD
    Return a dictionary mapping address and device to neighborhood information from the ip output
    """
    res = {}
    for line in iter(output.splitlines()):
        neigh_match = NEIGH_MATCHER.match(line)
        if neigh_match:
            identifier, infos = _structured_neigh(neigh_match)
            res[identifier] = infos

    return res

def links():
    """
    Return information about all network links on the system
    """
    output = __salt__['cmd.run']('ip -o link show')
    return _structured_links_output(output)

def link(name):
    """
    Return information about a given network link on the system
    """
    output = __salt__['cmd.run']('ip -o link show {0}'.format(name))
    match = LINK_MATCHER.match(output)
    if match:
        return _structured_link(LINK_MATCHER.match(output))

def addresses_with_options(options):
    """
    Return information about addresses for a given "ip addr show" set of options
    eg netconfig.addresses_with_options 'scope host'
    """
    output = __salt__['cmd.run']('ip -o addr show {0}'.format(options))
    return _structured_addresses_output(output)

def addresses():
    """
    Return information about addresses for all network links on the system
    """
    return addresses_with_options('')

def addresses_for(name):
    """
    Return information about addresses for a given network link on the system
    """
    parsed = addresses_with_options('dev {0}'.format(name))
    if parsed.has_key(name):
        return parsed[name]

def neighbours_with_options(options):
    """
    Return information about neighbours for a given "ip neigh show" set of options
    eg netconfig.neighbours_with_options 'nud noarp'
    """
    output = __salt__['cmd.run']('ip -o neigh show {0}'.format(options))
    return _structured_neigh_output(output)

def neighbours():
    """
    Return information about all known neighbours
    """
    return neighbours_with_options('')

def neighbours_for(name):
    """
    Return information about neighbours for a given network link on the system
    """
    return neighbours_with_options('dev {0}'.format(name))

def all_neighbours():
    """
    Return information about all attempted neighboors, including failed ones
    """
    return neighbours_with_options('nud all')

# TODO: brctl show
# TODO: ip maddr show
# TODO: ifenslave -a (not sure how parseable this is)

# For networking nerds:
#   TODO: brctl showmacs name
#   TODO: ip tunnel show
#   TODO: ip route show table all (looks like hell)
#   TODO: ip mroute show
