def __virtual__():
    """
    Only run on Linux systems
    """
    return 'netstat' if __grains__['kernel'] == 'Linux' else False

def s():
    """
    Return the statistics available in netstat -s.
    The netstat command is not needed: we use kernel-provided files directly.
    """
    stats = {}
    lines = open('/proc/net/netstat').readlines() + \
            open('/proc/net/snmp').readlines()

    currently_in_header_line = True
    for line in lines:
        sections = line.split(': ')
        prefix, list = sections[0], sections[1].strip()
        stats.setdefault(prefix, {})
        items = list.split(' ')
        if currently_in_header_line:
            headers = items
        else:
            for pos in range(len(headers)):
                stats[prefix][headers[pos]] = int(items[pos])
        currently_in_header_line = not currently_in_header_line

    return stats
