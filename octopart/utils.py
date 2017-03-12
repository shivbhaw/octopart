from collections import OrderedDict


def chunked(_list, chunksize=20):
    """
    Partitions list into chunks of a given size.

    NOTE: Octopart enforces that its 'parts/match' endpoint take no more
    than 20 queries in a single request.

    Args:
        _list (list): list to be partitioned
        chunksize (int): size of resulting chunks

    Returns:
        list of lists.
    """
    chunks = []
    for i in range(0, len(_list), chunksize):
        chunks.append(_list[i:i + chunksize])
    return chunks


def unique(_list):
    """
    Removes duplicate entries from list, keeping it in the original order.
    """
    return list(OrderedDict.fromkeys(_list))
